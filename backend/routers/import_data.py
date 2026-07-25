"""
数据导入 API路由
支持: CSV导入, API实时搜索
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import csv
import io
import json
import uuid
import logging
from pathlib import Path

from services.database import (
    get_conn, create_import_batch, update_import_batch, 
    batch_create_buyers, add_shipment, get_data_source
)
from services.sources import (
    create_source, get_all_sources, 
    VolzaSource, PanjivaSource, ImportGeniusSource
)
from services.sources.google_maps import GoogleMapsError
from services.ai_service import AIScorer

logger = logging.getLogger(__name__)

router = APIRouter()


class APISearchRequest(BaseModel):
    keyword: str
    country: Optional[str] = None
    source: str = "google_maps"
    limit: int = 100
    save_to_db: bool = True


class BatchScoreRequest(BaseModel):
    buyer_ids: List[int]
    model: Optional[str] = "gpt-4o"


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    source: str = Form("volza"),
    enable_ai_score: bool = Form(True)
):
    """
    CSV导入
    source: volza / panjiva / importgenius / manual
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    content = await file.read()
    csv_text = content.decode('utf-8', errors='ignore')
    
    # 解析CSV
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    
    if not rows:
        raise HTTPException(status_code=400, detail="CSV文件为空")
    
    # 创建导入批次
    with get_conn() as conn:
        batch_id = create_import_batch(conn, source, file.filename)
        update_import_batch(conn, batch_id, total=len(rows), status='processing')
    
    try:
        # 根据数据源解析
        source_instance = create_source(source)
        
        if source_instance:
            buyers_data = source_instance.parse_csv_data(rows)
        else:
            # 手动模式 - 通用字段映射
            buyers_data = _parse_manual_csv(rows)
        
        # 导入数据库
        with get_conn() as conn:
            success, failed = batch_create_buyers(conn, [b.to_dict() for b in buyers_data])
            
            # 更新批次状态
            update_import_batch(conn, batch_id, 
                               imported_records=success,
                               failed_records=failed,
                               status='completed')
        
        return {
            'batch_id': batch_id,
            'total': len(rows),
            'imported': success,
            'failed': failed,
            'message': f'导入完成，成功{success}条，失败{failed}条'
        }
    
    except Exception as e:
        with get_conn() as conn:
            update_import_batch(conn, batch_id, status='failed', error=str(e))
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


def _parse_manual_csv(rows: List[Dict]) -> List:
    """解析手动导入的CSV（通用格式）"""
    from services.sources.base import BuyerData
    
    buyers = {}
    
    for row in rows:
        company = (row.get('Company Name') or row.get('company_name') or 
                   row.get('公司名称') or row.get('company') or '')
        
        if not company:
            continue
        
        key = company.lower().strip()
        
        if key not in buyers:
            buyers[key] = BuyerData(
                company_name=company.strip(),
                country=row.get('Country') or row.get('country') or row.get('国家', ''),
                city=row.get('City') or row.get('city') or row.get('城市', ''),
                industry=row.get('Industry') or row.get('industry') or row.get('行业', ''),
                products=[],
                hs_code=[],
                website=row.get('Website') or row.get('website') or row.get('网站', ''),
                email=row.get('Email') or row.get('email') or row.get('邮箱', ''),
                phone=row.get('Phone') or row.get('phone') or row.get('电话', ''),
                whatsapp=row.get('WhatsApp') or row.get('whatsapp', ''),
                source='manual',
            )
        
        # 累加产品
        for field in ['Product', 'products', 'Products', '产品']:
            product = row.get(field, '')
            if product and product not in buyers[key].products:
                buyers[key].products.append(product)
        
        # HS Code
        for field in ['HS Code', 'hs_code', 'HSCODE']:
            hs = row.get(field, '')
            if hs and hs not in buyers[key].hs_code:
                buyers[key].hs_code.append(hs)
    
    return list(buyers.values())


def _load_source_config(source_name: str) -> Dict[str, Any]:
    """从数据库加载数据源配置"""
    source_record = get_data_source(source_name)
    if not source_record:
        return {}
    config = source_record.get('config', {})
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    return config if isinstance(config, dict) else {}


def _deduplicate_buyers(conn, buyers_data: List[Dict[str, Any]]) -> tuple:
    """
    去重逻辑，返回 (new_buyers, duplicate_count)
    去重优先级：
    1. source + source_id/place_id
    2. website 域名
    3. company_name + country + city
    4. phone
    """
    new_buyers = []
    duplicates = 0

    for buyer in buyers_data:
        is_dup = False

        # 1. source + source_id
        source_id = buyer.get('source_id')
        source = buyer.get('source', '')
        if source_id and source:
            cursor = conn.execute(
                "SELECT id FROM buyers WHERE source = ? AND source_url LIKE ?",
                (source, f"%{source_id}%")
            )
            if cursor.fetchone():
                is_dup = True

        # 2. website 域名
        if not is_dup and buyer.get('website'):
            domain = buyer['website'].replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            if domain:
                cursor = conn.execute(
                    "SELECT id FROM buyers WHERE website LIKE ?",
                    (f"%{domain}%",)
                )
                if cursor.fetchone():
                    is_dup = True

        # 3. company_name + country + city
        if not is_dup and buyer.get('company_name'):
            company = buyer['company_name'].strip().lower()
            country = (buyer.get('country') or '').strip().lower()
            city = (buyer.get('city') or '').strip().lower()
            cursor = conn.execute(
                "SELECT id FROM buyers WHERE LOWER(company_name) = ? AND LOWER(COALESCE(country,'')) = ? AND LOWER(COALESCE(city,'')) = ?",
                (company, country, city)
            )
            if cursor.fetchone():
                is_dup = True

        # 4. phone
        if not is_dup and buyer.get('phone'):
            phone_clean = buyer['phone'].replace(' ', '').replace('-', '')
            if len(phone_clean) >= 7:
                cursor = conn.execute(
                    "SELECT id FROM buyers WHERE REPLACE(REPLACE(phone, ' ', ''), '-', '') = ?",
                    (phone_clean,)
                )
                if cursor.fetchone():
                    is_dup = True

        if is_dup:
            duplicates += 1
        else:
            new_buyers.append(buyer)

    return new_buyers, duplicates


@router.post("/api-search")
async def api_search(request: APISearchRequest):
    """
    通过API搜索采购商（实时外部搜索）
    source: google_maps / serpapi / zoominfo / apollo
    """
    # 从数据库加载数据源配置
    source_config = _load_source_config(request.source)

    # 创建数据源实例（传入配置）
    source_instance = create_source(request.source, source_config)

    if not source_instance:
        return {
            'success': False,
            'source': request.source,
            'error_code': 'SOURCE_NOT_FOUND',
            'message': f'不支持的数据源: {request.source}',
            'detail': f'可用数据源: {", ".join(get_all_sources().keys())}'
        }

    # 验证配置
    valid, msg = source_instance.validate_config()
    if not valid:
        return {
            'success': False,
            'source': request.source,
            'error_code': 'CONFIG_INVALID',
            'message': msg,
            'detail': '请前往设置页面配置对应数据源的 API Key'
        }

    # 执行搜索
    try:
        # 使用异步搜索（如果适配器支持）
        if hasattr(source_instance, 'search_async'):
            results = await source_instance.search_async(
                keyword=request.keyword,
                country=request.country,
                limit=request.limit
            )
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: source_instance.search(
                    keyword=request.keyword,
                    country=request.country,
                    limit=request.limit
                )
            )
    except GoogleMapsError as e:
        return {
            'success': False,
            'source': request.source,
            'error_code': e.error_code,
            'message': e.message,
            'detail': e.detail
        }
    except Exception as e:
        logger.error(f"[api-search] {request.source} error: {e}")
        return {
            'success': False,
            'source': request.source,
            'error_code': 'SEARCH_FAILED',
            'message': f'搜索失败: {str(e)}',
            'detail': ''
        }

    # 搜索成功但无结果
    if not results:
        return {
            'success': True,
            'source': request.source,
            'found': 0,
            'imported': 0,
            'duplicates': 0,
            'data': [],
            'message': '本次搜索成功，但未找到匹配商户'
        }

    # 去重 + 保存
    imported = 0
    duplicates = 0

    if request.save_to_db:
        buyers_dicts = [b.to_dict() for b in results]
        with get_conn() as conn:
            new_buyers, duplicates = _deduplicate_buyers(conn, buyers_dicts)
            if new_buyers:
                imported, _ = batch_create_buyers(conn, new_buyers)

    return {
        'success': True,
        'source': request.source,
        'found': len(results),
        'imported': imported,
        'duplicates': duplicates,
        'data': [b.to_dict() for b in results],
    }


@router.post("/batch-score")
async def batch_score(request: BatchScoreRequest):
    """
    批量AI评分
    """
    from services.database import get_buyer, get_shipments, update_buyer, get_conn
    from services.ai_service import AIScorer
    
    # 获取配置
    with get_conn() as conn:
        config_str = conn.execute(
            "SELECT value FROM system_config WHERE key = 'ai_config'"
        ).fetchone()
    
    config = {}
    if config_str:
        try:
            config = json.loads(config_str[0])
        except:
            pass
    
    scorer = AIScorer(config)
    
    # 获取待评分采购商
    buyers_to_score = []
    with get_conn() as conn:
        for buyer_id in request.buyer_ids:
            buyer = get_buyer(conn, buyer_id)
            if buyer:
                shipments = get_shipments(conn, buyer_id)
                buyer['shipments'] = shipments
                buyers_to_score.append((buyer_id, buyer))
    
    if not buyers_to_score:
        raise HTTPException(status_code=400, detail="没有找到待评分的采购商")
    
    # 批量评分
    results = scorer.batch_score(buyers_to_score)
    
    # 更新数据库
    updated = 0
    with get_conn() as conn:
        for buyer_id, score_data in results.items():
            update_buyer(conn, buyer_id, {
                'ai_score': score_data.get('score', 0),
                'ai_level': score_data.get('level', 'C'),
                'buyer_type': score_data.get('buyer_type'),
                'risk_level': score_data.get('risk_level', 'medium'),
            })
            updated += 1
    
    return {
        'total': len(buyers_to_score),
        'scored': updated,
        'results': results
    }


@router.get("/batches")
async def list_batches(limit: int = 20):
    """导入批次列表"""
    with get_conn() as conn:
        batches = list_import_batches(conn, limit)
    return batches


@router.get("/sources")
async def list_sources():
    """可用数据源列表（含配置状态）"""
    sources_registry = get_all_sources()
    result = []

    with get_conn() as conn:
        cursor = conn.execute("SELECT * FROM data_sources ORDER BY priority")
        rows = cursor.fetchall()

        for row in rows:
            r = dict(row)
            config = {}
            if r.get('config'):
                try:
                    config = json.loads(r['config'])
                except:
                    config = {}

            # 判断是否已配置（有api_key）
            configured = bool(config.get('api_key') or config.get('client_id'))

            # 隐藏完整key
            safe_config = {}
            for k, v in config.items():
                if 'key' in k.lower() or 'secret' in k.lower():
                    safe_config[k] = (v[:6] + '***') if v and len(v) > 6 else ('***' if v else '')
                else:
                    safe_config[k] = v

            # 判断是否支持搜索（在注册表中有实现类即可）
            supports_search = r['name'] in sources_registry

            result.append({
                'name': r['name'],
                'display_name': r.get('display_name', r['name']),
                'api_type': r.get('api_type', 'api'),
                'enabled': bool(r.get('enabled', 1)),
                'configured': configured,
                'supports_search': supports_search,
                'config': safe_config,
            })

    return result


@router.get("/sources/{source_name}")
async def get_source_info(source_name: str):
    """获取数据源详情"""
    sources = get_all_sources()
    
    if source_name not in sources:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM data_sources WHERE name = ?", (source_name,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="数据源配置不存在")
        
        result = dict(row)
        if result.get('config'):
            try:
                result['config'] = json.loads(result['config'])
            except:
                result['config'] = {}
    
    return result


def list_import_batches(conn, limit=20):
    """导入批次列表（内部函数）"""
    cursor = conn.execute(
        "SELECT * FROM import_batches ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    return [dict(row) for row in cursor.fetchall()]

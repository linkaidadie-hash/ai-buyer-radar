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
from pathlib import Path

from services.database import (
    get_conn, create_import_batch, update_import_batch, 
    batch_create_buyers, add_shipment
)
from services.sources import (
    create_source, get_all_sources, 
    VolzaSource, PanjivaSource, ImportGeniusSource
)
from services.ai_service import AIScorer

router = APIRouter()


class APISearchRequest(BaseModel):
    keyword: str
    country: Optional[str] = None
    source: str = "google_maps"
    limit: int = 100


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


@router.post("/api-search")
async def api_search(request: APISearchRequest):
    """
    通过API搜索采购商
    source: google_maps / linkedin / zoominfo / apollo
    """
    source_instance = create_source(request.source)
    
    if not source_instance:
        raise HTTPException(status_code=400, detail=f"不支持的数据源: {request.source}")
    
    # 验证配置
    valid, msg = source_instance.validate_config()
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    # 搜索
    results = source_instance.search(
        keyword=request.keyword,
        country=request.country,
        limit=request.limit
    )
    
    # 导入数据库
    if results:
        with get_conn() as conn:
            success, failed = batch_create_buyers(
                conn, [b.to_dict() for b in results]
            )
        
        return {
            'found': len(results),
            'imported': success,
            'data': [b.to_dict() for b in results[:10]]  # 返回前10条预览
        }
    
    return {'found': 0, 'imported': 0, 'data': []}


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
    """可用数据源列表"""
    sources = get_all_sources()
    result = []
    
    with get_conn() as conn:
        from services.database import rows_to_list
        cursor = conn.execute("SELECT * FROM data_sources ORDER BY priority")
        rows = cursor.fetchall()
        
        for row in rows:
            r = dict(row)
            if r.get('config'):
                try:
                    r['config'] = json.loads(r['config'])
                except:
                    r['config'] = {}
            result.append(r)
    
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
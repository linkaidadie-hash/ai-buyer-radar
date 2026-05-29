"""
AI评分 & 联系辅助 API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

from services.database import get_conn, get_buyer, get_shipments, update_buyer, rows_to_list
from services.ai_service import AIScorer, AIOutreachGenerator

router = APIRouter()


class ScoreRequest(BaseModel):
    buyer_id: int


class BatchScoreRequest(BaseModel):
    buyer_ids: List[int]


class OutreachRequest(BaseModel):
    buyer_id: int
    channel: str = "email"  # email / whatsapp / linkedin / followup
    product: Optional[str] = None
    language: str = "en"


@router.post("/score")
async def score_buyer(request: ScoreRequest):
    """AI单条评分"""
    from services.database import get_buyer, get_shipments
    
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
    
    # 获取采购商数据
    with get_conn() as conn:
        buyer = get_buyer(conn, request.buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        
        shipments = get_shipments(conn, request.buyer_id)
        buyer['shipments'] = shipments
    
    # AI评分
    result = scorer.score_buyer(buyer)
    
    # 更新数据库
    with get_conn() as conn:
        update_buyer(conn, request.buyer_id, {
            'ai_score': result.get('score', 0),
            'ai_level': result.get('level', 'C'),
            'buyer_type': result.get('buyer_type'),
            'risk_level': result.get('risk_level', 'medium'),
        })
    
    return result


@router.post("/batch-score")
async def batch_score(request: BatchScoreRequest):
    """批量AI评分"""
    from services.database import get_buyer, get_shipments
    
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
    buyers_data = []
    with get_conn() as conn:
        for buyer_id in request.buyer_ids:
            buyer = get_buyer(conn, buyer_id)
            if buyer:
                shipments = get_shipments(conn, buyer_id)
                buyer['shipments'] = shipments
                buyers_data.append((buyer_id, buyer))
    
    if not buyers_data:
        raise HTTPException(status_code=400, detail="没有找到待评分的采购商")
    
    # 批量评分
    def progress_callback(current, total):
        print(f"[AI] Scoring: {current}/{total}")
    
    results = scorer.batch_score(buyers_data, progress_callback)
    
    # 批量更新数据库
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
        'total': len(buyers_data),
        'scored': updated,
        'results': results
    }


@router.post("/outreach")
async def generate_outreach(request: OutreachRequest):
    """生成联系话术"""
    from services.database import get_buyer
    
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
    
    generator = AIOutreachGenerator(config)
    
    # 获取采购商
    with get_conn() as conn:
        buyer = get_buyer(conn, request.buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
    
    # 生成话术
    if request.channel == 'email':
        content = generator.generate_email(
            buyer, request.product, request.language
        )
        return {'channel': 'email', 'content': content}
    
    elif request.channel == 'whatsapp':
        content = generator.generate_whatsapp(
            buyer, request.product, request.language
        )
        return {'channel': 'whatsapp', 'content': content}
    
    elif request.channel == 'linkedin':
        result = generator.generate_linkedin_request(
            buyer, request.product, request.language
        )
        return {'channel': 'linkedin', **result}
    
    elif request.channel == 'followup':
        content = generator.generate_followup(
            buyer, 'email', request.language
        )
        return {'channel': 'followup', 'content': content}
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的渠道: {request.channel}")


@router.get("/outreach/channels")
async def list_channels():
    """支持的联系渠道"""
    return [
        {'value': 'email', 'label': '邮件', 'description': '开发信邮件'},
        {'value': 'whatsapp', 'label': 'WhatsApp', 'description': 'WhatsApp消息'},
        {'value': 'linkedin', 'label': 'LinkedIn', 'description': 'LinkedIn连接请求'},
        {'value': 'followup', 'label': '跟进', 'description': '二次跟进话术'},
    ]


@router.get("/outreach/languages")
async def list_languages():
    """支持的语言"""
    return [
        {'value': 'en', 'label': 'English'},
        {'value': 'ar', 'label': 'العربية (Arabic)'},
        {'value': 'fr', 'label': 'Français'},
        {'value': 'es', 'label': 'Español'},
        {'value': 'zh', 'label': '中文'},
        {'value': 'ru', 'label': 'Русский'},
        {'value': 'pt', 'label': 'Português'},
        {'value': 'de', 'label': 'Deutsch'},
    ]


@router.get("/templates")
async def list_ai_templates():
    """AI提示词模板列表"""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM ai_templates WHERE enabled = 1"
        )
        rows = cursor.fetchall()
    
    templates = []
    for row in rows:
        r = dict(row)
        if r.get('variables'):
            try:
                r['variables'] = json.loads(r['variables'])
            except:
                r['variables'] = []
        templates.append(r)
    
    return templates


@router.put("/templates/{template_id}")
async def update_template(template_id: int, data: Dict[str, Any]):
    """更新AI模板"""
    with get_conn() as conn:
        update_fields = []
        values = []
        
        for field in ['prompt_template', 'model', 'temperature', 'max_tokens', 'enabled']:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])
        
        if update_fields:
            update_fields.append("updated_at = datetime('now')")
            values.append(template_id)
            sql = f"UPDATE ai_templates SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(sql, values)
    
    return {'message': '更新成功'}
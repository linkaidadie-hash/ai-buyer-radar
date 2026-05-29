"""
采购商管理 API路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

from services.database import (
    get_conn, create_buyer, get_buyer, update_buyer, delete_buyer,
    list_buyers, get_shipments, get_contacts, get_followups,
    add_shipment, add_contact, add_followup, get_stats
)

router = APIRouter()


class BuyerCreate(BaseModel):
    company_name: str
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    products: Optional[List[str]] = None
    hs_code: Optional[List[str]] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None


class BuyerUpdate(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    products: Optional[List[str]] = None
    hs_code: Optional[List[str]] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ShipmentCreate(BaseModel):
    product: str
    hs_code: Optional[str] = None
    supplier: Optional[str] = None
    origin_country: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    date: Optional[str] = None
    value: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class ContactCreate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    source: Optional[str] = None
    is_primary: Optional[int] = 0


class FollowupCreate(BaseModel):
    method: str
    subject: Optional[str] = None
    content: str
    result: Optional[str] = None
    next_followup: Optional[str] = None
    followup_date: Optional[str] = None


@router.get("/list")
async def list_buyers_api(
    country: Optional[str] = None,
    status: Optional[str] = None,
    ai_level: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """采购商列表"""
    filters = {}
    if country: filters['country'] = country
    if status: filters['status'] = status
    if ai_level: filters['ai_level'] = ai_level
    if source: filters['source'] = source
    if search: filters['search'] = search
    
    with get_conn() as conn:
        data, total = list_buyers(conn, filters, page, page_size)
    
    return {
        'data': data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }


@router.get("/{buyer_id}")
async def get_buyer_api(buyer_id: int):
    """获取采购商详情"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        
        # 同时获取关联数据
        shipments = get_shipments(conn, buyer_id)
        contacts = get_contacts(conn, buyer_id)
        followups = get_followups(conn, buyer_id)
    
    buyer['shipments'] = shipments
    buyer['contacts'] = contacts
    buyer['followups'] = followups
    
    # 解析JSON字段
    for field in ['products', 'hs_code']:
        if buyer.get(field):
            try:
                buyer[field] = json.loads(buyer[field])
            except:
                buyer[field] = []
    
    return buyer


@router.post("")
async def create_buyer_api(data: BuyerCreate):
    """创建采购商"""
    with get_conn() as conn:
        buyer_id = create_buyer(conn, data.model_dump(exclude_none=True))
    
    return {'id': buyer_id, 'message': '创建成功'}


@router.put("/{buyer_id}")
async def update_buyer_api(buyer_id: int, data: BuyerUpdate):
    """更新采购商"""
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有要更新的字段")
    
    with get_conn() as conn:
        success = update_buyer(conn, buyer_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="采购商不存在")
    
    return {'message': '更新成功'}


@router.delete("/{buyer_id}")
async def delete_buyer_api(buyer_id: int):
    """删除采购商"""
    with get_conn() as conn:
        success = delete_buyer(conn, buyer_id)
        if not success:
            raise HTTPException(status_code=404, detail="采购商不存在")
    
    return {'message': '删除成功'}


@router.post("/{buyer_id}/shipments")
async def add_shipment_api(buyer_id: int, data: ShipmentCreate):
    """添加进口记录"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        
        shipment_id = add_shipment(conn, buyer_id, data.model_dump())
    
    return {'id': shipment_id, 'message': '添加成功'}


@router.post("/{buyer_id}/contacts")
async def add_contact_api(buyer_id: int, data: ContactCreate):
    """添加联系人"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        
        contact_id = add_contact(conn, buyer_id, data.model_dump())
    
    return {'id': contact_id, 'message': '添加成功'}


@router.post("/{buyer_id}/followups")
async def add_followup_api(buyer_id: int, data: FollowupCreate):
    """添加跟进记录"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        
        followup_id = add_followup(conn, buyer_id, data.model_dump())
        
        # 如果设置了下次跟进时间，更新采购商状态
        if data.followup_date:
            update_buyer(conn, buyer_id, {'status': 'contacted'})
    
    return {'id': followup_id, 'message': '添加成功'}


@router.get("/{buyer_id}/shipments")
async def get_shipments_api(buyer_id: int):
    """获取进口记录"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        shipments = get_shipments(conn, buyer_id)
    return shipments


@router.get("/{buyer_id}/contacts")
async def get_contacts_api(buyer_id: int):
    """获取联系人"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        contacts = get_contacts(conn, buyer_id)
    return contacts


@router.get("/{buyer_id}/followups")
async def get_followups_api(buyer_id: int):
    """获取跟进记录"""
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        followups = get_followups(conn, buyer_id)
    return followups


@router.get("/stats/summary")
async def get_stats_api():
    """获取统计数据"""
    return get_stats()


@router.get("/status/list")
async def list_status():
    """获取所有状态选项"""
    return [
        {'value': 'new', 'label': '新增'},
        {'value': 'contacted', 'label': '已联系'},
        {'value': 'replied', 'label': '已回复'},
        {'value': 'interested', 'label': '有意向'},
        {'value': 'quoted', 'label': '已报价'},
        {'value': 'closed', 'label': '已成交'},
        {'value': 'invalid', 'label': '无效'},
        {'value': 'blacklist', 'label': '黑名单'},
    ]


@router.get("/level/list")
async def list_levels():
    """获取所有等级选项"""
    return [
        {'value': 'A', 'label': 'A级 - 优先跟进'},
        {'value': 'B', 'label': 'B级 - 重点跟进'},
        {'value': 'C', 'label': 'C级 - 普通跟进'},
        {'value': 'D', 'label': 'D级 - 暂不跟进'},
    ]
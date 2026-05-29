"""
报价相关API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from services.quote_service import ProductService, QuoteService, OrderService, ShippingService
from services.database import get_conn

router = APIRouter()


# ============================================================
# 产品管理
# ============================================================

class ProductCreate(BaseModel):
    name_cn: Optional[str] = None
    name_en: Optional[str] = None
    sku: str
    cost_price: float
    moq: int = 100
    unit: str = 'pcs'
    length_cm: float = 0
    width_cm: float = 0
    height_cm: float = 0
    weight_kg: float = 0
    profit_rate: float = 30
    category: Optional[str] = None
    description: Optional[str] = None


@router.get("/products")
async def list_products(category: Optional[str] = None):
    """产品列表"""
    service = ProductService()
    return service.list_products(category)


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """获取产品"""
    service = ProductService()
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product


@router.post("/products")
async def create_product(data: ProductCreate):
    """添加产品"""
    service = ProductService()
    product_id = service.add_product(data.model_dump())
    return {"id": product_id, "message": "添加成功"}


# ============================================================
# AI报价
# ============================================================

class QuoteRequest(BaseModel):
    items: List[Dict[str, Any]]  # [{product_id, quantity, unit_price(可选)}]
    country: str
    shipping_method: str = 'sea'
    price_term: str = 'FOB Shanghai'
    port_from: str = 'Shanghai'


@router.post("/calculate")
async def calculate_quote(request: QuoteRequest):
    """计算报价"""
    service = QuoteService()
    result = service.calculate_quote(
        items=request.items,
        country=request.country,
        shipping_method=request.shipping_method,
        price_term=request.price_term,
        port_from=request.port_from
    )
    return result


# ============================================================
# 报价单
# ============================================================

class QuotationCreate(BaseModel):
    buyer_name: str
    buyer_country: str
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    items: List[Dict[str, Any]]
    country: str
    shipping_method: str = 'sea'


@router.post("/quotations")
async def create_quotation(request: QuotationCreate):
    """创建报价单"""
    service = QuoteService()
    buyer = {
        'name': request.buyer_name,
        'country': request.buyer_country,
        'phone': request.buyer_phone,
        'email': request.buyer_email
    }
    result = service.create_quotation(
        buyer=buyer,
        items=request.items,
        country=request.country,
        shipping_method=request.shipping_method
    )
    return result


@router.get("/quotations/{quotation_id}")
async def get_quotation(quotation_id: int):
    """获取报价单"""
    service = QuoteService()
    quotation = service.get_quotation(quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="报价单不存在")
    return quotation


@router.get("/quotations")
async def list_quotations(limit: int = 50):
    """报价单列表"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM quotations 
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        result = []
        for row in rows:
            r = dict(row)
            r['items'] = json.loads(r['items'])
            result.append(r)
        return result


# ============================================================
# 订单
# ============================================================

class OrderCreate(BaseModel):
    quotation_id: Optional[int] = None
    buyer_name: str
    buyer_country: str
    items: List[Dict[str, Any]]
    total_amount: float


@router.post("/orders")
async def create_order(request: OrderCreate):
    """创建订单"""
    service = OrderService()
    buyer = {
        'name': request.buyer_name,
        'country': request.buyer_country,
    }
    result = service.create_order(
        quotation_id=request.quotation_id,
        buyer=buyer,
        items=request.items,
        total_amount=request.total_amount
    )
    return result


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str):
    """更新订单状态"""
    service = OrderService()
    success = service.update_status(order_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"message": "状态已更新"}


@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    """获取订单"""
    service = OrderService()
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.get("/orders")
async def list_orders(status: Optional[str] = None, limit: int = 50):
    """订单列表"""
    service = OrderService()
    return service.list_orders(status, limit)


# ============================================================
# 运费
# ============================================================

@router.get("/shipping/rates")
async def list_shipping_rates(country: Optional[str] = None):
    """运费列表"""
    service = ShippingService()
    return service.list_rates(country)


@router.get("/shipping/quote")
async def get_shipping_quote(
    country: str,
    method: str = 'sea',
    volume_m3: float = 0,
    weight_kg: float = 0
):
    """计算运费"""
    service = ShippingService()
    return service.get_quote(country, method, volume_m3, weight_kg)


# ============================================================
# 国家港口
# ============================================================

@router.get("/countries")
async def list_countries():
    """常用国家列表"""
    return [
        {'code': 'NG', 'name': 'Nigeria', 'port': 'Lagos (Apapa)'},
        {'code': 'GH', 'name': 'Ghana', 'port': 'Accra'},
        {'code': 'KE', 'name': 'Kenya', 'port': 'Mombasa'},
        {'code': 'ZA', 'name': 'South Africa', 'port': 'Durban'},
        {'code': 'AE', 'name': 'UAE', 'port': 'Dubai (Jebel Ali)'},
        {'code': 'SA', 'name': 'Saudi Arabia', 'port': 'Jeddah'},
        {'code': 'EG', 'name': 'Egypt', 'port': 'Port Said'},
        {'code': 'TZ', 'name': 'Tanzania', 'port': 'Dar es Salaam'},
        {'code': 'MY', 'name': 'Malaysia', 'port': 'Kuala Lumpur'},
        {'code': 'ID', 'name': 'Indonesia', 'port': 'Jakarta'},
        {'code': 'VN', 'name': 'Vietnam', 'port': 'Ho Chi Minh City'},
        {'code': 'PH', 'name': 'Philippines', 'port': 'Manila'},
        {'code': 'PK', 'name': 'Pakistan', 'port': 'Karachi'},
        {'code': 'IN', 'name': 'India', 'port': 'Mumbai'},
    ]


@router.get("/order/statuses")
async def list_order_statuses():
    """订单状态列表"""
    return [
        {'value': 'inquiry', 'label': '询盘中'},
        {'value': 'quote', 'label': '已报价'},
        {'value': 'sample', 'label': '打样中'},
        {'value': 'payment', 'label': '待付款'},
        {'value': 'production', 'label': '生产中'},
        {'value': 'shipped', 'label': '已发货'},
        {'value': 'delivered', 'label': '已到港'},
        {'value': 'completed', 'label': '已完成'},
        {'value': 'cancelled', 'label': '已取消'},
    ]
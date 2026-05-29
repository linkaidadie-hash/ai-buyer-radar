"""导出管理路由"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, List
import csv
import io
from pathlib import Path
from datetime import datetime

router = APIRouter()

EXPORT_DIR = Path(__file__).parent.parent.parent.parent / "exports"


@router.get("/buyers/csv")
async def export_buyers_csv(
    country: Optional[str] = None,
    status: Optional[str] = None,
    ai_level: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None
):
    """导出采购商CSV"""
    from services.database import get_conn, list_buyers
    
    filters = {}
    if country: filters['country'] = country
    if status: filters['status'] = status
    if ai_level: filters['ai_level'] = ai_level
    if source: filters['source'] = source
    if search: filters['search'] = search
    
    with get_conn() as conn:
        buyers, _ = list_buyers(conn, filters, page=1, page_size=10000)
    
    # 生成CSV
    output = io.StringIO()
    fieldnames = ['id', 'company_name', 'country', 'city', 'industry', 
                 'products', 'website', 'email', 'phone', 'whatsapp',
                 'linkedin', 'source', 'ai_score', 'ai_level', 'status']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for buyer in buyers:
        row = buyer.copy()
        # JSON字段处理
        if isinstance(row.get('products'), str):
            import json
            try:
                row['products'] = '|'.join(json.loads(row['products']))
            except:
                row['products'] = row['products']
        writer.writerow(row)
    
    # 保存文件
    EXPORT_DIR.mkdir(exist_ok=True)
    filename = f"buyers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = EXPORT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(output.getvalue())
    
    return FileResponse(
        filepath,
        media_type='text/csv',
        filename=filename
    )


@router.get("/buyers/excel")
async def export_buyers_excel(
    country: Optional[str] = None,
    status: Optional[str] = None,
    ai_level: Optional[str] = None,
    source: Optional[str] = None
):
    """导出采购商Excel（需安装openpyxl）"""
    try:
        from openpyxl import Workbook
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl未安装，请使用CSV导出")
    
    from services.database import get_conn, list_buyers
    
    filters = {}
    if country: filters['country'] = country
    if status: filters['status'] = status
    if ai_level: filters['ai_level'] = ai_level
    if source: filters['source'] = source
    
    with get_conn() as conn:
        buyers, _ = list_buyers(conn, filters, page=1, page_size=10000)
    
    # 创建Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "采购商"
    
    # 表头
    headers = ['ID', '公司名称', '国家', '城市', '行业', '产品', 
               '网站', '邮箱', '电话', 'WhatsApp', 'LinkedIn',
               '数据源', 'AI评分', 'AI等级', '状态']
    ws.append(headers)
    
    # 数据
    for buyer in buyers:
        ws.append([
            buyer.get('id'),
            buyer.get('company_name'),
            buyer.get('country'),
            buyer.get('city'),
            buyer.get('industry'),
            buyer.get('products'),
            buyer.get('website'),
            buyer.get('email'),
            buyer.get('phone'),
            buyer.get('whatsapp'),
            buyer.get('linkedin'),
            buyer.get('source'),
            buyer.get('ai_score'),
            buyer.get('ai_level'),
            buyer.get('status'),
        ])
    
    # 保存
    EXPORT_DIR.mkdir(exist_ok=True)
    filename = f"buyers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = EXPORT_DIR / filename
    wb.save(filepath)
    
    return FileResponse(filepath, media_type='application/xlsx', filename=filename)


@router.get("/history")
async def get_export_history(limit: int = 20):
    """导出历史记录"""
    # 简单实现：读取导出目录下的文件
    EXPORT_DIR.mkdir(exist_ok=True)
    files = []
    
    for f in sorted(EXPORT_DIR.glob("buyers_export_*.csv"), reverse=True)[:limit]:
        files.append({
            'filename': f.name,
            'size': f.stat().st_size,
            'created': datetime.fromtimestamp(f.stat().st_ctime).isoformat()
        })
    
    return files
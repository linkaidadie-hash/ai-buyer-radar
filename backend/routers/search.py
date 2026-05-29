"""采购商搜索路由"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

router = APIRouter()


@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=1),
    country: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """快速搜索采购商"""
    from services.database import get_conn, rows_to_list
    
    with get_conn() as conn:
        sql = """
        SELECT id, company_name, country, city, industry, ai_score, ai_level, status
        FROM buyers
        WHERE company_name LIKE ? OR products LIKE ? OR industry LIKE ?
        """
        params = [f"%{q}%", f"%{q}%", f"%{q}%"]
        
        if country:
            sql += " AND country = ?"
            params.append(country)
        
        sql += " ORDER BY ai_score DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(sql, params)
        return cursor.fetchall()


@router.get("/advanced")
async def advanced_search(
    keyword: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    ai_level: Optional[str] = None,
    ai_score_min: Optional[int] = None,
    ai_score_max: Optional[int] = None,
    source: Optional[str] = None,
    has_email: Optional[bool] = None,
    has_phone: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """高级搜索"""
    from services.database import get_conn
    
    where_clauses = []
    params = []
    
    if keyword:
        where_clauses.append("(company_name LIKE ? OR products LIKE ? OR industry LIKE ?)")
        k = f"%{keyword}%"
        params.extend([k, k, k])
    
    if country:
        where_clauses.append("country = ?")
        params.append(country)
    
    if industry:
        where_clauses.append("industry = ?")
        params.append(industry)
    
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    
    if ai_level:
        where_clauses.append("ai_level = ?")
        params.append(ai_level)
    
    if ai_score_min is not None:
        where_clauses.append("ai_score >= ?")
        params.append(ai_score_min)
    
    if ai_score_max is not None:
        where_clauses.append("ai_score <= ?")
        params.append(ai_score_max)
    
    if source:
        where_clauses.append("source = ?")
        params.append(source)
    
    if has_email:
        where_clauses.append("email IS NOT NULL AND email != ''")
    
    if has_phone:
        where_clauses.append("phone IS NOT NULL AND phone != ''")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    with get_conn() as conn:
        # Count
        count_sql = f"SELECT COUNT(*) FROM buyers WHERE {where_sql}"
        cursor = conn.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        # Data
        offset = (page - 1) * page_size
        sql = f"""
        SELECT * FROM buyers
        WHERE {where_sql}
        ORDER BY ai_score DESC
        LIMIT ? OFFSET ?
        """
        cursor = conn.execute(sql, params + [page_size, offset])
        rows = [dict(row) for row in cursor.fetchall()]
    
    return {
        'data': rows,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }


@router.get("/countries")
async def get_countries():
    """获取所有国家列表"""
    from services.database import get_conn
    
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT country, COUNT(*) as count 
            FROM buyers 
            WHERE country IS NOT NULL AND country != ''
            GROUP BY country 
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        return [{'country': row[0], 'count': row[1]} for row in rows]


@router.get("/industries")
async def get_industries():
    """获取所有行业列表"""
    from services.database import get_conn
    
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT industry, COUNT(*) as count 
            FROM buyers 
            WHERE industry IS NOT NULL AND industry != ''
            GROUP BY industry 
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        return [{'industry': row[0], 'count': row[1]} for row in rows]


@router.get("/sources")
async def get_sources():
    """获取所有数据源列表"""
    from services.database import get_conn
    
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT source, COUNT(*) as count 
            FROM buyers 
            WHERE source IS NOT NULL AND source != ''
            GROUP BY source 
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        return [{'source': row[0], 'count': row[1]} for row in rows]
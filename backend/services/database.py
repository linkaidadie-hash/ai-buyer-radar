"""
数据库服务 - SQLite
"""
import sqlite3
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "database" / "buyers.db"


def get_db_path():
    """获取数据库路径"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_conn():
    """获取数据库连接上下文"""
    conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库"""
    # 主schema
    schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"
    if schema_path.exists():
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        with get_conn() as conn:
            conn.executescript(schema)
    
    # 报价schema
    schema_quote_path = Path(__file__).parent.parent.parent / "database" / "schema_quote.sql"
    if schema_quote_path.exists():
        with open(schema_quote_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        with get_conn() as conn:
            conn.executescript(schema)
    
    print(f"[DB] 数据库初始化完成: {get_db_path()}")


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """将Row转为字典"""
    if row is None:
        return {}
    return dict(row)


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """将Rows列表转为字典列表"""
    return [row_to_dict(row) for row in rows]


# ============================================================
# 采购商 (Buyers) CRUD
# ============================================================

def create_buyer(conn: sqlite3.Connection, data: Dict[str, Any]) -> int:
    """创建采购商"""
    data.setdefault('id', None)
    data.setdefault('ai_score', 0)
    data.setdefault('ai_level', 'C')
    data.setdefault('risk_level', 'medium')
    data.setdefault('status', 'new')
    data.setdefault('created_at', datetime.now().isoformat())
    data.setdefault('updated_at', datetime.now().isoformat())
    
    # JSON字段
    for field in ['products', 'hs_code']:
        if field in data and not isinstance(data[field], str):
            data[field] = json.dumps(data[field], ensure_ascii=False)
    
    sql = """
    INSERT INTO buyers (company_name, country, city, industry, products, hs_code,
        website, email, phone, whatsapp, linkedin, facebook,
        source, source_url, ai_score, ai_level, buyer_type, risk_level,
        status, notes, import_batch, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor = conn.execute(sql, (
        data['company_name'], data.get('country'), data.get('city'),
        data.get('industry'), data.get('products'), data.get('hs_code'),
        data.get('website'), data.get('email'), data.get('phone'),
        data.get('whatsapp'), data.get('linkedin'), data.get('facebook'),
        data.get('source'), data.get('source_url'), data.get('ai_score'),
        data.get('ai_level'), data.get('buyer_type'), data.get('risk_level'),
        data.get('status'), data.get('notes'), data.get('import_batch'),
        data.get('created_at'), data.get('updated_at')
    ))
    return cursor.lastrowid


def get_buyer(conn: sqlite3.Connection, buyer_id: int) -> Optional[Dict[str, Any]]:
    """获取单个采购商"""
    cursor = conn.execute("SELECT * FROM buyers WHERE id = ?", (buyer_id,))
    row = cursor.fetchone()
    return row_to_dict(row)


def update_buyer(conn: sqlite3.Connection, buyer_id: int, data: Dict[str, Any]) -> bool:
    """更新采购商"""
    data['updated_at'] = datetime.now().isoformat()
    
    # JSON字段
    for field in ['products', 'hs_code']:
        if field in data and not isinstance(data[field], str):
            data[field] = json.dumps(data[field], ensure_ascii=False)
    
    set_clauses = [f"{k} = ?" for k in data.keys()]
    set_clauses.append("updated_at = ?")
    
    sql = f"UPDATE buyers SET {', '.join(set_clauses)} WHERE id = ?"
    values = list(data.values()) + [data['updated_at'], buyer_id]
    
    cursor = conn.execute(sql, values)
    return cursor.rowcount > 0


def delete_buyer(conn: sqlite3.Connection, buyer_id: int) -> bool:
    """删除采购商"""
    cursor = conn.execute("DELETE FROM buyers WHERE id = ?", (buyer_id,))
    return cursor.rowcount > 0


def list_buyers(conn: sqlite3.Connection, filters: Dict[str, Any] = None, 
                page: int = 1, page_size: int = 20) -> tuple[List[Dict], int]:
    """采购商列表（支持分页和筛选）"""
    filters = filters or {}
    
    where_clauses = []
    values = []
    
    if filters.get('country'):
        where_clauses.append("country = ?")
        values.append(filters['country'])
    if filters.get('status'):
        where_clauses.append("status = ?")
        values.append(filters['status'])
    if filters.get('ai_level'):
        where_clauses.append("ai_level = ?")
        values.append(filters['ai_level'])
    if filters.get('source'):
        where_clauses.append("source = ?")
        values.append(filters['source'])
    if filters.get('search'):
        where_clauses.append("(company_name LIKE ? OR products LIKE ?)")
        search_term = f"%{filters['search']}%"
        values.extend([search_term, search_term])
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # 总数
    count_sql = f"SELECT COUNT(*) FROM buyers WHERE {where_sql}"
    cursor = conn.execute(count_sql, values)
    total = cursor.fetchone()[0]
    
    # 分页
    offset = (page - 1) * page_size
    sql = f"""
    SELECT * FROM buyers 
    WHERE {where_sql}
    ORDER BY ai_score DESC, updated_at DESC
    LIMIT ? OFFSET ?
    """
    cursor = conn.execute(sql, values + [page_size, offset])
    rows = cursor.fetchall()
    
    return rows_to_list(rows), total


def batch_create_buyers(conn: sqlite3.Connection, buyers_data: List[Dict[str, Any]]) -> tuple[int, int]:
    """批量创建采购商，返回 (成功数, 失败数)"""
    success = 0
    failed = 0
    batch_id = str(uuid.uuid4())[:8]
    
    for data in buyers_data:
        data['import_batch'] = batch_id
        try:
            create_buyer(conn, data)
            success += 1
        except Exception as e:
            failed += 1
            print(f"[DB] 创建采购商失败: {data.get('company_name')} - {e}")
    
    return success, failed


# ============================================================
# 进口记录 (Shipment Records)
# ============================================================

def add_shipment(conn: sqlite3.Connection, buyer_id: int, data: Dict[str, Any]) -> int:
    """添加进口记录"""
    sql = """
    INSERT INTO shipment_records (buyer_id, product, hs_code, supplier, origin_country,
        quantity, unit, date, value, source, source_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor = conn.execute(sql, (
        buyer_id, data.get('product'), data.get('hs_code'), data.get('supplier'),
        data.get('origin_country'), data.get('quantity'), data.get('unit'),
        data.get('date'), data.get('value'), data.get('source'), data.get('source_url')
    ))
    return cursor.lastrowid


def get_shipments(conn: sqlite3.Connection, buyer_id: int) -> List[Dict[str, Any]]:
    """获取采购商的进口记录"""
    cursor = conn.execute(
        "SELECT * FROM shipment_records WHERE buyer_id = ? ORDER BY date DESC",
        (buyer_id,)
    )
    return rows_to_list(cursor.fetchall())


# ============================================================
# 联系人 (Contacts)
# ============================================================

def add_contact(conn: sqlite3.Connection, buyer_id: int, data: Dict[str, Any]) -> int:
    """添加联系人"""
    sql = """
    INSERT INTO contacts (buyer_id, name, position, department, email, phone,
        mobile, whatsapp, linkedin, source, is_primary)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor = conn.execute(sql, (
        buyer_id, data.get('name'), data.get('position'), data.get('department'),
        data.get('email'), data.get('phone'), data.get('mobile'),
        data.get('whatsapp'), data.get('linkedin'), data.get('source'),
        data.get('is_primary', 0)
    ))
    return cursor.lastrowid


def get_contacts(conn: sqlite3.Connection, buyer_id: int) -> List[Dict[str, Any]]:
    """获取采购商的联系人"""
    cursor = conn.execute(
        "SELECT * FROM contacts WHERE buyer_id = ? ORDER BY is_primary DESC, id ASC",
        (buyer_id,)
    )
    return rows_to_list(cursor.fetchall())


def update_contact(conn: sqlite3.Connection, contact_id: int, data: Dict[str, Any]) -> bool:
    """更新联系人"""
    data['updated_at'] = datetime.now().isoformat()
    set_clauses = [f"{k} = ?" for k in data.keys()]
    set_clauses.append("updated_at = ?")
    
    sql = f"UPDATE contacts SET {', '.join(set_clauses)} WHERE id = ?"
    values = list(data.values()) + [data['updated_at'], contact_id]
    
    cursor = conn.execute(sql, values)
    return cursor.rowcount > 0


# ============================================================
# 跟进记录 (Followups)
# ============================================================

def add_followup(conn: sqlite3.Connection, buyer_id: int, data: Dict[str, Any]) -> int:
    """添加跟进记录"""
    sql = """
    INSERT INTO followups (buyer_id, date, method, subject, content, result,
        next_followup, followup_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor = conn.execute(sql, (
        buyer_id, data.get('date', datetime.now().strftime('%Y-%m-%d')),
        data.get('method'), data.get('subject'), data.get('content'),
        data.get('result'), data.get('next_followup'), data.get('followup_date')
    ))
    return cursor.lastrowid


def get_followups(conn: sqlite3.Connection, buyer_id: int) -> List[Dict[str, Any]]:
    """获取采购商的跟进记录"""
    cursor = conn.execute(
        "SELECT * FROM followups WHERE buyer_id = ? ORDER BY date DESC",
        (buyer_id,)
    )
    return rows_to_list(cursor.fetchall())


def get_followup_due() -> List[Dict[str, Any]]:
    """获取待跟进采购商"""
    with get_conn() as conn:
        cursor = conn.execute("SELECT * FROM v_followup_due")
        return rows_to_list(cursor.fetchall())


# ============================================================
# AI评分
# ============================================================

def batch_score_buyers(conn: sqlite3.Connection, buyer_ids: List[int], 
                       scores: Dict[int, Dict[str, Any]]) -> int:
    """批量更新AI评分"""
    updated = 0
    for buyer_id, score_data in scores.items():
        if buyer_id not in buyer_ids:
            continue
        data = {
            'ai_score': score_data.get('score', 0),
            'ai_level': score_data.get('level', 'C'),
            'buyer_type': score_data.get('buyer_type'),
            'risk_level': score_data.get('risk_level', 'medium'),
            'updated_at': datetime.now().isoformat()
        }
        set_clauses = [f"{k} = ?" for k in data.keys()]
        sql = f"UPDATE buyers SET {', '.join(set_clauses)} WHERE id = ?"
        cursor = conn.execute(sql, list(data.values()) + [buyer_id])
        if cursor.rowcount > 0:
            updated += 1
    return updated


# ============================================================
# 统计数据
# ============================================================

def get_stats() -> Dict[str, Any]:
    """获取统计数据"""
    with get_conn() as conn:
        stats = {}
        
        # 总采购商
        cursor = conn.execute("SELECT COUNT(*) FROM buyers")
        stats['total_buyers'] = cursor.fetchone()[0]
        
        # 各状态数量
        cursor = conn.execute("SELECT status, COUNT(*) FROM buyers GROUP BY status")
        stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 各等级数量
        cursor = conn.execute("SELECT ai_level, COUNT(*) FROM buyers GROUP BY ai_level")
        stats['by_level'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 各数据源数量
        cursor = conn.execute("SELECT source, COUNT(*) FROM buyers GROUP BY source")
        stats['by_source'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 各国家数量 TOP10
        cursor = conn.execute("""
            SELECT country, COUNT(*) as cnt 
            FROM buyers 
            WHERE country IS NOT NULL 
            GROUP BY country 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        stats['top_countries'] = [dict(row) for row in cursor.fetchall()]
        
        # 平均AI评分
        cursor = conn.execute("SELECT AVG(ai_score) FROM buyers WHERE ai_score > 0")
        stats['avg_ai_score'] = round(cursor.fetchone()[0] or 0, 1)
        
        return stats


# ============================================================
# 数据导入
# ============================================================

def create_import_batch(conn: sqlite3.Connection, source: str, file_name: str) -> str:
    """创建导入批次"""
    batch_id = str(uuid.uuid4())[:8]
    sql = """
    INSERT INTO import_batches (batch_id, source, file_name, status)
    VALUES (?, ?, ?, 'pending')
    """
    conn.execute(sql, (batch_id, source, file_name))
    return batch_id


def update_import_batch(conn: sqlite3.Connection, batch_id: str, 
                        total: int = None, imported: int = None, 
                        failed: int = None, status: str = None, error: str = None):
    """更新导入批次"""
    updates = []
    values = []
    if total is not None:
        updates.append("total_records = ?")
        values.append(total)
    if imported is not None:
        updates.append("imported_records = ?")
        values.append(imported)
    if failed is not None:
        updates.append("failed_records = ?")
        values.append(failed)
    if status is not None:
        updates.append("status = ?")
        values.append(status)
        if status == 'completed':
            updates.append("completed_at = ?")
            values.append(datetime.now().isoformat())
    if error is not None:
        updates.append("error_log = ?")
        values.append(error)
    
    if updates:
        values.append(batch_id)
        sql = f"UPDATE import_batches SET {', '.join(updates)} WHERE batch_id = ?"
        conn.execute(sql, values)


def list_import_batches(conn: sqlite3.Connection, limit: int = 20) -> List[Dict]:
    """导入批次列表"""
    cursor = conn.execute(
        "SELECT * FROM import_batches ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    return rows_to_list(cursor.fetchall())


# ============================================================
# API日志
# ============================================================

def log_api_call(conn: sqlite3.Connection, source: str, endpoint: str,
                 request_data: str = None, response_status: int = None,
                 response_data: str = None, error: str = None,
                 tokens_used: int = None, cost_usd: float = None):
    """记录API调用"""
    sql = """
    INSERT INTO api_logs (source, endpoint, request_data, response_status,
        response_data, error, tokens_used, cost_usd)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(sql, (source, endpoint, request_data, response_status,
                       response_data, error, tokens_used, cost_usd))


def get_api_usage(source: str = None, days: int = 7) -> Dict[str, Any]:
    """获取API使用统计"""
    with get_conn() as conn:
        where = "WHERE created_at >= datetime('now', ?)"
        params = [f"-{days} days"]
        if source:
            where += " AND source = ?"
            params.append(source)
        
        sql = f"""
        SELECT source, COUNT(*) as calls, SUM(tokens_used) as tokens, 
               SUM(cost_usd) as cost
        FROM api_logs {where}
        GROUP BY source
        """
        cursor = conn.execute(sql, params)
        return {row[0]: {'calls': row[1], 'tokens': row[2], 'cost': row[3]} 
                for row in cursor.fetchall()}


# ============================================================
# 数据源配置
# ============================================================

def get_data_source(name: str) -> Optional[Dict]:
    """获取数据源配置"""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM data_sources WHERE name = ?", (name,)
        )
        row = cursor.fetchone()
        result = row_to_dict(row)
        if result and result.get('config'):
            result['config'] = json.loads(result['config'])
        return result


def update_data_source_usage(name: str):
    """更新数据源使用计数"""
    with get_conn() as conn:
        conn.execute("""
            UPDATE data_sources 
            SET used_today = used_today + 1, last_used = datetime('now')
            WHERE name = ?
        """, (name,))


def get_enabled_sources() -> List[Dict]:
    """获取已启用的数据源列表"""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM data_sources WHERE enabled = 1 ORDER BY priority ASC"
        )
        rows = cursor.fetchall()
        result = rows_to_list(rows)
        for r in result:
            if r.get('config'):
                r['config'] = json.loads(r['config'])
        return result


# ============================================================
# 系统配置
# ============================================================

def get_config(key: str, default: Any = None) -> Any:
    """获取系统配置"""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT value FROM system_config WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default


def set_config(key: str, value: Any):
    """设置系统配置"""
    with get_conn() as conn:
        value_str = json.dumps(value) if not isinstance(value, str) else value
        conn.execute("""
            INSERT INTO system_config (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')
        """, (key, value_str, value_str))
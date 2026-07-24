"""AI供应商管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import time

router = APIRouter()

SUPPORTED_PROVIDER_TYPES = [
    'minimax', 'openai', 'deepseek', 'qwen', 'gemini', 'kimi', 'glm', 'custom'
]

# 默认供应商种子数据
DEFAULT_PROVIDERS = [
    {'name': 'minimax', 'display_name': 'MiniMax', 'provider_type': 'minimax',
     'base_url': 'https://api.minimax.chat/v1', 'model': 'abab6.5s-chat'},
    {'name': 'openai', 'display_name': 'OpenAI', 'provider_type': 'openai',
     'base_url': 'https://api.openai.com/v1', 'model': 'gpt-4o'},
    {'name': 'deepseek', 'display_name': 'DeepSeek', 'provider_type': 'deepseek',
     'base_url': 'https://api.deepseek.com/v1', 'model': 'deepseek-chat'},
    {'name': 'qwen', 'display_name': 'Qwen', 'provider_type': 'qwen',
     'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'model': 'qwen-plus'},
    {'name': 'gemini', 'display_name': 'Gemini', 'provider_type': 'gemini',
     'base_url': 'https://generativelanguage.googleapis.com/v1beta', 'model': 'gemini-pro'},
    {'name': 'kimi', 'display_name': 'Kimi', 'provider_type': 'kimi',
     'base_url': 'https://api.moonshot.cn/v1', 'model': 'moonshot-v1-8k'},
    {'name': 'glm', 'display_name': 'GLM', 'provider_type': 'glm',
     'base_url': 'https://open.bigmodel.cn/api/paas/v4', 'model': 'glm-4'},
]


def init_ai_providers_table():
    """初始化ai_providers表并种子默认数据"""
    from services.database import get_conn
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT,
                provider_type TEXT NOT NULL,
                enabled INTEGER DEFAULT 0,
                is_default INTEGER DEFAULT 0,
                api_key TEXT DEFAULT '',
                base_url TEXT,
                model TEXT,
                backup_model TEXT,
                timeout INTEGER DEFAULT 30,
                max_retries INTEGER DEFAULT 2,
                config_json TEXT DEFAULT '{}',
                last_test_status TEXT,
                last_test_message TEXT,
                last_test_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        # 种子默认供应商（仅当表为空时）
        cursor = conn.execute("SELECT COUNT(*) FROM ai_providers")
        count = cursor.fetchone()[0]
        if count == 0:
            for p in DEFAULT_PROVIDERS:
                conn.execute("""
                    INSERT OR IGNORE INTO ai_providers
                    (name, display_name, provider_type, enabled, is_default, api_key, base_url, model)
                    VALUES (?, ?, ?, 0, 0, '', ?, ?)
                """, (p['name'], p['display_name'], p['provider_type'], p['base_url'], p['model']))


def _mask_api_key(key: str) -> str:
    """遮蔽API Key，只显示前4位和后4位"""
    if not key:
        return ''
    if len(key) <= 8:
        return '****'
    return key[:4] + '*' * (len(key) - 8) + key[-4:]


def _row_to_dict(row) -> Dict[str, Any]:
    """将数据库行转为字典，并遮蔽api_key"""
    d = dict(row)
    if 'api_key' in d:
        d['api_key_masked'] = _mask_api_key(d.get('api_key', ''))
        del d['api_key']
    if 'config_json' in d and isinstance(d['config_json'], str):
        try:
            d['config_json'] = json.loads(d['config_json'])
        except (json.JSONDecodeError, TypeError):
            d['config_json'] = {}
    return d


class ProviderCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    provider_type: str
    enabled: int = 0
    is_default: int = 0
    api_key: str = ''
    base_url: Optional[str] = None
    model: Optional[str] = None
    backup_model: Optional[str] = None
    timeout: int = 30
    max_retries: int = 2
    config_json: Optional[Dict[str, Any]] = None


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    provider_type: Optional[str] = None
    enabled: Optional[int] = None
    is_default: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    backup_model: Optional[str] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    config_json: Optional[Dict[str, Any]] = None


@router.get("/providers")
async def list_providers():
    """列出所有AI供应商"""
    init_ai_providers_table()
    from services.database import get_conn
    with get_conn() as conn:
        cursor = conn.execute("SELECT * FROM ai_providers ORDER BY id")
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]


@router.post("/providers")
async def create_provider(data: ProviderCreate):
    """创建AI供应商"""
    if data.provider_type not in SUPPORTED_PROVIDER_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的供应商类型: {data.provider_type}")

    from services.database import get_conn
    config_str = json.dumps(data.config_json or {}, ensure_ascii=False)

    with get_conn() as conn:
        # 检查名称唯一性
        cursor = conn.execute("SELECT id FROM ai_providers WHERE name = ?", (data.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail=f"供应商名称 '{data.name}' 已存在")

        # 如果设为默认，先取消其他默认
        if data.is_default:
            conn.execute("UPDATE ai_providers SET is_default = 0")

        cursor = conn.execute("""
            INSERT INTO ai_providers
            (name, display_name, provider_type, enabled, is_default, api_key,
             base_url, model, backup_model, timeout, max_retries, config_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.name, data.display_name or data.name, data.provider_type,
            data.enabled, data.is_default, data.api_key,
            data.base_url, data.model, data.backup_model,
            data.timeout, data.max_retries, config_str
        ))
        provider_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM ai_providers WHERE id = ?", (provider_id,))
        return _row_to_dict(cursor.fetchone())


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: int, data: ProviderUpdate):
    """更新AI供应商（api_key为空字符串时保留原key）"""
    from services.database import get_conn

    with get_conn() as conn:
        cursor = conn.execute("SELECT * FROM ai_providers WHERE id = ?", (provider_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="供应商不存在")

        updates = []
        values = []

        if data.display_name is not None:
            updates.append("display_name = ?")
            values.append(data.display_name)
        if data.provider_type is not None:
            if data.provider_type not in SUPPORTED_PROVIDER_TYPES:
                raise HTTPException(status_code=400, detail=f"不支持的供应商类型: {data.provider_type}")
            updates.append("provider_type = ?")
            values.append(data.provider_type)
        if data.enabled is not None:
            updates.append("enabled = ?")
            values.append(data.enabled)
        if data.is_default is not None:
            if data.is_default:
                conn.execute("UPDATE ai_providers SET is_default = 0")
            updates.append("is_default = ?")
            values.append(data.is_default)
        if data.api_key is not None and data.api_key != '':
            # 空字符串表示不更新key
            updates.append("api_key = ?")
            values.append(data.api_key)
        if data.base_url is not None:
            updates.append("base_url = ?")
            values.append(data.base_url)
        if data.model is not None:
            updates.append("model = ?")
            values.append(data.model)
        if data.backup_model is not None:
            updates.append("backup_model = ?")
            values.append(data.backup_model)
        if data.timeout is not None:
            updates.append("timeout = ?")
            values.append(data.timeout)
        if data.max_retries is not None:
            updates.append("max_retries = ?")
            values.append(data.max_retries)
        if data.config_json is not None:
            updates.append("config_json = ?")
            values.append(json.dumps(data.config_json, ensure_ascii=False))

        if updates:
            updates.append("updated_at = datetime('now')")
            values.append(provider_id)
            sql = f"UPDATE ai_providers SET {', '.join(updates)} WHERE id = ?"
            conn.execute(sql, values)

        cursor = conn.execute("SELECT * FROM ai_providers WHERE id = ?", (provider_id,))
        return _row_to_dict(cursor.fetchone())


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: int):
    """删除AI供应商"""
    from services.database import get_conn
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM ai_providers WHERE id = ?", (provider_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="供应商不存在")
    return {"message": "删除成功"}


@router.post("/providers/{provider_id}/test")
async def test_provider(provider_id: int):
    """测试AI供应商连接"""
    import httpx

    from services.database import get_conn
    with get_conn() as conn:
        cursor = conn.execute("SELECT * FROM ai_providers WHERE id = ?", (provider_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="供应商不存在")

    provider = dict(row)
    api_key = provider.get('api_key', '')
    base_url = provider.get('base_url', '')
    model = provider.get('model', '')

    if not api_key:
        result = {'success': False, 'message': 'API Key未配置', 'latency_ms': 0}
        _save_test_result(provider_id, result)
        return result

    if not base_url:
        result = {'success': False, 'message': 'Base URL未配置', 'latency_ms': 0}
        _save_test_result(provider_id, result)
        return result

    # 发起最小化chat completion请求
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': 'hi'}],
        'max_tokens': 5,
    }

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
        latency_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            result = {'success': True, 'message': '连接成功', 'latency_ms': latency_ms}
        else:
            detail = ''
            try:
                err = resp.json()
                detail = err.get('error', {}).get('message', '') or str(err)
            except Exception:
                detail = resp.text[:200]
            result = {'success': False, 'message': f'HTTP {resp.status_code}: {detail}', 'latency_ms': latency_ms}
    except httpx.TimeoutException:
        latency_ms = int((time.time() - start) * 1000)
        result = {'success': False, 'message': '连接超时(15s)', 'latency_ms': latency_ms}
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        result = {'success': False, 'message': f'连接失败: {str(e)}', 'latency_ms': latency_ms}

    _save_test_result(provider_id, result)
    return result


def _save_test_result(provider_id: int, result: dict):
    """保存测试结果到数据库"""
    from services.database import get_conn
    status = 'success' if result['success'] else 'failed'
    with get_conn() as conn:
        conn.execute("""
            UPDATE ai_providers
            SET last_test_status = ?, last_test_message = ?, last_test_at = datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (status, result['message'], provider_id))


@router.put("/providers/{provider_id}/default")
async def set_default_provider(provider_id: int):
    """设置默认AI供应商"""
    from services.database import get_conn
    with get_conn() as conn:
        cursor = conn.execute("SELECT id FROM ai_providers WHERE id = ?", (provider_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="供应商不存在")

        conn.execute("UPDATE ai_providers SET is_default = 0")
        conn.execute("UPDATE ai_providers SET is_default = 1, updated_at = datetime('now') WHERE id = ?",
                     (provider_id,))
    return {"message": "设置成功"}

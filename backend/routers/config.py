"""系统配置路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

router = APIRouter()


class ConfigUpdate(BaseModel):
    key: str
    value: Any


@router.get("/{key}")
async def get_config(key: str):
    """获取配置"""
    from services.database import get_config as db_get_config
    value = db_get_config(key)
    return {"key": key, "value": value}


@router.put("/{key}")
async def set_config(key: str, data: ConfigUpdate):
    """设置配置"""
    from services.database import set_config as db_set_config
    db_set_config(key, data.value)
    return {"message": "设置成功"}


@router.get("/ai/model")
async def get_ai_model():
    """获取当前AI模型配置"""
    from services.database import get_config
    model = get_config('ai_model', 'gpt-4o')
    return {"model": model}


@router.put("/ai/model")
async def set_ai_model(data: Dict[str, str]):
    """设置AI模型"""
    from services.database import set_config
    if 'model' in data:
        set_config('ai_model', data['model'])
    return {"message": "设置成功"}


@router.get("/ai/config")
async def get_ai_config():
    """获取AI配置（含密钥）"""
    from services.database import get_config
    config = get_config('ai_config', {})
    # 隐藏密钥
    if isinstance(config, dict):
        for key in ['openai_key', 'deepseek_key']:
            if key in config:
                config[key] = config[key][:8] + '***' if config[key] else ''
    return config


@router.put("/ai/config")
async def update_ai_config(data: Dict[str, Any]):
    """更新AI配置"""
    from services.database import set_config
    
    # 合并现有配置
    from services.database import get_config
    existing = get_config('ai_config', {})
    if isinstance(existing, str):
        try:
            existing = json.loads(existing)
        except:
            existing = {}
    
    # 更新
    existing.update(data)
    set_config('ai_config', existing)
    
    return {"message": "配置更新成功"}


@router.get("/datasource/list")
async def list_datasources():
    """数据源列表"""
    from services.database import get_conn
    with get_conn() as conn:
        cursor = conn.execute("SELECT * FROM data_sources ORDER BY priority")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            r = dict(row)
            if r.get('config'):
                try:
                    r['config'] = json.loads(r['config'])
                except:
                    r['config'] = {}
            result.append(r)
        return result


@router.put("/datasource/{name}")
async def update_datasource(name: str, data: Dict[str, Any]):
    """更新数据源配置"""
    from services.database import get_conn
    
    # 只允许更新config字段
    config_json = data.get('config')
    if config_json:
        config_str = json.dumps(config_json)
    else:
        config_str = json.dumps(data.get('config', {}))
    
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE data_sources SET config = ? WHERE name = ?",
            (config_str, name)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="数据源不存在")
    
    return {"message": "更新成功"}


@router.get("/api/usage")
async def get_api_usage(days: int = 7):
    """API使用统计"""
    from services.database import get_api_usage as db_get_api_usage
    return db_get_api_usage(days=days)
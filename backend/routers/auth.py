"""认证路由 - Token-based认证，PBKDF2密码哈希，登录频率限制"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import hashlib
import secrets
import time
import json
import os

router = APIRouter()
security = HTTPBearer(auto_error=False)

# 内存token存储（单实例足够）
_active_tokens: dict = {}  # token -> {"username": ..., "expires": ...}
TOKEN_TTL = 86400 * 7  # 7天

# 登录频率限制: {ip: [timestamps]}
_login_attempts: dict = {}
MAX_ATTEMPTS_PER_MINUTE = 5

# 默认账号（首次启动写入system_config）
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "buyer2024"

# PBKDF2 参数
_PBKDF2_ITERATIONS = 260000
_SALT_LENGTH = 16


def _hash_password(password: str, salt: bytes = None) -> str:
    """使用PBKDF2-HMAC-SHA256哈希密码，返回 salt_hex:hash_hex"""
    if salt is None:
        salt = os.urandom(_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _PBKDF2_ITERATIONS)
    return salt.hex() + ':' + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    """验证密码是否匹配存储的哈希"""
    try:
        salt_hex, hash_hex = stored.split(':', 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _PBKDF2_ITERATIONS)
        return secrets.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def _check_rate_limit(ip: str) -> bool:
    """检查IP是否超过登录频率限制，返回True表示允许"""
    now = time.time()
    window = 60.0  # 1分钟窗口

    if ip not in _login_attempts:
        _login_attempts[ip] = []

    # 清理过期记录
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < window]

    if len(_login_attempts[ip]) >= MAX_ATTEMPTS_PER_MINUTE:
        return False

    _login_attempts[ip].append(now)
    return True


def _get_credentials() -> dict:
    """从数据库获取账号配置"""
    from services.database import get_config
    creds = get_config('auth_credentials')
    if not creds:
        # 初始化默认账号
        default = {
            'username': DEFAULT_USERNAME,
            'password_hash': _hash_password(DEFAULT_PASSWORD)
        }
        from services.database import set_config
        set_config('auth_credentials', default)
        return default
    if isinstance(creds, str):
        creds = json.loads(creds)
    return creds


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """验证token依赖 - 其他路由可使用此依赖"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    token = credentials.credentials
    info = _active_tokens.get(token)
    if not info:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    if time.time() > info['expires']:
        del _active_tokens[token]
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return info['username']


def is_valid_token(token: str) -> bool:
    """检查token是否有效（供中间件使用，不抛异常）"""
    info = _active_tokens.get(token)
    if not info:
        return False
    if time.time() > info['expires']:
        del _active_tokens[token]
        return False
    return True


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    """登录"""
    # 频率限制
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")

    creds = _get_credentials()
    if req.username != creds['username']:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not _verify_password(req.password, creds['password_hash']):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = secrets.token_hex(32)
    _active_tokens[token] = {
        'username': req.username,
        'expires': time.time() + TOKEN_TTL
    }
    return {'token': token, 'username': req.username}


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """登出"""
    if credentials and credentials.credentials in _active_tokens:
        del _active_tokens[credentials.credentials]
    return {'message': '已登出'}


@router.get("/check")
async def check(username: str = Depends(verify_token)):
    """检查登录状态"""
    return {'username': username, 'valid': True}


@router.put("/password")
async def change_password(
    req: ChangePasswordRequest,
    username: str = Depends(verify_token)
):
    """修改密码"""
    creds = _get_credentials()
    if not _verify_password(req.old_password, creds['password_hash']):
        raise HTTPException(status_code=400, detail="原密码错误")
    creds['password_hash'] = _hash_password(req.new_password)
    from services.database import set_config
    set_config('auth_credentials', creds)
    return {'message': '密码修改成功'}

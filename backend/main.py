"""
AI海外采购商雷达系统 V1
FastAPI 后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from routers import buyers, search, import_data, ai_score, contacts, followups, export, config, quote
from routers import auth, ai_providers
from services.database import init_db

# 全局异常处理
from fastapi.responses import JSONResponse
from fastapi import Request
import traceback

app = FastAPI(
    title="AI Buyer Radar API",
    description="AI海外采购商雷达系统 API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导出目录
EXPORT_DIR = Path(__file__).parent.parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
app.mount("/exports", StaticFiles(directory=str(EXPORT_DIR)), name="exports")


# ============================================================
# Auth中间件 - 检查Bearer token
# ============================================================
_AUTH_SKIP_PATHS = {'/api/auth/login', '/api/health'}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """对/api/*路由进行token验证（跳过登录和健康检查）"""
    path = request.url.path

    # 跳过非API路径（静态文件等）
    if not path.startswith('/api'):
        return await call_next(request)

    # 跳过不需要认证的路径
    if path in _AUTH_SKIP_PATHS:
        return await call_next(request)

    # 检查Authorization头
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JSONResponse(status_code=401, content={"detail": "未登录"})

    token = auth_header[7:]
    if not auth.is_valid_token(token):
        return JSONResponse(status_code=401, content={"detail": "登录已过期，请重新登录"})

    return await call_next(request)


# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(ai_providers.router, prefix="/api/config/ai", tags=["AI供应商"])
app.include_router(buyers.router, prefix="/api/buyers", tags=["采购商管理"])
app.include_router(search.router, prefix="/api/search", tags=["采购商搜索"])
app.include_router(import_data.router, prefix="/api/import", tags=["数据导入"])
app.include_router(ai_score.router, prefix="/api/ai", tags=["AI评分"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["联系人管理"])
app.include_router(followups.router, prefix="/api/followups", tags=["跟进管理"])
app.include_router(export.router, prefix="/api/export", tags=["导出管理"])
app.include_router(config.router, prefix="/api/config", tags=["系统配置"])
app.include_router(quote.router, prefix="/api/quote", tags=["轻报价系统"])


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    init_db()
    # 初始化AI供应商表
    ai_providers.init_ai_providers_table()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常捕获"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "detail": traceback.format_exc() if __debug__ else None
        }
    )


@app.get("/health")
async def health():
    """健康检查 - 含数据库连通性"""
    db_status = "ok"
    try:
        from services.database import get_conn
        with get_conn() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_status = "error"
    return {"status": "ok", "database": db_status, "version": "1.0.0"}


@app.get("/api/health")
async def api_health():
    """API健康检查别名"""
    db_status = "ok"
    try:
        from services.database import get_conn
        with get_conn() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_status = "error"
    return {"status": "ok", "database": db_status, "version": "1.0.0"}


# 前端静态文件（必须在所有API路由之后注册，避免拦截API请求）
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

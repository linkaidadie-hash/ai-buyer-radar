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

# 静态文件 - 前端dist + 导出目录
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
EXPORT_DIR = Path(__file__).parent.parent / "exports"

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


EXPORT_DIR.mkdir(exist_ok=True)
app.mount("/exports", StaticFiles(directory=str(EXPORT_DIR)), name="exports")

# 注册路由
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


@app.get("/")
async def root():
    return {"message": "AI Buyer Radar API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
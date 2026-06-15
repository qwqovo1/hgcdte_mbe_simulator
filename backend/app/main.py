"""
FastAPI 主入口文件
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import api
from app.routers import experiment_router
from app.routers import ai_router

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于分子束外延(MBE)技术的HgCdTe数字孪生仿真平台后端API",
)

# 配置 CORS 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──────────────────────────────────────────
# 基础 API 路由
app.include_router(
    api.router,
    prefix=settings.API_PREFIX,
    tags=["基础信息"],
)

# 实验模块路由
app.include_router(
    experiment_router.router,
    prefix=f"{settings.API_PREFIX}/experiment",
    tags=["Experiment"],
)

# AI 分析模块路由
app.include_router(
    ai_router.router,
    prefix=f"{settings.API_PREFIX}/ai",
    tags=["AI分析"],
)


@app.get("/", tags=["Root"])
async def root():
    """根路径 - 服务状态"""
    return {
        "message": "电子束外延数字孪生系统API服务运行中",
        "version": settings.VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
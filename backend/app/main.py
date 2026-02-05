"""
FastAPI 主入口文件
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import api
from app.routers import experiment_router  # 【新增】导入新开发的实验模块路由

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api.router, prefix=settings.API_PREFIX)
# 【新增】注册实验模块专属路由，同样遵循 API 前缀
app.include_router(experiment_router.router, prefix=f"{settings.API_PREFIX}/experiment", tags=["Experiment"])

@app.get("/")
async def root():
    return {"message": "电子束外延数字孪生系统API服务运行中"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
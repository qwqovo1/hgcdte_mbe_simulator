"""
API路由模块
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/info")
async def get_project_info():
    """获取项目信息"""
    return {
        "title": "电子束外延数字孪生项目",
        "description": "基于分子束外延(MBE)技术的数字孪生仿真平台",
        "version": "1.0.0",
        "features": [
            "实时工艺参数监控",
            "薄膜生长过程仿真",
            "AI辅助工艺优化",
            "三维可视化展示"
        ]
    }

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}
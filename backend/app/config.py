"""
项目配置文件
"""

import os


class Settings:
    # 项目基本信息
    PROJECT_NAME: str = "电子束外延数字孪生系统"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # DeepSeek API 配置（环境变量优先）
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


settings = Settings()
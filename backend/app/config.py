"""
项目配置文件
"""


class Settings:
    # 项目基本信息
    PROJECT_NAME: str = "电子束外延数字孪生系统"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
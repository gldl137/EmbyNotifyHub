import os
from typing import Optional


class Config:
    """应用配置类"""

    # FastAPI
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "7000"))
    ENV: str = os.getenv("ENV", "development")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")

    # TMDB API
    TMDB_API_KEY: Optional[str] = os.getenv("TMDB_API_KEY")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"
    TMDB_LANGUAGE: str = "zh-CN"

    # 企业微信
    WECOM_CORPID: Optional[str] = os.getenv("WECOM_CORPID")
    WECOM_AGENTID: Optional[str] = os.getenv("WECOM_AGENTID")
    WECOM_SECRET: Optional[str] = os.getenv("WECOM_SECRET")
    WECOM_TOUSER: str = os.getenv("WECOM_TOUSER", "@all")

    # Emby
    EMBY_BASE_URL: Optional[str] = os.getenv("EMBY_BASE_URL")
    EMBY_API_KEY: Optional[str] = os.getenv("EMBY_API_KEY")

    # 缓存
    CACHE_TTL_TMDB: int = int(os.getenv("CACHE_TTL_TMDB", "86400"))  # 24小时
    CACHE_TTL_TOKEN: int = int(os.getenv("CACHE_TTL_TOKEN", "7200"))  # 2小时


config = Config()

"""应用配置 - 使用 pydantic-settings 管理配置项，支持环境变量覆盖"""

from pydantic_settings import BaseSettings

from typing import Optional





class Settings(BaseSettings):

    """应用配置类，所有配置项均可通过环境变量覆盖"""



    # 数据库配置

    DATABASE_URL: str = "sqlite:///./ticket_monitor.db"



    # JWT 配置

    SECRET_KEY: str = "please-change-this-secret-key-in-production"

    JWT_ALGORITHM: str = "HS256"

    JWT_EXPIRE_MINUTES: int = 1440  # 默认 24 小时



    # 邮件 SMTP 配置（可选）

    SMTP_HOST: Optional[str] = "smtp.qq.com"

    SMTP_PORT: int = 465

    SMTP_USER: Optional[str] = None

    SMTP_PASSWORD: Optional[str] = None



    # Firebase Cloud Messaging 配置（可选）

    FCM_CREDENTIALS_PATH: Optional[str] = None



    # 监控默认检查间隔（秒）

    CHECK_INTERVAL_DEFAULT: int = 30



    class Config:

        env_file = ".env"

        env_file_encoding = "utf-8"





# 全局配置单例

settings = Settings()


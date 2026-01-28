from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = Field(..., alias='BOT_TOKEN')
    admin_ids: list[int] = Field(default_factory=list)
    redis_url: str = Field(default='redis://redis:6379/0')
    celery_broker: str = Field(default='redis://redis:6379/1')
    celery_backend: str = Field(default='redis://redis:6379/2')
    max_file_size_mb: int = Field(default=1900)
    rate_limit_requests: int = Field(default=5)
    rate_limit_period: int = Field(default=60)
    download_timeout: int = Field(default=600)
    download_path: str = Field(default='/tmp/downloads')
    log_path: str = Field(default='/tmp/logs')
    
    class Config:
        env_file = '.env'
        case_sensitive = False


settings = Settings()

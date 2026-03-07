from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # 数据源配置
    primary_data_source: str = "sina"
    enable_data_cache: bool = True
    cache_ttl_seconds: int = 300

    # 指标配置
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    bollinger_period: int = 20
    bollinger_std: int = 2

    # 风险偏好阈值
    conservative_buy_threshold: float = 0.7
    conservative_sell_threshold: float = -0.7
    aggressive_buy_threshold: float = 0.5
    aggressive_sell_threshold: float = -0.5

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "sqlite:///./agent_api_proxy.db"
    
    # Reddit API
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "AgentAPIProxy/1.0"
    reddit_username: str = ""
    reddit_password: str = ""
    
    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""
    
    # Rate Limiting (requests per minute per API key)
    rate_limit_per_minute: int = 30
    
    # Pricing (in cents)
    cost_reddit_post: int = 10
    cost_reddit_search: int = 5
    cost_email_send: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

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
    
    # Facebook Messenger
    facebook_page_token: str = ""
    facebook_page_id: str = ""
    facebook_app_secret: str = ""
    facebook_verify_token: str = ""
    
    # Twitter API (OAuth 1.0a)
    twitter_consumer_key: str = ""
    twitter_consumer_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    
    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_callback_url: str = "https://agent-api-proxy-production.up.railway.app/api/github/callback"
    
    # Frontend URL (for OAuth redirects)
    frontend_url: str = "https://agent-api-proxy-production.up.railway.app"
    
    # Rate Limiting (requests per minute per API key)
    rate_limit_per_minute: int = 30
    
    # Pricing (in cents)
    cost_reddit_post: int = 10
    cost_reddit_search: int = 5
    cost_email_send: int = 15
    cost_twitter_tweet: int = 10
    cost_github_create_repo: int = 10
    cost_github_push_file: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

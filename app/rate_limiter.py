from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

from app.config import get_settings

settings = get_settings()


def get_api_key_identifier(request: Request) -> str:
    """
    Extract API key from request for rate limiting
    Falls back to IP address if no API key
    """
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Return API key
    
    return get_remote_address(request)  # Fallback to IP


limiter = Limiter(
    key_func=get_api_key_identifier,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)

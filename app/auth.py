from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, APIKey

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> str:
    """
    Validate API key and return user_id
    """
    api_key = credentials.credentials
    
    # Query database for API key
    db_key = db.query(APIKey).filter(
        APIKey.api_key == api_key,
        APIKey.is_active == 1
    ).first()
    
    if not db_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )
    
    return db_key.user_id

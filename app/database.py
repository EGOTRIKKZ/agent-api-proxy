from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import secrets

from app.config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class APIKey(Base):
    """API Key model for authentication"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # SQLite doesn't have boolean
    

class UsageLog(Base):
    """Usage tracking model"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    endpoint = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cost = Column(Integer, nullable=False)  # Cost in cents
    success = Column(Integer, default=1)  # SQLite doesn't have boolean
    error_message = Column(String, nullable=True)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_api_key(db, user_id: str) -> str:
    """Create a new API key for a user"""
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    db_api_key = APIKey(
        user_id=user_id,
        api_key=api_key
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return api_key


def log_usage(db, user_id: str, endpoint: str, cost: int, success: bool = True, error_message: str = None):
    """Log API usage"""
    log_entry = UsageLog(
        user_id=user_id,
        endpoint=endpoint,
        cost=cost,
        success=1 if success else 0,
        error_message=error_message
    )
    db.add(log_entry)
    db.commit()

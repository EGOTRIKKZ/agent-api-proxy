from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db, get_db, create_api_key, UsageLog, APIKey
from app.routers import reddit, email, facebook, blog, twitter, github
from app.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield


# Create FastAPI app
app = FastAPI(
    title="Agent API Proxy",
    description="API proxy service for AI agents to access external APIs",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error handler"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please slow down."
        }
    )


# Include routers
app.include_router(reddit.router)
app.include_router(email.router)
app.include_router(facebook.router)
app.include_router(twitter.router)
app.include_router(github.router)
app.include_router(blog.router)


# Mount static files for landing page
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve landing page"""
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Agent API Proxy</h1><p>Landing page not found. See /docs for API documentation.</p>",
            status_code=200
        )


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    """Serve privacy policy page"""
    try:
        with open("static/privacy.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Privacy Policy</h1><p>Privacy policy not found.</p>",
            status_code=404
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/admin/create-api-key")
async def admin_create_api_key(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to create a new API key
    
    WARNING: In production, protect this endpoint with proper authentication!
    This is a minimal MVP implementation.
    """
    try:
        api_key = create_api_key(db=db, user_id=user_id)
        return {
            "success": True,
            "user_id": user_id,
            "api_key": api_key,
            "message": "API key created successfully. Keep it secure!"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/admin/usage/{user_id}")
async def get_user_usage(
    user_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for a user
    
    WARNING: In production, protect this endpoint with proper authentication!
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.timestamp >= cutoff_date
    ).all()
    
    total_cost = sum(log.cost for log in logs)
    total_requests = len(logs)
    successful_requests = sum(1 for log in logs if log.success)
    
    # Group by endpoint
    endpoint_stats = {}
    for log in logs:
        if log.endpoint not in endpoint_stats:
            endpoint_stats[log.endpoint] = {
                "count": 0,
                "cost": 0,
                "success": 0,
                "failed": 0
            }
        endpoint_stats[log.endpoint]["count"] += 1
        endpoint_stats[log.endpoint]["cost"] += log.cost
        if log.success:
            endpoint_stats[log.endpoint]["success"] += 1
        else:
            endpoint_stats[log.endpoint]["failed"] += 1
    
    return {
        "user_id": user_id,
        "period_days": days,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": total_requests - successful_requests,
        "total_cost_cents": total_cost,
        "total_cost_dollars": total_cost / 100,
        "endpoint_breakdown": endpoint_stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
import praw

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/reddit", tags=["Reddit"])
settings = get_settings()


# Request/Response Models
class RedditPostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    text: str = Field(..., max_length=40000)
    subreddit: str = Field(..., min_length=1)


class RedditPostResponse(BaseModel):
    success: bool
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    message: str


class RedditSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    subreddit: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class RedditSearchResult(BaseModel):
    title: str
    subreddit: str
    author: str
    score: int
    url: str
    created_utc: float
    num_comments: int
    selftext: str


class RedditSearchResponse(BaseModel):
    success: bool
    count: int
    results: List[RedditSearchResult]


def get_reddit_client():
    """Get configured Reddit client"""
    if not all([
        settings.reddit_client_id,
        settings.reddit_client_secret,
        settings.reddit_username,
        settings.reddit_password
    ]):
        raise HTTPException(
            status_code=503,
            detail="Reddit API not configured on server"
        )
    
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
        username=settings.reddit_username,
        password=settings.reddit_password
    )


@router.post("/post", response_model=RedditPostResponse)
async def create_reddit_post(
    request: RedditPostRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a text post on Reddit
    
    Requires valid Reddit API credentials configured on server.
    Cost: $0.10 per post
    """
    try:
        reddit = get_reddit_client()
        
        # Submit post
        subreddit = reddit.subreddit(request.subreddit)
        submission = subreddit.submit(
            title=request.title,
            selftext=request.text
        )
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/reddit/post",
            cost=settings.cost_reddit_post,
            success=True
        )
        
        return RedditPostResponse(
            success=True,
            post_url=f"https://reddit.com{submission.permalink}",
            post_id=submission.id,
            message="Post created successfully"
        )
        
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/reddit/post",
            cost=0,  # Don't charge for failures
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Reddit post: {str(e)}"
        )


@router.get("/search", response_model=RedditSearchResponse)
async def search_reddit(
    query: str,
    subreddit: Optional[str] = None,
    limit: int = 10,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search Reddit posts
    
    Search across all of Reddit or within a specific subreddit.
    Cost: $0.05 per search
    """
    try:
        reddit = get_reddit_client()
        
        # Search subreddit or all of Reddit
        if subreddit:
            search_target = reddit.subreddit(subreddit)
        else:
            search_target = reddit.subreddit("all")
        
        # Perform search
        results = []
        for submission in search_target.search(query, limit=limit):
            results.append(RedditSearchResult(
                title=submission.title,
                subreddit=submission.subreddit.display_name,
                author=str(submission.author),
                score=submission.score,
                url=f"https://reddit.com{submission.permalink}",
                created_utc=submission.created_utc,
                num_comments=submission.num_comments,
                selftext=submission.selftext[:500]  # Truncate long text
            ))
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/reddit/search",
            cost=settings.cost_reddit_search,
            success=True
        )
        
        return RedditSearchResponse(
            success=True,
            count=len(results),
            results=results
        )
        
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/reddit/search",
            cost=0,  # Don't charge for failures
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search Reddit: {str(e)}"
        )

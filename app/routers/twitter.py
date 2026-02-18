from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import tweepy

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/twitter", tags=["Twitter"])
settings = get_settings()


# Request/Response Models
class TweetRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=280)
    reply_to_tweet_id: Optional[str] = None


class TweetResponse(BaseModel):
    success: bool
    message: str
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None


def get_twitter_client():
    """Get configured Twitter API v2 client"""
    if not all([
        settings.twitter_consumer_key,
        settings.twitter_consumer_secret,
        settings.twitter_access_token,
        settings.twitter_access_token_secret
    ]):
        raise HTTPException(
            status_code=503,
            detail="Twitter API not configured on server"
        )
    
    try:
        client = tweepy.Client(
            consumer_key=settings.twitter_consumer_key,
            consumer_secret=settings.twitter_consumer_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_token_secret
        )
        return client
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Twitter client: {str(e)}"
        )


@router.post("/tweet", response_model=TweetResponse)
async def post_tweet(
    request: TweetRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post a tweet to Twitter
    
    Requires valid Twitter API credentials configured on server.
    Cost: $0.10 per tweet
    
    Parameters:
    - text: Tweet content (1-280 characters)
    - reply_to_tweet_id: Optional tweet ID to reply to
    """
    try:
        client = get_twitter_client()
        
        # Post tweet
        kwargs = {"text": request.text}
        if request.reply_to_tweet_id:
            kwargs["in_reply_to_tweet_id"] = request.reply_to_tweet_id
        
        response = client.create_tweet(**kwargs)
        
        tweet_id = response.data["id"]
        tweet_url = f"https://twitter.com/user/status/{tweet_id}"
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twitter/tweet",
            cost=settings.cost_twitter_tweet,
            success=True
        )
        
        return TweetResponse(
            success=True,
            message="Tweet posted successfully",
            tweet_id=tweet_id,
            tweet_url=tweet_url
        )
        
    except tweepy.TweepyException as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twitter/tweet",
            cost=0,  # Don't charge for failures
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Twitter API error: {str(e)}"
        )
    
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twitter/tweet",
            cost=0,
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post tweet: {str(e)}"
        )

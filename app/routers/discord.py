from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, HttpUrl
import httpx

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/discord", tags=["Discord"])
settings = get_settings()


# Request/Response Models
class WebhookSendRequest(BaseModel):
    webhook_url: HttpUrl = Field(..., description="Discord webhook URL")
    content: str = Field(default="", max_length=2000, description="Message text")
    username: str = Field(default="Agent API Proxy", max_length=80, description="Override bot username")
    avatar_url: HttpUrl = Field(default=None, description="Override bot avatar URL")
    embeds: list = Field(default=[], description="Rich embeds (optional)")


class WebhookSendResponse(BaseModel):
    success: bool
    message: str
    message_id: str = None


@router.post("/webhook/send", response_model=WebhookSendResponse)
async def send_webhook(
    request: WebhookSendRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message via Discord webhook
    
    No Discord API setup required - just provide your webhook URL.
    
    Get webhook URL from Discord:
    1. Server Settings → Integrations → Webhooks
    2. Create Webhook
    3. Copy Webhook URL
    
    Cost: $0.05 per message
    """
    try:
        # Build Discord payload
        payload = {
            "content": request.content,
            "username": request.username,
        }
        
        if request.avatar_url:
            payload["avatar_url"] = str(request.avatar_url)
        
        if request.embeds:
            payload["embeds"] = request.embeds
        
        # Send to Discord webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(request.webhook_url),
                json=payload,
                params={"wait": "true"}  # Wait for Discord to return message ID
            )
            
            if response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Discord webhook error: {response.text}"
                )
            
            # Extract message ID if available
            message_id = None
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("id")
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/discord/webhook/send",
            cost=settings.cost_discord_webhook,
            success=True
        )
        
        return WebhookSendResponse(
            success=True,
            message="Message sent to Discord",
            message_id=message_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/discord/webhook/send",
            cost=0,  # Don't charge for failures
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send webhook: {str(e)}"
        )


# Embed builder helper models
class EmbedField(BaseModel):
    name: str = Field(..., max_length=256)
    value: str = Field(..., max_length=1024)
    inline: bool = Field(default=False)


class EmbedAuthor(BaseModel):
    name: str = Field(..., max_length=256)
    url: HttpUrl = Field(default=None)
    icon_url: HttpUrl = Field(default=None)


class EmbedFooter(BaseModel):
    text: str = Field(..., max_length=2048)
    icon_url: HttpUrl = Field(default=None)


class Embed(BaseModel):
    title: str = Field(default=None, max_length=256)
    description: str = Field(default=None, max_length=4096)
    url: HttpUrl = Field(default=None)
    color: int = Field(default=None, description="Color as integer (e.g. 0x5865F2 for Discord blurple)")
    timestamp: str = Field(default=None, description="ISO8601 timestamp")
    author: EmbedAuthor = Field(default=None)
    footer: EmbedFooter = Field(default=None)
    fields: list[EmbedField] = Field(default=[])
    image_url: HttpUrl = Field(default=None, description="Large image URL")
    thumbnail_url: HttpUrl = Field(default=None, description="Small thumbnail URL")


class WebhookSendEmbedRequest(BaseModel):
    webhook_url: HttpUrl = Field(..., description="Discord webhook URL")
    embed: Embed = Field(..., description="Rich embed to send")
    username: str = Field(default="Agent API Proxy", max_length=80)
    avatar_url: HttpUrl = Field(default=None)


@router.post("/webhook/send-embed", response_model=WebhookSendResponse)
async def send_webhook_embed(
    request: WebhookSendEmbedRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a rich embed message via Discord webhook
    
    Embeds support formatted content with titles, descriptions, fields,
    images, colors, and more.
    
    Cost: $0.05 per message
    """
    try:
        # Build embed object
        embed_dict = {}
        if request.embed.title:
            embed_dict["title"] = request.embed.title
        if request.embed.description:
            embed_dict["description"] = request.embed.description
        if request.embed.url:
            embed_dict["url"] = str(request.embed.url)
        if request.embed.color:
            embed_dict["color"] = request.embed.color
        if request.embed.timestamp:
            embed_dict["timestamp"] = request.embed.timestamp
        if request.embed.author:
            author_dict = {"name": request.embed.author.name}
            if request.embed.author.url:
                author_dict["url"] = str(request.embed.author.url)
            if request.embed.author.icon_url:
                author_dict["icon_url"] = str(request.embed.author.icon_url)
            embed_dict["author"] = author_dict
        if request.embed.footer:
            footer_dict = {"text": request.embed.footer.text}
            if request.embed.footer.icon_url:
                footer_dict["icon_url"] = str(request.embed.footer.icon_url)
            embed_dict["footer"] = footer_dict
        if request.embed.fields:
            embed_dict["fields"] = [
                {"name": f.name, "value": f.value, "inline": f.inline}
                for f in request.embed.fields
            ]
        if request.embed.image_url:
            embed_dict["image"] = {"url": str(request.embed.image_url)}
        if request.embed.thumbnail_url:
            embed_dict["thumbnail"] = {"url": str(request.embed.thumbnail_url)}
        
        # Build Discord payload
        payload = {
            "username": request.username,
            "embeds": [embed_dict]
        }
        
        if request.avatar_url:
            payload["avatar_url"] = str(request.avatar_url)
        
        # Send to Discord webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(request.webhook_url),
                json=payload,
                params={"wait": "true"}
            )
            
            if response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Discord webhook error: {response.text}"
                )
            
            # Extract message ID if available
            message_id = None
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("id")
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/discord/webhook/send-embed",
            cost=settings.cost_discord_webhook,
            success=True
        )
        
        return WebhookSendResponse(
            success=True,
            message="Embed sent to Discord",
            message_id=message_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/discord/webhook/send-embed",
            cost=0,
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send embed: {str(e)}"
        )

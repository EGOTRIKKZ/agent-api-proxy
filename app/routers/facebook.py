import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx

from app.config import get_settings

router = APIRouter(prefix="/api/facebook", tags=["Facebook"])
settings = get_settings()


@router.get("/config-check")
async def config_check():
    """Debug endpoint to check if Facebook config is loaded"""
    return {
        "facebook_page_id_set": bool(settings.facebook_page_id),
        "facebook_page_token_set": bool(settings.facebook_page_token),
        "facebook_verify_token_set": bool(settings.facebook_verify_token),
        "facebook_app_secret_set": bool(settings.facebook_app_secret),
        "verify_token_value": settings.facebook_verify_token or "NOT_SET"
    }


# Request/Response Models
class FacebookWebhookEntry(BaseModel):
    """Single entry in a Facebook webhook batch"""
    id: str
    time: int
    messaging: List[Dict[str, Any]]


class FacebookWebhook(BaseModel):
    """Facebook webhook payload structure"""
    object: str
    entry: List[FacebookWebhookEntry]


def verify_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """
    Verify that the webhook request came from Facebook
    
    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value
        app_secret: Facebook app secret
    
    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False
    
    expected_signature = signature.split("=")[1]
    
    # Compute HMAC-SHA256
    mac = hmac.new(
        app_secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    )
    computed_signature = mac.hexdigest()
    
    return hmac.compare_digest(computed_signature, expected_signature)


async def forward_to_openclaw(message_data: Dict[str, Any]):
    """
    Forward incoming Facebook message to OpenClaw gateway
    
    Args:
        message_data: Parsed message from Facebook webhook
    """
    try:
        # Extract message details
        sender_id = message_data.get("sender", {}).get("id")
        message_text = message_data.get("message", {}).get("text", "")
        
        if not sender_id or not message_text:
            return
        
        # TODO: Configure OpenClaw webhook URL in settings
        # For now, just log that we received it
        print(f"📨 Facebook message from {sender_id}: {message_text}")
        
        # In production, this would POST to OpenClaw:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         settings.openclaw_webhook_url,
        #         json={
        #             "channel": "facebook",
        #             "sender_id": sender_id,
        #             "message": message_text,
        #             "timestamp": message_data.get("timestamp")
        #         }
        #     )
        
    except Exception as e:
        print(f"❌ Error forwarding to OpenClaw: {e}")


@router.get("/webhook")
async def verify_webhook(
    request: Request,
):
    """
    Facebook webhook verification endpoint
    
    Facebook sends a GET request with:
    - hub.mode=subscribe
    - hub.verify_token=<your-verify-token>
    - hub.challenge=<random-string>
    
    We must respond with the challenge if the verify token matches.
    """
    params = request.query_params
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # Debug logging
    print(f"🔍 Webhook verify attempt:")
    print(f"  Mode: {mode}")
    print(f"  Token received: {token}")
    print(f"  Token expected: {settings.facebook_verify_token}")
    print(f"  Challenge: {challenge}")
    
    # Check if mode and token are correct
    if mode == "subscribe" and token == settings.facebook_verify_token:
        print("✅ Facebook webhook verified!")
        return int(challenge)
    else:
        raise HTTPException(
            status_code=403,
            detail="Webhook verification failed"
        )


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Facebook webhook receiver endpoint
    
    Receives messages and events from Facebook Messenger.
    Verifies signature and forwards to OpenClaw for processing.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature (if app secret is configured)
    if settings.facebook_app_secret:
        if not x_hub_signature_256:
            raise HTTPException(
                status_code=401,
                detail="Missing X-Hub-Signature-256 header"
            )
        
        if not verify_signature(body, x_hub_signature_256, settings.facebook_app_secret):
            raise HTTPException(
                status_code=401,
                detail="Invalid signature"
            )
    
    # Parse webhook payload
    try:
        data = await request.json()
        
        # Facebook sends 'page' object for Messenger
        if data.get("object") != "page":
            return {"status": "ignored", "reason": "not a page event"}
        
        # Process each entry
        for entry in data.get("entry", []):
            # Process each messaging event
            for messaging_event in entry.get("messaging", []):
                
                # Handle message received
                if "message" in messaging_event:
                    await forward_to_openclaw(messaging_event)
                
                # Handle postback (button clicks)
                elif "postback" in messaging_event:
                    # Future: handle button clicks
                    pass
                
                # Handle message read
                elif "read" in messaging_event:
                    # Future: track read receipts
                    pass
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/send")
async def send_message(
    recipient_id: str,
    message: str,
    page_access_token: Optional[str] = None
):
    """
    Send a message via Facebook Messenger
    
    Args:
        recipient_id: Facebook user ID (PSID)
        message: Text message to send
        page_access_token: Optional override for page token
    """
    token = page_access_token or settings.facebook_page_token
    
    if not token:
        raise HTTPException(
            status_code=503,
            detail="Facebook Page Access Token not configured"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://graph.facebook.com/v21.0/me/messages",
                params={"access_token": token},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": message}
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "recipient_id": result.get("recipient_id")
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )


class FacebookPostRequest(BaseModel):
    """Request model for posting to Facebook page"""
    message: str
    page_id: Optional[str] = None
    page_access_token: Optional[str] = None


@router.post("/post")
async def post_to_page(request: FacebookPostRequest):
    """
    Post a message to the Facebook Page timeline
    
    Args:
        request: Post request containing message and optional overrides
    """
    token = request.page_access_token or settings.facebook_page_token
    page = request.page_id or settings.facebook_page_id
    
    if not token or not page:
        raise HTTPException(
            status_code=503,
            detail="Facebook Page configuration missing"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v21.0/{page}/feed",
                params={"access_token": token},
                json={"message": request.message}
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "post_id": result.get("id")
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post to page: {str(e)}"
        )

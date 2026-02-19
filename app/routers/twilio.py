from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import httpx
import base64

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/twilio", tags=["Twilio"])
settings = get_settings()

# In-memory credential storage (TODO: move to encrypted DB for production)
user_credentials = {}


# Request/Response Models
class SetCredentialsRequest(BaseModel):
    account_sid: str = Field(..., description="Twilio Account SID")
    auth_token: str = Field(..., description="Twilio Auth Token")
    from_phone: str = Field(..., description="Your Twilio phone number (E.164 format: +1234567890)")


class SetCredentialsResponse(BaseModel):
    success: bool
    message: str


class SendSMSRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number (E.164 format: +1234567890)")
    body: str = Field(..., min_length=1, max_length=1600, description="Message text")


class SendSMSResponse(BaseModel):
    success: bool
    message_sid: str
    status: str
    message: str


class MakeCallRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number (E.164 format: +1234567890)")
    twiml_url: str = Field(..., description="URL to TwiML instructions for the call")


class MakeCallResponse(BaseModel):
    success: bool
    call_sid: str
    status: str
    message: str


def get_user_credentials(user_id: str) -> tuple[str, str, str]:
    """Get stored Twilio credentials for user"""
    creds = user_credentials.get(user_id)
    if not creds:
        raise HTTPException(
            status_code=401,
            detail="Twilio credentials not set. Call /api/twilio/set-credentials first."
        )
    return creds["account_sid"], creds["auth_token"], creds["from_phone"]


@router.post("/set-credentials", response_model=SetCredentialsResponse)
async def set_twilio_credentials(
    request: SetCredentialsRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Store your Twilio credentials
    
    Get credentials from: https://console.twilio.com/
    - Account SID: Found on dashboard
    - Auth Token: Found on dashboard (click to reveal)
    - From Phone: Your Twilio phone number
    
    This endpoint is free - no charge for storing credentials.
    """
    # Verify credentials by testing them against Twilio API
    auth_string = f"{request.account_sid}:{request.auth_token}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.twilio.com/2010-04-01/Accounts/{request.account_sid}.json",
            headers={"Authorization": f"Basic {auth_b64}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid Twilio credentials. Please check and try again."
            )
    
    # Store credentials (TODO: encrypt in production)
    user_credentials[user_id] = {
        "account_sid": request.account_sid,
        "auth_token": request.auth_token,
        "from_phone": request.from_phone
    }
    
    return SetCredentialsResponse(
        success=True,
        message="Twilio credentials stored successfully"
    )


@router.post("/sms/send", response_model=SendSMSResponse)
async def send_sms(
    request: SendSMSRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send an SMS message via Twilio
    
    Phone numbers must be in E.164 format: +1234567890
    
    Cost: $0.10 per message (plus Twilio's per-message cost)
    """
    try:
        account_sid, auth_token, from_phone = get_user_credentials(user_id)
        
        # Build auth header
        auth_string = f"{account_sid}:{auth_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Send SMS via Twilio API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "To": request.to,
                    "From": from_phone,
                    "Body": request.body
                }
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Twilio API error: {response.text}"
                )
            
            data = response.json()
            message_sid = data.get("sid", "")
            status = data.get("status", "unknown")
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twilio/sms/send",
            cost=settings.cost_twilio_sms,
            success=True
        )
        
        return SendSMSResponse(
            success=True,
            message_sid=message_sid,
            status=status,
            message="SMS sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twilio/sms/send",
            cost=0,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send SMS: {str(e)}"
        )


@router.post("/call/make", response_model=MakeCallResponse)
async def make_call(
    request: MakeCallRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Make a phone call via Twilio
    
    Requires TwiML URL that returns instructions for the call.
    Example TwiML for text-to-speech:
    
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Hello! This is a call from your AI agent.</Say>
    </Response>
    ```
    
    Host your TwiML at a public URL or use Twilio's TwiML Bins.
    
    Cost: $0.15 per call (plus Twilio's per-minute cost)
    """
    try:
        account_sid, auth_token, from_phone = get_user_credentials(user_id)
        
        # Build auth header
        auth_string = f"{account_sid}:{auth_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Make call via Twilio API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json",
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "To": request.to,
                    "From": from_phone,
                    "Url": request.twiml_url
                }
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Twilio API error: {response.text}"
                )
            
            data = response.json()
            call_sid = data.get("sid", "")
            status = data.get("status", "unknown")
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twilio/call/make",
            cost=settings.cost_twilio_call,
            success=True
        )
        
        return MakeCallResponse(
            success=True,
            call_sid=call_sid,
            status=status,
            message="Call initiated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/twilio/call/make",
            cost=0,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to make call: {str(e)}"
        )

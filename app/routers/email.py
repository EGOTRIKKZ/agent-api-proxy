from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/email", tags=["Email"])
settings = get_settings()


# Request/Response Models
class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=100000)


class EmailSendResponse(BaseModel):
    success: bool
    message: str
    message_id: str = None


def get_sendgrid_client():
    """Get configured SendGrid client"""
    if not settings.sendgrid_api_key:
        raise HTTPException(
            status_code=503,
            detail="SendGrid API not configured on server"
        )
    
    if not settings.sendgrid_from_email:
        raise HTTPException(
            status_code=503,
            detail="SendGrid from_email not configured on server"
        )
    
    return SendGridAPIClient(settings.sendgrid_api_key)


@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    request: EmailSendRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send an email via SendGrid
    
    Requires valid SendGrid API key configured on server.
    Cost: $0.15 per email
    """
    try:
        sg = get_sendgrid_client()
        
        # Create email message
        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=request.to,
            subject=request.subject,
            html_content=request.body.replace('\n', '<br>')
        )
        
        # Send email
        response = sg.send(message)
        
        # Extract message ID from headers if available
        message_id = response.headers.get('X-Message-Id', 'unknown')
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/email/send",
            cost=settings.cost_email_send,
            success=True
        )
        
        return EmailSendResponse(
            success=True,
            message="Email sent successfully",
            message_id=message_id
        )
        
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/email/send",
            cost=0,  # Don't charge for failures
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )

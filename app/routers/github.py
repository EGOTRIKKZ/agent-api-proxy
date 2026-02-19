from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import httpx
import secrets

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/github", tags=["GitHub"])
settings = get_settings()

# In-memory state storage (TODO: move to Redis/DB for production)
oauth_states = {}
user_tokens = {}


# Request/Response Models
class GitHubAuthResponse(BaseModel):
    auth_url: str
    state: str


class CreateRepoRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    private: bool = Field(default=False)


class CreateRepoResponse(BaseModel):
    success: bool
    repo_url: str
    message: str


class PushFileRequest(BaseModel):
    repo: str = Field(..., description="Format: owner/repo")
    path: str = Field(..., description="File path in repo")
    content: str = Field(..., max_length=1000000)
    message: str = Field(default="Update via Agent API Proxy")
    branch: str = Field(default="main")


class PushFileResponse(BaseModel):
    success: bool
    commit_sha: str
    message: str


@router.get("/authorize", response_model=GitHubAuthResponse)
async def github_authorize(
    user_id: str = Depends(get_current_user),
):
    """
    Start GitHub OAuth flow
    
    Returns authorization URL for user to visit.
    """
    if not settings.github_client_id:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth not configured on server"
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = user_id
    
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_callback_url}"
        f"&scope=repo,user"
        f"&state={state}"
    )
    
    return GitHubAuthResponse(auth_url=auth_url, state=state)


@router.get("/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    GitHub OAuth callback endpoint
    
    Exchanges code for access token and stores it.
    """
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    user_id = oauth_states.pop(state)
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to exchange code: {response.text}"
            )
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=500,
                detail="No access token in response"
            )
    
    # Store token (TODO: encrypt and store in DB)
    user_tokens[user_id] = access_token
    
    return RedirectResponse(
        url=f"{settings.frontend_url}/github-connected",
        status_code=302
    )


def get_user_token(user_id: str) -> str:
    """Get stored GitHub token for user"""
    token = user_tokens.get(user_id)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="GitHub not connected. Call /api/github/authorize first."
        )
    return token


@router.post("/create-repo", response_model=CreateRepoResponse)
async def create_repo(
    request: CreateRepoRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new GitHub repository
    
    Cost: $0.10 per repo creation
    """
    try:
        token = get_user_token(user_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json={
                    "name": request.name,
                    "description": request.description,
                    "private": request.private
                }
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GitHub API error: {response.text}"
                )
            
            repo_data = response.json()
            repo_url = repo_data["html_url"]
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/github/create-repo",
            cost=settings.cost_github_create_repo,
            success=True
        )
        
        return CreateRepoResponse(
            success=True,
            repo_url=repo_url,
            message="Repository created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/github/create-repo",
            cost=0,
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create repository: {str(e)}"
        )


@router.post("/push-file", response_model=PushFileResponse)
async def push_file(
    request: PushFileRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Push a file to GitHub repository
    
    Cost: $0.05 per file push
    """
    try:
        token = get_user_token(user_id)
        
        # Get current file SHA if it exists (needed for updates)
        async with httpx.AsyncClient() as client:
            # Check if file exists
            get_response = await client.get(
                f"https://api.github.com/repos/{request.repo}/contents/{request.path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                params={"ref": request.branch}
            )
            
            # Prepare request data
            import base64
            content_bytes = request.content.encode('utf-8')
            content_b64 = base64.b64encode(content_bytes).decode('utf-8')
            
            data = {
                "message": request.message,
                "content": content_b64,
                "branch": request.branch
            }
            
            # If file exists, include SHA for update
            if get_response.status_code == 200:
                file_data = get_response.json()
                data["sha"] = file_data["sha"]
            
            # Push file
            put_response = await client.put(
                f"https://api.github.com/repos/{request.repo}/contents/{request.path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json=data
            )
            
            if put_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=put_response.status_code,
                    detail=f"GitHub API error: {put_response.text}"
                )
            
            commit_data = put_response.json()
            commit_sha = commit_data["commit"]["sha"]
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/github/push-file",
            cost=settings.cost_github_push_file,
            success=True
        )
        
        return PushFileResponse(
            success=True,
            commit_sha=commit_sha,
            message="File pushed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/github/push-file",
            cost=0,
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to push file: {str(e)}"
        )

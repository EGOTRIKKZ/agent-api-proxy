from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import httpx
import secrets

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.config import get_settings

router = APIRouter(prefix="/api/vercel", tags=["Vercel"])
settings = get_settings()

# In-memory token storage (TODO: move to encrypted DB for production)
user_tokens = {}


# Request/Response Models
class SetTokenRequest(BaseModel):
    vercel_token: str = Field(..., description="Vercel personal access token")


class SetTokenResponse(BaseModel):
    success: bool
    message: str


class DeployRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=100, description="Vercel project name")
    git_url: str = Field(default=None, description="GitHub repo URL (optional if project exists)")
    framework: str = Field(default=None, description="Framework preset (nextjs, vite, etc.)")
    build_command: str = Field(default=None, description="Custom build command")
    output_directory: str = Field(default=None, description="Output directory (e.g. 'dist', '.next')")
    install_command: str = Field(default=None, description="Custom install command")
    environment_variables: dict = Field(default={}, description="Environment variables")


class DeployResponse(BaseModel):
    success: bool
    deployment_url: str
    deployment_id: str
    message: str


class ProjectListResponse(BaseModel):
    success: bool
    projects: list
    message: str


class DeploymentStatusResponse(BaseModel):
    success: bool
    status: str  # BUILDING, READY, ERROR, etc.
    url: str
    created_at: str


def get_user_token(user_id: str) -> str:
    """Get stored Vercel token for user"""
    token = user_tokens.get(user_id)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Vercel token not set. Call /api/vercel/set-token first."
        )
    return token


@router.post("/set-token", response_model=SetTokenResponse)
async def set_vercel_token(
    request: SetTokenRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Store your Vercel personal access token
    
    Get token from: https://vercel.com/account/tokens
    
    This endpoint is free - no charge for storing credentials.
    """
    # Verify token by testing it against Vercel API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.vercel.com/v2/user",
            headers={"Authorization": f"Bearer {request.vercel_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid Vercel token. Please check and try again."
            )
    
    # Store token (TODO: encrypt in production)
    user_tokens[user_id] = request.vercel_token
    
    return SetTokenResponse(
        success=True,
        message="Vercel token stored successfully"
    )


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all Vercel projects
    
    Cost: $0.05 per request
    """
    try:
        token = get_user_token(user_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.vercel.com/v9/projects",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vercel API error: {response.text}"
                )
            
            data = response.json()
            projects = data.get("projects", [])
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/vercel/projects",
            cost=settings.cost_vercel_list,
            success=True
        )
        
        return ProjectListResponse(
            success=True,
            projects=projects,
            message=f"Found {len(projects)} projects"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/vercel/projects",
            cost=0,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.post("/deploy", response_model=DeployResponse)
async def deploy_project(
    request: DeployRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deploy a project to Vercel
    
    Can deploy from Git URL or trigger redeploy of existing project.
    
    Cost: $0.25 per deployment
    """
    try:
        token = get_user_token(user_id)
        
        # Build deployment payload
        payload = {
            "name": request.project_name,
            "gitSource": {},
        }
        
        if request.git_url:
            # Extract repo info from GitHub URL
            # Expected format: https://github.com/owner/repo
            parts = request.git_url.rstrip('/').split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1].replace('.git', '')
                payload["gitSource"] = {
                    "type": "github",
                    "repo": f"{owner}/{repo}",
                    "ref": "main"  # Can be made configurable
                }
        
        if request.framework:
            payload["framework"] = request.framework
        
        if request.build_command:
            payload["buildCommand"] = request.build_command
        
        if request.output_directory:
            payload["outputDirectory"] = request.output_directory
        
        if request.install_command:
            payload["installCommand"] = request.install_command
        
        if request.environment_variables:
            env_array = [
                {"key": k, "value": v, "target": ["production", "preview", "development"]}
                for k, v in request.environment_variables.items()
            ]
            payload["env"] = env_array
        
        # Create deployment
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.vercel.com/v13/deployments",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vercel API error: {response.text}"
                )
            
            data = response.json()
            deployment_url = data.get("url", "")
            deployment_id = data.get("id", "")
            
            # Add https:// prefix if not present
            if deployment_url and not deployment_url.startswith("http"):
                deployment_url = f"https://{deployment_url}"
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/vercel/deploy",
            cost=settings.cost_vercel_deploy,
            success=True
        )
        
        return DeployResponse(
            success=True,
            deployment_url=deployment_url,
            deployment_id=deployment_id,
            message="Deployment started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/vercel/deploy",
            cost=0,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy: {str(e)}"
        )


@router.get("/deployment/{deployment_id}/status", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check deployment status
    
    Cost: $0.02 per check
    """
    try:
        token = get_user_token(user_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.vercel.com/v13/deployments/{deployment_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vercel API error: {response.text}"
                )
            
            data = response.json()
            status = data.get("readyState", "UNKNOWN")
            url = data.get("url", "")
            if url and not url.startswith("http"):
                url = f"https://{url}"
            created_at = data.get("createdAt", "")
        
        # Log successful usage
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/vercel/deployment/status",
            cost=settings.cost_vercel_status,
            success=True
        )
        
        return DeploymentStatusResponse(
            success=True,
            status=status,
            url=url,
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_usage(
            db=db,
            user_id=user_id,
            endpoint="/api/vercel/deployment/status",
            cost=0,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment status: {str(e)}"
        )

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated

from ...core.database import get_db
from ...services.auth_service import AuthService
from ...schemas.user import UserCreate, UserResponse, Token
from ...core.config import settings
from ..deps import get_current_user

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user with the following information:
    - Email (must be unique)
    - Username (must be unique, 3-50 characters)
    - Password (minimum 8 characters)
    
    Returns the created user information without the password.
    """
)
async def register(
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Register a new user in the system.
    
    Args:
        user: User registration information including email, username, and password
        db: Database session
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If email or username already exists
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(user)

@router.post(
    "/token",
    response_model=Token,
    summary="Login and get access token",
    description="""
    Authenticate user and return an access token.
    Use the email address as the username when logging in.
    """
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Authenticate user and generate access token.
    
    Args:
        form_data: OAuth2 form containing username (email) and password
        db: Database session
        
    Returns:
        Token: Access token for authenticated user
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(form_data.username, form_data.password)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information",
    description="Returns the information of the currently authenticated user."
)
async def get_current_user_endpoint(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get information about the currently authenticated user.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        UserResponse: Current user information
    """
    return current_user 
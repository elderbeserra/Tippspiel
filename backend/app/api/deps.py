from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import ValidationError
from typing import Annotated, Optional

from ..core.config import settings
from ..core.database import get_db
from ..services.auth_service import AuthService
from ..schemas.user import UserResponse, TokenPayload
from ..models.user import User
from ..models.league import League

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token from OAuth2 scheme
        db: Database session
        
    Returns:
        UserResponse: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from sqlalchemy import select
    query = select(User).where(User.id == token_data.sub)
    result = db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse.model_validate(user)

async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Get the current authenticated admin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current authenticated admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return current_user

async def get_current_superadmin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Get the current authenticated superadmin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current authenticated superadmin user
        
    Raises:
        HTTPException: If user is not a superadmin
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required",
        )
    
    return current_user

def get_league_admin(league_id: int):
    """
    Factory function that returns a dependency to check if the current user is the admin (owner) of the specified league.
    
    Args:
        league_id: ID of the league to check
        
    Returns:
        A dependency function that checks if the current user is the league admin
    """
    async def _check_league_admin(
        current_user: UserResponse = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> UserResponse:
        """
        Check if the current user is the admin (owner) of the specified league.
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            UserResponse: Current authenticated user if they are the league admin
            
        Raises:
            HTTPException: If user is not the league admin
        """
        # Superadmins can perform any league admin action
        if current_user.is_superadmin:
            return current_user
            
        # Check if the user is the league owner
        from sqlalchemy import select
        query = select(League).where(League.id == league_id)
        result = db.execute(query)
        league = result.scalar_one_or_none()
        
        if not league:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found",
            )
        
        # Get the owner_id as a regular integer
        owner_id = getattr(league, 'owner_id')
        if hasattr(owner_id, 'scalar'):
            owner_id = owner_id.scalar()
        
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be the league admin to perform this action",
            )
        
        return current_user
        
    return _check_league_admin 
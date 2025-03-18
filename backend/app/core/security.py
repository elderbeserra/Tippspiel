from datetime import datetime, timedelta, UTC
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
import secrets

from .config import settings

# Password hashing configuration
pwd_context = CryptContext(
    schemes=["argon2"],  # Using Argon2 as primary hashing algorithm
    deprecated="auto",
    argon2__memory_cost=65536,  # 64MB
    argon2__time_cost=4,  # 4 iterations
    argon2__parallelism=2  # Number of parallel threads
)

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using Argon2.
    
    Args:
        plain_password: The password to verify
        hashed_password: The hashed password to verify against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    
    Args:
        password: The password to hash
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access"
    })
    
    # Add additional security claims
    to_encode["jti"] = secrets.token_urlsafe(16)  # Unique token ID
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        dict: The decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def generate_password_reset_token(email: str) -> str:
    """
    Generate a password reset token.
    
    Args:
        email: The user's email
        
    Returns:
        str: The reset token
    """
    expires = datetime.now(UTC) + timedelta(hours=24)
    token_data = {
        "sub": email,
        "exp": expires,
        "type": "reset",
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm=ALGORITHM)

def verify_password_reset_token(token: str) -> str:
    """
    Verify a password reset token.
    
    Args:
        token: The reset token to verify
        
    Returns:
        str: The user's email if token is valid
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        return payload["sub"]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        ) 
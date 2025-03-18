from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from jose import JWTError, jwt
from typing import cast
from sqlalchemy.exc import IntegrityError

from ..core.config import settings
from ..models.user import User
from ..schemas.user import UserCreate
from ..core.security import get_password_hash, verify_password, create_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def register_user(self, user_create: UserCreate) -> User:
        # Check if email already exists
        email_query = select(User).where(User.email == user_create.email)
        email_result = self.db.execute(email_query)
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Check if username already exists
        username_query = select(User).where(User.username == user_create.username)
        username_result = self.db.execute(username_query)
        if username_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
            
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=get_password_hash(user_create.password)
        )
        self.db.add(db_user)
        try:
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            self.db.rollback()
            error_message = str(e)
            if "users.email" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            elif "users.username" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration failed"
                )

    async def authenticate_user(self, email: str, password: str) -> dict:
        query = select(User).where(User.email == email)
        result = self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Get the string value of hashed_password using scalar()
        hashed_password = str(user.hashed_password)
        
        if not verify_password(password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}

    async def get_current_user(self, token: str) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = cast(int, payload.get("sub"))
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
            
        query = select(User).where(User.id == user_id)
        result = self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
        return user
        
    async def get_user_by_id(self, user_id: int) -> User:
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            User: User object if found, None otherwise
        """
        query = select(User).where(User.id == user_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none() 
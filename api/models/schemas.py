from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi_users import schemas
from .user import UserRole

class UserRead(schemas.BaseUser[int]):
    id: int
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    @property
    def full_name(self) -> Optional[str]:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name

class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    role: Optional[UserRole] = UserRole.ANNOTATOR
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserInfo(BaseModel):
    """Public user information"""
    id: int
    email: EmailStr
    role: UserRole
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

class LoginResponse(BaseModel):
    """Login response with user info"""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo 
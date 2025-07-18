from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.auth import (
    fastapi_users, 
    auth_backend, 
    current_active_user,
    current_admin_user,
    current_annotator_user
)
from api.models.user import User, UserRole
from api.models.schemas import UserCreate, UserRead, UserUpdate, UserInfo
from api.database import get_async_session

router = APIRouter()

# Include FastAPI Users routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend), 
    prefix="/jwt", 
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/register",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Custom authentication endpoints
@router.get("/me", response_model=UserInfo, tags=["auth"])
async def get_current_user_info(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user information and update last login"""
    # Update last login timestamp
    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.utcnow())
    )
    await session.commit()
    
    return UserInfo(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.get("/users/list", response_model=List[UserInfo], tags=["admin"])
async def list_users(
    admin_user: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """List all users (admin only)"""
    result = await session.execute(select(User))
    users = result.scalars().all()
    
    return [
        UserInfo(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
        for user in users
    ]

@router.patch("/users/{user_id}/role", response_model=UserInfo, tags=["admin"])
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    admin_user: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update user role (admin only)"""
    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update role
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(role=new_role)
    )
    await session.commit()
    await session.refresh(user)
    
    return UserInfo(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.get("/protected/admin", tags=["admin"])
async def admin_only_endpoint(admin_user: User = Depends(current_admin_user)):
    """Admin-only endpoint for testing"""
    return {
        "message": "Hello Admin!",
        "user": admin_user.email,
        "role": admin_user.role
    }

@router.get("/protected/annotator", tags=["annotator"])
async def annotator_endpoint(user: User = Depends(current_annotator_user)):
    """Annotator endpoint (admins can also access)"""
    return {
        "message": "Hello Annotator!",
        "user": user.email,
        "role": user.role
    } 
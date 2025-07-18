from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from fastapi_users.db import SQLAlchemyBaseUserTable
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANNOTATOR = "annotator"

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    hashed_password = Column(String(1024), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Custom fields
    role = Column(Enum(UserRole), default=UserRole.ANNOTATOR, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self) -> Optional[str]:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_superuser
    
    @property
    def is_annotator(self) -> bool:
        return self.role == UserRole.ANNOTATOR 
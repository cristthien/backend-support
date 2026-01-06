"""
Authentication Pydantic schemas
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRoleEnum(str, Enum):
    """User role enum for API responses"""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(BaseModel):
    """Schema for user creation (email OTP)"""
    email: EmailStr


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication"""
    credential: str  # Google ID token


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    auth_provider: str
    role: str
    is_active: bool
    is_verified: bool
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: int
    email: str


class OTPRequest(BaseModel):
    """Request to send OTP"""
    email: EmailStr


class OTPVerify(BaseModel):
    """Verify OTP code"""
    email: EmailStr
    code: str


class AccountResponse(BaseModel):
    """Account info in OTP verify response"""
    id: int
    name: str
    email: str
    role: str


class OTPVerifyResponse(BaseModel):
    """Response for OTP verification - matches frontend schema"""
    token: str
    expiresAt: str
    account: AccountResponse


class UpdateUserRoleRequest(BaseModel):
    """Request to update user role (admin only)"""
    role: UserRoleEnum


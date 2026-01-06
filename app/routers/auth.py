"""
Authentication routes for Google OAuth and Email OTP
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from typing import List

from app.db.session import get_db
from app.schemas.auth import (
    OTPRequest, OTPVerify, Token, UserResponse,
    GoogleAuthRequest, OTPVerifyResponse, AccountResponse,
    UpdateUserRoleRequest
)
from app.models.user import User, AuthProvider, UserRole
from app.repositories import user_repository, otp_repository
from app.services.auth_service import create_access_token, generate_otp
from app.services.email_service import send_otp_email
from app.core.security import get_current_active_user, require_admin
from app.core.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/email/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(
    request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request OTP for email login (passwordless)
    Creates user if doesn't exist, sends OTP to email
    """
    try:
        # Check if user exists
        user = await user_repository.get_user_by_email(db, request.email)
        
        # If user doesn't exist, create one
        if not user:
            user = await user_repository.create_user(
                db=db,
                email=request.email,
                auth_provider=AuthProvider.EMAIL_OTP,
                is_verified=False
            )
            logger.info(f"Created new user with email: {request.email}")
        
        # Generate and save OTP
        otp_code = generate_otp()
        await otp_repository.create_otp(db, user.id, otp_code)
        
        # Send OTP via email
        email_sent = await send_otp_email(request.email, otp_code)
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email"
            )
        
        return {
            "message": "OTP sent to your email",
            "email": request.email
        }
        
    except Exception as e:
        logger.error(f"Error in request_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process OTP request"
        )


@router.post("/email/verify-otp", response_model=OTPVerifyResponse)
async def verify_otp(
    request: OTPVerify,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and return JWT token
    """
    # Get user
    user = await user_repository.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify OTP
    otp = await otp_repository.get_valid_otp(db, user.id, request.code)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Mark OTP as used
    await otp_repository.mark_otp_used(db, otp)
    
    # Verify user if not already verified
    if not user.is_verified:
        user = await user_repository.verify_user(db, user)
    
    # Create access token with expiration time
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=expires_delta
    )
    
    # Calculate expiration datetime
    from datetime import datetime, timezone
    expires_at = datetime.now(timezone.utc) + expires_delta
    
    return OTPVerifyResponse(
        token=access_token,
        expiresAt=expires_at.isoformat(),
        account=AccountResponse(
            id=user.id,
            name=user.full_name or user.email.split('@')[0],
            email=user.email,
            role=user.role.value
        )
    )


@router.post("/google", response_model=Token)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google OAuth
    """
    try:
        # Verify Google ID token
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            settings.google_client_id
        )
        
        # Extract user info from token
        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        full_name = idinfo.get("name")
        profile_picture = idinfo.get("picture")
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token"
            )
        
        # Check if user exists by Google ID
        user = await user_repository.get_user_by_google_id(db, google_id)
        
        # If not found, check by email
        if not user:
            user = await user_repository.get_user_by_email(db, email)
        
        # Create new user if doesn't exist
        if not user:
            user = await user_repository.create_user(
                db=db,
                email=email,
                auth_provider=AuthProvider.GOOGLE,
                google_id=google_id,
                full_name=full_name,
                profile_picture=profile_picture,
                is_verified=True  # Google users are pre-verified
            )
            logger.info(f"Created new Google user: {email}")
        
        # Create access token
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except ValueError as e:
        # Invalid token
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google credentials"
        )
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate with Google"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Get all users (admin only)
    """
    users = await user_repository.get_all_users(db)
    return [UserResponse.model_validate(user) for user in users]


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Update user role (admin only)
    """
    # Get target user
    user = await user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from demoting themselves
    if user.id == admin_user.id and request.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )
    
    # Update role
    updated_user = await user_repository.update_user_role(db, user, UserRole(request.role.value))
    return UserResponse.model_validate(updated_user)

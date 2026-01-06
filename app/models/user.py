"""
User model for authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from app.db.base import Base, TimestampMixin
import enum


class AuthProvider(str, enum.Enum):
    """Authentication provider types"""
    EMAIL_OTP = "email_otp"
    GOOGLE = "google"


class UserRole(str, enum.Enum):
    """User role types for authorization"""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    """User model for storing user information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    auth_provider = Column(SQLEnum(AuthProvider), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # For Google OAuth, we store additional info
    google_id = Column(String, unique=True, nullable=True, index=True)
    full_name = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)


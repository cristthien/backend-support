"""
OTP model for email-based authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime, timedelta
from app.db.base import Base
from app.core.config import settings


class OTP(Base):
    """OTP model for email verification codes"""
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @classmethod
    def create_expiry(cls) -> datetime:
        """Create expiry datetime for OTP"""
        return datetime.utcnow() + timedelta(minutes=settings.otp_expire_minutes)
    
    def is_expired(self) -> bool:
        """Check if OTP is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if OTP is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()

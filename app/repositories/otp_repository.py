"""
OTP repository for database operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.otp import OTP
from datetime import datetime
from typing import Optional


async def create_otp(db: AsyncSession, user_id: int, code: str) -> OTP:
    """Create a new OTP"""
    otp = OTP(
        user_id=user_id,
        code=code,
        expires_at=OTP.create_expiry(),
        is_used=False
    )
    db.add(otp)
    await db.commit()
    await db.refresh(otp)
    return otp


async def get_valid_otp(db: AsyncSession, user_id: int, code: str) -> Optional[OTP]:
    """Get valid (unused and not expired) OTP for user"""
    result = await db.execute(
        select(OTP)
        .where(OTP.user_id == user_id)
        .where(OTP.code == code)
        .where(OTP.is_used == False)
        .where(OTP.expires_at > datetime.utcnow())
        .order_by(OTP.created_at.desc())
    )
    return result.scalar_one_or_none()


async def mark_otp_used(db: AsyncSession, otp: OTP) -> OTP:
    """Mark OTP as used"""
    otp.is_used = True
    await db.commit()
    await db.refresh(otp)
    return otp


async def delete_expired_otps(db: AsyncSession) -> int:
    """Delete all expired OTPs"""
    result = await db.execute(
        delete(OTP).where(OTP.expires_at < datetime.utcnow())
    )
    await db.commit()
    return result.rowcount

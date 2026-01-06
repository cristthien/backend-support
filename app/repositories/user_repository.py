"""
User repository for database operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, AuthProvider, UserRole
from typing import Optional, List


async def count_users(db: AsyncSession) -> int:
    """Count total users in database"""
    result = await db.execute(select(func.count(User.id)))
    return result.scalar() or 0


async def create_user(
    db: AsyncSession,
    email: str,
    auth_provider: AuthProvider,
    google_id: Optional[str] = None,
    full_name: Optional[str] = None,
    profile_picture: Optional[str] = None,
    is_verified: bool = False
) -> User:
    """Create a new user. First user is auto-promoted to ADMIN."""
    # Check if this is the first user
    user_count = await count_users(db)
    role = UserRole.ADMIN if user_count == 0 else UserRole.USER
    
    user = User(
        email=email,
        auth_provider=auth_provider,
        google_id=google_id,
        full_name=full_name,
        profile_picture=profile_picture,
        is_verified=is_verified,
        is_active=True,
        role=role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
    """Get user by Google ID"""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def verify_user(db: AsyncSession, user: User) -> User:
    """Mark user as verified"""
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user


async def get_all_users(db: AsyncSession) -> List[User]:
    """Get all users (for admin)"""
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def update_user_role(db: AsyncSession, user: User, new_role: UserRole) -> User:
    """Update user role"""
    user.role = new_role
    await db.commit()
    await db.refresh(user)
    return user


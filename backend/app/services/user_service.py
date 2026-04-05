from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..security import verify_password, get_password_hash


class UserService:
    """Service for user-related operations"""

    @staticmethod
    async def create(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        is_superuser: bool = False
    ) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_superuser=is_superuser
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get a user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = await UserService.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all users (superuser only)"""
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_all_with_pagination(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all users with pagination"""
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        users = result.scalars().all()

        # Get total count
        count_result = await db.execute(select(User.id))
        total = len(count_result.scalars().all())

        return {
            "items": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        email: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """Update user information"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            return None

        if email is not None:
            # Check if email is already taken by another user
            existing_user = await UserService.get_by_email(db, email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already registered")

            user.email = email

        if is_active is not None:
            user.is_active = is_active

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> Optional[User]:
        """Change user password"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            return None

        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Incorrect old password")

        # Update password
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """Delete a user"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            return False

        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    async def is_superuser(db: AsyncSession, user: User) -> bool:
        """Check if user is a superuser"""
        return user.is_superuser

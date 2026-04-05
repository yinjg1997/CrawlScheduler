"""
重置user用户密码为user123
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from app.database import async_session
from app.models.user import User
from app.security import get_password_hash


async def reset_user_password():
    """重置user用户密码"""
    async with async_session() as db:
        # 查找user用户
        result = await db.execute(select(User).where(User.username == "user"))
        user_user = result.scalar_one_or_none()

        if user_user:
            # 重置密码为user123
            hashed_password = get_password_hash("user123")
            await db.execute(
                update(User)
                .where(User.username == "user")
                .values(hashed_password=hashed_password)
            )
            await db.commit()
            print("✅ user用户密码已重置为 user123")
        else:
            print("❌ 未找到user用户")


if __name__ == "__main__":
    asyncio.run(reset_user_password())

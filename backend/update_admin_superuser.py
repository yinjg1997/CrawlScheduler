"""
将admin用户设置为超级用户
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from app.database import async_session
from app.models.user import User


async def update_admin_superuser():
    """将admin用户设置为超级用户"""
    async with async_session() as db:
        # 查找admin用户
        result = await db.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()

        if admin_user:
            # 更新admin用户为超级用户
            await db.execute(
                update(User)
                .where(User.username == "admin")
                .values(is_superuser=True)
            )
            await db.commit()
            print("✅ admin用户已成功设置为超级用户")
        else:
            print("❌ 未找到admin用户")


if __name__ == "__main__":
    asyncio.run(update_admin_superuser())

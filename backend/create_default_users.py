"""
创建默认用户脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import async_session
from app.services.user_service import UserService


async def create_default_users():
    """创建默认用户"""
    default_users = [
        {
            "username": "admin",
            "email": "admin@crwlscheduler.com",
            "password": "admin123",
            "is_superuser": True  # admin为管理员
        },
        {
            "username": "user",
            "email": "user@crwlscheduler.com",
            "password": "user123",
            "is_superuser": False
        }
    ]

    async with async_session() as db:
        for user_data in default_users:
            # 检查用户是否已存在
            existing_user = await UserService.get_by_username(db, user_data["username"])

            if existing_user:
                print(f"用户 '{user_data['username']}' 已存在，跳过创建")
                continue

            # 创建用户
            user = await UserService.create(
                db,
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                is_superuser=user_data["is_superuser"]
            )

            print(f"✅ 用户创建成功:")
            print(f"   用户名: {user.username}")
            print(f"   邮箱: {user.email}")
            print(f"   是否管理员: {'是' if user.is_superuser else '否'}")
            print()

        print("\n所有默认用户创建完成！")
        print("\n登录信息:")
        print("=" * 50)
        for user_data in default_users:
            print(f"用户名: {user_data['username']}")
            print(f"密码:   {user_data['password']}")
            print(f"角色:   {'管理员' if user_data['is_superuser'] else '普通用户'}")
            print("-" * 50)
        print("=" * 50)
        print("\n⚠️  重要提示:")
        print("1. 生产环境部署时请立即修改默认密码")
        print("2. 建议在首次登录后修改密码")
        print("3. 如果不需要默认账号，可以删除这些用户")


if __name__ == "__main__":
    asyncio.run(create_default_users())

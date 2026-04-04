from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from typing import List, Optional, Dict, Any
import subprocess
import shutil

from ..models.python_environment import PythonEnvironment
from ..schemas.python_environment import PythonEnvironmentCreate, PythonEnvironmentUpdate, PythonEnvironmentListItem, PythonEnvironmentResponse


class PythonEnvironmentService:
    """Service for managing Python environments"""

    @staticmethod
    async def create(db: AsyncSession, env: PythonEnvironmentCreate) -> PythonEnvironment:
        """Create a new Python environment"""
        db_env = PythonEnvironment(**env.model_dump())
        db.add(db_env)
        await db.commit()
        await db.refresh(db_env)
        return db_env

    @staticmethod
    async def get_by_id(db: AsyncSession, env_id: int) -> Optional[PythonEnvironment]:
        """Get a Python environment by ID"""
        result = await db.execute(
            select(PythonEnvironment).where(PythonEnvironment.id == env_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[PythonEnvironment]:
        """Get all Python environments"""
        result = await db.execute(
            select(PythonEnvironment)
            .offset(skip)
            .limit(limit)
            .order_by(PythonEnvironment.name)
        )
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession,
        env_id: int,
        env_update: PythonEnvironmentUpdate
    ) -> Optional[PythonEnvironment]:
        """Update a Python environment"""
        env = await PythonEnvironmentService.get_by_id(db, env_id)
        if not env:
            return None

        update_data = env_update.model_dump(exclude_unset=True)
        await db.execute(
            update(PythonEnvironment)
            .where(PythonEnvironment.id == env_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(env)
        return env

    @staticmethod
    async def delete(db: AsyncSession, env_id: int) -> bool:
        """Delete a Python environment"""
        # Don't allow deletion of default system environments
        env = await PythonEnvironmentService.get_by_id(db, env_id)
        if not env:
            return False
        if env.is_default:
            raise ValueError("Cannot delete default system environment")

        result = await db.execute(
            delete(PythonEnvironment).where(PythonEnvironment.id == env_id)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    def get_system_python() -> Optional[dict]:
        """Get system Python information"""
        try:
            python_path = shutil.which("python3") or shutil.which("python")
            if python_path:
                result = subprocess.run(
                    [python_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=2  # Reduced timeout from 5 to 2 seconds
                )
                if result.returncode == 0:
                    version = result.stderr.strip() or result.stdout.strip()
                    return {
                        "id": -1,  # Negative ID for system environments
                        "name": "System Python",
                        "path": python_path,
                        "version": version,
                        "type": "system",
                        "is_active": True,
                        "is_default": True
                    }
        except Exception:
            pass
        return None

    @staticmethod
    def get_conda_environments() -> List[dict]:
        """Get conda environments"""
        environments = []
        env_counter = -2  # Start from -2 for conda environments
        try:
            conda_path = shutil.which("conda")
            if conda_path:
                result = subprocess.run(
                    ["conda", "env", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('#') or not line:
                            continue

                        parts = line.split()
                        if not parts:
                            continue

                        env_name = parts[0]
                        is_active = env_name.endswith('*')
                        if is_active:
                            env_name = env_name[:-1].strip()

                        env_path = None
                        if len(parts) > 1:
                            env_path = parts[-1]

                        # Get Python path first
                        if env_path:
                            python_path = f"{env_path}/bin/python"
                        else:
                            python_path = f"{conda_path.replace('/bin/conda', '/envs/' + env_name + '/bin/python')}"

                        # Get Python version by directly calling the Python executable (much faster than conda run)
                        try:
                            version_result = subprocess.run(
                                [python_path, "--version"],
                                capture_output=True,
                                text=True,
                                timeout=2  # Reduced timeout from 10 to 2 seconds
                            )
                            version = version_result.stderr.strip() or version_result.stdout.strip()
                        except Exception:
                            version = "Unknown"

                        environments.append({
                            "id": env_counter,
                            "name": f"conda: {env_name}" + (" (active)" if is_active else ""),
                            "path": python_path,
                            "version": version,
                            "type": "conda",
                            "is_active": is_active,
                            "is_default": False
                        })
                        env_counter -= 1
        except Exception as e:
            print(f"Error getting conda environments: {e}")

        return environments

    @staticmethod
    async def get_all_environments_with_system(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get all environments including system and conda environments with pagination"""
        environments = []

        # Add system Python
        system_python = PythonEnvironmentService.get_system_python()
        if system_python:
            environments.append(PythonEnvironmentListItem(**system_python))

        # Add conda environments
        conda_envs = PythonEnvironmentService.get_conda_environments()
        for env in conda_envs:
            environments.append(PythonEnvironmentListItem(**env))

        # Add user-defined environments
        user_envs = await PythonEnvironmentService.get_all(db, skip=0, limit=1000)  # Get all user envs first
        for env in user_envs:
            environments.append(PythonEnvironmentListItem(
                id=env.id,
                name=env.name,
                path=env.path,
                version=env.version,
                type='user',
                is_active=env.is_active
            ))

        # Get total count
        total = len(environments)

        # Apply pagination
        paginated_environments = environments[skip:skip + limit]

        return {
            "total": total,
            "items": paginated_environments
        }

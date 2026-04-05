from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from ..models import Project
from ..schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for managing project operations"""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all projects with crawler count and filtering"""
        # Build base query
        query = select(Project)

        # Apply search filter (name or description)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Project.name.like(search_pattern),
                    Project.description.like(search_pattern)
                )
            )

        # Apply date range filter
        conditions = []
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from)
                conditions.append(Project.created_at >= date_from_dt)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to)
                # Add one day to include the end date
                from datetime import timedelta
                date_to_dt = date_to_dt + timedelta(days=1)
                conditions.append(Project.created_at < date_to_dt)
            except ValueError:
                pass

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count with filters
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results with crawler count
        from ..models import Crawler
        query = query.outerjoin(Crawler).options(selectinload(Project.crawlers)).group_by(Project.id)
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Project.created_at.desc())
        )
        items = list(result.scalars().all())

        # Add crawler count to each item
        for item in items:
            item.crawler_count = len(item.crawlers) if item.crawlers else 0

        return {
            "total": total,
            "items": items
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
        """Get a project by ID"""
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.crawlers))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project:
            project.crawler_count = len(project.crawlers) if project.crawlers else 0
        return project

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Project]:
        """Get a project by name"""
        result = await db.execute(
            select(Project).where(Project.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_projects(db: AsyncSession) -> List[Project]:
        """Get all active projects"""
        result = await db.execute(
            select(Project)
            .where(Project.is_active == True)
            .order_by(Project.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, project: ProjectCreate) -> Project:
        """Create a new project"""
        # Check if project with same name exists
        existing = await ProjectService.get_by_name(db, project.name)
        if existing:
            raise ValueError(f"Project with name '{project.name}' already exists")

        db_project = Project(**project.model_dump())
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        db_project.crawler_count = 0
        return db_project

    @staticmethod
    async def update(
        db: AsyncSession,
        project_id: int,
        project_update: ProjectUpdate
    ) -> Optional[Project]:
        """Update a project"""
        db_project = await ProjectService.get_by_id(db, project_id)
        if not db_project:
            return None

        # Check if new name conflicts with existing project
        if project_update.name and project_update.name != db_project.name:
            existing = await ProjectService.get_by_name(db, project_update.name)
            if existing:
                raise ValueError(f"Project with name '{project_update.name}' already exists")

        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_project, field, value)

        await db.commit()
        await db.refresh(db_project)
        db_project.crawler_count = len(db_project.crawlers) if db_project.crawlers else 0
        return db_project

    @staticmethod
    async def delete(db: AsyncSession, project_id: int) -> bool:
        """Delete a project (will cascade delete all crawlers)"""
        db_project = await ProjectService.get_by_id(db, project_id)
        if not db_project:
            return False

        await db.execute(
            delete(Project).where(Project.id == project_id)
        )
        await db.commit()
        return True

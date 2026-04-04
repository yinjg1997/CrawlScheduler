from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from ..models import TaskExecution, Crawler
from ..schemas.task import TaskExecutionResponse


class PaginatedResponse(BaseModel):
    total: int
    items: List[TaskExecutionResponse]


class TaskService:
    """Service for managing task execution operations"""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        crawler_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> dict:
        """Get all task executions with filters and pagination"""
        query = select(TaskExecution)

        if crawler_id is not None:
            query = query.where(TaskExecution.crawler_id == crawler_id)

        if status is not None:
            query = query.where(TaskExecution.status == status)

        # Search by crawler name (via join)
        if search:
            query = query.join(Crawler).where(
                Crawler.name.ilike(f"%{search}%")
            )

        # Date range filter
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.where(TaskExecution.created_at >= from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                # Add one day to include the end date
                to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.where(TaskExecution.created_at <= to_date)
            except ValueError:
                pass

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.options(
            selectinload(TaskExecution.crawler),
            selectinload(TaskExecution.schedule)
        ).order_by(TaskExecution.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return {
            "total": total,
            "items": items
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, task_id: int) -> Optional[TaskExecution]:
        """Get a task execution by ID"""
        result = await db.execute(
            select(TaskExecution)
            .options(
                selectinload(TaskExecution.crawler),
                selectinload(TaskExecution.schedule)
            )
            .where(TaskExecution.id == task_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        crawler_id: int,
        triggered_by: str = "manual",
        schedule_id: Optional[int] = None
    ) -> TaskExecution:
        """Create a new task execution"""
        # Verify crawler exists
        crawler = await db.get(Crawler, crawler_id)
        if not crawler:
            raise ValueError(f"Crawler with ID {crawler_id} not found")

        task = TaskExecution(
            crawler_id=crawler_id,
            status="pending",
            triggered_by=triggered_by,
            schedule_id=schedule_id
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Reload with relationships to avoid MissingGreenlet error
        result = await db.execute(
            select(TaskExecution)
            .options(
                selectinload(TaskExecution.crawler),
                selectinload(TaskExecution.schedule)
            )
            .where(TaskExecution.id == task.id)
        )
        return result.scalar_one()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        task_id: int,
        status: str,
        exit_code: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[TaskExecution]:
        """Update task execution status"""
        task = await TaskService.get_by_id(db, task_id)
        if not task:
            return None

        task.status = status

        if status == "running":
            task.started_at = datetime.utcnow()
        elif status in ["success", "failed", "cancelled"]:
            task.finished_at = datetime.utcnow()
            if task.started_at:
                task.duration = int((task.finished_at - task.started_at).total_seconds())

        if exit_code is not None:
            task.exit_code = exit_code

        if error_message is not None:
            task.error_message = error_message

        await db.commit()
        await db.refresh(task)

        # Reload with relationships to avoid MissingGreenlet error
        result = await db.execute(
            select(TaskExecution)
            .options(
                selectinload(TaskExecution.crawler),
                selectinload(TaskExecution.schedule)
            )
            .where(TaskExecution.id == task_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_log_file_path(db: AsyncSession, task_id: int) -> Optional[str]:
        """Get log file path for a task"""
        task = await TaskService.get_by_id(db, task_id)
        if not task:
            return None
        return task.log_file_path

    @staticmethod
    async def get_logs(db: AsyncSession, task_id: int, offset: int = 0, limit: int = 1000) -> List[str]:
        """Get log lines for a task"""
        task = await TaskService.get_by_id(db, task_id)
        if not task or not task.log_file_path:
            return []

        try:
            with open(task.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[offset:offset + limit]
        except FileNotFoundError:
            return []

    @staticmethod
    async def cancel(db: AsyncSession, task_id: int) -> Optional[TaskExecution]:
        """Cancel a task execution"""
        task = await TaskService.get_by_id(db, task_id)
        if not task:
            return None

        if task.status not in ["pending", "running"]:
            raise ValueError(f"Cannot cancel task with status: {task.status}")

        return await TaskService.update_status(db, task_id, "cancelled")

    @staticmethod
    async def get_statistics(db: AsyncSession, crawler_id: Optional[int] = None) -> dict:
        """Get task execution statistics"""
        query = select(TaskExecution)

        if crawler_id is not None:
            query = query.where(TaskExecution.crawler_id == crawler_id)

        result = await db.execute(
            query.with_entities(
                func.count(TaskExecution.id).label('total'),
                func.sum(func.case((TaskExecution.status == 'success', 1), else_=0)).label('success'),
                func.sum(func.case((TaskExecution.status == 'failed', 1), else_=0)).label('failed'),
                func.sum(func.case((TaskExecution.status == 'running', 1), else_=0)).label('running')
            )
        )

        row = result.fetchone()
        return {
            'total': row.total or 0,
            'success': row.success or 0,
            'failed': row.failed or 0,
            'running': row.running or 0
        }

    @staticmethod
    async def delete(db: AsyncSession, task_id: int) -> bool:
        """Delete a task execution"""
        task = await TaskService.get_by_id(db, task_id)
        if not task:
            return False

        # Check if task is running
        if task.status == 'running':
            raise ValueError("Cannot delete a running task")

        # Delete log file if exists
        if task.log_file_path:
            try:
                import os
                if os.path.exists(task.log_file_path):
                    os.remove(task.log_file_path)
            except Exception:
                pass

        await db.delete(task)
        await db.commit()
        return True

    @staticmethod
    async def bulk_delete(db: AsyncSession, task_ids: List[int]) -> dict:
        """Delete multiple task executions"""
        deleted_count = 0
        skipped_count = 0

        for task_id in task_ids:
            try:
                success = await TaskService.delete(db, task_id)
                if success:
                    deleted_count += 1
                else:
                    skipped_count += 1
            except ValueError:
                # Task is running, skip it
                skipped_count += 1
            except Exception:
                # Other errors, skip it
                skipped_count += 1

        return {
            'deleted_count': deleted_count,
            'skipped_count': skipped_count,
            'total_requested': len(task_ids)
        }

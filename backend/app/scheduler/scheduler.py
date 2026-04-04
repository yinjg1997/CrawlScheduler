from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import async_session
from ..services.task_service import TaskService
from ..services.schedule_service import ScheduleService
from ..config import settings


# Global scheduler instance
scheduler = AsyncIOScheduler()


async def execute_scheduled_task(schedule_id: int) -> None:
    """Execute a scheduled task"""
    async with async_session() as db:
        try:
            # Get schedule
            schedule = await ScheduleService.get_by_id(db, schedule_id)
            if not schedule or not schedule.is_active:
                return

            # Create task execution
            task = await TaskService.create(
                db,
                crawler_id=schedule.crawler_id,
                triggered_by="schedule",
                schedule_id=schedule_id
            )

            # Update next run time
            await ScheduleService.update_next_run_time(db, schedule_id)

            # Execute task (run in background)
            from ..services.executor import TaskExecutor
            asyncio = __import__('asyncio')
            asyncio.create_task(TaskExecutor.execute(db, task.id))

        except Exception as e:
            print(f"Error executing scheduled task {schedule_id}: {e}")


async def add_schedule_job(schedule_id: int, cron_expression: str) -> None:
    """Add a schedule job to the scheduler"""
    try:
        # Parse cron expression (5 parts: minute hour day month weekday)
        parts = cron_expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        minute, hour, day, month, day_of_week = parts

        scheduler.add_job(
            execute_scheduled_task,
            trigger=CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            ),
            id=str(schedule_id),
            args=[schedule_id],
            replace_existing=True
        )
    except Exception as e:
        print(f"Error adding schedule job {schedule_id}: {e}")
        raise


async def remove_schedule_job(schedule_id: int) -> None:
    """Remove a schedule job from the scheduler"""
    try:
        scheduler.remove_job(str(schedule_id))
    except Exception as e:
        print(f"Error removing schedule job {schedule_id}: {e}")


async def update_schedule_job(schedule_id: int, cron_expression: str, is_active: bool) -> None:
    """Update a schedule job in the scheduler"""
    if is_active:
        await add_schedule_job(schedule_id, cron_expression)
    else:
        await remove_schedule_job(schedule_id)


async def setup_scheduler() -> None:
    """Setup scheduler with all active schedules from database"""
    if not settings.SCHEDULER_ENABLED:
        return

    async with async_session() as db:
        try:
            schedules = await ScheduleService.get_active_schedules(db)

            for schedule in schedules:
                await add_schedule_job(schedule.id, schedule.cron_expression)

            scheduler.start()
            print(f"Scheduler started with {len(schedules)} active schedules")

        except Exception as e:
            print(f"Error setting up scheduler: {e}")


async def shutdown_scheduler() -> None:
    """Shutdown scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shutdown")

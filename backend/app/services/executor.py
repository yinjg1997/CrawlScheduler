import asyncio
import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Set
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket
from .task_service import TaskService
from .crawler_service import CrawlerService
from ..config import settings


class TaskExecutor:
    """Service for executing crawler tasks"""

    # Track running tasks: {task_id: subprocess.Popen}
    _running_tasks: Dict[int, subprocess.Popen] = {}

    # Track WebSocket connections: {task_id: Set[WebSocket]}
    _ws_connections: Dict[int, Set[WebSocket]] = {}

    @staticmethod
    async def execute(db: AsyncSession, task_id: int) -> None:
        """Execute a crawler task"""
        from ..models import TaskExecution, Crawler
        from ..database import async_session

        # Use a new session for the executor to avoid conflicts
        async with async_session() as executor_db:
            task = await executor_db.get(TaskExecution, task_id)
            if not task:
                raise ValueError(f"Task with ID {task_id} not found")

            crawler = await executor_db.get(Crawler, task.crawler_id)
            if not crawler:
                raise ValueError(f"Crawler with ID {task.crawler_id} not found")

            # Create log file
            log_file_path = settings.LOGS_DIR / f"task_{task_id}_{datetime.now(ZoneInfo(settings.TIMEZONE)).strftime('%Y%m%d_%H%M%S')}.log"
            task.log_file_path = str(log_file_path)
            await executor_db.commit()

            # Update task status to running
            task = await TaskService.update_status(executor_db, task_id, "running")
            await TaskExecutor._broadcast_status_update(task_id, task.status)

        try:
            # Prepare working directory
            work_dir = Path(crawler.working_directory)
            work_dir.mkdir(parents=True, exist_ok=True)

            # Build execution command with custom Python interpreter if specified
            exec_command = crawler.command
            if crawler.python_executable:
                import re
                # Check if command already starts with python
                if re.match(r'^python3?\s+', crawler.command, re.IGNORECASE):
                    # Replace python with custom interpreter
                    exec_command = re.sub(
                        r'^python3?\s+',
                        f'{crawler.python_executable} ',
                        crawler.command,
                        count=1,
                        flags=re.IGNORECASE
                    )
                else:
                    # Wrap command with custom python interpreter
                    exec_command = f'{crawler.python_executable} -m {crawler.command}'

            # Execute command
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                process = await asyncio.create_subprocess_shell(
                    exec_command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=str(work_dir),
                    shell=True
                )

                # Track running process
                TaskExecutor._running_tasks[task_id] = process

                # Wait for process to complete
                return_code = await process.wait()

            # Update task status based on exit code
            status = "success" if return_code == 0 else "failed"
            task = await TaskService.update_status(
                executor_db,
                task_id,
                status,
                exit_code=return_code,
                error_message=f"Process exited with code {return_code}" if return_code != 0 else None
            )
            await TaskExecutor._broadcast_status_update(task_id, task.status)

        except asyncio.CancelledError:
            # Task was cancelled
            task = await TaskService.update_status(executor_db, task_id, "cancelled")
            await TaskExecutor._broadcast_status_update(task_id, task.status)
            raise
        except Exception as e:
            # Task failed with error
            task = await TaskService.update_status(
                executor_db,
                task_id,
                "failed",
                error_message=str(e)
            )
            await TaskExecutor._broadcast_status_update(task_id, task.status)
        finally:
            # Remove from running tasks
            if task_id in TaskExecutor._running_tasks:
                del TaskExecutor._running_tasks[task_id]

    @staticmethod
    async def cancel_task(task_id: int) -> bool:
        """Cancel a running task"""
        if task_id not in TaskExecutor._running_tasks:
            return False

        process = TaskExecutor._running_tasks[task_id]
        process.terminate()

        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

        return True

    @staticmethod
    def add_ws_connection(task_id: int, websocket: WebSocket) -> None:
        """Add a WebSocket connection for a task"""
        if task_id not in TaskExecutor._ws_connections:
            TaskExecutor._ws_connections[task_id] = set()
        TaskExecutor._ws_connections[task_id].add(websocket)

    @staticmethod
    def remove_ws_connection(task_id: int, websocket: WebSocket) -> None:
        """Remove a WebSocket connection for a task"""
        if task_id in TaskExecutor._ws_connections:
            TaskExecutor._ws_connections[task_id].discard(websocket)
            if not TaskExecutor._ws_connections[task_id]:
                del TaskExecutor._ws_connections[task_id]

    @staticmethod
    async def stream_logs(task_id: int, websocket: WebSocket) -> None:
        """Stream logs to a WebSocket connection"""
        TaskExecutor.add_ws_connection(task_id, websocket)

        try:
            # Send buffered logs first
            log_file = Path(settings.LOGS_DIR) / f"task_{task_id}.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        await websocket.send_json({"type": "log", "data": line.rstrip()})

            # Stream new logs as they arrive
            last_size = log_file.stat().st_size if log_file.exists() else 0

            while task_id in TaskExecutor._running_tasks or task_id in TaskExecutor._ws_connections:
                try:
                    if log_file.exists():
                        current_size = log_file.stat().st_size
                        if current_size > last_size:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                                for line in new_lines:
                                    await websocket.send_json({"type": "log", "data": line.rstrip()})
                            last_size = current_size

                    await asyncio.sleep(0.5)
                except Exception:
                    break

            await websocket.send_json({"type": "complete"})

        finally:
            TaskExecutor.remove_ws_connection(task_id, websocket)

    @staticmethod
    async def _broadcast_status_update(task_id: int, status: str) -> None:
        """Broadcast status update to all connected clients"""
        if task_id in TaskExecutor._ws_connections:
            for ws in list(TaskExecutor._ws_connections[task_id]):
                try:
                    await ws.send_json({"type": "status", "task_id": task_id, "status": status})
                except Exception:
                    # Connection might be closed
                    TaskExecutor.remove_ws_connection(task_id, ws)

    @staticmethod
    def is_task_running(task_id: int) -> bool:
        """Check if a task is currently running"""
        return task_id in TaskExecutor._running_tasks

    @staticmethod
    def get_running_tasks() -> list:
        """Get list of currently running task IDs"""
        return list(TaskExecutor._running_tasks.keys())

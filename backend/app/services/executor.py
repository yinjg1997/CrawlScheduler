import asyncio
import subprocess
import os
import platform
import signal
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket
import psutil
from .task_service import TaskService
from .crawler_service import CrawlerService
from ..config import settings


class TaskExecutor:
    """Service for executing crawler tasks with cross-platform support"""

    # Track running tasks: {task_id: process_info}
    # process_info: {'process': asyncio.subprocess.Process, 'psutil': psutil.Process}
    _running_tasks: Dict[int, Dict] = {}

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

            # Get crawler with project relationship
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            result = await executor_db.execute(
                select(Crawler)
                .options(selectinload(Crawler.project))
                .where(Crawler.id == task.crawler_id)
            )
            crawler = result.scalar_one_or_none()
            if not crawler:
                raise ValueError(f"Crawler with ID {task.crawler_id} not found")

            # Get working directory and python executable from project
            working_directory = None
            python_executable = None

            if crawler.project:
                working_directory = crawler.project.working_directory
                python_executable = crawler.project.python_executable

            if not working_directory:
                raise ValueError(f"Crawler must be associated with a project that has a working directory")

            # Create log file with fixed name for WebSocket streaming
            log_file_path = settings.LOGS_DIR / f"task_{task_id}.log"
            task.log_file_path = str(log_file_path)
            await executor_db.commit()

            # Update task status to running
            task = await TaskService.update_status(executor_db, task_id, "running")
            await TaskExecutor._broadcast_status_update(task_id, task.status)

        try:
            # Prepare working directory
            work_dir = Path(working_directory)
            work_dir.mkdir(parents=True, exist_ok=True)

            # Build cross-platform execution command
            exec_command, use_shell = TaskExecutor._build_exec_command(crawler.command, python_executable)

            # Prepare environment variables
            env = TaskExecutor._prepare_environment()

            # Create log file with appropriate mode
            with open(log_file_path, 'w', encoding='utf-8', buffering=1) as log_file:
                # Execute command - use create_subprocess_exec for better cross-platform support
                process = await TaskExecutor._execute_command(
                    exec_command,
                    log_file,
                    str(work_dir),
                    env,
                    use_shell
                )

                # Get psutil process for enhanced control
                psutil_proc = psutil.Process(process.pid)

                # Track running process with both asyncio and psutil handles
                TaskExecutor._running_tasks[task_id] = {
                    'process': process,
                    'psutil': psutil_proc,
                    'task': task
                }

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
    def _build_exec_command(command: str, python_executable: Optional[str] = None) -> Tuple[str, bool]:
        """
        Build cross-platform execution command
        Returns (command, use_shell)
        """
        # Build execution command with custom Python interpreter if specified
        exec_command = command
        use_shell = False

        if python_executable:
            # Check if command already starts with python
            command_lower = command.lower()
            if command_lower.startswith('python ') or command_lower.startswith('python3 '):
                # Find the space after python/python3
                prefix_end = command_lower.find(' ')
                # Replace python with custom interpreter
                exec_command = f'{python_executable} {command[prefix_end + 1:]}'
            elif command.endswith('.py'):
                # Command is a Python script file, execute it directly
                # Use double quotes for Windows path handling
                exec_command = f'{python_executable} "{command}"'
            else:
                # Command might be a module or package, use -m
                exec_command = f'{python_executable} -m {command}'

        # Determine if we need to use shell
        current_platform = platform.system()
        if current_platform == "Windows":
            # Windows might need shell for complex commands
            use_shell = any(char in exec_command for char in ['|', '&', '>', '<', '&&', '||'])
        elif current_platform == "Darwin" or current_platform == "Linux":
            # Unix-like systems generally don't need shell for simple commands
            use_shell = any(char in exec_command for char in ['|', '&', '>', '<', '&&', '||', ';'])

        return exec_command, use_shell

    @staticmethod
    def _prepare_environment() -> Dict[str, str]:
        """Prepare cross-platform environment variables"""
        env = os.environ.copy()

        # Set PYTHONUNBUFFERED for real-time logging
        env['PYTHONUNBUFFERED'] = '1'

        # Platform-specific environment settings
        current_platform = platform.system()
        if current_platform == "Windows":
            # Windows-specific settings
            env['PYTHONIOENCODING'] = 'utf-8'
        elif current_platform == "Darwin":
            # macOS-specific settings if needed
            pass
        elif current_platform == "Linux":
            # Linux-specific settings if needed
            pass

        return env

    @staticmethod
    async def _execute_command(
        command: str,
        log_file,
        working_dir: str,
        env: Dict[str, str],
        use_shell: bool = False
    ) -> asyncio.subprocess.Process:
        """Execute command with cross-platform support"""
        if use_shell:
            # Use shell for complex commands
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=working_dir,
                shell=True,
                env=env
            )
        else:
            # Parse command into components for direct execution
            # Simple parsing by splitting on spaces (might need improvement for complex cases)
            if platform.system() == "Windows":
                # Windows: use shell with proper command formatting
                # For commands with paths containing spaces, wrap in quotes
                if '"' in command:
                    # Command already has quotes, use as-is
                    cmd_to_run = command
                else:
                    # Quote the entire command for Windows shell
                    cmd_to_run = f'"{command}"'

                process = await asyncio.create_subprocess_shell(
                    cmd_to_run,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=working_dir,
                    shell=True,
                    env=env
                )
            else:
                # Unix-like systems - try to parse command
                # This is a simple parser, might need improvement for complex cases
                command_parts = []
                current_part = ""
                in_quote = False
                quote_char = None

                for char in command:
                    if char in ['"', "'"] and (not in_quote or quote_char == char):
                        in_quote = not in_quote
                        quote_char = char if in_quote else None
                    elif char.isspace() and not in_quote:
                        if current_part:
                            command_parts.append(current_part)
                            current_part = ""
                    else:
                        current_part += char

                if current_part:
                    command_parts.append(current_part)

                if not command_parts:
                    # Fallback to shell if parsing fails
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        cwd=working_dir,
                        shell=True,
                        env=env
                    )
                else:
                    # Use parsed command
                    process = await asyncio.create_subprocess_exec(
                        *command_parts,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        cwd=working_dir,
                        env=env
                    )

        return process

    @staticmethod
    async def cancel_task(task_id: int) -> bool:
        """Cancel a running task with cross-platform support"""
        if task_id not in TaskExecutor._running_tasks:
            return False

        task_info = TaskExecutor._running_tasks[task_id]
        process = task_info['process']
        psutil_proc = task_info['psutil']

        try:
            # Use psutil for cross-platform process termination
            if psutil_proc.is_running():
                # Try graceful termination first
                psutil_proc.terminate()

                try:
                    # Wait up to 5 seconds for process to terminate
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    TaskExecutor._force_terminate(psutil_proc, process)

            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            # Process already terminated or access denied
            print(f"Process already terminated or access denied: {e}")
            return True

        except Exception as e:
            print(f"Error cancelling task {task_id}: {e}")
            return False

    @staticmethod
    def _force_terminate(psutil_proc: psutil.Process, process: asyncio.subprocess.Process) -> None:
        """Force terminate a process with platform-specific handling"""
        try:
            current_platform = platform.system()

            if current_platform == "Windows":
                # Windows: use kill() method
                psutil_proc.kill()
            elif current_platform == "Darwin" or current_platform == "Linux":
                # Unix-like: try SIGTERM first, then SIGKILL
                try:
                    psutil_proc.send_signal(signal.SIGTERM)
                    # Give it a moment
                    import time
                    time.sleep(0.1)

                    if psutil_proc.is_running():
                        psutil_proc.send_signal(signal.SIGKILL)
                except psutil.AccessDenied:
                    # If we can't send signals, try kill()
                    psutil_proc.kill()

            # Ensure asyncio process is cleaned up
            if process.returncode is None:
                process.kill()

        except Exception as e:
            print(f"Error in force termination: {e}")

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
            no_change_count = 0
            max_no_change = 10  # Stop after 5 seconds of no changes (0.5s * 10)

            while task_id in TaskExecutor._running_tasks or (task_id in TaskExecutor._ws_connections and no_change_count < max_no_change):
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
                            no_change_count = 0
                        else:
                            no_change_count += 1

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
        if task_id not in TaskExecutor._running_tasks:
            return False

        task_info = TaskExecutor._running_tasks[task_id]
        psutil_proc = task_info['psutil']

        try:
            return psutil_proc.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process is no longer running
            return False

    @staticmethod
    def get_running_tasks() -> list:
        """Get list of currently running task IDs"""
        running_tasks = []

        for task_id, task_info in list(TaskExecutor._running_tasks.items()):
            psutil_proc = task_info['psutil']

            try:
                if psutil_proc.is_running():
                    running_tasks.append(task_id)
                else:
                    # Clean up dead processes
                    del TaskExecutor._running_tasks[task_id]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Clean up processes that no longer exist
                del TaskExecutor._running_tasks[task_id]

        return running_tasks

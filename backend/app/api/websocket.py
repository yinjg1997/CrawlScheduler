from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import async_session
from ..services.task_service import TaskService
from ..services.executor import TaskExecutor

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/tasks/{task_id}/logs")
async def task_logs_websocket(websocket: WebSocket, task_id: int):
    """WebSocket endpoint for streaming task logs in real-time"""
    await websocket.accept()

    async with async_session() as db:
        try:
            # Verify task exists
            task = await TaskService.get_by_id(db, task_id)
            if not task:
                await websocket.close(code=4004, reason="Task not found")
                return

            # Stream logs
            await TaskExecutor.stream_logs(task_id, websocket)

        except WebSocketDisconnect:
            print(f"WebSocket disconnected for task {task_id}")
        except Exception as e:
            print(f"Error in WebSocket for task {task_id}: {e}")
            await websocket.close(code=1011, reason=str(e))


@router.websocket("/ws/tasks/status")
async def tasks_status_websocket(websocket: WebSocket):
    """WebSocket endpoint for receiving task status updates"""
    await websocket.accept()

    try:
        while True:
            # Send current running tasks
            running_tasks = TaskExecutor.get_running_tasks()

            async with async_session() as db:
                tasks_info = []
                for task_id in running_tasks:
                    task = await TaskService.get_by_id(db, task_id)
                    if task:
                        tasks_info.append({
                            "task_id": task.id,
                            "crawler_id": task.crawler_id,
                            "status": task.status
                        })

                await websocket.send_json({
                    "type": "status_update",
                    "running_tasks": tasks_info
                })

            # Wait before next update
            import asyncio
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        print("Status WebSocket disconnected")
    except Exception as e:
        print(f"Error in status WebSocket: {e}")
        await websocket.close(code=1011, reason=str(e))

"""爬虫任务执行器

通过 subprocess.Popen + 线程池执行爬虫脚本，
不依赖 asyncio.create_subprocess_exec，兼容所有事件循环类型（Selector/Proactor）。
"""

import asyncio
import os
import re
import subprocess
import traceback
from pathlib import Path
from typing import Dict, Set

import psutil
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from .task_service import TaskService
from ..config import settings


class TaskExecutor:
    """爬虫任务执行器，负责任务的启动、取消、日志流式传输和状态管理"""

    # 运行中的任务: {task_id: {'process': Popen, 'psutil': psutil.Process}}
    _running_tasks: Dict[int, Dict] = {}

    # 已取消的任务 ID 集合，用于防止 execute 完成时覆盖 cancelled 状态
    _cancelled_tasks: Set[int] = set()

    # WebSocket 连接: {task_id: Set[WebSocket]}
    _ws_connections: Dict[int, Set[WebSocket]] = {}

    # ANSI 转义序列（颜色码等）的正则
    _ANSI_RE = re.compile(r'\x1b\[[0-9;]*m|\[[\d;]*m')

    @staticmethod
    def _decode_line(raw: bytes) -> str:
        """将子进程输出的 bytes 解码为字符串，兼容 UTF-8 和 GBK"""
        for encoding in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
            try:
                text = raw.decode(encoding)
                return TaskExecutor._ANSI_RE.sub('', text).rstrip('\n\r')
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode('utf-8', errors='replace').rstrip('\n\r')

    @staticmethod
    def _parse_command(command: str, python_executable: str, working_directory: str) -> list:
        """解析命令字符串，构建 subprocess.Popen 所需的参数列表

        支持的 command 格式:
        - "python xxx.py" / "python3 xxx.py"  →  [python_exe, "绝对路径/xxx.py"]
        - "python -c ..." / "python -m ..."   →  [python_exe, "-c/m", ...]
        - "xxx.py"                            →  [python_exe, "绝对路径/xxx.py"]
        - "scrapy crawl xxx"                  →  [python_exe, "-m", "scrapy", "crawl", "xxx"]
        - 其他命令 (如 git pull)              →  通过 shell 直接执行
        """
        import shlex
        cmd = command.strip()
        lower = cmd.lower()

        # python -c "..." / python -m ... → 保留 python 后面的参数
        if lower.startswith(('python3 -', 'python -')):
            parts = shlex.split(cmd)
            return [python_executable] + parts[1:]

        # 去掉 "python xxx" 或 "python3 xxx" 前缀
        if lower.startswith('python3 '):
            cmd = cmd[cmd.index(' ') + 1:]
        elif lower.startswith('python '):
            cmd = cmd[cmd.index(' ') + 1:]

        # .py 文件：构建绝对路径
        if cmd.endswith('.py'):
            if not os.path.isabs(cmd):
                cmd = os.path.join(working_directory, cmd)
            return [python_executable, cmd]

        # scrapy crawl xxx 等：用 -m 方式调用
        if lower.startswith('scrapy '):
            parts = cmd.split()
            return [python_executable, "-m"] + parts

        # 其他命令（git pull、npm install 等）
        return shlex.split(cmd)

    # ==================== 状态更新 ====================

    @staticmethod
    async def _update_status(task_id: int, status: str, **kwargs) -> None:
        """使用独立的数据库会话更新任务状态并广播通知"""
        from ..database import async_session
        try:
            async with async_session() as db:
                task = await TaskService.update_status(db, task_id, status, **kwargs)
                await TaskExecutor._broadcast_status_update(task_id, task.status)
        except Exception as e:
            print(f"[执行器] 更新任务 {task_id} 状态失败: {e}")

    # ==================== 核心执行逻辑 ====================

    @staticmethod
    async def execute(db: AsyncSession, task_id: int) -> None:
        """执行爬虫任务

        流程:
        1. 从数据库读取任务和爬虫配置
        2. 构建脚本绝对路径
        3. 通过线程池启动 subprocess.Popen 子进程
        4. 在线程池中读取子进程输出并写入日志文件
        5. 子进程结束后更新任务状态
        """
        from ..models import TaskExecution, Crawler
        from ..database import async_session
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        print(f"[执行器] 开始执行任务 {task_id}")

        # ---- 第一步：读取任务配置 ----
        async with async_session() as session:
            task = await session.get(TaskExecution, task_id)
            if not task:
                print(f"[执行器] 任务 {task_id} 不存在")
                return

            result = await session.execute(
                select(Crawler)
                .options(selectinload(Crawler.project))
                .where(Crawler.id == task.crawler_id)
            )
            crawler = result.scalar_one_or_none()
            if not crawler:
                print(f"[执行器] 任务 {task_id} 对应的爬虫不存在")
                return
            if not crawler.project:
                print(f"[执行器] 爬虫 {crawler.id} 未关联项目")
                return

            working_directory = crawler.project.working_directory
            python_executable = crawler.project.python_executable
            command = crawler.command
            log_file_path = str(settings.LOGS_DIR / f"task_{task_id}.log")

            # 保存日志文件路径到数据库
            task.log_file_path = log_file_path
            await session.commit()

        # 校验必要参数
        if not working_directory or not python_executable:
            await TaskExecutor._update_status(
                task_id, "failed",
                error_message="项目缺少工作目录或 Python 解释器路径"
            )
            return

        # ---- 第二步：解析命令，构建执行参数列表 ----
        cmd_args = TaskExecutor._parse_command(command, python_executable, working_directory)

        print(f"[执行器] 执行命令: {cmd_args}")
        print(f"[执行器] 工作目录: {working_directory}")

        # 更新状态为运行中
        await TaskExecutor._update_status(task_id, "running")

        # ---- 第三步：启动子进程并执行 ----
        try:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            loop = asyncio.get_event_loop()

            def _start_process():
                return subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=working_directory,
                )

            process = await loop.run_in_executor(None, _start_process)
            psutil_proc = psutil.Process(process.pid)

            TaskExecutor._running_tasks[task_id] = {
                'process': process,
                'psutil': psutil_proc,
            }

            # 在线程池中读取输出并写入日志文件
            def _read_output():
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    for raw_line in process.stdout:
                        line = TaskExecutor._decode_line(raw_line)
                        f.write(line + '\n')
                        f.flush()
                return process.wait()

            return_code = await loop.run_in_executor(None, _read_output)

            # ---- 第四步：更新最终状态 ----
            print(f"[执行器] 任务 {task_id} 执行完成，返回码: {return_code}")
            if task_id in TaskExecutor._cancelled_tasks:
                # 任务已被取消，不再覆盖为 failed
                print(f"[执行器] 任务 {task_id} 已取消，跳过状态更新")
            else:
                status = "success" if return_code == 0 else "failed"
                await TaskExecutor._update_status(
                    task_id, status,
                    exit_code=return_code,
                    error_message=f"退出码 {return_code}" if return_code != 0 else None
                )

        except asyncio.CancelledError:
            await TaskExecutor._update_status(task_id, "cancelled")
            raise
        except Exception as e:
            print(f"[执行器] 任务 {task_id} 执行异常: {e}")
            traceback.print_exc()
            await TaskExecutor._update_status(task_id, "failed", error_message=str(e))
        finally:
            TaskExecutor._running_tasks.pop(task_id, None)
            TaskExecutor._cancelled_tasks.discard(task_id)

    # ==================== 任务取消 ====================

    @staticmethod
    async def cancel_task(task_id: int) -> bool:
        """取消运行中的任务

        先尝试优雅终止（terminate），等待 5 秒后强制杀死进程。
        """
        TaskExecutor._cancelled_tasks.add(task_id)

        if task_id not in TaskExecutor._running_tasks:
            return False

        task_info = TaskExecutor._running_tasks[task_id]
        process = task_info['process']
        psutil_proc = task_info['psutil']

        try:
            if psutil_proc.is_running():
                psutil_proc.terminate()
                try:
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, process.wait),
                        timeout=5
                    )
                except asyncio.TimeoutError:
                    try:
                        psutil_proc.kill()
                    except Exception:
                        pass
                    try:
                        process.kill()
                    except Exception:
                        pass
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True
        except Exception as e:
            print(f"[执行器] 取消任务 {task_id} 失败: {e}")
            return False

    # ==================== WebSocket 管理 ====================

    @staticmethod
    def add_ws_connection(task_id: int, websocket: WebSocket) -> None:
        """添加 WebSocket 连接"""
        if task_id not in TaskExecutor._ws_connections:
            TaskExecutor._ws_connections[task_id] = set()
        TaskExecutor._ws_connections[task_id].add(websocket)

    @staticmethod
    def remove_ws_connection(task_id: int, websocket: WebSocket) -> None:
        """移除 WebSocket 连接，无连接时清理键"""
        if task_id in TaskExecutor._ws_connections:
            TaskExecutor._ws_connections[task_id].discard(websocket)
            if not TaskExecutor._ws_connections[task_id]:
                del TaskExecutor._ws_connections[task_id]

    # ==================== 日志流式传输 ====================

    @staticmethod
    async def stream_logs(task_id: int, websocket: WebSocket) -> None:
        """通过 WebSocket 实时推送任务日志

        先发送已有的历史日志，再轮询日志文件持续推送新内容，
        任务结束且日志无变化后发送完成信号。
        """
        TaskExecutor.add_ws_connection(task_id, websocket)
        try:
            log_file = Path(settings.LOGS_DIR) / f"task_{task_id}.log"

            # 发送历史日志
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        await websocket.send_json({"type": "log", "data": line.rstrip()})

            # 持续轮询新日志
            last_size = log_file.stat().st_size if log_file.exists() else 0
            no_change_count = 0

            while task_id in TaskExecutor._running_tasks or (
                task_id in TaskExecutor._ws_connections and no_change_count < 10
            ):
                try:
                    if log_file.exists():
                        current_size = log_file.stat().st_size
                        if current_size > last_size:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                f.seek(last_size)
                                for line in f:
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

    # ==================== 状态广播 ====================

    @staticmethod
    async def _broadcast_status_update(task_id: int, status: str) -> None:
        """向所有已连接的 WebSocket 客户端广播状态变更"""
        if task_id in TaskExecutor._ws_connections:
            for ws in list(TaskExecutor._ws_connections[task_id]):
                try:
                    await ws.send_json({"type": "status", "task_id": task_id, "status": status})
                except Exception:
                    TaskExecutor.remove_ws_connection(task_id, ws)

    # ==================== 查询方法 ====================

    @staticmethod
    def is_task_running(task_id: int) -> bool:
        """检查指定任务是否正在运行"""
        if task_id not in TaskExecutor._running_tasks:
            return False
        try:
            return TaskExecutor._running_tasks[task_id]['psutil'].is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    @staticmethod
    def get_running_tasks() -> list:
        """获取所有正在运行的任务 ID 列表，同时清理已结束的任务"""
        result = []
        for task_id, info in list(TaskExecutor._running_tasks.items()):
            try:
                if info['psutil'].is_running():
                    result.append(task_id)
                else:
                    del TaskExecutor._running_tasks[task_id]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                del TaskExecutor._running_tasks[task_id]
        return result

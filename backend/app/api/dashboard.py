import os
from fastapi import APIRouter, Depends
from pathlib import Path

import psutil

from ..auth import get_current_active_user
from ..config import settings
from ..services.executor import TaskExecutor

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _get_log_dir_size(path: Path) -> int:
    """计算目录下所有文件的总大小（字节）"""
    total = 0
    if not path.exists():
        return 0
    for entry in os.scandir(path):
        if entry.is_file(follow_symlinks=False):
            total += entry.stat(follow_symlinks=False).st_size
    return total


def _format_size(bytes_size: int) -> str:
    """将字节数格式化为人类可读的字符串"""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


@router.get("/system", dependencies=[Depends(get_current_active_user)])
async def get_system_info():
    """获取系统资源信息"""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    log_size = _get_log_dir_size(settings.LOGS_DIR)

    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.5),
            "count": psutil.cpu_count(),
        },
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": round(mem.used / mem.total * 100, 1),
            "total_human": _format_size(mem.total),
            "used_human": _format_size(mem.used),
            "available_human": _format_size(mem.available),
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "total_human": _format_size(disk.total),
            "used_human": _format_size(disk.used),
            "free_human": _format_size(disk.free),
        },
        "logs": {
            "total_size": log_size,
            "total_size_human": _format_size(log_size),
        },
        "running_tasks": len(TaskExecutor.get_running_tasks()),
    }

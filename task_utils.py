"""任务管理工具函数"""
import json
import os
from datetime import datetime
from typing import Optional

TASKS_FILE = "tasks.json"


def load_tasks() -> dict:
    """加载任务列表"""
    if not os.path.exists(TASKS_FILE):
        return {"project": "", "created_at": "", "requirements_doc": "", "tasks": []}
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(data: dict) -> None:
    """保存任务列表"""
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 任务状态常量
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_BLOCKED = "blocked"
STATUS_NEEDS_MANUAL = "needs_manual"  # 需要人工干预


def get_next_task(data: dict) -> Optional[dict]:
    """智能选择下一个待执行任务

    选择逻辑：
    1. 过滤出pending状态的任务（排除needs_manual）
    2. 排除依赖未完成的任务
    3. 按优先级排序选择最高优先级
    """
    # 过滤掉需要人工干预的任务
    pending_tasks = [t for t in data["tasks"]
                     if t["status"] == STATUS_PENDING]
    if not pending_tasks:
        return None

    # 检查依赖是否完成（排除needs_manual的依赖）
    completed_ids = {t["id"] for t in data["tasks"]
                     if t["status"] == STATUS_COMPLETED}
    eligible = []
    for task in pending_tasks:
        deps = task.get("dependencies", [])
        if all(d in completed_ids for d in deps):
            eligible.append(task)

    if not eligible:
        # 所有pending任务都有未完成的依赖，返回None
        return None

    # 优先级排序: high > medium > low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    eligible.sort(key=lambda t: priority_order.get(t.get("priority", "medium"), 1))
    return eligible[0]


def update_task_status(data: dict, task_id: int, status: str,
                        result: str = None, issues: list = None) -> None:
    """更新任务状态"""
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
            if result:
                task["result"] = result
            if issues:
                task["issues"] = issues
            if status == "completed":
                task["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break
    save_tasks(data)


def get_task_summary(data: dict) -> dict:
    """获取任务统计"""
    total = len(data["tasks"])
    completed = sum(1 for t in data["tasks"] if t["status"] == STATUS_COMPLETED)
    pending = sum(1 for t in data["tasks"] if t["status"] == STATUS_PENDING)
    in_progress = sum(1 for t in data["tasks"] if t["status"] == STATUS_IN_PROGRESS)
    blocked = sum(1 for t in data["tasks"] if t["status"] == STATUS_BLOCKED)
    needs_manual = sum(1 for t in data["tasks"] if t["status"] == STATUS_NEEDS_MANUAL)
    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "blocked": blocked,
        "needs_manual": needs_manual
    }


def mark_task_manual(data: dict, task_id: int, reason: str = None) -> bool:
    """标记任务为需要人工干预"""
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = STATUS_NEEDS_MANUAL
            if reason:
                task["manual_reason"] = reason
            save_tasks(data)
            return True
    return False
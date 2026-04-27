"""监控任务路由 - 任务的增删改查和状态管理"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.monitor_task import MonitorTask
from app.models.ticket_status import TicketStatus
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskStatusResponse
from app.services.scheduler import add_monitor_job, remove_monitor_job

router = APIRouter(prefix="/api/tasks", tags=["监控任务"])


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有监控任务"""
    tasks = db.query(MonitorTask).filter(MonitorTask.user_id == current_user.id).all()
    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新的监控任务

    - 验证平台名称合法性
    - 关联当前登录用户
    """
    valid_platforms = {"damai", "maoyan", "funwandao"}
    if task_data.platform not in valid_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的平台：{task_data.platform}，支持的平台：{', '.join(valid_platforms)}",
        )

    new_task = MonitorTask(
        user_id=current_user.id,
        platform=task_data.platform,
        event_url=task_data.event_url,
        event_name=task_data.event_name,
        target_session=task_data.target_session,
        check_interval=task_data.check_interval,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 启动监控调度作业
    add_monitor_job(new_task.id, new_task.check_interval)

    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新监控任务（支持部分更新）

    - 只更新请求体中提供的字段
    - 只能更新自己的任务
    """
    task = db.query(MonitorTask).filter(
        MonitorTask.id == task_id,
        MonitorTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或无权访问",
        )

    # 部分更新：只更新提供了值的字段
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    # 根据 is_active 状态更新调度作业
    if task.is_active:
        add_monitor_job(task.id, task.check_interval)
    else:
        remove_monitor_job(task.id)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除监控任务

    - 只能删除自己的任务
    - 级联删除关联的状态记录和通知
    """
    task = db.query(MonitorTask).filter(
        MonitorTask.id == task_id,
        MonitorTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或无权访问",
        )

    db.delete(task)
    db.commit()

    # 移除监控调度作业
    remove_monitor_job(task_id)

    return None


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务最近一次票务状态快照

    - 验证任务归属
    - 按检查时间降序返回最新一条
    """
    # 验证任务归属
    task = db.query(MonitorTask).filter(
        MonitorTask.id == task_id,
        MonitorTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或无权访问",
        )

    # 获取最新一条状态快照
    latest_status = (
        db.query(TicketStatus)
        .filter(TicketStatus.task_id == task_id)
        .order_by(TicketStatus.checked_at.desc())
        .first()
    )
    if not latest_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无票务状态数据",
        )

    return latest_status

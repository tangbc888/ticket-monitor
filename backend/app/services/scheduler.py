"""定时任务调度器 - 基于 APScheduler 管理监控任务的定时执行"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.monitor_task import MonitorTask
from app.services.monitor_engine import monitor_engine

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = AsyncIOScheduler()


async def run_monitor_check(task_id: int):
    """执行单个任务的检查，并在发现回流票时触发通知

    此函数由调度器定时调用，负责：
    1. 创建数据库会话
    2. 调用监控引擎检查任务
    3. 如果发现回流票，触发通知推送
    """
    db = SessionLocal()
    try:
        result = await monitor_engine.check_task(task_id, db)
        if result:
            # 触发通知推送（WebSocket + 其他渠道）
            # 延迟导入避免循环依赖
            from app.services.notification_service import notification_service
            await notification_service.notify(result)
            logger.info(f"[调度器] 任务 {task_id} 发现回流票，已触发通知推送")
    except Exception as e:
        logger.error(f"[调度器] 执行监控检查任务 {task_id} 失败: {e}")
    finally:
        db.close()


def add_monitor_job(task_id: int, interval_seconds: int = 30):
    """为监控任务添加定时调度作业

    Args:
        task_id: 监控任务 ID
        interval_seconds: 检查间隔（秒），默认 30 秒
    """
    job_id = f"monitor_task_{task_id}"
    # 如果已存在则先移除
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        run_monitor_check,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id=job_id,
        args=[task_id],
        replace_existing=True,
    )
    logger.info(f"[调度器] 已添加监控作业: task_id={task_id}, 间隔={interval_seconds}秒")


def remove_monitor_job(task_id: int):
    """移除监控任务的调度作业

    Args:
        task_id: 监控任务 ID
    """
    job_id = f"monitor_task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"[调度器] 已移除监控作业: task_id={task_id}")


def init_scheduler(db: Session):
    """初始化调度器，加载所有活跃的监控任务

    在应用启动时调用，遍历数据库中所有 is_active=True 的任务，
    为每个任务创建定时调度作业。

    Args:
        db: 数据库会话
    """
    active_tasks = db.query(MonitorTask).filter(MonitorTask.is_active == True).all()
    for task in active_tasks:
        add_monitor_job(task.id, task.check_interval)

    logger.info(f"[调度器] 已加载 {len(active_tasks)} 个活跃监控任务")


def start_scheduler():
    """启动调度器（在应用启动时调用）"""
    if not scheduler.running:
        scheduler.start()
        logger.info("[调度器] 定时任务调度器已启动")


def shutdown_scheduler():
    """关闭调度器（在应用关闭时调用）"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[调度器] 定时任务调度器已关闭")

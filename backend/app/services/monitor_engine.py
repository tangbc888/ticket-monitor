"""监控引擎 - 负责执行票务状态检查和变更检测"""
import json
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.platforms import get_adapter
from app.models.monitor_task import MonitorTask
from app.models.ticket_status import TicketStatus
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class MonitorEngine:
    """票务监控引擎核心

    负责：
    1. 执行单个监控任务的票务状态检查
    2. 对比前后状态，检测回流票（无票 -> 有票）
    3. 生成通知记录
    """

    async def check_task(self, task_id: int, db: Session) -> Optional[dict]:
        """执行单个监控任务的检查

        流程：
        1. 从数据库获取 MonitorTask
        2. 根据 platform 获取对应的适配器
        3. 调用 check_ticket_status 获取当前状态
        4. 查询上一次的 TicketStatus 快照
        5. 对比前后状态，检测变化（特别是 "无票->有票" 的回流票情况）
        6. 将新状态保存到 TicketStatus 表
        7. 如果检测到回流票，创建 Notification 记录并返回变化信息
        """
        task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task or not task.is_active:
            return None

        try:
            # 获取平台适配器并检查票务状态
            adapter = get_adapter(task.platform)
            current_status = await adapter.check_ticket_status(task.event_url)

            # 获取上一次状态快照
            last_status = db.query(TicketStatus).filter(
                TicketStatus.task_id == task_id
            ).order_by(TicketStatus.checked_at.desc()).first()

            # 保存当前状态快照到数据库
            new_status = TicketStatus(
                task_id=task_id,
                status_data=json.dumps(current_status.model_dump(), ensure_ascii=False),
                checked_at=datetime.now()
            )
            db.add(new_status)
            db.commit()

            # 对比状态变化，检测回流票
            changes = self._detect_changes(last_status, current_status)

            if changes:
                # 发现回流票，创建通知记录
                message = self._build_notification_message(task, changes)
                notification = Notification(
                    user_id=task.user_id,
                    task_id=task_id,
                    message=message,
                    type="ticket_available"
                )
                db.add(notification)
                db.commit()

                logger.info(f"[监控引擎] 任务 {task_id} 发现回流票: {message}")

                return {
                    "task_id": task_id,
                    "user_id": task.user_id,
                    "event_name": task.event_name,
                    "message": message,
                    "changes": changes,
                    "notification_id": notification.id
                }

            logger.debug(f"[监控引擎] 任务 {task_id} 未检测到状态变化")
            return None

        except Exception as e:
            logger.error(f"[监控引擎] 监控任务 {task_id} 检查失败: {e}")
            return None

    def _detect_changes(self, last_status_record, current_status) -> List[dict]:
        """对比前后状态，检测回流票

        比较每个票档的 available 状态：
        - 如果上次为 False（无票），现在为 True（有票），则为回流票
        - 如果 last_status_record 为 None（首次检查），且当前有可用票，也返回

        Returns:
            变化的票档列表，每项包含 name, price, old_status, new_status
        """
        changes = []
        current_prices = current_status.prices

        if last_status_record is None:
            # 首次检查，如果有票则记录
            for price in current_prices:
                if price.available:
                    changes.append({
                        "name": price.name,
                        "price": price.price,
                        "old_status": "首次检查",
                        "new_status": price.status,
                    })
            return changes

        # 解析上次状态数据
        try:
            last_data = json.loads(last_status_record.status_data)
            last_prices = last_data.get("prices", [])
        except (json.JSONDecodeError, TypeError):
            logger.warning("[监控引擎] 上次状态数据解析失败，视为首次检查")
            for price in current_prices:
                if price.available:
                    changes.append({
                        "name": price.name,
                        "price": price.price,
                        "old_status": "数据异常",
                        "new_status": price.status,
                    })
            return changes

        # 构建上次票档的名称->状态映射
        last_price_map = {}
        for lp in last_prices:
            name = lp.get("name", "")
            last_price_map[name] = lp

        # 对比每个票档
        for price in current_prices:
            last_price = last_price_map.get(price.name)
            if last_price:
                # 检测 无票 -> 有票 的变化（回流票）
                was_available = last_price.get("available", False)
                if not was_available and price.available:
                    changes.append({
                        "name": price.name,
                        "price": price.price,
                        "old_status": last_price.get("status", "无票"),
                        "new_status": price.status,
                    })
            else:
                # 新出现的票档，且有票
                if price.available:
                    changes.append({
                        "name": price.name,
                        "price": price.price,
                        "old_status": "新增票档",
                        "new_status": price.status,
                    })

        return changes

    def _build_notification_message(self, task, changes: List[dict]) -> str:
        """构建通知消息文本

        示例：「周杰伦演唱会-北京站」发现回流票！内场VIP(?1280)、看台A(?680) 现在有票！
        """
        ticket_parts = []
        for change in changes:
            name = change["name"]
            price = change["price"]
            if price > 0:
                ticket_parts.append(f"{name}(?{price:.0f})")
            else:
                ticket_parts.append(name)

        tickets_str = "、".join(ticket_parts)
        message = f"「{task.event_name}」发现回流票！{tickets_str} 现在有票！"
        return message


# 全局单例
monitor_engine = MonitorEngine()

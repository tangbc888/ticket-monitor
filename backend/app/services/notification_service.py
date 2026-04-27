"""通知服务 - 负责通过多种渠道发送通知（WebSocket、邮件、FCM）"""
import logging
import json
import os
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """多通道通知推送服务

    支持以下推送渠道：
    1. WebSocket - 实时推送给在线用户
    2. 邮件 (SMTP) - 异步发送邮件通知
    3. FCM (Firebase Cloud Messaging) - 推送到 Android 设备

    邮件和 FCM 均为可选功能，未配置时自动禁用，不影响其他功能。
    """

    def __init__(self):
        """初始化通知服务，尝试启用邮件和 FCM 通道"""
        self._email_enabled = False
        self._fcm_enabled = False
        self._init_email()
        self._init_fcm()

    def _init_email(self):
        """初始化邮件服务

        从 config 读取 SMTP 配置，如果 SMTP_HOST、SMTP_USER、SMTP_PASSWORD
        都已配置，则启用邮件通知功能。
        """
        try:
            from app.config import settings
            if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
                self._email_enabled = True
                logger.info("[通知服务] 邮件通知已启用 (SMTP: %s)", settings.SMTP_HOST)
            else:
                logger.info("[通知服务] SMTP 未完整配置，邮件通知已禁用")
        except Exception as e:
            logger.warning("[通知服务] 初始化邮件服务失败: %s", e)

    def _init_fcm(self):
        """初始化 Firebase Cloud Messaging

        从 config 读取 FCM_CREDENTIALS_PATH，如果凭证文件存在，
        使用 firebase_admin.initialize_app() 初始化 FCM。
        凭证文件不存在时只打日志，不报错，FCM 功能自动禁用。
        """
        try:
            from app.config import settings
            cred_path = settings.FCM_CREDENTIALS_PATH
            if not cred_path:
                logger.info("[通知服务] FCM 凭证路径未配置，FCM 推送已禁用")
                return

            if not os.path.exists(cred_path):
                logger.info("[通知服务] FCM 凭证文件不存在: %s，FCM 推送已禁用", cred_path)
                return

            import firebase_admin
            from firebase_admin import credentials

            # 避免重复初始化
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)

            self._fcm_enabled = True
            logger.info("[通知服务] FCM 推送已启用")
        except Exception as e:
            logger.warning("[通知服务] 初始化 FCM 失败: %s", e)

    async def notify(self, result: dict) -> None:
        """统一通知入口 - 被监控引擎调用

        result 包含：
        - task_id, user_id, event_name, message, changes, notification_id

        流程：
        1. 通过 WebSocket 实时推送给在线用户
        2. 发送邮件通知（如果启用且用户开启）
        3. 发送 FCM 推送（如果启用）
        """
        user_id = result.get("user_id")
        message = result.get("message", "")
        event_name = result.get("event_name", "")

        if not user_id or not message:
            return

        # 构建通知数据
        notification_data = {
            "type": "ticket_available",
            "task_id": result.get("task_id"),
            "notification_id": result.get("notification_id"),
            "event_name": event_name,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "changes": result.get("changes", [])
        }

        # 1. WebSocket 推送
        await self._send_websocket(user_id, notification_data)

        # 2. 邮件通知
        await self._send_email(user_id, event_name, message)

        # 3. FCM 推送
        await self._send_fcm(user_id, event_name, message)

        logger.info("[通知服务] 已向用户 %d 发送通知: %s", user_id, message[:80])

    async def _send_websocket(self, user_id: int, data: dict):
        """通过 WebSocket 推送给在线用户

        发送前检查用户是否启用了 WebSocket 通知偏好。
        """
        # 检查用户通知偏好
        if not self._check_user_preference(user_id, "websocket"):
            return

        try:
            from app.services.ws_manager import manager
            await manager.send_to_user(user_id, data)
            logger.info("[通知服务] WebSocket 通知已推送给用户 %d", user_id)
        except Exception as e:
            logger.error("[通知服务] WebSocket 推送失败: %s", e)

    async def _send_email(self, user_id: int, event_name: str, message: str):
        """发送邮件通知

        流程：
        1. 检查邮件服务是否启用
        2. 检查用户是否开启邮件通知
        3. 从数据库获取用户邮箱
        4. 使用 aiosmtplib 异步发送 HTML 格式邮件
        """
        if not self._email_enabled:
            return

        # 检查用户通知偏好
        if not self._check_user_preference(user_id, "email"):
            return

        from app.database import SessionLocal
        from app.models.user import User

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.email:
                return

            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from app.config import settings

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"【票务提醒】{event_name} 发现回流票！"
            msg["From"] = settings.SMTP_USER
            msg["To"] = user.email

            # HTML 邮件正文
            html_content = f"""
            <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #FF6B6B, #FF8E53); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h2 style="margin: 0;">? 票务监控提醒</h2>
                </div>
                <div style="background: #f9f9f9; padding: 20px; border: 1px solid #eee; border-radius: 0 0 10px 10px;">
                    <h3 style="color: #333;">{event_name}</h3>
                    <p style="color: #666; font-size: 16px;">{message}</p>
                    <p style="color: #999; font-size: 12px; margin-top: 20px;">
                        此邮件由票务监控助手自动发送，请尽快前往平台购票。
                    </p>
                </div>
            </div>
            """
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True
            )
            logger.info("[通知服务] 邮件通知已发送至 %s", user.email)

        except Exception as e:
            logger.error("[通知服务] 邮件发送失败: %s", e)
        finally:
            db.close()

    async def _send_fcm(self, user_id: int, event_name: str, message: str):
        """通过 Firebase Cloud Messaging 推送到 Android 设备

        流程：
        1. 检查 FCM 是否启用
        2. 从数据库获取用户的 fcm_token
        3. 使用 firebase_admin.messaging 发送推送
        4. 如果 token 无效，自动清除数据库中的 token
        """
        if not self._fcm_enabled:
            return

        from app.database import SessionLocal
        from app.models.user import User

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.fcm_token:
                return

            import firebase_admin.messaging as fcm_messaging

            fcm_message = fcm_messaging.Message(
                notification=fcm_messaging.Notification(
                    title=f"? {event_name}",
                    body=message
                ),
                data={
                    "type": "ticket_available",
                    "event_name": event_name,
                    "click_action": "OPEN_NOTIFICATION"
                },
                token=user.fcm_token
            )

            response = fcm_messaging.send(fcm_message)
            logger.info("[通知服务] FCM 推送成功: %s", response)

        except Exception as e:
            logger.error("[通知服务] FCM 推送失败: %s", e)
            # 如果是 token 无效错误，清除 token
            error_str = str(e).lower()
            if "invalid-registration-token" in error_str or "not-registered" in error_str:
                try:
                    user.fcm_token = None
                    db.commit()
                    logger.info("[通知服务] 已清除用户 %d 的无效 FCM token", user_id)
                except Exception:
                    pass
        finally:
            db.close()

    def _check_user_preference(self, user_id: int, channel: str) -> bool:
        """检查用户是否启用了指定通知渠道

        Args:
            user_id: 用户 ID
            channel: 通知渠道名 ("email" 或 "websocket")

        Returns:
            用户是否启用该渠道，查询失败时默认返回 True（不阻断通知）
        """
        from app.database import SessionLocal
        from app.models.user import User

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            if channel == "email":
                # 默认 True（字段为 None 时视为启用）
                return user.email_notify_enabled is not False
            elif channel == "websocket":
                return user.websocket_notify_enabled is not False
            return True
        except Exception as e:
            logger.warning("[通知服务] 查询用户通知偏好失败: %s", e)
            return True  # 查询失败时默认不阻断
        finally:
            db.close()


# 全局单例
notification_service = NotificationService()

"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户表 - 存储注册用户信息"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    fcm_token = Column(String(500), nullable=True)  # Firebase Cloud Messaging 令牌
    created_at = Column(DateTime, server_default=func.now())

    # 通知偏好设置
    email_notify_enabled = Column(Boolean, default=True)        # 是否启用邮件通知
    websocket_notify_enabled = Column(Boolean, default=True)    # 是否启用 WebSocket 通知

    # 关联关系
    tasks = relationship("MonitorTask", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

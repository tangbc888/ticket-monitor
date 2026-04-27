"""通知模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    """通知表 - 存储发送给用户的所有通知记录"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("monitor_tasks.id"), nullable=True, index=True)
    message = Column(Text, nullable=False)                # 通知内容
    type = Column(String(20), nullable=False)             # 通知类型：websocket/email/fcm
    is_read = Column(Boolean, default=False)              # 是否已读
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="notifications")
    task = relationship("MonitorTask", back_populates="notifications")

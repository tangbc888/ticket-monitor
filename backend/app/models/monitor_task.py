"""监控任务模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MonitorTask(Base):
    """监控任务表 - 存储用户创建的票务监控任务"""
    __tablename__ = "monitor_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)        # 平台名称：damai/maoyan/funwandao
    event_url = Column(String(500), nullable=False)       # 活动页面 URL
    event_name = Column(String(200), nullable=False)      # 活动/演出名称
    target_session = Column(String(200), nullable=True)   # 目标场次（可选）
    check_interval = Column(Integer, default=30)          # 检查间隔（秒）
    is_active = Column(Boolean, default=True)             # 是否启用
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="tasks")
    statuses = relationship("TicketStatus", back_populates="task", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="task", cascade="all, delete-orphan")

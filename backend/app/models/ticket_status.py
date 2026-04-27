"""票务状态模型"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TicketStatus(Base):
    """票务状态表 - 存储每次检查的票务状态快照"""
    __tablename__ = "ticket_statuses"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("monitor_tasks.id"), nullable=False, index=True)
    status_data = Column(Text, nullable=True)  # JSON 字符串，存储票务状态详情
    checked_at = Column(DateTime, server_default=func.now())

    # 关联关系
    task = relationship("MonitorTask", back_populates="statuses")

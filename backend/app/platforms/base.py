"""平台适配器抽象基类 - 定义所有平台适配器的统一接口"""
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


class EventInfo(BaseModel):
    """活动基本信息"""
    platform: str
    event_id: str
    name: str
    artist: str = ""
    venue: str = ""
    date: str = ""
    url: str = ""
    poster_url: str = ""


class TicketPrice(BaseModel):
    """票价档位信息"""
    name: str          # 档位名称，如"内场VIP"
    price: float
    available: bool    # 是否有票
    status: str = ""   # 状态描述


class TicketStatusInfo(BaseModel):
    """票务状态信息"""
    event_name: str
    event_url: str
    platform: str
    prices: List[TicketPrice]
    checked_at: str = ""


class EventDetail(BaseModel):
    """活动详情（包含场次和票务状态）"""
    event_info: EventInfo
    sessions: List[str] = []     # 场次列表
    ticket_status: Optional[TicketStatusInfo] = None


class PlatformAdapter(ABC):
    """平台适配器抽象基类，所有票务平台适配器需继承此类并实现相应方法"""

    @abstractmethod
    async def search_events(self, keyword: str) -> List[EventInfo]:
        """搜索活动/演出

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的活动列表
        """
        pass

    @abstractmethod
    async def check_ticket_status(self, event_url: str) -> TicketStatusInfo:
        """检查票务状态

        Args:
            event_url: 活动页面 URL

        Returns:
            当前票务状态信息
        """
        pass

    @abstractmethod
    async def get_event_detail(self, event_url: str) -> EventDetail:
        """获取活动详情

        Args:
            event_url: 活动页面 URL

        Returns:
            活动详细信息（含场次和票务状态）
        """
        pass

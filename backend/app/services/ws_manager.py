"""WebSocket 连接管理器 - 管理用户的 WebSocket 实时连接"""
import logging
from typing import Dict, List
from fastapi import WebSocket
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器，按用户ID管理活跃连接"""

    def __init__(self):
        # 用户ID -> WebSocket 连接列表（一个用户可能有多个设备连接）
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """接受 WebSocket 连接并加入活跃连接池

        Args:
            user_id: 用户ID
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        """从活跃连接池中移除断开的连接

        Args:
            user_id: 用户ID
            websocket: 要移除的 WebSocket 连接
        """
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            # 如果该用户没有任何活跃连接，则清理
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, message: dict):
        """向指定用户的所有活跃连接发送消息

        在连接已关闭时优雅处理，捕获异常并清理死连接。

        Args:
            user_id: 目标用户ID
            message: 要发送的消息字典
        """
        if user_id not in self.active_connections:
            return

        disconnected = []
        message_text = json.dumps(message, ensure_ascii=False)

        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(message_text)
            except Exception as e:
                logger.warning("[WS管理器] 发送失败，清理死连接 (user_id=%d): %s", user_id, e)
                disconnected.append(ws)

        # 清理已断开的连接
        for ws in disconnected:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict):
        """向所有活跃连接广播消息

        Args:
            message: 要广播的消息字典
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


# 全局单例
manager = ConnectionManager()

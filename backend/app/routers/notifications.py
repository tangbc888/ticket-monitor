"""通知路由 - 通知查询、标记已读、WebSocket 推送"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, SessionLocal
from app.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas import NotificationResponse
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="是否只返回未读通知"),
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(50, ge=1, le=200, description="每页条数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的通知列表

    - 支持分页
    - 支持仅显示未读通知
    - 按创建时间降序排列
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notifications


@router.put("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记当前用户所有通知为已读"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "所有通知已标记为已读"}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记单条通知为已读"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在或无权访问",
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.websocket("/ws")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """WebSocket 实时通知端点

    - 通过 query 参数传入 JWT token 进行认证
    - 认证成功后建立持久连接，接收实时通知推送
    - 连接断开时自动清理
    """
    # 验证 JWT token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            await websocket.close(code=4001, reason="无效的 token")
            return
    except JWTError:
        await websocket.close(code=4001, reason="无效的 token")
        return

    # 验证用户存在
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=4001, reason="用户不存在")
            return
    finally:
        db.close()

    # 建立连接
    await manager.connect(user_id, websocket)
    try:
        # 发送连接成功消息
        await websocket.send_json({"type": "connected", "message": "WebSocket 连接成功"})
        # 保持连接，等待断开
        while True:
            # 接收客户端消息（心跳等），保持连接不断开
            data = await websocket.receive_text()
            # 可以处理客户端发来的 ping 消息
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)

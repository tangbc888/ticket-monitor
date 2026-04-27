"""用户设置路由 - 通知偏好和默认配置管理"""

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from sqlalchemy.exc import IntegrityError



from app.config import settings as app_settings

from app.database import get_db

from app.dependencies import get_current_user

from app.models.user import User

from app.schemas import UserSettingsResponse, UserSettingsUpdate



router = APIRouter(prefix="/api/settings", tags=["用户设置"])





@router.get("", response_model=UserSettingsResponse)

async def get_settings(

    current_user: User = Depends(get_current_user),

):

    """获取当前用户的设置



    返回通知偏好和默认检查间隔等配置项。

    """

    return UserSettingsResponse(

        email=current_user.email or "",

        email_notify_enabled=current_user.email_notify_enabled if current_user.email_notify_enabled is not None else True,

        websocket_notify_enabled=current_user.websocket_notify_enabled if current_user.websocket_notify_enabled is not None else True,

        default_check_interval=app_settings.CHECK_INTERVAL_DEFAULT,

    )





@router.put("", response_model=UserSettingsResponse)

async def update_settings(

    data: UserSettingsUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """更新当前用户的设置



    支持更新以下配置：

    - email_notify_enabled: 是否启用邮件通知

    - websocket_notify_enabled: 是否启用 WebSocket 实时通知

    - default_check_interval: 默认监控检查间隔（秒）

    """

    if data.email is not None:
        # 先检查邮箱是否已被其他用户占用
        existing = db.query(User).filter(
            User.email == data.email, User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
        current_user.email = data.email

    if data.email_notify_enabled is not None:
        current_user.email_notify_enabled = data.email_notify_enabled

    if data.websocket_notify_enabled is not None:
        current_user.websocket_notify_enabled = data.websocket_notify_enabled

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")



    return UserSettingsResponse(

        email=current_user.email or "",

        email_notify_enabled=current_user.email_notify_enabled if current_user.email_notify_enabled is not None else True,

        websocket_notify_enabled=current_user.websocket_notify_enabled if current_user.websocket_notify_enabled is not None else True,

        default_check_interval=app_settings.CHECK_INTERVAL_DEFAULT,

    )


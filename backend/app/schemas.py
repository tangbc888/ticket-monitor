"""Pydantic 模型 - 请求/响应数据验证"""

from pydantic import BaseModel, Field, validator

from typing import Optional, List

import re

from datetime import datetime





# ============ 用户相关 ============



class UserCreate(BaseModel):

    """用户注册请求"""

    username: str = Field(..., min_length=2, max_length=50, description="用户名")

    email: str = Field(..., description="邮箱地址")

    password: str = Field(..., min_length=6, max_length=100, description="密码")





class UserLogin(BaseModel):

    """用户登录请求"""

    username: str

    password: str





class UserResponse(BaseModel):

    """用户信息响应"""

    id: int

    username: str

    email: str

    message: str = ""



    class Config:

        from_attributes = True





class Token(BaseModel):

    """JWT 令牌响应"""

    access_token: str

    token_type: str = "bearer"





# ============ 监控任务相关 ============



class TaskCreate(BaseModel):

    """创建监控任务请求"""

    platform: str = Field(..., description="平台名称：damai/maoyan/funwandao")

    event_url: str = Field(..., description="活动页面 URL")

    event_name: str = Field(..., description="活动/演出名称")

    target_session: Optional[str] = Field(None, description="目标场次")

    check_interval: int = Field(30, ge=10, le=3600, description="检查间隔（秒）")





class TaskUpdate(BaseModel):

    """更新监控任务请求（所有字段可选）"""

    platform: Optional[str] = None

    event_url: Optional[str] = None

    event_name: Optional[str] = None

    target_session: Optional[str] = None

    check_interval: Optional[int] = Field(None, ge=10, le=3600)

    is_active: Optional[bool] = None





class TaskResponse(BaseModel):

    """监控任务响应"""

    id: int

    user_id: int

    platform: str

    event_url: str

    event_name: str

    target_session: Optional[str] = None

    check_interval: int

    is_active: bool

    created_at: Optional[datetime] = None



    class Config:

        from_attributes = True





class TaskStatusResponse(BaseModel):

    """任务票务状态快照响应"""

    id: int

    task_id: int

    status_data: Optional[str] = None

    checked_at: Optional[datetime] = None



    class Config:

        from_attributes = True





# ============ 通知相关 ============



class NotificationResponse(BaseModel):

    """通知响应"""

    id: int

    user_id: int

    task_id: Optional[int] = None

    message: str

    type: str

    is_read: bool

    created_at: Optional[datetime] = None



    class Config:

        from_attributes = True





# ============ FCM Token 相关 ============



class FCMTokenUpdate(BaseModel):

    """更新 FCM Token 请求"""

    fcm_token: str = Field(..., min_length=1, max_length=500, description="Firebase Cloud Messaging 设备令牌")





# ============ 用户设置相关 ============



class UserSettingsResponse(BaseModel):

    """用户设置响应"""

    email: str = ""

    email_notify_enabled: bool = True

    websocket_notify_enabled: bool = True

    default_check_interval: int = 30



    class Config:

        from_attributes = True





class UserSettingsUpdate(BaseModel):

    """更新用户设置请求（所有字段可选）"""

    email: Optional[str] = None

    email_notify_enabled: Optional[bool] = None

    websocket_notify_enabled: Optional[bool] = None

    default_check_interval: Optional[int] = Field(None, ge=10, le=3600, description="默认检查间隔（秒）")

    @validator("email")
    def validate_email(cls, v):
        if v is not None and v != "":
            if not re.match(r"^[\w.+-]+@[\w-]+\.[\w.-]+$", v):
                raise ValueError("邮箱格式不正确")
        return v





# ============ 搜索相关 ============



class SearchRequest(BaseModel):

    """演出搜索请求"""

    keyword: str = Field(..., min_length=1, description="搜索关键词")

    platform: Optional[str] = Field("all", description="平台：damai/maoyan/funwandao/all")





class EventInfoResponse(BaseModel):

    """演出信息响应"""

    platform: str

    event_id: str

    name: str

    artist: str = ""

    venue: str = ""

    date: str = ""

    url: str = ""

    poster_url: str = ""



class EventDetailResponse(BaseModel):

    """演出详情响应（含场次列表）"""

    event_id: str

    platform: str

    sessions: List[str] = []

    name: str = ""

    venue: str = ""

    artist: str = ""

    date: str = ""


"""认证路由 - 用户注册、登录、令牌管理"""

from datetime import datetime, timedelta



from fastapi import APIRouter, Depends, HTTPException, status

from jose import jwt

from passlib.context import CryptContext

from sqlalchemy.orm import Session



from app.config import settings

from app.database import get_db

from app.dependencies import get_current_user

from app.models.user import User

from app.schemas import UserCreate, UserLogin, UserResponse, Token, FCMTokenUpdate



router = APIRouter(prefix="/api/auth", tags=["认证"])



# 密码加密上下文

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")





def hash_password(password: str) -> str:

    """对密码进行 bcrypt 哈希"""

    return pwd_context.hash(password)





def verify_password(plain_password: str, hashed_password: str) -> bool:

    """验证密码是否匹配"""

    return pwd_context.verify(plain_password, hashed_password)





def create_access_token(user_id: int) -> str:

    """生成 JWT 访问令牌



    Args:

        user_id: 用户ID，写入 token 的 sub 字段



    Returns:

        编码后的 JWT 字符串

    """

    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {"sub": str(user_id), "exp": expire}

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)





@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)

async def register(user_data: UserCreate, db: Session = Depends(get_db)):

    """用户注册



    - 检查用户名和邮箱是否已被注册

    - 使用 bcrypt 加密密码

    - 返回新用户信息

    """

    # 检查用户名是否已存在

    if db.query(User).filter(User.username == user_data.username).first():

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="用户名已被注册",

        )

    # 检查邮箱是否已存在

    if db.query(User).filter(User.email == user_data.email).first():

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="邮箱已被注册",

        )



    # 创建用户

    new_user = User(

        username=user_data.username,

        email=user_data.email,

        hashed_password=hash_password(user_data.password),

    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)



    return UserResponse(

        id=new_user.id,

        username=new_user.username,

        email=new_user.email,

        message="注册成功",

    )





@router.post("/login", response_model=Token)

async def login(user_data: UserLogin, db: Session = Depends(get_db)):

    """用户登录



    - 验证用户名和密码

    - 返回 JWT 访问令牌

    """

    user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not verify_password(user_data.password, user.hashed_password):

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="用户名或密码错误",

            headers={"WWW-Authenticate": "Bearer"},

        )



    access_token = create_access_token(user.id)

    return Token(access_token=access_token, token_type="bearer")





@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "email_notify_enabled": current_user.email_notify_enabled,
        "websocket_notify_enabled": current_user.websocket_notify_enabled,
        "created_at": str(current_user.created_at) if current_user.created_at else None,
    }



@router.put("/fcm-token")

async def update_fcm_token(

    data: FCMTokenUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """更新当前用户的 FCM 设备令牌



    - 用于 Android 客户端绑定 FCM 推送 Token

    - 需要 JWT 认证

    """

    current_user.fcm_token = data.fcm_token

    db.commit()

    return {"message": "FCM Token 已更新"}


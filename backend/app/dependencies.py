"""公共依赖 - JWT 认证、当前用户获取等"""

from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from sqlalchemy.orm import Session



from app.config import settings

from app.database import get_db

from app.models.user import User



# OAuth2 密码承载方案，tokenUrl 指向登录端点

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")





async def get_current_user(

    token: str = Depends(oauth2_scheme),

    db: Session = Depends(get_db),

) -> User:

    """从 JWT token 中解析当前登录用户



    Args:

        token: Authorization 头中的 Bearer token

        db: 数据库会话



    Returns:

        当前登录的用户对象



    Raises:

        HTTPException 401: token 无效或用户不存在

    """

    credentials_exception = HTTPException(

        status_code=status.HTTP_401_UNAUTHORIZED,

        detail="无法验证凭据",

        headers={"WWW-Authenticate": "Bearer"},

    )

    try:

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        user_id_str = payload.get("sub")

        if user_id_str is None:

            raise credentials_exception

        user_id = int(user_id_str)

    except JWTError:

        raise credentials_exception



    user = db.query(User).filter(User.id == user_id).first()

    if user is None:

        raise credentials_exception

    return user


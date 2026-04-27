"""数据库连接配置 - SQLAlchemy 引擎、会话和基础模型"""

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings



# 创建数据库引擎

# SQLite 需要 connect_args={"check_same_thread": False} 以支持多线程

engine = create_engine(

    settings.DATABASE_URL,

    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},

    pool_size=10,

    max_overflow=20,

    pool_pre_ping=True,

    echo=False,

)



# 创建会话工厂

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# 声明式基类，所有模型继承此类

Base = declarative_base()





def get_db():

    """FastAPI 依赖注入函数，提供数据库会话"""

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


"""票务监控提醒系统 - FastAPI 应用入口"""

from contextlib import asynccontextmanager

from typing import List, Optional



from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query

from fastapi.middleware.cors import CORSMiddleware

from jose import JWTError, jwt



from app.config import settings

from app.database import engine, Base, SessionLocal

from app.routers import auth, tasks, notifications

from app.routers import settings as settings_router

from app.models.user import User

from app.schemas import SearchRequest, EventInfoResponse, EventDetailResponse

from app.services.scheduler import start_scheduler, shutdown_scheduler, init_scheduler

from app.services.ws_manager import manager





@asynccontextmanager

async def lifespan(app: FastAPI):

    """应用生命周期管理：启动时初始化数据库和调度器，关闭时清理资源"""

    # 启动时：创建数据库表

    Base.metadata.create_all(bind=engine)

    # 启动定时任务调度器

    start_scheduler()

    # 加载所有活跃的监控任务到调度器

    db = SessionLocal()

    try:

        init_scheduler(db)

    finally:

        db.close()

    yield

    # 关闭时：停止调度器

    shutdown_scheduler()





app = FastAPI(

    title="票务监控提醒系统",

    description="自动监控各大票务平台余票状态，及时推送通知提醒",

    version="0.1.0",

    lifespan=lifespan,

)



# CORS 中间件配置（开发阶段允许所有来源）

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



# 注册路由

app.include_router(auth.router)

app.include_router(tasks.router)

app.include_router(notifications.router)

app.include_router(settings_router.router)





@app.get("/health", tags=["健康检查"])

async def health_check():

    """健康检查端点，用于确认服务是否正常运行"""

    return {"status": "ok", "service": "票务监控提醒系统"}





# ============ 演出搜索端点 ============



# 模拟演出数据（平台适配器尚未完整实现，先返回模拟数据用于前端开发）

MOCK_EVENTS = [

    {

        "platform": "damai",

        "event_id": "dm001",

        "name": "周杰伦2026巡回演唱会-北京站",

        "artist": "周杰伦",

        "venue": "国家体育场（鸟巢）",

        "date": "2026-06-15",

        "url": "https://detail.damai.cn/item.htm?id=123",

        "poster_url": "",

    },

    {

        "platform": "maoyan",

        "event_id": "my001",

        "name": "林俊杰JJ20世界巡回演唱会-上海站",

        "artist": "林俊杰",

        "venue": "梅赛德斯奔驰文化中心",

        "date": "2026-07-20",

        "url": "https://show.maoyan.com/event/123",

        "poster_url": "",

    },

    {

        "platform": "funwandao",

        "event_id": "fwd001",

        "name": "草莓音乐节2026",

        "artist": "多位艺人",

        "venue": "北京世园公园",

        "date": "2026-05-01",

        "url": "https://www.funwandao.com/event/123",

        "poster_url": "",

    },

    {

        "platform": "damai",

        "event_id": "dm002",

        "name": "薛之谦2026天外来物巡回演唱会-广州站",

        "artist": "薛之谦",

        "venue": "广州天河体育中心",

        "date": "2026-08-10",

        "url": "https://detail.damai.cn/item.htm?id=456",

        "poster_url": "",

    },

    {

        "platform": "maoyan",

        "event_id": "my002",

        "name": "五月天2026好好好想见到你巡回演唱会-成都站",

        "artist": "五月天",

        "venue": "凤凰山体育公园",

        "date": "2026-09-05",

        "url": "https://show.maoyan.com/event/456",

        "poster_url": "",

    },

]



def generate_mock_events(keyword: str, platform: str = "all") -> list:

    """根据关键词动态生成模拟演出数据（已弃用，保留作为历史代码参考）"""

    return []





@app.post("/api/search", response_model=List[EventInfoResponse], tags=["搜索"])

async def search_events(req: SearchRequest):

    """搜索演出/活动



    - 根据关键词搜索

    - 支持按平台筛选

    - 优先尝试调用真实平台适配器（并发 + 超时控制），全部失败时回退到静态模拟数据

    """

    import asyncio

    import logging

    from app.platforms import get_adapter, PLATFORM_ADAPTERS



    search_logger = logging.getLogger(__name__)

    real_results = []



    # 确定要搜索的平台列表

    if req.platform and req.platform != "all":

        platforms_to_search = [req.platform] if req.platform in PLATFORM_ADAPTERS else []

    else:

        platforms_to_search = list(PLATFORM_ADAPTERS.keys())



    # 并发调用真实平台适配器搜索，整体限时 8 秒（给真实 API 更多时间）

    async def _search_one(platform_name: str):

        try:

            adapter = get_adapter(platform_name)

            events = await adapter.search_events(req.keyword)

            search_logger.info(f"[搜索] 平台 {platform_name} 返回 {len(events)} 条结果")

            return [event.model_dump() for event in events]

        except Exception as e:

            search_logger.warning(f"[搜索] 平台 {platform_name} 搜索失败: {e}")

            return []



    if platforms_to_search:

        try:

            results_list = await asyncio.wait_for(

                asyncio.gather(*[_search_one(p) for p in platforms_to_search]),

                timeout=8.0,

            )

            for r in results_list:

                real_results.extend(r)

        except asyncio.TimeoutError:

            search_logger.warning("[搜索] 真实平台搜索超时，回退到模拟数据")



    # 如果真实搜索有结果，返回真实结果

    if real_results:

        search_logger.info(f"[搜索] 关键词「{req.keyword}」共找到 {len(real_results)} 条真实结果")

        return real_results



    # 回退到静态模拟数据（仅当所有平台都完全失败时）

    search_logger.info(f"[搜索] 真实搜索无结果，回退到静态模拟数据")

    results = list(MOCK_EVENTS)



    # 按平台过滤

    if req.platform and req.platform != "all":

        results = [e for e in results if e["platform"] == req.platform]



    # 按关键词过滤（模拟搜索：匹配名称、艺人、场馆）

    keyword = req.keyword.lower()

    results = [

        e for e in results

        if keyword in e["name"].lower()

        or keyword in e["artist"].lower()

        or keyword in e["venue"].lower()

    ]



    return results





# ============ 演出详情端点（获取场次列表） ============



@app.get("/api/events/detail", response_model=EventDetailResponse, tags=["搜索"])
async def get_event_detail(
    event_id: str = Query(..., description="演出ID"),
    platform: str = Query("damai", description="平台名称"),
):
    """获取演出详情（含场次列表）

    前端在"添加监控"弹窗打开时调用此接口，获取该演出的场次信息。
    """
    import logging
    from app.platforms import get_adapter, PLATFORM_ADAPTERS

    detail_logger = logging.getLogger(__name__)

    if platform not in PLATFORM_ADAPTERS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"不支持的平台：{platform}")

    try:
        adapter = get_adapter(platform)
        # 构建演出 URL（大麦格式）
        if platform == "damai":
            event_url = f"https://detail.damai.cn/item.htm?id={event_id}"
        elif platform == "maoyan":
            event_url = f"https://show.maoyan.com/event/{event_id}"
        elif platform == "funwandao":
            event_url = f"https://www.funwandao.com/event/{event_id}"
        else:
            event_url = ""

        detail = await adapter.get_event_detail(event_url)
        detail_logger.info(
            f"[详情] 平台={platform}, event_id={event_id}, "
            f"场次数={len(detail.sessions)}"
        )
        return {
            "event_id": event_id,
            "platform": platform,
            "sessions": detail.sessions,
            "name": detail.event_info.name,
            "venue": detail.event_info.venue,
            "artist": detail.event_info.artist,
            "date": detail.event_info.date,
        }
    except Exception as e:
        detail_logger.error(f"[详情] 获取演出详情失败: {e}")
        return {
            "event_id": event_id,
            "platform": platform,
            "sessions": [],
            "name": "",
            "venue": "",
            "artist": "",
            "date": "",
        }





# ============ WebSocket 通知端点 ============



@app.websocket("/ws/notifications")

async def ws_notifications(websocket: WebSocket, token: str = Query(...)):

    """顶层 WebSocket 通知端点



    - 通过 ?token=xxx 传入 JWT token 进行认证

    - 认证成功后建立持久连接，接收实时通知推送

    """

    # 验证 JWT token

    try:

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        user_id: int = int(payload.get("sub"))

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

        await websocket.send_json({"type": "connected", "message": "WebSocket 连接成功"})

        while True:

            data = await websocket.receive_text()

            if data == "ping":

                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:

        manager.disconnect(user_id, websocket)


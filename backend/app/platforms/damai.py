"""大麦网平台适配器 - 实现大麦网的活动搜索和票务状态检查

搜索使用大麦 mtop 网关 API (mtop.damai.wireless.search.broadcast.list)，
通过两步请求（获取令牌 + 签名请求）绕过接口鉴权。
票务状态和详情通过解析 HTML 详情页获取。
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from app.platforms.base import (
    PlatformAdapter, EventInfo, TicketPrice, TicketStatusInfo, EventDetail
)

logger = logging.getLogger(__name__)

# User-Agent 轮换列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# 移动端 User-Agent（用于 mtop API）
MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
]

# mtop 网关配置
MTOP_BASE_URL = "https://mtop.damai.cn/h5"
MTOP_APP_KEY = "12574478"
MTOP_JSV = "2.7.2"
MTOP_SEARCH_API = "mtop.damai.wireless.search.broadcast.list"
MTOP_SEARCH_VER = "1.0"

# 场次详情 API（获取演出详细信息、场次列表、场馆、艺人等）
MTOP_DETAIL_API = "mtop.alibaba.damai.detail.getdetail"
MTOP_DETAIL_VER = "1.2"

# 座位/票价 API（获取具体场次的座位区域、票价档位、库存状态）
MTOP_SEAT_API = "mtop.alibaba.damai.detail.subpage.getdetail"
MTOP_SEAT_VER = "2.0"


class DamaiAdapter(PlatformAdapter):
    """大麦网适配器 - 实现大麦网的活动搜索和票务状态检查"""

    PLATFORM_NAME = "damai"

    def __init__(self):
        self.base_url = "https://search.damai.cn"
        self.detail_url = "https://detail.damai.cn"
        self.timeout = 15.0  # 请求超时时间（秒）

    def _get_headers(self) -> dict:
        """获取带随机 UA 的请求头（PC端，用于详情页）"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": "https://www.damai.cn/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _get_mtop_headers(self) -> dict:
        """获取 mtop API 请求头（移动端）"""
        return {
            "User-Agent": random.choice(MOBILE_USER_AGENTS),
            "Accept": "application/json",
            "Referer": "https://m.damai.cn/",
        }

    async def _random_delay(self):
        """随机延迟 1-2 秒，避免被封"""
        delay = random.uniform(1, 2)
        await asyncio.sleep(delay)

    @staticmethod
    def _compute_mtop_sign(token: str, timestamp: str, app_key: str, data: str) -> str:
        """计算 mtop 网关请求签名

        签名算法: md5(token + '&' + timestamp + '&' + appKey + '&' + data)
        """
        sign_str = f"{token}&{timestamp}&{app_key}&{data}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    async def _mtop_request(self, api_name: str, api_ver: str, data_obj: dict) -> Optional[dict]:
        """发起 mtop 网关请求（两步：获取令牌 + 签名请求）

        第一步: 发送一个带假签名的请求，服务器会返回 _m_h5_tk cookie
        第二步: 从 cookie 中提取令牌，计算正确签名后再次请求

        Args:
            api_name: API 名称，如 mtop.damai.wireless.search.broadcast.list
            api_ver: API 版本，如 1.0
            data_obj: 请求数据字典

        Returns:
            成功返回响应 JSON 中的 data 字段，失败返回 None
        """
        data_str = json.dumps(data_obj, ensure_ascii=False)
        headers = self._get_mtop_headers()
        api_url = f"{MTOP_BASE_URL}/{api_name}/{api_ver}/"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            # 第一步：获取 _m_h5_tk cookie（发送假签名请求）
            t1 = str(int(time.time() * 1000))
            params1 = {
                "jsv": MTOP_JSV,
                "appKey": MTOP_APP_KEY,
                "t": t1,
                "sign": "dummy",
                "api": api_name,
                "v": api_ver,
                "type": "originaljson",
                "dataType": "json",
                "data": data_str,
            }

            try:
                await client.get(api_url, params=params1, headers=headers)
            except httpx.HTTPError as e:
                logger.error(f"[大麦] mtop 获取令牌失败: {e}")
                return None

            # 从 cookie 中提取令牌
            m_h5_tk = ""
            for cookie in client.cookies.jar:
                if cookie.name == "_m_h5_tk":
                    m_h5_tk = cookie.value
                    break

            if not m_h5_tk:
                logger.warning("[大麦] mtop 未获取到 _m_h5_tk cookie")
                return None

            token = m_h5_tk.split("_")[0]

            # 第二步：使用正确签名发起真实请求
            t2 = str(int(time.time() * 1000))
            sign = self._compute_mtop_sign(token, t2, MTOP_APP_KEY, data_str)

            params2 = {
                "jsv": MTOP_JSV,
                "appKey": MTOP_APP_KEY,
                "t": t2,
                "sign": sign,
                "api": api_name,
                "v": api_ver,
                "type": "originaljson",
                "dataType": "json",
                "data": data_str,
            }

            try:
                resp = await client.get(api_url, params=params2, headers=headers)
                result = resp.json()
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                logger.error(f"[大麦] mtop 签名请求失败: {e}")
                return None

            # 检查返回状态
            ret = result.get("ret", [])
            if not any("SUCCESS" in r for r in ret):
                error_msg = ret[0] if ret else "未知错误"
                logger.warning(f"[大麦] mtop API 返回错误: {error_msg}")
                return None

            return result.get("data")

    def _build_event_url(self, item_id) -> str:
        """根据项目 ID 构建大麦网详情页 URL"""
        return f"https://detail.damai.cn/item.htm?id={item_id}"

    def _parse_mtop_item(self, item: dict) -> Optional[EventInfo]:
        """将 mtop API 返回的单个 item 解析为 EventInfo

        mtop item 字段说明:
        - itemId: 项目ID
        - name: 项目名称
        - cityName: 城市名
        - venueName: 场馆名
        - showTime: 演出时间
        - priceLow: 最低票价
        - verticalPic: 竖版海报图
        - categoryName: 分类名（演唱会/话剧等）
        - status: 状态码 (0=售卖中, 1=即将开抢, 2=售卖中)
        - itemSaleStatus: 售卖状态
        """
        try:
            item_id = str(item.get("itemId", ""))
            name = item.get("name", "")
            if not item_id or not name:
                return None

            # 构建状态文本
            status_code = item.get("status", "")
            sale_status = item.get("itemSaleStatus", -1)
            on_sale_time = item.get("onSaleTime", "")

            if on_sale_time:
                status_text = on_sale_time  # 如 "明天13:18开抢"
            elif sale_status == 0 or status_code == "0" or status_code == "2":
                status_text = "售票中"
            elif sale_status == 2 or status_code == "1":
                status_text = "即将开售"
            else:
                status_text = "售票中"

            # 价格处理
            price_low = item.get("priceLow", "")
            price_text = f"{price_low}元起" if price_low else ""

            # 场馆信息：城市 + 场馆名
            city = item.get("cityName", "")
            venue = item.get("venueName", "")
            venue_full = f"{city} | {venue}" if city and venue else venue or city

            return EventInfo(
                platform=self.PLATFORM_NAME,
                event_id=item_id,
                name=name,
                artist="",  # mtop API 不返回单独的艺人字段
                venue=venue_full,
                date=item.get("showTime", ""),
                url=self._build_event_url(item_id),
                poster_url=item.get("verticalPic", ""),
            )
        except Exception as e:
            logger.warning(f"[大麦] 解析 mtop 搜索结果项失败: {e}")
            return None

    async def search_events(self, keyword: str) -> List[EventInfo]:
        """搜索大麦网演出 - 使用 mtop 网关 API

        通过大麦移动端 mtop API 获取演出列表数据，
        从返回的所有模块（热门必抢、即将开抢、正在热抢）中收集项目，
        按关键字过滤后返回匹配结果。

        如果 mtop API 失败，回退到 searchajax.html 尝试。
        """
        events = []
        seen_ids = set()

        try:
            # 搜索不需要随机延迟，用户发起的搜索应快速响应

            # 方法一：mtop 网关 API
            logger.info(f"[大麦] 使用 mtop API 搜索: {keyword}")
            data = await self._mtop_request(
                MTOP_SEARCH_API,
                MTOP_SEARCH_VER,
                {"keyword": keyword, "pageIndex": 1, "pageSize": 20, "cityId": 0},
            )

            if data and "modules" in data:
                modules = data["modules"]
                keyword_lower = keyword.lower()

                for module in modules:
                    items = module.get("items", [])
                    for item in items:
                        item_name = item.get("name", "")
                        # 按关键字过滤：名称中包含搜索关键字
                        if keyword_lower not in item_name.lower():
                            continue

                        item_id = str(item.get("itemId", ""))
                        if item_id in seen_ids:
                            continue
                        seen_ids.add(item_id)

                        event = self._parse_mtop_item(item)
                        if event:
                            events.append(event)

                logger.info(
                    f"[大麦] mtop API 搜索「{keyword}」，"
                    f"从 {sum(len(m.get('items', [])) for m in modules)} 个项目中"
                    f"匹配到 {len(events)} 条结果"
                )

            # 如果 mtop 没有结果，尝试 searchajax.html 回退
            if not events:
                logger.info(f"[大麦] mtop 无匹配结果，尝试 searchajax.html 回退")
                events = await self._search_via_ajax(keyword)

        except Exception as e:
            logger.error(f"[大麦] 搜索发生未知错误: {e}")

        return events

    async def _search_via_ajax(self, keyword: str) -> List[EventInfo]:
        """回退方法：尝试通过 searchajax.html 搜索（可能被反爬拦截）"""
        events = []
        try:
            params = {
                "keyword": keyword,
                "cty": "",
                "ctl": "",
                "sctl": "",
                "tsg": "0",
                "st": "",
                "et": "",
                "order": "1",
                "pageSize": "30",
                "currPage": "1",
                "tn": "",
            }

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/searchajax.html",
                    params=params,
                    headers=self._get_headers(),
                )
                response.raise_for_status()

            # 检测是否被反爬拦截（TMD 验证码页面）
            if "_____tmd_____" in response.text or "captcha" in response.text.lower():
                logger.warning("[大麦] searchajax.html 被反爬拦截（TMD验证码）")
                return events

            # 尝试解析 JSON 响应
            try:
                data = response.json()
                if isinstance(data, dict) and "pageData" in data:
                    page_data = data["pageData"]
                    result_data = page_data.get("resultData", [])

                    if isinstance(result_data, list):
                        for item in result_data:
                            try:
                                item_id = str(item.get("projectid", item.get("id", "")))
                                name = item.get("nameNoHtml", item.get("name", ""))
                                if not name:
                                    continue

                                # 清理 HTML 标签
                                import re
                                name_clean = re.sub(r"<[^>]+>", "", name)

                                city = item.get("cityname", "")
                                venue = item.get("venue", "")
                                venue_full = f"{city} | {venue}" if city and venue else venue or city

                                events.append(EventInfo(
                                    platform=self.PLATFORM_NAME,
                                    event_id=item_id,
                                    name=name_clean,
                                    artist="",
                                    venue=venue_full,
                                    date=item.get("showtime", ""),
                                    url=self._build_event_url(item_id),
                                    poster_url=item.get("verticalPic", ""),
                                ))
                            except Exception as e:
                                logger.warning(f"[大麦] 解析 searchajax 结果项失败: {e}")
                                continue

                    logger.info(f"[大麦] searchajax 搜索「{keyword}」找到 {len(events)} 条结果")
            except (ValueError, KeyError):
                logger.warning("[大麦] searchajax 响应非 JSON 格式")

        except httpx.HTTPError as e:
            logger.error(f"[大麦] searchajax 请求失败: {e}")
        except Exception as e:
            logger.error(f"[大麦] searchajax 搜索发生错误: {e}")

        return events

    async def _fetch_detail_via_mtop(self, event_id: str) -> Optional[dict]:
        """通过 mtop 详情 API 获取演出完整数据

        调用 mtop.alibaba.damai.detail.getdetail/1.2，返回解析后的 result 字典。
        内部包含 detailViewComponentMap.item 下的 staticData / item / dynamicExtData。
        """
        try:
            data = await self._mtop_request(
                MTOP_DETAIL_API, MTOP_DETAIL_VER, {"itemId": event_id}
            )
            if not data:
                return None

            result_str = data.get("result", "")
            if isinstance(result_str, str):
                return json.loads(result_str)
            elif isinstance(result_str, dict):
                return result_str
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"[大麦] 解析 mtop 详情数据失败: {e}")
        return None

    def _extract_perform_dates(self, static_data: dict) -> list:
        """从 serviceNotes 中提取场次日期列表

        大麦的场次信息隐藏在 itemBase.serviceNotes[].tagDescJson.performRules 中。
        """
        sessions = []
        try:
            item_base = static_data.get("itemBase", {})
            service_notes = item_base.get("serviceNotes", [])
            for note in service_notes:
                tag_desc_json = note.get("tagDescJson", "")
                if not tag_desc_json:
                    continue
                try:
                    desc_obj = json.loads(tag_desc_json)
                    perform_rules = desc_obj.get("performRules", [])
                    for rule in perform_rules:
                        perform_date = rule.get("performDate", "")
                        if perform_date:
                            sessions.append(perform_date)
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception as e:
            logger.warning(f"[大麦] 提取场次日期失败: {e}")

        # 如果没有从 serviceNotes 中提取到，用 showTime 兜底
        if not sessions:
            show_time = static_data.get("itemBase", {}).get("showTime", "")
            if show_time:
                sessions.append(show_time)

        return sessions

    @staticmethod
    def _parse_price_range(price_range_str: str) -> list:
        """解析价格区间字符串为票价列表

        如 '¥317 - ¥1717' -> [317.0, 1717.0]
        """
        import re
        prices = []
        for m in re.finditer(r'[\d.]+', price_range_str):
            try:
                prices.append(float(m.group()))
            except ValueError:
                pass
        return prices

    @staticmethod
    def _determine_buy_status(buy_btn_status: int, buy_btn_text: str) -> tuple:
        """根据购买按钮状态判断售票情况

        Returns:
            (available: bool, status_text: str)
        """
        text = buy_btn_text or ""
        # buyBtnStatus 常见值:
        # 0/1 = 可购买, 100 = 不支持该渠道, 其他 = 售罄/未开售等

        # 明确不可购买的状态
        if any(kw in text for kw in ["售罄", "无票", "已售完", "暂时售罄", "暂时缺货", "已结束"]):
            return False, "无票"
        elif any(kw in text for kw in ["即将开抢", "即将开售", "预售", "未开售"]):
            return False, "即将开抢"

        # 可购买状态（含仅APP可购，说明票仍在售，只是渠道受限）
        if any(kw in text for kw in ["立即购买", "立即抢购", "选座购买", "有票"]):
            return True, "有票"
        elif any(kw in text for kw in ["不支持购票", "该渠道", "仅APP可购", "APP购买"]):
            # H5 渠道不支持，但演出本身仍在售，标记为可购买
            return True, "仅APP可购"
        elif buy_btn_status in (0, 1):
            return True, "有票"
        else:
            return False, text or "状态未知"

    async def _fetch_seat_info(self, event_id: str, perform_id: str = "") -> Optional[dict]:
        """尝试通过座位 API 获取票价档位信息

        调用 mtop.alibaba.damai.detail.subpage.getdetail/2.0。
        注意：该接口在 H5 环境下可能被安全策略拦截，失败时返回 None。
        """
        try:
            data_obj = {"itemId": event_id}
            if perform_id:
                data_obj["performId"] = perform_id

            data = await self._mtop_request(
                MTOP_SEAT_API, MTOP_SEAT_VER, data_obj
            )
            if not data:
                return None

            result_str = data.get("result", "")
            if isinstance(result_str, str):
                return json.loads(result_str)
            elif isinstance(result_str, dict):
                return result_str
        except Exception as e:
            logger.debug(f"[大麦] 座位 API 调用失败（可能被安全策略拦截）: {e}")
        return None

    async def check_ticket_status(self, event_url: str) -> TicketStatusInfo:
        """检查大麦网演出票务状态

        优先使用 mtop 详情 API 获取状态信息（价格区间、购买按钮状态等），
        如果 mtop 失败则回退到 HTML 页面解析。
        """
        prices = []
        event_name = ""

        # 从 URL 中提取 event_id
        event_id = ""
        if "id=" in event_url:
            event_id = event_url.split("id=")[-1].split("&")[0]

        try:
            await self._random_delay()

            # ── 方法一：通过 mtop 详情 API 获取状态 ──
            if event_id:
                logger.info(f"[大麦] 通过 mtop API 检查票务状态: itemId={event_id}")
                result = await self._fetch_detail_via_mtop(event_id)

                if result:
                    component_map = result.get("detailViewComponentMap", {})
                    item_node = component_map.get("item", {})
                    static_data = item_node.get("staticData", {})
                    item_data = item_node.get("item", {})

                    # 提取演出名称
                    event_name = static_data.get("itemBase", {}).get("itemName", "")

                    # 提取价格区间
                    price_range = item_data.get("priceRange", "")
                    price_values = self._parse_price_range(price_range)

                    # 判断购买状态
                    buy_btn_status = item_data.get("buyBtnStatus", -1)
                    buy_btn_text = item_data.get("buyBtnText", "")
                    available, status_text = self._determine_buy_status(
                        buy_btn_status, buy_btn_text
                    )

                    # 尝试通过座位 API 获取详细票档
                    seat_result = await self._fetch_seat_info(event_id)
                    if seat_result:
                        # 如果座位 API 有返回，尝试解析详细票档
                        logger.info("[大麦] 座位 API 返回数据，解析详细票档")
                        sku_list = seat_result.get("skuList", seat_result.get("priceList", []))
                        for sku in sku_list:
                            sku_name = sku.get("skuName", sku.get("priceName", "未知档位"))
                            sku_price = float(sku.get("price", sku.get("priceValue", 0)))
                            sku_available = sku.get("canBuy", sku.get("hasStock", False))
                            prices.append(TicketPrice(
                                name=sku_name,
                                price=sku_price,
                                available=bool(sku_available),
                                status="有票" if sku_available else "无票",
                            ))

                    # 如果座位 API 没有详细票档，用价格区间生成概要信息
                    if not prices:
                        if len(price_values) >= 2:
                            prices.append(TicketPrice(
                                name=f"最低票价",
                                price=price_values[0],
                                available=available,
                                status=status_text,
                            ))
                            prices.append(TicketPrice(
                                name=f"最高票价",
                                price=price_values[-1],
                                available=available,
                                status=status_text,
                            ))
                        elif len(price_values) == 1:
                            prices.append(TicketPrice(
                                name="票价",
                                price=price_values[0],
                                available=available,
                                status=status_text,
                            ))
                        else:
                            prices.append(TicketPrice(
                                name="默认票档",
                                price=0,
                                available=available,
                                status=status_text,
                            ))

                    logger.info(
                        f"[大麦] mtop API 票务状态: {event_name}，"
                        f"价格区间={price_range}，状态={status_text}，"
                        f"共 {len(prices)} 个票档"
                    )

                    return TicketStatusInfo(
                        event_name=event_name,
                        event_url=event_url,
                        platform=self.PLATFORM_NAME,
                        prices=prices,
                        checked_at=datetime.now().isoformat(),
                    )

            # ── 方法二：回退到 HTML 页面解析 ──
            logger.info(f"[大麦] mtop API 未获取到数据，回退到 HTML 解析")
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(event_url, headers=self._get_headers())
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            title_el = soup.select_one("h1.detail-title, .perform-title, h1, title")
            if title_el:
                event_name = title_el.get_text(strip=True)

            page_text = soup.get_text()
            if any(kw in page_text for kw in ["有票", "立即购买", "选座购买", "立即抢购"]):
                prices.append(TicketPrice(
                    name="默认票档", price=0, available=True, status="有票"
                ))
            elif any(kw in page_text for kw in ["无票", "售罄", "已售完"]):
                prices.append(TicketPrice(
                    name="默认票档", price=0, available=False, status="无票"
                ))
            elif any(kw in page_text for kw in ["即将开抢", "即将开售"]):
                prices.append(TicketPrice(
                    name="默认票档", price=0, available=False, status="即将开抢"
                ))
            else:
                prices.append(TicketPrice(
                    name="默认票档", price=0, available=False, status="状态未知"
                ))

            logger.info(f"[大麦] HTML 解析票务状态完成: {event_name}，共 {len(prices)} 个票档")

        except httpx.HTTPError as e:
            logger.error(f"[大麦] 请求演出详情页失败: {e}")
            prices.append(TicketPrice(
                name="默认票档", price=0, available=False, status="请求失败"
            ))
        except Exception as e:
            logger.error(f"[大麦] 检查票务状态发生未知错误: {e}")
            prices.append(TicketPrice(
                name="默认票档", price=0, available=False, status="检查失败"
            ))

        return TicketStatusInfo(
            event_name=event_name,
            event_url=event_url,
            platform=self.PLATFORM_NAME,
            prices=prices,
            checked_at=datetime.now().isoformat(),
        )

    async def get_event_detail(self, event_url: str) -> EventDetail:
        """获取大麦网演出详情

        优先使用 mtop.alibaba.damai.detail.getdetail/1.2 获取结构化数据，
        包括演出名称、场馆、艺人、场次日期、价格区间、巡演信息等。
        如果 mtop 失败则回退到 HTML 页面解析。
        """
        # 从 URL 中提取 event_id
        event_id = ""
        if "id=" in event_url:
            event_id = event_url.split("id=")[-1].split("&")[0]

        try:
            await self._random_delay()

            # ── 方法一：通过 mtop 详情 API ──
            if event_id:
                logger.info(f"[大麦] 通过 mtop API 获取演出详情: itemId={event_id}")
                result = await self._fetch_detail_via_mtop(event_id)

                if result:
                    component_map = result.get("detailViewComponentMap", {})
                    item_node = component_map.get("item", {})
                    static_data = item_node.get("staticData", {})
                    dynamic_data = item_node.get("dynamicExtData", {})
                    item_data = item_node.get("item", {})

                    item_base = static_data.get("itemBase", {})
                    venue_data = static_data.get("venue", {})

                    # 提取艺人名称
                    artist_name = ""
                    artists = dynamic_data.get("artists", [])
                    if artists:
                        artist_name = artists[0].get("artistName", "")
                    if not artist_name:
                        brand_artists = dynamic_data.get("brandArtists", [])
                        if brand_artists:
                            artist_name = brand_artists[0].get("name", "")

                    # 构建场馆信息
                    city = item_base.get("cityName", venue_data.get("venueCityName", ""))
                    venue_name = venue_data.get("venueName", "")
                    venue_full = f"{city} | {venue_name}" if city and venue_name else venue_name or city

                    event_info = EventInfo(
                        platform=self.PLATFORM_NAME,
                        event_id=event_id,
                        name=item_base.get("itemName", ""),
                        artist=artist_name,
                        venue=venue_full,
                        date=item_base.get("showTime", ""),
                        url=event_url,
                        poster_url=item_base.get("itemPic", ""),
                    )

                    # 提取场次日期列表
                    sessions = self._extract_perform_dates(static_data)

                    # 获取票务状态
                    ticket_status = await self.check_ticket_status(event_url)

                    logger.info(
                        f"[大麦] mtop API 获取演出详情完成: {event_info.name}，"
                        f"场馆={venue_full}，场次数={len(sessions)}，"
                        f"艺人={artist_name}"
                    )

                    return EventDetail(
                        event_info=event_info,
                        sessions=sessions,
                        ticket_status=ticket_status,
                    )

            # ── 方法二：回退到 HTML 页面解析 ──
            logger.info(f"[大麦] mtop API 未获取到数据，回退到 HTML 解析演出详情")
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(event_url, headers=self._get_headers())
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            title_el = soup.select_one("h1.detail-title, .perform-title, h1, title")
            venue_el = soup.select_one(".venue, .perform-venue, [class*=venue]")
            date_el = soup.select_one(".date, .perform-date, [class*=date], [class*=time]")
            poster_el = soup.select_one(".poster img, .detail-img img, img.poster")

            event_info = EventInfo(
                platform=self.PLATFORM_NAME,
                event_id=event_id,
                name=title_el.get_text(strip=True) if title_el else "",
                venue=venue_el.get_text(strip=True) if venue_el else "",
                date=date_el.get_text(strip=True) if date_el else "",
                url=event_url,
                poster_url=poster_el.get("src", "") if poster_el else "",
            )

            sessions = []
            session_items = soup.select(
                ".session-item, .perform-session, [class*=session] li, "
                ".date-select .item, .date-item"
            )
            for s_item in session_items:
                session_text = s_item.get_text(strip=True)
                if session_text:
                    sessions.append(session_text)

            ticket_status = await self.check_ticket_status(event_url)

            logger.info(f"[大麦] HTML 解析演出详情完成: {event_info.name}")

            return EventDetail(
                event_info=event_info,
                sessions=sessions,
                ticket_status=ticket_status,
            )

        except Exception as e:
            logger.error(f"[大麦] 获取演出详情失败: {e}")
            return EventDetail(
                event_info=EventInfo(
                    platform=self.PLATFORM_NAME,
                    event_id=event_id,
                    name="获取失败",
                    url=event_url,
                ),
            )

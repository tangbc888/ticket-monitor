"""猫眼平台适配器 - 实现猫眼演出的活动搜索和票务状态检查"""

import asyncio

import logging

import random

from datetime import datetime

from typing import List



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





class MaoyanAdapter(PlatformAdapter):

    """猫眼适配器 - 实现猫眼演出的活动搜索和票务状态检查"""



    PLATFORM_NAME = "maoyan"



    def __init__(self):

        self.base_url = "https://show.maoyan.com"

        self.timeout = 5.0



    def _get_headers(self) -> dict:

        """获取带随机 UA 的请求头"""

        return {

            "User-Agent": random.choice(USER_AGENTS),

            "Referer": "https://show.maoyan.com/",

            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",

        }



    async def _random_delay(self):

        """随机延迟 1-2 秒，避免被封"""

        delay = random.uniform(1, 2)

        await asyncio.sleep(delay)



    async def search_events(self, keyword: str) -> List[EventInfo]:

        """通过猫眼演出搜索页面抓取演出列表



        使用 httpx 请求猫眼搜索页，用 BeautifulSoup 解析 HTML 提取结果。

        """

        events = []

        try:

            # 搜索不需要随机延迟，用户发起的搜索应快速响应



            url = f"{self.base_url}/search"

            params = {"keyword": keyword}



            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:

                response = await client.get(url, params=params, headers=self._get_headers())

                response.raise_for_status()



            soup = BeautifulSoup(response.text, "html.parser")



            # 猫眼搜索结果的常见选择器，尝试多种可能的结构

            items = soup.select(

                ".show-item, .result-item, .event-item, "

                ".search-result-item, .show-list .item, "

                "[class*='show-item'], [class*='result'], [class*='event']"

            )



            for item in items:

                try:

                    link = item.select_one("a[href]")

                    if not link:

                        continue



                    href = link.get("href", "")



                    # 提取标题

                    title_el = item.select_one(

                        ".show-name, .item-title, .title, h3, h4, "

                        "[class*='name'], [class*='title']"

                    )

                    # 提取场馆

                    venue_el = item.select_one(

                        ".show-venue, .venue, [class*='venue'], [class*='location']"

                    )

                    # 提取日期

                    date_el = item.select_one(

                        ".show-date, .date, .time, [class*='date'], [class*='time']"

                    )

                    # 提取艺人

                    artist_el = item.select_one(

                        ".show-artist, .artist, [class*='artist'], [class*='performer']"

                    )

                    # 提取海报

                    poster_el = item.select_one("img[src]")



                    # 拼接完整 URL

                    event_url = ""

                    if href.startswith("http"):

                        event_url = href

                    elif href.startswith("/"):

                        event_url = f"{self.base_url}{href}"

                    elif href:

                        event_url = f"https:{href}" if href.startswith("//") else href



                    # 提取事件 ID

                    event_id = ""

                    if event_url:

                        parts = event_url.rstrip("/").split("/")

                        if parts:

                            event_id = parts[-1]



                    name = title_el.get_text(strip=True) if title_el else ""

                    if not name:

                        name = link.get_text(strip=True)

                    if not name:

                        continue



                    events.append(EventInfo(

                        platform=self.PLATFORM_NAME,

                        event_id=event_id,

                        name=name,

                        artist=artist_el.get_text(strip=True) if artist_el else "",

                        venue=venue_el.get_text(strip=True) if venue_el else "",

                        date=date_el.get_text(strip=True) if date_el else "",

                        url=event_url,

                        poster_url=poster_el.get("src", "") if poster_el else "",

                    ))

                except Exception as e:

                    logger.warning(f"[猫眼] 解析搜索结果项失败: {e}")

                    continue



            logger.info(f"[猫眼] 搜索关键词「{keyword}」，找到 {len(events)} 条结果")



        except httpx.HTTPError as e:

            logger.error(f"[猫眼] 搜索请求失败: {e}")

        except Exception as e:

            logger.error(f"[猫眼] 搜索发生未知错误: {e}")



        return events



    async def check_ticket_status(self, event_url: str) -> TicketStatusInfo:

        """检查猫眼演出票务状态



        请求演出详情页，解析 HTML 提取票档信息。

        """

        prices = []

        event_name = ""



        try:

            await self._random_delay()



            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:

                response = await client.get(event_url, headers=self._get_headers())

                response.raise_for_status()



            soup = BeautifulSoup(response.text, "html.parser")



            # 提取演出名称

            title_el = soup.select_one(

                ".show-name, .detail-title, h1, .event-title, title"

            )

            if title_el:

                event_name = title_el.get_text(strip=True)



            # 提取票价档位

            sku_items = soup.select(

                ".ticket-item, .price-item, .sku-item, "

                "[class*=ticket-item], [class*=price-item], [class*=sku]"

            )



            for item in sku_items:

                try:

                    name_el = item.select_one(

                        ".ticket-name, .price-name, .sku-name, span, label"

                    )

                    name = name_el.get_text(strip=True) if name_el else "未知档位"



                    price_el = item.select_one(

                        ".ticket-price, .price, em, strong, [class*=price]"

                    )

                    price_text = price_el.get_text(strip=True) if price_el else "0"

                    price_digits = "".join(c for c in price_text if c.isdigit() or c == ".")

                    price_num = float(price_digits) if price_digits else 0.0



                    item_text = item.get_text()

                    item_classes = " ".join(item.get("class", []))

                    available = True

                    status_text = "有票"



                    if any(kw in item_text for kw in ["无票", "售罄", "暂无", "已售完"]):

                        available = False

                        status_text = "无票"

                    elif any(kw in item_classes for kw in ["disabled", "sold-out", "unavailable"]):

                        available = False

                        status_text = "无票"

                    elif any(kw in item_text for kw in ["即将开抢", "即将开售", "预售"]):

                        available = False

                        status_text = "即将开抢"



                    prices.append(TicketPrice(

                        name=name,

                        price=price_num,

                        available=available,

                        status=status_text,

                    ))

                except Exception as e:

                    logger.warning(f"[猫眼] 解析单个票档失败: {e}")

                    continue



            # 无具体票档时，从页面整体判断

            if not prices:

                page_text = soup.get_text()

                if any(kw in page_text for kw in ["有票", "立即购买", "选座购买"]):

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



            logger.info(f"[猫眼] 检查票务状态完成: {event_name}，共 {len(prices)} 个票档")



        except httpx.HTTPError as e:

            logger.error(f"[猫眼] 请求演出详情页失败: {e}")

            prices.append(TicketPrice(

                name="默认票档", price=0, available=False, status="请求失败"

            ))

        except Exception as e:

            logger.error(f"[猫眼] 检查票务状态发生未知错误: {e}")

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

        """获取猫眼演出详情"""

        try:

            await self._random_delay()



            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:

                response = await client.get(event_url, headers=self._get_headers())

                response.raise_for_status()



            soup = BeautifulSoup(response.text, "html.parser")



            title_el = soup.select_one(".show-name, .detail-title, h1, title")

            venue_el = soup.select_one(".venue, .show-venue, [class*=venue]")

            date_el = soup.select_one(".date, .show-date, [class*=date]")

            artist_el = soup.select_one(".artist, .show-artist, [class*=artist]")

            poster_el = soup.select_one(".poster img, .detail-img img, img.poster")



            # 提取事件 ID

            event_id = ""

            parts = event_url.rstrip("/").split("/")

            if parts:

                event_id = parts[-1]



            event_info = EventInfo(

                platform=self.PLATFORM_NAME,

                event_id=event_id,

                name=title_el.get_text(strip=True) if title_el else "",

                artist=artist_el.get_text(strip=True) if artist_el else "",

                venue=venue_el.get_text(strip=True) if venue_el else "",

                date=date_el.get_text(strip=True) if date_el else "",

                url=event_url,

                poster_url=poster_el.get("src", "") if poster_el else "",

            )



            # 提取场次列表

            sessions = []

            session_items = soup.select(

                ".session-item, .show-session, [class*=session] li, .date-item"

            )

            for s_item in session_items:

                session_text = s_item.get_text(strip=True)

                if session_text:

                    sessions.append(session_text)



            ticket_status = await self.check_ticket_status(event_url)



            logger.info(f"[猫眼] 获取演出详情完成: {event_info.name}")



            return EventDetail(

                event_info=event_info,

                sessions=sessions,

                ticket_status=ticket_status,

            )



        except Exception as e:

            logger.error(f"[猫眼] 获取演出详情失败: {e}")

            return EventDetail(

                event_info=EventInfo(

                    platform=self.PLATFORM_NAME,

                    event_id="",

                    name="获取失败",

                    url=event_url,

                ),

            )


"""
数据源抽象层
支持多数据源聚合和自动故障切换
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn/",
    }

    @abstractmethod
    def fetch_realtime(self, code: str) -> Optional[dict]:
        """获取实时行情"""
        pass

    @abstractmethod
    def fetch_kline(
        self, code: str, period: str = "daily", count: int = 100
    ) -> Optional[dict]:
        """获取K线数据

        Args:
            code: 证券代码
            period: 周期 (1/5/15/30/60/240 分钟)
            count: 数据条数
        """
        pass

    def _fetch(self, url: str, timeout: int = 10) -> Optional[str]:
        """HTTP请求"""
        try:
            req = Request(url, headers=self.HEADERS)
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except (URLError, HTTPError, TimeoutError) as e:
            logger.error(f"{self.__class__.__name__} 请求失败: {e}")
            return None

    def _detect_market(self, code: str) -> str:
        """判断市场: sh=上交所, sz=深交所"""
        if code.startswith(("51", "52", "58", "50", "56")):
            return "sh"
        elif code.startswith(("15", "16", "18", "17", "19")):
            return "sz"
        return "sh"


class SinaDataSource(DataSource):
    """新浪财经数据源"""

    def __init__(self):
        super().__init__()
        self.realtime_url = "https://hq.sinajs.cn/list={}"
        self.kline_url = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"

    def fetch_realtime(self, code: str) -> Optional[dict]:
        """获取实时行情"""
        market = self._detect_market(code)
        symbol = f"{market}{code}"
        url = self.realtime_url.format(symbol)

        resp = self._fetch(url)
        if not resp:
            return None

        match = re.search(r'="([^"]*)"', resp)
        if not match:
            return None

        parts = match.group(1).split(",")
        if len(parts) < 32:
            return None

        data = {
            "code": code,
            "name": parts[0],
            "open": float(parts[1]) if parts[1] else 0,
            "prev_close": float(parts[2]) if parts[2] else 0,
            "current": float(parts[3]) if parts[3] else 0,
            "high": float(parts[4]) if parts[4] else 0,
            "low": float(parts[5]) if parts[5] else 0,
            "volume": int(float(parts[8])) if parts[8] else 0,
            "amount": float(parts[9]) if parts[9] else 0,
            "date": parts[30] if len(parts) > 30 else "",
            "time": parts[31] if len(parts) > 31 else "",
            "bid1": [float(parts[10]), int(float(parts[11]))] if parts[10] else [0, 0],
            "bid2": [float(parts[12]), int(float(parts[13]))] if parts[12] else [0, 0],
            "bid3": [float(parts[14]), int(float(parts[15]))] if parts[14] else [0, 0],
            "bid4": [float(parts[16]), int(float(parts[17]))] if parts[16] else [0, 0],
            "bid5": [float(parts[18]), int(float(parts[19]))] if parts[18] else [0, 0],
            "ask1": [float(parts[20]), int(float(parts[21]))] if parts[20] else [0, 0],
            "ask2": [float(parts[22]), int(float(parts[23]))] if parts[22] else [0, 0],
            "ask3": [float(parts[24]), int(float(parts[25]))] if parts[24] else [0, 0],
            "ask4": [float(parts[26]), int(float(parts[27]))] if parts[26] else [0, 0],
            "ask5": [float(parts[28]), int(float(parts[29]))] if parts[28] else [0, 0],
            "fetch_time": datetime.now().isoformat(),
            "source": "sina",
        }

        if data["prev_close"] > 0:
            data["change"] = round(data["current"] - data["prev_close"], 3)
            data["change_pct"] = round((data["change"] / data["prev_close"]) * 100, 2)
        else:
            data["change"] = 0
            data["change_pct"] = 0

        logger.info(f"SinaDataSource 获取成功: {data['name']} {data['current']}")
        return data

    def fetch_kline(
        self, code: str, period: str = "daily", count: int = 100
    ) -> Optional[dict]:
        """获取K线数据

        Args:
            code: 证券代码
            period: 周期 (1/5/15/30/60/240 分钟)
            count: 数据条数
        """
        period_map = {
            "1min": 1,
            "5min": 5,
            "15min": 15,
            "30min": 30,
            "60min": 60,
            "daily": 240,
        }
        scale = period_map.get(period, 240)

        market = self._detect_market(code)
        symbol = f"{market}{code}"

        period_name = {
            1: "1分钟",
            5: "5分钟",
            15: "15分钟",
            30: "30分钟",
            60: "60分钟",
            240: "日K",
        }.get(scale, f"{scale}分钟")

        url = f"{self.kline_url}?symbol={symbol}&scale={scale}&datalen={count}"
        resp = self._fetch(url)
        if not resp:
            return None

        try:
            raw = json.loads(resp)
        except json.JSONDecodeError as e:
            logger.error(f"SinaDataSource JSON解析失败: {e}")
            return None

        if not raw:
            logger.error("SinaDataSource K线数据为空")
            return None

        klines = []
        for item in raw:
            klines.append({
                "date": item.get("day", ""),
                "open": float(item.get("open", 0)),
                "high": float(item.get("high", 0)),
                "low": float(item.get("low", 0)),
                "close": float(item.get("close", 0)),
                "volume": int(float(item.get("volume", 0))),
                "ma5": float(item.get("ma_price5", 0)),
                "ma10": float(item.get("ma_price10", 0)),
                "ma30": float(item.get("ma_price30", 0)),
                "vol_ma5": float(item.get("ma_volume5", 0)),
                "vol_ma10": float(item.get("ma_volume10", 0)),
                "vol_ma30": float(item.get("ma_volume30", 0)),
            })

        logger.info(f"SinaDataSource 获取 {period_name}K线 {len(klines)} 条")
        return {
            "code": code,
            "period": period_name,
            "period_scale": scale,
            "count": len(klines),
            "klines": klines,
            "fetch_time": datetime.now().isoformat(),
            "source": "sina",
        }


class TencentDataSource(DataSource):
    """腾讯财经数据源（备用）"""

    def __init__(self):
        super().__init__()
        self.realtime_url = "https://web.sqt.gtimg.cn/q={}"
        self.kline_url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    def fetch_realtime(self, code: str) -> Optional[dict]:
        """获取实时行情"""
        market = self._detect_market(code)
        # 腾讯使用不同格式: sh512400 或 sz159915
        symbol = f"{market}{code}"
        url = self.realtime_url.format(symbol)

        resp = self._fetch(url)
        if not resp:
            return None

        # 腾讯返回格式: v_sh512400="51...,..."
        match = re.search(r'v_.*?="([^"]*)"', resp)
        if not match:
            return None

        parts = match.group(1).split("~")
        if len(parts) < 40:
            return None

        data = {
            "code": code,
            "name": parts[1],
            "open": float(parts[5]) if parts[5] else 0,
            "prev_close": float(parts[4]) if parts[4] else 0,
            "current": float(parts[3]) if parts[3] else 0,
            "high": float(parts[33]) if parts[33] else 0,
            "low": float(parts[34]) if parts[34] else 0,
            "volume": int(float(parts[6])) if parts[6] else 0,
            "amount": float(parts[37]) if parts[37] else 0,
            "date": parts[30] if len(parts) > 30 else "",
            "time": parts[31] if len(parts) > 31 else "",
            "bid1": [float(parts[9]), int(float(parts[10]))] if parts[9] else [0, 0],
            "bid2": [float(parts[11]), int(float(parts[12]))] if parts[11] else [0, 0],
            "bid3": [float(parts[13]), int(float(parts[14]))] if parts[13] else [0, 0],
            "bid4": [float(parts[15]), int(float(parts[16]))] if parts[15] else [0, 0],
            "bid5": [float(parts[17]), int(float(parts[18]))] if parts[17] else [0, 0],
            "ask1": [float(parts[19]), int(float(parts[20]))] if parts[19] else [0, 0],
            "ask2": [float(parts[21]), int(float(parts[22]))] if parts[21] else [0, 0],
            "ask3": [float(parts[23]), int(float(parts[24]))] if parts[23] else [0, 0],
            "ask4": [float(parts[25]), int(float(parts[26]))] if parts[25] else [0, 0],
            "ask5": [float(parts[27]), int(float(parts[28]))] if parts[27] else [0, 0],
            "fetch_time": datetime.now().isoformat(),
            "source": "tencent",
        }

        if data["prev_close"] > 0:
            data["change"] = round(data["current"] - data["prev_close"], 3)
            data["change_pct"] = round((data["change"] / data["prev_close"]) * 100, 2)
        else:
            data["change"] = 0
            data["change_pct"] = 0

        logger.info(f"TencentDataSource 获取成功: {data['name']} {data['current']}")
        return data

    def fetch_kline(
        self, code: str, period: str = "daily", count: int = 100
    ) -> Optional[dict]:
        """获取K线数据

        Args:
            code: 证券代码
            period: 周期 (1/5/15/30/60/240 分钟)
            count: 数据条数
        """
        period_map = {
            "1min": 1,
            "5min": 5,
            "15min": 15,
            "30min": 30,
            "60min": 60,
            "daily": 240,
        }
        scale = period_map.get(period, 240)

        market = self._detect_market(code)
        symbol = f"{market}{code}"

        period_name = {
            1: "1分钟",
            5: "5分钟",
            15: "15分钟",
            30: "30分钟",
            60: "60分钟",
            240: "日K",
        }.get(scale, f"{scale}分钟")

        # 腾讯K线API
        url = f"{self.kline_url}?param={symbol},{scale},{count},qfq"
        resp = self._fetch(url)
        if not resp:
            return None

        try:
            raw = json.loads(resp)
        except json.JSONDecodeError as e:
            logger.error(f"TencentDataSource JSON解析失败: {e}")
            return None

        if not raw or "data" not in raw or symbol not in raw["data"]:
            logger.error("TencentDataSource K线数据格式异常")
            return None

        kline_data = raw["data"][symbol]
        if not kline_data:
            logger.error("TencentDataSource K线数据为空")
            return None

        # 腾讯返回格式: [[日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, ...]]
        klines = []
        for item in kline_data:
            if len(item) >= 6:
                klines.append({
                    "date": item[0],
                    "open": float(item[1]),
                    "high": float(item[3]),
                    "low": float(item[4]),
                    "close": float(item[2]),
                    "volume": int(float(item[5])),
                    "ma5": 0.0,
                    "ma10": 0.0,
                    "ma30": 0.0,
                    "vol_ma5": 0.0,
                    "vol_ma10": 0.0,
                    "vol_ma30": 0.0,
                })

        logger.info(f"TencentDataSource 获取 {period_name}K线 {len(klines)} 条")
        return {
            "code": code,
            "period": period_name,
            "period_scale": scale,
            "count": len(klines),
            "klines": klines,
            "fetch_time": datetime.now().isoformat(),
            "source": "tencent",
        }


class MultiSourceFetcher:
    """多数据源聚合器，自动故障切换"""

    def __init__(self, sources: Optional[List[DataSource]] = None):
        """初始化多数据源聚合器

        Args:
            sources: 数据源列表，默认使用 [SinaDataSource, TencentDataSource]
        """
        if sources is None:
            self.sources = [SinaDataSource(), TencentDataSource()]
        else:
            self.sources = sources

    def fetch_realtime(self, code: str) -> dict:
        """获取实时行情，自动故障切换

        Args:
            code: 证券代码

        Returns:
            实时行情数据

        Raises:
            RuntimeError: 所有数据源均不可用时抛出
        """
        for i, source in enumerate(self.sources):
            try:
                result = source.fetch_realtime(code)
                if result:
                    if i > 0:
                        logger.warning(
                            f"主数据源失败，使用备用数据源: {source.__class__.__name__}"
                        )
                    return result
            except Exception as e:
                logger.error(
                    f"{source.__class__.__name__} fetch_realtime 异常: {e}"
                )
                continue

        raise RuntimeError("所有数据源均不可用")

    def fetch_kline(
        self, code: str, period: str = "daily", count: int = 100
    ) -> dict:
        """获取K线数据，自动故障切换

        Args:
            code: 证券代码
            period: 周期 (1/5/15/30/60/240 分钟)
            count: 数据条数

        Returns:
            K线数据

        Raises:
            RuntimeError: 所有数据源均不可用时抛出
        """
        for i, source in enumerate(self.sources):
            try:
                result = source.fetch_kline(code, period, count)
                if result:
                    if i > 0:
                        logger.warning(
                            f"主数据源失败，使用备用数据源: {source.__class__.__name__}"
                        )
                    return result
            except Exception as e:
                logger.error(
                    f"{source.__class__.__name__} fetch_kline 异常: {e}"
                )
                continue

        raise RuntimeError("所有数据源均不可用")

    def fetch_all(
        self,
        code: str,
        periods: Optional[List[str]] = None,
        kline_count: int = 100,
    ) -> dict:
        """获取所有数据

        Args:
            code: 证券代码
            periods: K线周期列表，默认 ['daily', '60min', '30min']
            kline_count: 每个周期的K线条数

        Returns:
            包含实时行情和多个周期K线的数据字典
        """
        if periods is None:
            periods = ["daily", "60min", "30min"]

        results = {
            "code": code,
            "fetch_time": datetime.now().isoformat(),
        }

        # 获取实时行情
        try:
            realtime = self.fetch_realtime(code)
            results["realtime"] = realtime
            results["name"] = realtime["name"]
            results["market"] = self._detect_market(code)
        except RuntimeError as e:
            logger.error(f"获取实时行情失败: {e}")
            results["realtime"] = None
            results["name"] = ""
            results["market"] = ""

        # 获取各周期K线
        klines = {}
        for period in periods:
            try:
                kline_data = self.fetch_kline(code, period, kline_count)
                klines[f"kline_{period}"] = kline_data
            except RuntimeError as e:
                logger.error(f"获取{period}K线失败: {e}")
                klines[f"kline_{period}"] = None

        results["klines"] = klines
        return results

    def _detect_market(self, code: str) -> str:
        """判断市场: sh=上交所, sz=深交所"""
        if code.startswith(("51", "52", "58", "50", "56")):
            return "sh"
        elif code.startswith(("15", "16", "18", "17", "19")):
            return "sz"
        return "sh"

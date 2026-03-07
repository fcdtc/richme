#!/usr/bin/env python3
"""
ETF基金数据获取工具
使用新浪财经免费接口获取量化分析所需数据
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class ETFDataFetcher:
    """ETF数据获取器 - 基于新浪财经接口"""

    DATA_DIR = Path(__file__).parent / "data"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn/",
    }

    def __init__(self, etf_code: str):
        self.etf_code = etf_code.strip()
        self.market = self._detect_market()
        self.symbol = f"{self.market}{self.etf_code}"

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.etf_dir = self.DATA_DIR / self.etf_code
        self.etf_dir.mkdir(parents=True, exist_ok=True)

    def _detect_market(self) -> str:
        """判断市场: sh=上交所, sz=深交所"""
        if self.etf_code.startswith(("51", "52", "58", "50", "56")):
            return "sh"
        elif self.etf_code.startswith(("15", "16", "18", "17", "19")):
            return "sz"
        return "sh"

    def _fetch(self, url: str, timeout: int = 10) -> Optional[str]:
        """HTTP请求"""
        try:
            req = Request(url, headers=self.HEADERS)
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except (URLError, HTTPError, TimeoutError) as e:
            print(f"  [错误] {e}")
            return None

    def _save_json(self, data: dict, filename: str):
        filepath = self.etf_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [保存] {filepath}")

    def _save_csv(self, data: list, headers: list, filename: str):
        filepath = self.etf_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in data:
                f.write(",".join(str(v) for v in row) + "\n")
        print(f"  [保存] {filepath}")

    # ==================== 数据获取 ====================

    def get_realtime_quote(self) -> Optional[dict]:
        """获取实时行情"""
        print("\n[1/4] 获取实时行情...")

        url = f"https://hq.sinajs.cn/list={self.symbol}"
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
            "code": self.etf_code,
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
        }

        if data["prev_close"] > 0:
            data["change"] = round(data["current"] - data["prev_close"], 3)
            data["change_pct"] = round((data["change"] / data["prev_close"]) * 100, 2)
        else:
            data["change"] = 0
            data["change_pct"] = 0

        print(f"  [成功] {data['name']} {data['current']} ({data['change_pct']:+.2f}%)")
        return data

    def get_kline(self, scale: int = 240, count: int = 500) -> Optional[dict]:
        """
        获取K线数据

        Args:
            scale: K线周期
                - 1/5/15/30/60: 对应分钟K线
                - 240: 日K
            count: 数据条数
        """
        period_name = {
            1: "1分钟", 5: "5分钟", 15: "15分钟", 30: "30分钟",
            60: "60分钟", 240: "日K"
        }.get(scale, f"{scale}分钟")

        print(f"\n[获取{period_name}K线] 请求 {count} 条...")

        url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={self.symbol}&scale={scale}&datalen={count}"
        resp = self._fetch(url)
        if not resp:
            return None

        try:
            raw = json.loads(resp)
        except json.JSONDecodeError:
            print("  [错误] JSON解析失败")
            return None

        if not raw:
            print("  [错误] 数据为空")
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

        print(f"  [成功] 获取 {len(klines)} 条")
        return {
            "code": self.etf_code,
            "period": period_name,
            "count": len(klines),
            "klines": klines,
            "fetch_time": datetime.now().isoformat(),
        }

    # ==================== 主入口 ====================

    def fetch_all(self) -> dict:
        """获取所有数据"""
        print(f"\n{'='*50}")
        print(f"ETF {self.etf_code} ({'上交所' if self.market == 'sh' else '深交所'})")
        print(f"{'='*50}")

        results = {
            "code": self.etf_code,
            "market": self.market,
            "fetch_time": datetime.now().isoformat(),
        }

        # 1. 实时行情
        realtime = self.get_realtime_quote()
        if realtime:
            self._save_json(realtime, "realtime.json")
            results["name"] = realtime["name"]
            results["realtime"] = realtime

        # 2. 日K线
        daily = self.get_kline(scale=240, count=500)
        if daily:
            self._save_json(daily, "kline_daily.json")
            results["kline_daily"] = daily
            # CSV
            headers = ["date", "open", "high", "low", "close", "volume", "ma5", "ma10", "ma30"]
            rows = [[k["date"], k["open"], k["high"], k["low"], k["close"],
                    k["volume"], k["ma5"], k["ma10"], k["ma30"]] for k in daily["klines"]]
            self._save_csv(rows, headers, "kline_daily.csv")

        # 3. 60分钟K线
        m60 = self.get_kline(scale=60, count=200)
        if m60:
            self._save_json(m60, "kline_60min.json")
            results["kline_60min"] = m60

        # 4. 30分钟K线
        m30 = self.get_kline(scale=30, count=200)
        if m30:
            self._save_json(m30, "kline_30min.json")
            results["kline_30min"] = m30

        # 汇总
        summary = {
            "code": self.etf_code,
            "name": results.get("name", ""),
            "market": self.market,
            "fetch_time": results["fetch_time"],
            "files": [f.name for f in self.etf_dir.glob("*")],
        }
        self._save_json(summary, "summary.json")

        print(f"\n{'='*50}")
        print(f"完成! 数据目录: {self.etf_dir}")
        print(f"{'='*50}\n")

        return results


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python fetch_etf_data.py <ETF代码>")
        print("示例: python fetch_etf_data.py 512400")
        print("      python fetch_etf_data.py 512400 159915 510300")
        sys.exit(1)

    for code in sys.argv[1:]:
        try:
            fetcher = ETFDataFetcher(code)
            fetcher.fetch_all()
        except Exception as e:
            print(f"[错误] {code}: {e}")

        if code != sys.argv[-1]:
            time.sleep(0.5)


if __name__ == "__main__":
    main()

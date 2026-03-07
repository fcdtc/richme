#!/usr/bin/env python3
"""
测试数据源抽象层
验证多数据源聚合和故障切换功能
"""

import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.fetcher import (
    SinaDataSource,
    TencentDataSource,
    MultiSourceFetcher,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def test_single_source():
    """测试单个数据源"""
    print("\n" + "=" * 60)
    print("测试单个数据源")
    print("=" * 60)

    # 测试新浪数据源
    print("\n[1] 测试 SinaDataSource")
    sina = SinaDataSource()
    code = "512400"  # 中证1000ETF

    try:
        realtime = sina.fetch_realtime(code)
        if realtime:
            print(f"  实时行情: {realtime['name']} {realtime['current']} ({realtime['change_pct']:+.2f}%)")
        else:
            print("  获取实时行情失败")
    except Exception as e:
        print(f"  异常: {e}")

    try:
        kline = sina.fetch_kline(code, period="daily", count=10)
        if kline:
            print(f"  日K线: 获取 {kline['count']} 条数据")
            if kline['klines']:
                latest = kline['klines'][-1]
                print(f"  最新: {latest['date']} 收盘 {latest['close']}")
        else:
            print("  获取K线失败")
    except Exception as e:
        print(f"  异常: {e}")


def test_multi_source():
    """测试多数据源聚合器"""
    print("\n" + "=" * 60)
    print("测试多数据源聚合器")
    print("=" * 60)

    fetcher = MultiSourceFetcher()
    code = "159915"  # 创业板ETF

    print(f"\n[2] 测试 MultiSourceFetcher (代码: {code})")
    print(f"  数据源数量: {len(fetcher.sources)}")
    print(f"  数据源: {[s.__class__.__name__ for s in fetcher.sources]}")

    try:
        realtime = fetcher.fetch_realtime(code)
        if realtime:
            print(f"  实时行情: {realtime['name']} {realtime['current']} ({realtime['change_pct']:+.2f}%)")
            print(f"  数据来源: {realtime['source']}")
        else:
            print("  获取实时行情失败")
    except RuntimeError as e:
        print(f"  错误: {e}")

    try:
        kline = fetcher.fetch_kline(code, period="daily", count=5)
        if kline:
            print(f"  日K线: 获取 {kline['count']} 条数据")
            print(f"  数据来源: {kline['source']}")
            if kline['klines']:
                latest = kline['klines'][-1]
                print(f"  最新: {latest['date']} 收盘 {latest['close']}")
        else:
            print("  获取K线失败")
    except RuntimeError as e:
        print(f"  错误: {e}")


def test_fetch_all():
    """测试获取所有数据"""
    print("\n" + "=" * 60)
    print("测试获取所有数据")
    print("=" * 60)

    fetcher = MultiSourceFetcher()
    code = "510300"  # 沪深300ETF

    print(f"\n[3] 测试 fetch_all (代码: {code})")

    try:
        result = fetcher.fetch_all(
            code,
            periods=["daily", "60min"],
            kline_count=5,
        )

        if result.get("realtime"):
            print(f"  实时行情: {result['name']} {result['realtime']['current']}")

        for period, data in result.get("klines", {}).items():
            if data:
                print(f"  {period}: {data['count']} 条数据 (来源: {data['source']})")

    except Exception as e:
        print(f"  错误: {e}")


def test_failover():
    """测试故障切换"""
    print("\n" + "=" * 60)
    print("测试故障切换")
    print("=" * 60)

    # 创建一个会失败的数据源
    class FailDataSource:
        """测试用的失败数据源"""
        def fetch_realtime(self, code: str):
            raise Exception("模拟失败")

    fetcher = MultiSourceFetcher()
    code = "512880"  # 证券ETF

    print(f"\n[4] 测试故障切换 (代码: {code})")

    # 先测试正常情况
    try:
        realtime = fetcher.fetch_realtime(code)
        if realtime:
            print(f"  正常获取: {realtime['name']} (来源: {realtime['source']})")
    except RuntimeError as e:
        print(f"  错误: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("数据源抽象层测试")
    print("=" * 60)

    test_single_source()
    test_multi_source()
    test_fetch_all()
    test_failover()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

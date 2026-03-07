"""Data router for fetching market data."""

from fastapi import APIRouter, HTTPException
from backend.services.fetcher import MultiSourceFetcher
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])

# Initialize fetcher
fetcher = MultiSourceFetcher()


@router.get("/realtime/{code}")
async def get_realtime(code: str):
    """获取实时行情"""
    try:
        data = fetcher.fetch_realtime(code)
        return {
            "success": True,
            "data": data
        }
    except RuntimeError as e:
        logger.error(f"Failed to fetch realtime data for {code}: {e}")
        raise HTTPException(status_code=404, detail=f"无法获取 {code} 的实时行情数据")
    except Exception as e:
        logger.error(f"Unexpected error fetching realtime data for {code}: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时行情时发生错误: {str(e)}")


@router.get("/kline/{code}")
async def get_kline(code: str, period: str = "daily", count: int = 100):
    """获取K线数据"""
    try:
        # Validate period
        valid_periods = ["1min", "5min", "15min", "30min", "60min", "daily"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"无效的周期参数。支持的周期: {', '.join(valid_periods)}"
            )

        # Validate count
        if count < 1 or count > 1000:
            raise HTTPException(
                status_code=400,
                detail="count 参数必须在 1-1000 之间"
            )

        data = fetcher.fetch_kline(code, period, count)
        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Failed to fetch kline data for {code}: {e}")
        raise HTTPException(status_code=404, detail=f"无法获取 {code} 的K线数据")
    except Exception as e:
        logger.error(f"Unexpected error fetching kline data for {code}: {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据时发生错误: {str(e)}")

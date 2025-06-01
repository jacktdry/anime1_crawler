"""
動畫爬蟲工具模組
"""

import time
import random
import logging
import functools
from datetime import datetime
from urllib.parse import quote
from typing import List, Tuple, Optional

from config import SEASON_MAPPING, SITE_CONFIG, REQUEST_CONFIG

logger = logging.getLogger(__name__)


def retry_on_exception(retries: int = 3, delay: int = 1):
    """
    重試裝飾器
    
    Args:
        retries: 重試次數
        delay: 基礎延遲時間（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:  # 最後一次嘗試
                        logger.error(f"在執行 {func.__name__} 時發生錯誤（重試 {i+1}/{retries}）: {str(e)}")
                        raise
                    logger.warning(f"在執行 {func.__name__} 時發生錯誤（重試 {i+1}/{retries}）: {str(e)}")
                    time.sleep(delay * (i + 1))  # 指數退避
            return None
        return wrapper
    return decorator


def get_season_in_english(season: str) -> str:
    """
    將中文季節轉換成英文
    
    Args:
        season: 中文季節名稱
        
    Returns:
        英文季節名稱
    """
    return SEASON_MAPPING['chinese_to_english'].get(season, '')


def get_encoded_url(year: int, season: str) -> str:
    """
    將年份和季節轉換成正確的 URL 編碼
    
    Args:
        year: 年份
        season: 季節
        
    Returns:
        編碼後的完整 URL
    """
    chinese_url = f"{year}年{season}季新番"
    encoded_path = quote(chinese_url)
    return f"{SITE_CONFIG['base_url']}/{encoded_path}"


def get_current_season() -> str:
    """
    根據當前月份獲取對應的季節
    
    Returns:
        當前季節的中文名稱
    """
    current_month = datetime.now().month
    for months, season in SEASON_MAPPING['month_to_season'].items():
        if current_month in months:
            return season
    return '春'  # 預設值


def calculate_recent_seasons(seasons_count: int = 3) -> List[Tuple[int, str]]:
    """
    計算需要爬取的最近幾個季度
    
    Args:
        seasons_count: 需要的季度數量
        
    Returns:
        (年份, 季節) 的列表
    """
    current_date = datetime.now()
    current_year = current_date.year
    current_season = get_current_season()
    
    seasons_order = SEASON_MAPPING['order']
    current_season_index = seasons_order.index(current_season)
    
    seasons_to_crawl = []
    for i in range(seasons_count):
        season_index = (current_season_index - i) % 4
        year_offset = (current_season_index - i) // 4
        year = current_year + year_offset
        seasons_to_crawl.append((year, seasons_order[season_index]))
    
    return seasons_to_crawl


def should_skip_season(year: int, season: str, current_year: int, current_month: int) -> bool:
    """
    判斷是否應該跳過某個季節
    
    Args:
        year: 目標年份
        season: 目標季節
        current_year: 當前年份
        current_month: 當前月份
        
    Returns:
        是否應該跳過
    """
    if year != current_year:
        return False
        
    season_start_months = {
        '春': 4, '夏': 7, '秋': 10, '冬': 1
    }
    
    start_month = season_start_months.get(season, 1)
    if season == '冬' and current_month >= 10:  # 處理跨年的冬季
        return False
    
    return current_month < start_month


def add_random_delay(min_delay: float, max_delay: float) -> None:
    """
    添加隨機延遲
    
    Args:
        min_delay: 最小延遲時間（秒）
        max_delay: 最大延遲時間（秒）
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def extract_cat_id_from_href(href: str) -> Optional[str]:
    """
    從 href 中提取 cat_id
    
    Args:
        href: 連結地址
        
    Returns:
        提取的 cat_id，如果沒找到則返回 None
    """
    if '?cat=' in href:
        return href.split('?cat=')[1]
    return None
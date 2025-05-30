import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote
from datetime import datetime
import time
import os
from pathlib import Path
import re
import concurrent.futures
import threading
from queue import Queue
import random
import logging
import functools

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def retry_on_exception(retries=3, delay=1):
    """重試裝飾器"""
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

class AnimeDataManager:
    def __init__(self, filename="anime_data.json"):
        self.filename = filename
        self.data_lock = threading.Lock()
        self.file_lock = threading.Lock()
        self.data = self.load_existing_data()
        
        # 確保輸出目錄存在（僅當有目錄時才建立）
        dir_name = os.path.dirname(self.filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
    
    def load_existing_data(self):
        """載入現有的資料檔案"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"無法載入現有資料: {str(e)}")
            return {}
    
    def save_anime(self, year, season, anime_info):
        """保存單一動畫資訊到檔案（僅標題與cat_id）"""
        with self.data_lock:
            # 確保年度和季節存在
            if str(year) not in self.data:
                self.data[str(year)] = {}
            if season not in self.data[str(year)]:
                self.data[str(year)][season] = []

            # 檢查是否已存在相同的動畫
            existing_anime = None
            for idx, anime in enumerate(self.data[str(year)][season]):
                if anime.get('cat_id') == anime_info.get('cat_id'):
                    existing_anime = idx
                    break

            if existing_anime is not None:
                # 更新現有動畫資訊
                self.data[str(year)][season][existing_anime] = anime_info
                logger.info(f"更新動畫資訊: {anime_info['title']}")
            else:
                # 新增動畫資訊
                self.data[str(year)][season].append(anime_info)
                logger.info(f"新增動畫資訊: {anime_info['title']}")

        # 寫入檔案
        with self.file_lock:
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存資料時發生錯誤: {str(e)}")

# 已移除集數相關函式：get_episode_number, get_anime_episodes, process_anime

@retry_on_exception(retries=3, delay=2)
def parse_anime_table(url, year, season, data_manager):
    """解析網頁中的動畫表格資料（僅標題與cat_id）"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 隨機延遲 1-3 秒
    time.sleep(random.uniform(1, 3))
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    if not table:
        logger.warning(f"在 {url} 中沒有找到表格")
        return []

    anime_list = []
    rows = table.find_all('tr')[1:]  # 跳過第一行（星期標題）

    for row in rows:
        cells = row.find_all('td')
        for cell in cells:
            link = cell.find('a')
            if link:
                title = link.text.strip()
                if title == "Anime1.me":
                    continue

                href = link.get('href', '')
                cat_id = None
                if '?cat=' in href:
                    cat_id = href.split('?cat=')[1]

                anime_info = {
                    'title': title,
                    'cat_id': cat_id
                }

                if cat_id:
                    data_manager.save_anime(year, get_season_in_english(season), anime_info)

                anime_list.append(anime_info)

    return anime_list

def get_season_in_english(season):
    """將中文季節轉換成英文"""
    season_map = {
        '春': 'spring',
        '夏': 'summer',
        '秋': 'fall',
        '冬': 'winter'
    }
    return season_map.get(season, '')

def get_encoded_url(year, season):
    """將年份和季節轉換成正確的 URL 編碼"""
    base_url = "https://anime1.me"
    chinese_url = f"{year}年{season}季新番"
    encoded_path = quote(chinese_url)
    return f"{base_url}/{encoded_path}"

def crawl_specific_seasons(seasons_to_crawl):
    """爬取指定的季度資料"""
    data_manager = AnimeDataManager()
    
    for year, season in seasons_to_crawl:
        url = get_encoded_url(year, season)
        parse_anime_table(url, year, season, data_manager)
        # 主要的延遲放在季度之間
        time.sleep(random.uniform(3, 5))

def crawl_from_year(start_year):
    """從指定年份開始爬取所有動畫資料"""
    data_manager = AnimeDataManager()
    current_date = datetime.now()
    current_year = current_date.year
    
    seasons = ['冬', '春', '夏', '秋']
    years_to_crawl = range(start_year, current_year + 1)
    
    for year in years_to_crawl:
        for season in seasons:
            # 如果是當前年份，只爬取到當前季節
            if year == current_year:
                current_month = current_date.month
                if (season == '春' and current_month < 4) or \
                   (season == '夏' and current_month < 7) or \
                   (season == '秋' and current_month < 10) or \
                   (season == '冬' and current_month < 1):
                    continue
            
            logger.info(f"正在爬取 {year} 年 {season}季 的動畫...")
            url = get_encoded_url(year, season)
            parse_anime_table(url, year, season, data_manager)
            # 避免對伺服器造成太大負擔
            time.sleep(random.uniform(3, 5))

def main():
    logger.info("開始爬取動畫資料...")
    data_file = Path("anime_data.json")
    
    if not data_file.exists():
        logger.info("找不到現有資料檔案，將從 2017 年開始爬取所有動畫資料...")
        crawl_from_year(2017)
    else:
        # 爬取最近三個季度的資料
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # 根據月份決定當前季節
        season_map = {
            (1, 2, 3): '冬',
            (4, 5, 6): '春',
            (7, 8, 9): '夏',
            (10, 11, 12): '秋'
        }
        current_season = next(s for months, s in season_map.items() if current_month in months)
        
        # 獲取當前季度和前兩個季度
        seasons_order = ['冬', '春', '夏', '秋']
        current_season_index = seasons_order.index(current_season)
        
        seasons_to_crawl = []
        for i in range(3):
            season_index = (current_season_index - i) % 4
            year_offset = (current_season_index - i) // 4
            year = current_year + year_offset
            seasons_to_crawl.append((year, seasons_order[season_index]))
        
        logger.info("找到現有資料，只更新最近三個季度...")
        logger.info(f"準備爬取以下季度: {seasons_to_crawl}")
        crawl_specific_seasons(seasons_to_crawl)
    
    logger.info("資料爬取完成")

if __name__ == "__main__":
    main()
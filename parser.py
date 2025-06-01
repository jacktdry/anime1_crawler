"""
網頁解析模組
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional

from config import REQUEST_CONFIG, SITE_CONFIG
from utils import retry_on_exception, add_random_delay, extract_cat_id_from_href
from data_manager import AnimeDataManager

logger = logging.getLogger(__name__)


class AnimeParser:
    """
    動畫網頁解析器
    
    負責從網頁中解析動畫資訊
    """
    
    def __init__(self):
        """初始化解析器"""
        self.headers = REQUEST_CONFIG['headers']
        self.skip_titles = SITE_CONFIG['skip_titles']
    
    def _extract_anime_from_link(self, link) -> Optional[Dict[str, str]]:
        """
        從連結中提取動畫資訊
        
        Args:
            link: BeautifulSoup 連結元素
            
        Returns:
            動畫資訊字典，如果無效則返回 None
        """
        title = link.text.strip()
        
        # 跳過特定標題
        if title in self.skip_titles:
            return None
        
        href = link.get('href', '')
        cat_id = extract_cat_id_from_href(href)
        
        return {
            'title': title,
            'cat_id': cat_id
        }
    
    def _extract_anime_from_table(self, table) -> List[Dict[str, str]]:
        """
        從表格中提取所有動畫資訊
        
        Args:
            table: BeautifulSoup 表格元素
            
        Returns:
            動畫資訊列表
        """
        anime_list = []
        rows = table.find_all('tr')[1:]  # 跳過第一行（星期標題）

        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                link = cell.find('a')
                if link:
                    anime_info = self._extract_anime_from_link(link)
                    if anime_info:
                        anime_list.append(anime_info)

        return anime_list
    
    @retry_on_exception(retries=REQUEST_CONFIG['retry_attempts'], 
                       delay=REQUEST_CONFIG['retry_delay'])
    def parse_anime_table(self, url: str, year: int, season: str, 
                         data_manager: AnimeDataManager) -> List[Dict[str, str]]:
        """
        解析網頁中的動畫表格資料
        
        Args:
            url: 目標網頁 URL
            year: 年份
            season: 季節（中文）
            data_manager: 資料管理器實例
            
        Returns:
            解析出的動畫資訊列表
        """
        # 添加隨機延遲避免對伺服器造成負擔
        delay_range = REQUEST_CONFIG['request_delay_range']
        add_random_delay(delay_range[0], delay_range[1])
        
        # 發送請求
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            logger.warning(f"在 {url} 中沒有找到表格")
            return []

        # 提取動畫資訊
        anime_list = self._extract_anime_from_table(table)
        
        # 保存有效的動畫資訊
        from utils import get_season_in_english
        english_season = get_season_in_english(season)
        
        for anime_info in anime_list:
            if anime_info.get('cat_id'):  # 只保存有 cat_id 的動畫
                data_manager.save_anime(year, english_season, anime_info)

        return anime_list


class CrawlerEngine:
    """
    爬蟲引擎
    
    協調解析器和資料管理器進行批量爬取
    """
    
    def __init__(self):
        """初始化爬蟲引擎"""
        self.parser = AnimeParser()
        self.data_manager = AnimeDataManager()
    
    def crawl_specific_seasons(self, seasons_to_crawl: List[tuple]) -> None:
        """
        爬取指定的季度資料
        
        Args:
            seasons_to_crawl: (年份, 季節) 的列表
        """
        from utils import get_encoded_url
        
        for year, season in seasons_to_crawl:
            logger.info(f"正在爬取 {year} 年 {season}季 的動畫...")
            url = get_encoded_url(year, season)
            
            try:
                self.parser.parse_anime_table(url, year, season, self.data_manager)
            except Exception as e:
                logger.error(f"爬取 {year} 年 {season}季 時發生錯誤: {str(e)}")
                continue
            
            # 在季度之間添加延遲
            delay_range = REQUEST_CONFIG['season_delay_range']
            add_random_delay(delay_range[0], delay_range[1])
    
    def crawl_from_year(self, start_year: int) -> None:
        """
        從指定年份開始爬取所有動畫資料
        
        Args:
            start_year: 開始年份
        """
        from datetime import datetime
        from utils import should_skip_season, get_encoded_url
        from config import SEASON_MAPPING
        
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        seasons = SEASON_MAPPING['order']
        years_to_crawl = range(start_year, current_year + 1)
        
        for year in years_to_crawl:
            for season in seasons:
                # 檢查是否應該跳過當前季節
                if should_skip_season(year, season, current_year, current_month):
                    continue
                
                logger.info(f"正在爬取 {year} 年 {season}季 的動畫...")
                url = get_encoded_url(year, season)
                
                try:
                    self.parser.parse_anime_table(url, year, season, self.data_manager)
                except Exception as e:
                    logger.error(f"爬取 {year} 年 {season}季 時發生錯誤: {str(e)}")
                    continue
                
                # 在季度之間添加延遲
                delay_range = REQUEST_CONFIG['season_delay_range']
                add_random_delay(delay_range[0], delay_range[1])
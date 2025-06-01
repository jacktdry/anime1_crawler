"""
動畫爬蟲主程式

這是一個用於爬取 Anime1.me 網站動畫資訊的程式。
程式會根據資料檔案的存在狀況決定是進行完整爬取還是只更新最近的資料。

使用方法:
    python anime_crawler.py

功能:
- 自動判斷是否需要完整爬取
- 支援增量更新最近三個季度的資料
- 具備重試機制和錯誤處理
- 動畫資料按標題排序保存
"""

import logging

from config import DATA_CONFIG, LOGGING_CONFIG
from data_manager import AnimeDataManager
from parser import CrawlerEngine
from utils import calculate_recent_seasons

# 設定日誌
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class AnimeCrawlerApp:
    """
    動畫爬蟲應用程式主類別
    
    協調各個模組完成動畫資料的爬取工作
    """
    
    def __init__(self):
        """初始化爬蟲應用程式"""
        self.data_manager = AnimeDataManager()
        self.crawler_engine = CrawlerEngine()
    
    def should_perform_full_crawl(self) -> bool:
        """
        判斷是否需要進行完整爬取

        Returns:
            True 如果需要完整爬取，False 如果只需要增量更新
        """
        return not self.data_manager.data_exists()
    
    def perform_full_crawl(self) -> None:
        """執行完整爬取"""
        start_year = DATA_CONFIG['start_year']
        logger.info(f"找不到現有資料檔案或內容為空，將從 {start_year} 年開始爬取所有動畫資料...")
        self.crawler_engine.crawl_from_year(start_year)
    
    def perform_incremental_update(self) -> None:
        """執行增量更新"""
        seasons_count = DATA_CONFIG['recent_seasons_count']
        seasons_to_crawl = calculate_recent_seasons(seasons_count)
        
        logger.info("找到現有資料，只更新最近三個季度...")
        logger.info(f"準備爬取以下季度: {seasons_to_crawl}")

        self.crawler_engine.crawl_specific_seasons(seasons_to_crawl)
    
    def run(self) -> None:
        """執行爬蟲主程式"""
        logger.info("開始爬取動畫資料...")

        try:
            if self.should_perform_full_crawl():
                self.perform_full_crawl()
            else:
                self.perform_incremental_update()

            logger.info("資料爬取完成")

        except Exception as e:
            logger.error(f"爬取過程中發生錯誤: {str(e)}")
            raise


def main():
    """主程式入口點"""
    app = AnimeCrawlerApp()
    app.run()


if __name__ == "__main__":
    main()
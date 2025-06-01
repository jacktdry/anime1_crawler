"""
動畫爬蟲測試腳本

用於測試重構後的爬蟲程式各模組是否正常運作
"""

import logging
import tempfile
import os
import sys
from pathlib import Path

# 將父目錄添加到 Python 路徑，以便導入主程式模組
sys.path.insert(0, str(Path(__file__).parent.parent))

# 設定測試用的日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_config_import():
    """測試配置模組導入"""
    try:
        from config import DATA_CONFIG, REQUEST_CONFIG, SEASON_MAPPING
        logger.info("✅ 配置模組導入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 配置模組導入失敗: {e}")
        return False

def test_utils_functions():
    """測試工具函數"""
    try:
        from utils import get_season_in_english, get_encoded_url, calculate_recent_seasons
        
        # 測試季節轉換
        assert get_season_in_english('春') == 'spring'
        assert get_season_in_english('夏') == 'summer'
        
        # 測試 URL 編碼
        url = get_encoded_url(2024, '春')
        assert 'anime1.me' in url
        assert '2024' in url
        
        # 測試計算最近季度
        seasons = calculate_recent_seasons(3)
        assert len(seasons) == 3
        assert all(isinstance(season, tuple) for season in seasons)
        
        logger.info("✅ 工具函數測試通過")
        return True
    except Exception as e:
        logger.error(f"❌ 工具函數測試失敗: {e}")
        return False

def test_data_manager():
    """測試資料管理器"""
    try:
        from data_manager import AnimeDataManager
        
        # 使用臨時檔案進行測試
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 初始化資料管理器
            dm = AnimeDataManager(tmp_path)
            
            # 測試保存動畫資訊
            anime_info = {'title': '測試動畫', 'cat_id': 'test123'}
            dm.save_anime(2024, 'spring', anime_info)
            
            # 檢查資料是否正確保存
            data = dm.get_data()
            assert '2024' in data
            assert 'spring' in data['2024']
            assert len(data['2024']['spring']) == 1
            assert data['2024']['spring'][0]['title'] == '測試動畫'
            
            logger.info("✅ 資料管理器測試通過")
            return True
            
        finally:
            # 清理臨時檔案
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"❌ 資料管理器測試失敗: {e}")
        return False

def test_parser_classes():
    """測試解析器類別"""
    try:
        from parser import AnimeParser, CrawlerEngine
        
        # 測試解析器初始化
        parser = AnimeParser()
        assert hasattr(parser, 'headers')
        assert hasattr(parser, 'skip_titles')
        
        # 測試爬蟲引擎初始化
        engine = CrawlerEngine()
        assert hasattr(engine, 'parser')
        assert hasattr(engine, 'data_manager')
        
        logger.info("✅ 解析器類別測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 解析器類別測試失敗: {e}")
        return False

def test_main_app():
    """測試主應用程式類別"""
    try:
        from main import AnimeCrawlerApp
        
        # 測試應用程式初始化
        app = AnimeCrawlerApp()
        assert hasattr(app, 'data_manager')
        assert hasattr(app, 'crawler_engine')
        
        # 測試判斷是否需要完整爬取的邏輯
        result = app.should_perform_full_crawl()
        assert isinstance(result, bool)
        
        logger.info("✅ 主應用程式類別測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 主應用程式類別測試失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    logger.info("開始執行動畫爬蟲測試...")
    
    tests = [
        ("配置模組", test_config_import),
        ("工具函數", test_utils_functions),
        ("資料管理器", test_data_manager),
        ("解析器類別", test_parser_classes),
        ("主應用程式", test_main_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"正在測試: {test_name}")
        if test_func():
            passed += 1
        logger.info("-" * 50)
    
    logger.info(f"測試完成! 通過: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 所有測試都通過了！程式重構成功。")
        return True
    else:
        logger.warning("⚠️  部分測試失敗，請檢查相關模組。")
        return False

if __name__ == "__main__":
    run_all_tests()
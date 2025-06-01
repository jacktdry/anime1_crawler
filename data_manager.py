"""
動畫資料管理模組
"""

import json
import os
import threading
import logging
from typing import Dict, Any, List
from pathlib import Path

from config import DATA_CONFIG

logger = logging.getLogger(__name__)


class AnimeDataManager:
    """
    動畫資料管理器
    
    負責處理動畫資料的載入、保存和排序
    """
    
    def __init__(self, filename: str = None):
        """
        初始化資料管理器
        
        Args:
            filename: 資料檔案路徑，預設使用配置檔案中的設定
        """
        self.filename = filename or DATA_CONFIG['output_file']
        self.data_lock = threading.Lock()
        self.file_lock = threading.Lock()
        self.data = self._load_existing_data()
        
        # 確保輸出目錄存在
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """確保輸出目錄存在"""
        dir_name = os.path.dirname(self.filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
    
    def _load_existing_data(self) -> Dict[str, Any]:
        """
        載入現有的資料檔案
        
        Returns:
            載入的資料字典，如果檔案不存在或格式錯誤則返回空字典
        """
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"無法載入現有資料: {str(e)}")
            return {}
    
    def _sort_anime_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        對動畫資料按照 title 進行排序
        
        Args:
            data: 原始資料字典
            
        Returns:
            排序後的資料字典
        """
        sorted_data = {}
        for year_key, year_data in data.items():
            sorted_data[year_key] = {}
            for season_key, anime_list in year_data.items():
                # 按照 title 排序
                sorted_data[year_key][season_key] = sorted(
                    anime_list, 
                    key=lambda x: x.get('title', '')
                )
        return sorted_data
    
    def _find_existing_anime_index(self, anime_list: List[Dict], anime_info: Dict[str, str]) -> int:
        """
        查找現有動畫的索引
        
        Args:
            anime_list: 動畫列表
            anime_info: 要查找的動畫資訊
            
        Returns:
            找到的索引，如果沒找到則返回 -1
        """
        cat_id = anime_info.get('cat_id')
        if not cat_id:
            return -1
            
        for idx, anime in enumerate(anime_list):
            if anime.get('cat_id') == cat_id:
                return idx
        return -1
    
    def save_anime(self, year: int, season: str, anime_info: Dict[str, str]) -> None:
        """
        保存單一動畫資訊到檔案
        
        Args:
            year: 年份
            season: 季節（英文）
            anime_info: 動畫資訊字典，包含 title 和 cat_id
        """
        with self.data_lock:
            year_str = str(year)
            
            # 確保年度和季節存在
            if year_str not in self.data:
                self.data[year_str] = {}
            if season not in self.data[year_str]:
                self.data[year_str][season] = []

            # 檢查是否已存在相同的動畫
            anime_list = self.data[year_str][season]
            existing_index = self._find_existing_anime_index(anime_list, anime_info)

            if existing_index != -1:
                # 更新現有動畫資訊
                self.data[year_str][season][existing_index] = anime_info
                logger.info(f"更新動畫資訊: {anime_info.get('title', 'Unknown')}")
            else:
                # 新增動畫資訊
                self.data[year_str][season].append(anime_info)
                logger.info(f"新增動畫資訊: {anime_info.get('title', 'Unknown')}")

        # 寫入檔案
        self._save_to_file()
    
    def _save_to_file(self) -> None:
        """將資料保存到檔案"""
        with self.file_lock:
            try:
                # 在寫入前對所有動畫列表按照 title 排序
                sorted_data = self._sort_anime_data(self.data)
                
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(sorted_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存資料時發生錯誤: {str(e)}")
    
    def data_exists(self) -> bool:
        """
        檢查資料檔案是否存在且非空
        
        Returns:
            True 如果資料檔案存在且非空，否則 False
        """
        data_file = Path(self.filename)
        if not data_file.exists():
            return False
            
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return bool(data)  # 檢查資料是否非空
        except Exception as e:
            logger.warning(f"檢查資料檔案時發生錯誤: {str(e)}")
            return False
    
    def get_data(self) -> Dict[str, Any]:
        """
        獲取當前的資料
        
        Returns:
            資料字典的副本
        """
        with self.data_lock:
            return self.data.copy()
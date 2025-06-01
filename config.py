"""
動畫爬蟲配置檔案
"""

# 網路請求配置
REQUEST_CONFIG = {
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'retry_attempts': 3,
    'retry_delay': 2,
    'request_delay_range': (1, 3),  # 隨機延遲範圍（秒）
    'season_delay_range': (3, 5)   # 季節間延遲範圍（秒）
}

# 資料配置
DATA_CONFIG = {
    'output_file': 'docs/anime_data.json',
    'start_year': 2017,
    'recent_seasons_count': 3
}

# 季節對應
SEASON_MAPPING = {
    'chinese_to_english': {
        '春': 'spring',
        '夏': 'summer',
        '秋': 'fall',
        '冬': 'winter'
    },
    'month_to_season': {
        (1, 2, 3): '冬',
        (4, 5, 6): '春',
        (7, 8, 9): '夏',
        (10, 11, 12): '秋'
    },
    'order': ['冬', '春', '夏', '秋']
}

# 網站配置
SITE_CONFIG = {
    'base_url': 'https://anime1.me',
    'skip_titles': ['Anime1.me']
}

# 日誌配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s [%(levelname)s] %(message)s'
}
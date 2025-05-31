# anime1.me 動畫季度資料爬蟲

## 專案簡介
本專案用於自動化爬取 [anime1.me](https://anime1.me) 各季度動畫名稱與 ID，方便其他專案進行資料整合或延伸應用。

## 功能特色
- 自動爬取 anime1.me 各年度、季度的動畫名稱與對應 ID
- 輸出結構化 JSON 檔案，便於後續資料處理
- 支援批次更新與資料覆蓋
- 程式碼簡潔，易於維護與擴充

## 安裝與執行方式

### 環境需求
- Python 版本：3.8 以上

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 執行指令範例
```bash
python anime_crawler.py
```

## 輸出說明

執行後會於 `docs/anime_data.json` 產生動畫資料，結構如下：

```json
{
  "2017": {
    "winter": [
      {
        "title": "élDLIVE宇宙警探",
        "cat_id": "21"
      },
      {
        "title": "超・少年偵探團NEO",
        "cat_id": "7"
      }
      // ... 其他動畫
    ],
    "spring": [
      // ...
    ],
    // ...
  },
  // 其他年份
}
```
- 最外層為年份（字串）
- 第二層為季度（如 "winter", "spring", "summer", "fall"）
- 每個季度為動畫陣列，包含：
  - `title`：動畫名稱
  - `cat_id`：動畫在 anime1.me 的分類 ID

## 依賴
requirements.txt 內容如下：
```
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
python-dotenv==1.0.0
beautifulsoup4==4.12.2
urllib3==2.0.7
```

## 授權
MIT

---

# English Version

## Project Introduction
This project automates the crawling of anime titles and IDs for each season from [anime1.me](https://anime1.me), making it convenient for data integration or further application in other projects.

## Features
- Automatically crawls anime titles and corresponding IDs for each year and season from anime1.me
- Outputs structured JSON files for easy data processing
- Supports batch updates and data overwriting
- Clean code, easy to maintain and extend

## Installation & Usage

### Requirements
- Python version: 3.8 or above

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Example Command
```bash
python anime_crawler.py
```

## Output Description

After execution, the anime data will be generated in `docs/anime_data.json` with the following structure:

```json
{
  "2017": {
    "winter": [
      {
        "title": "élDLIVE宇宙警探",
        "cat_id": "21"
      },
      {
        "title": "超・少年偵探團NEO",
        "cat_id": "7"
      }
      // ... other anime
    ],
    "spring": [
      // ...
    ],
    // ...
  },
  // other years
}
```
- The outermost layer is the year (string)
- The second layer is the season (e.g., "winter", "spring", "summer", "fall")
- Each season contains an array of anime objects, each including:
  - `title`: Anime title
  - `cat_id`: Category ID on anime1.me

## Dependencies
Contents of requirements.txt:
```
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
python-dotenv==1.0.0
beautifulsoup4==4.12.2
urllib3==2.0.7
```

## License
MIT
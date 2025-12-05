ASUS Router News Automation
這是一個端到端的自動化面試專案。目標是爬取 ASUS Router 相關資安新聞，存入 MySQL 資料庫，並自動填寫至 Google 表單。

🛠 技術堆疊 (Tech Stack)
- **Language**: Python 3.14.1
- **Database**: MySQL 8.0 (Dockerized)
- **Scraper**: Requests + BeautifulSoup
- **Automation**: Selenium WebDriver
- **Infrastructure**: Docker & Docker Compose

🚀 環境建置 (Windows 開發環境)
第 0 階段：安裝編輯器 (Cursor、Docker)
1.下載 Cursor 作為程式碼編輯器
  前往 Cursor 官網，下載安裝檔。
  執行安裝程式，並依照指示完成安裝。

2.下載Docker
  前往 Docker 官網，下載安裝檔。
  執行安裝程式，並依照指示完成安裝。

------------------------------------------------------------------------------------------------
※如果你是第一次在 Windows 上執行此專案，請依照以下步驟設定 Python 虛擬環境。

第 1 階段：在電腦上安裝 Python (引擎)
1. 開啟 Cursor 的終端機，檢查python是否已安裝
    python --version 或 py --version 或 python3 --version

2.下載與安裝
  前往 Python 官網下載頁面。
  點擊黃色按鈕 Download Python 3.x.x。
  ※執行下載的安裝檔 (⚠️ 重要)
  務必勾選最下方的 ☑️ Add Python.exe to PATH (將 Python 加入環境變數)。
  點選 Install Now 完成安裝。

3.打開 Cursor
  點擊左側邊欄的「方塊圖示」 (Extensions)。
  搜尋 Python。
  找到由 Microsoft 開發的那個（通常下載量最高），點擊 Install。 (這個套件會幫你做語法高亮、程式碼補全、還能幫你選虛擬環境)

4.安裝完成後回到步驟1，檢查是否安裝成功，安裝成功後，接續5.開啟專案資料夾。

5.開啟專案資料夾
  在電腦桌面或你習慣的地方，建立一個新資料夾，命名為 asus-news。
  在 Cursor 中，點選 File -> Open Folder，選擇這個資料夾。

------------------------------------------------------------------------------------------------
第 2 階段：建立虛擬環境 (Virtual Environment) - 為避免影響電腦其他專案，需要建立一個獨立的環境。
1.開啟 Cursor 的終端機
  使用快捷鍵 Ctrl + ` 開啟終端機。
  確保終端機路徑是在這個專案的資料夾底下。

2.請依序輸入以下指令：
  Windows:
  (1). 建立虛擬環境 (只需做一次)
       python -m venv .venv
  (2). 啟動虛擬環境 (每次重開 Cursor 都要確認前面有 (.venv) 字樣，通常 Cursor 會自動偵測)
       .venv\Scripts\activate

  Mac / Linux:
  (1). 建立虛擬環境
       python3 -m venv .venv
  (2). 啟動虛擬環境
       source .venv/bin/activate

註:
Q:如果遇到.venv\Scripts\activate錯誤為Windows PowerShell 安全性限制問題
A:解決方法
  步驟 1：修改執行權限
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  步驟 2：權限改好後，再執行一次原本的指令
💡如何確認成功？
   看到 Terminal 的最前面出現了綠色或白色的 (.venv) 字樣

------------------------------------------------------------------------------------------------
第 3 階段：驗證與安裝依賴
1.在 Cursor 左側檔案總管按右鍵 -> New File -> 命名為 requirements.txt。

2.貼上以下內容:
  requests>=2.31.0
  beautifulsoup4>=4.12.0
  selenium>=4.16.0
  webdriver-manager>=4.0.1
  mysql-connector-python>=8.2.0
  python-dotenv>=1.0.0
  pandas>=2.1.0

3.回到終端機，輸入安裝指令：
  pip install -r requirements.txt

------------------------------------------------------------------------------------------------
第 4 階段：Docker 化
在 Docker 環境中，我們會定義兩個主要的 Service：
db: MySQL 8.0 資料庫。
app: 之後要跑 Python 爬蟲的容器 (目前我們先預留設定，重點先讓 DB 跑起來)。

1.建立資料庫初始化腳本 (init.sql)
  (1)在專案根目錄建立一個資料夾，命名為 db。

  (2)在 db 資料夾內建立一個檔案 init.sql。

  (3)貼上以下 SQL 碼(2個TABLE)：
    -- db/init.sql

    -- 1. 建立並使用資料庫
    CREATE DATABASE IF NOT EXISTS security_news;
    USE security_news;

    -- 2. 建立新聞資料表
    CREATE TABLE IF NOT EXISTS news (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        publish_date DATE NOT NULL,
        url VARCHAR(2048) NOT NULL,
        source VARCHAR(100),
        
        -- 新增: 新聞摘要 (對應爬蟲的 description)
        description TEXT,
        
        -- 流程圖邏輯核心欄位:
        -- status: 'N'=新資料(New), 'Y'=已填表(Yes), 'E'=錯誤(Error)
        status CHAR(1) DEFAULT 'N' NOT NULL,
        
        -- fail_count: 紀錄填表失敗次數 (流程圖: 失敗超過3次 -> E)
        fail_count INT DEFAULT 0,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        -- 去重機制: 同一天、同標題的新聞視為重複，拒絕寫入
        UNIQUE KEY unique_news_check (title, publish_date)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

    -- 3. 建立執行紀錄表 (Optional: 用於紀錄每次 Script 執行狀況)
    CREATE TABLE IF NOT EXISTS execution_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_processed INT DEFAULT 0,
        success_count INT DEFAULT 0,
        error_count INT DEFAULT 0,
        log_message TEXT
    );

  (4)建立暫時的 Dockerfile (docker-compose.yml 裡面參照了 build: .，需要一個 Dockerfile 才能跑)
     a.在專案根目錄建立 Dockerfile。
     b.貼上以下內容：
       # 使用 Python 3.9 Slim
        FROM python:3.9-slim

        # 設定環境變數
        ENV PYTHONDONTWRITEBYTECODE=1
        ENV PYTHONUNBUFFERED=1

        # 設定工作目錄
        WORKDIR /app

        # 1. 安裝系統依賴
        # 我們需要 gnupg 來處理金鑰
        RUN apt-get update && apt-get install -y \
            wget \
            gnupg \
            unzip \
            curl \
            # Chrome 執行所需依賴 (Debian 12/13 適用)
            libnss3 \
            libxss1 \
            libasound2 \
            fonts-liberation \
            libnspr4 \
            xdg-utils \
            libgbm1 \
            libu2f-udev \
            libvulkan1 \
            && rm -rf /var/lib/apt/lists/*

        # 2. 安裝 Google Chrome (使用新版 signed-by 機制，不使用 apt-key)
        RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | \
            gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
            && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
            > /etc/apt/sources.list.d/google-chrome.list \
            && apt-get update \
            && apt-get install -y google-chrome-stable

        # 3. 安裝 Python 套件
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        # 4. 複製程式碼
        COPY . .

        # 5. 預設指令
        CMD ["tail", "-f", "/dev/null"]

     c.啟動 Docker Desktop

     d.打開終端機，重設連線
       docker context use default

     e.打開終端機，嘗試連線
       docker ps

     f.打開終端機，執行會自動建置包含 Chrome 的 Python 環境以及初始化 MySQL 資料庫
       docker-compose up -d --build

     g.打開終端機，查看現在的狀態
       docker ps
       
       情況 A：看到空蕩蕩的標題，或是什麼都沒有
       CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES
       
       情況 B：看到兩行資料 (mysql 和 python)，例如:
       CONTAINER ID   IMAGE              ...   STATUS          NAMES
       abc12345       mysql:8.0          ...   Up 5 seconds    asus_news_db
       def67890       asus-news-app      ...   Up 5 seconds    asus_news_worker

       ※如果有情況A，可能是Dockerfile中的依賴或驗證版本問題，將Dockerfile重新確認後，再重新做
         強制重新下載所有的 Chrome 和依賴套件，確保你的新 Dockerfile 邏輯被真正執行。
         docker-compose build --no-cache
         建置成功後（沒有報錯），再啟動它
         docker-compose up -d --force-recreate

================================================================================================
🚀 撰寫爬蟲程式建置 (Windows 開發環境)

第 1 階段：建立專案結構
1.在根目錄下建立app 資料夾

2.在app資料夾下，建立以下檔案
    asus-news/
    ├── app/                    # 核心應用程式邏輯
    │   ├── __init__.py
    │   ├── main.py             # 程式進入點 (Entry Point)
    │   ├── config.py           # 設定檔讀取 (讀取 env)
    │   ├── scraper.py          # 爬蟲邏輯 (Requests/BS4)
    │   ├── utils.py            # 工具包
    │   ├── database.py         # 資料庫操作 (MySQL 連線與 CRUD)
    │   ├── form_filler.py      # 自動填表邏輯 (Selenium)
    │── └── logger.py           # 日誌設定 (Logging)

------------------------------------------------------------------------------------------------
第 2 階段：撰寫程式碼

1.請將以下內容複製到 app/scraper.py
  import logging
  import time
  import random
  from typing import List, Dict
  from selenium import webdriver
  from selenium.webdriver.chrome.service import Service
  from selenium.webdriver.chrome.options import Options
  from selenium.webdriver.common.by import By
  from selenium.webdriver.support.ui import WebDriverWait
  from selenium.webdriver.support import expected_conditions as EC
  from webdriver_manager.chrome import ChromeDriverManager

  # 設定 Log 格式
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
  logger = logging.getLogger(__name__)

  class NewsScraper:
        def __init__(self):
            self.driver = self._setup_driver()

        def _setup_driver(self) -> webdriver.Chrome:
            chrome_options = Options()
            
            # --- [關鍵修正] 針對 Docker 環境的最佳化參數 ---
            # 使用新版 headless 模式 (比舊版更穩定)
            chrome_options.add_argument("--headless=new")
            
            # 解決 Docker 共享記憶體不足導致的崩潰
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # 解決 Linux root 權限問題
            chrome_options.add_argument("--no-sandbox")
            
            # 禁用 GPU (Linux 伺服器通常沒顯卡)
            chrome_options.add_argument("--disable-gpu")
            
            # 設定固定視窗大小，避免 RWD 造成元素位置跑掉
            chrome_options.add_argument("--window-size=1920,1080")
            
            # 增加穩定性的額外參數
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            
            # 偽裝 User-Agent (避免被 Google 認定為機器人)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            logger.info("正在初始化 Chrome Driver (v2)...")
            
            # 自動安裝並設定 Driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver

        def scrape_google_news(self, keyword: str = "ASUS router security") -> List[Dict]:
            results = []
            try:
                # 加入時間篩選參數 &tbs=qdr:m6 (最近 6 個月)
                url = f"https://www.google.com/search?q={keyword}&tbm=nws&tbs=qdr:m6"
                logger.info(f"前往 URL: {url}")
                
                self.driver.get(url)
                
                # 隨機延遲，模擬人類閱讀 (Anti-Scraping)
                sleep_time = random.uniform(2, 5)
                logger.info(f"隨機延遲: 等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

                # 等待新聞區塊載入 (最多等 15 秒)
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.SoaBEf"))
                )

                articles = self.driver.find_elements(By.CSS_SELECTOR, "div.SoaBEf")
                logger.info(f"找到 {len(articles)} 篇相關新聞")

                for article in articles:
                    try:
                        title_elem = article.find_element(By.CSS_SELECTOR, "div[role='heading']")
                        link_elem = article.find_element(By.TAG_NAME, "a")
                        date_elem = article.find_element(By.CSS_SELECTOR, ".OSrXXb span")
                        
                        # 嘗試抓取摘要
                        try:
                            desc_elem = article.find_element(By.CSS_SELECTOR, ".GI74Re")
                            description = desc_elem.text
                        except:
                            description = ""

                        title = title_elem.text
                        link = link_elem.get_attribute("href")
                        date_str = date_elem.text

                        # 簡單過濾
                        if "ASUS" in title.upper() or "華碩" in title:
                            results.append({
                                "title": title,
                                "url": link,
                                "date_raw": date_str,
                                "source": "Google News",
                                "description": description
                            })
                    except Exception as e:
                        # 單篇失敗不影響整體
                        continue

            except Exception as e:
                logger.error(f"爬蟲執行期間發生錯誤: {e}")
                # 如果是 Timeout，可能是被 Google 擋了，建議保留截圖 (進階功能)
                # self.driver.save_screenshot("error_screenshot.png")
                
            finally:
                try:
                    self.driver.quit()
                    logger.info("瀏覽器已關閉")
                except:
                    pass
            
            return results

2.請將以下內容複製到 app/utils.py，建立日期處理工具
    import re
    from datetime import datetime, timedelta

    def parse_relative_date(date_str: str) -> str:
        """
        將 Google News 的相對時間 (e.g., '3 天前', '1 週前') 
        轉換為標準日期格式 (YYYY-MM-DD)。
        """
        today = datetime.now()
        
        try:
            # 去除前後空白
            date_str = date_str.strip()

            # 處理 "2025年5月28日" 這種絕對日期
            if "年" in date_str and "月" in date_str:
                dt = datetime.strptime(date_str, "%Y年%m月%d日")
                return dt.strftime("%Y-%m-%d")

            # 處理 "X 天前"
            days_match = re.search(r'(\d+)\s*天前', date_str)
            if days_match:
                days = int(days_match.group(1))
                dt = today - timedelta(days=days)
                return dt.strftime("%Y-%m-%d")

            # 處理 "X 週前"
            weeks_match = re.search(r'(\d+)\s*週前', date_str)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                dt = today - timedelta(weeks=weeks)
                return dt.strftime("%Y-%m-%d")

            # 處理 "X 小時前" (視為今天)
            hours_match = re.search(r'(\d+)\s*小時前', date_str)
            if hours_match:
                return today.strftime("%Y-%m-%d")
                
            # 處理 "昨天"
            if "昨天" in date_str:
                dt = today - timedelta(days=1)
                return dt.strftime("%Y-%m-%d")

            # 若都無法解析，回傳今天 (或你可以選擇拋出錯誤)
            return today.strftime("%Y-%m-%d")

        except Exception as e:
            print(f"日期解析失敗: {date_str}, 錯誤: {e}")
            return today.strftime("%Y-%m-%d")

3.請將以下內容複製到 app/database.py，建立連線資料庫及寫入
    import mysql.connector
    import os
    import logging
    from typing import List, Dict, Optional

    # 設定 logger
    logger = logging.getLogger(__name__)

    class Database:
        def __init__(self):
            # 從環境變數讀取連線資訊 (Docker Compose 裡設定的)
            self.config = {
                'user': os.getenv('DB_USER', 'scraper_user'),
                'password': os.getenv('DB_PASSWORD', 'scraper_password'),
                'host': os.getenv('DB_HOST', 'mysql-db'),
                'database': os.getenv('DB_NAME', 'security_news'),
                'raise_on_warnings': False,
                'autocommit': False # 我們手動 commit 以確保交易完整性
            }

        def get_connection(self):
            """建立並回傳資料庫連線"""
            return mysql.connector.connect(**self.config)

        def insert_news(self, news_list: List[Dict]) -> int:
            """
            流程圖步驟 3 & 4: 寫入資料並去重
            - 使用 INSERT IGNORE 忽略已存在的 (title + publish_date)
            - 預設 status 為 'N'
            """
            if not news_list:
                return 0

            inserted_count = 0
            conn = None
            cursor = None
            
            try:
                conn = self.get_connection()
                cursor = conn.cursor()

                # SQL 語法: 若複合鍵重複則忽略，否則插入新資料
                sql = """
                INSERT IGNORE INTO news (title, url, publish_date, source, description, status, fail_count)
                VALUES (%s, %s, %s, %s, %s, 'N', 0)
                """

                for item in news_list:
                    val = (
                        item['title'],
                        item['url'],
                        item['publish_date'],
                        item['source'],
                        item.get('description', '')  # 取得摘要，若無則為空字串
                    )
                    cursor.execute(sql, val)
                    
                    # 檢查這筆是否真的寫入 (rowcount > 0 代表成功插入，0 代表被 IGNORE)
                    if cursor.rowcount > 0:
                        inserted_count += 1
                    else:
                        logger.debug(f"Duplicate found (Skipped): {item['title'][:30]}...")

                conn.commit()
                logger.info(f"[DB] 批次作業結束: 輸入 {len(news_list)} 筆 -> 實際新增 {inserted_count} 筆 (重複 {len(news_list)-inserted_count} 筆)")

            except mysql.connector.Error as err:
                logger.error(f"[DB Error] 寫入失敗: {err}")
                if conn:
                    conn.rollback()
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()
            
            return inserted_count

        def get_pending_news(self) -> List[Dict]:
            """
            流程圖步驟 5: 獲取所有狀態為 'N' (New) 的資料，準備進行填表
            """
            conn = None
            cursor = None
            results = []
            try:
                conn = self.get_connection()
                cursor = conn.cursor(dictionary=True) # 回傳字典格式，方便存取欄位
                
                # 依照日期排序，舊的新聞先處理
                sql = "SELECT * FROM news WHERE status = 'N' ORDER BY publish_date ASC"
                cursor.execute(sql)
                results = cursor.fetchall()
                
            except mysql.connector.Error as err:
                logger.error(f"[DB Error] 讀取待處理資料失敗: {err}")
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()
            return results

        def update_status(self, news_id: int, status: str):
            """
            流程圖步驟 7: 填表成功後，更新狀態 (例如變更為 'Y')
            """
            conn = None
            cursor = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                sql = "UPDATE news SET status = %s WHERE id = %s"
                cursor.execute(sql, (status, news_id))
                conn.commit()
                logger.info(f"[DB] 新聞 ID {news_id} 狀態更新為: '{status}'")
                
            except mysql.connector.Error as err:
                logger.error(f"[DB Error] 更新狀態失敗: {err}")
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()

        def record_failure(self, news_id: int):
            """
            流程圖失敗迴圈邏輯: 
            1. 失敗次數 (fail_count) + 1
            2. 若失敗次數 >= 3，將 status 設為 'E' (Error/放棄)
            """
            conn = None
            cursor = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # 1. 增加失敗次數
                sql_update = "UPDATE news SET fail_count = fail_count + 1 WHERE id = %s"
                cursor.execute(sql_update, (news_id,))
                
                # 2. 檢查目前失敗次數
                sql_check = "SELECT fail_count FROM news WHERE id = %s"
                cursor.execute(sql_check, (news_id,))
                result = cursor.fetchone()
                
                if result:
                    current_fail_count = result[0]
                    logger.warning(f"[DB] 新聞 ID {news_id} 失敗次數增加為: {current_fail_count}")
                    
                    # 3. 判斷是否超過閾值 (例如 3 次)
                    if current_fail_count >= 3:
                        sql_mark_error = "UPDATE news SET status = 'E' WHERE id = %s"
                        cursor.execute(sql_mark_error, (news_id,))
                        logger.error(f"[DB] 新聞 ID {news_id} 失敗次數過多 (>=3)，標記為 Error (E)")
                
                conn.commit()
                
            except mysql.connector.Error as err:
                logger.error(f"[DB Error] 紀錄失敗次數錯誤: {err}")
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()

4.請將以下內容複製到 app/main.py，更新主程式
    import logging
    import time
    import random
    import os
    from datetime import datetime  # <--- [新增] 用於紀錄擷取時間
    from scraper import NewsScraper
    from database import Database
    from utils import parse_relative_date
    from form_filler import FormFiller  # <--- [重要] 引入填表模組

    # 設定全域 Log 格式
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    def process_scraping_job():
        """
        [Phase 1] 爬蟲與入庫流程
        對應流程圖: 爬蟲 -> 資料清洗 -> 寫入資料庫(判斷是否存在)
        """
        logger.info("=== 階段一: 啟動爬蟲作業 ===")
        
        # 1. 初始化爬蟲
        scraper = NewsScraper()
        keyword = "ASUS router security"
        
        # 2. 執行爬取
        logger.info(f"正在搜尋關鍵字: {keyword}")
        raw_data = scraper.scrape_google_news(keyword)
        
        if not raw_data:
            logger.warning("本次未抓取到任何資料，跳過入庫流程。")
            return

        # 3. 資料清洗 (Data Cleaning) - [針對流程圖需求強化]
        logger.info("正在清洗資料格式 (日期標準化 & 去除空白)...")
        cleaned_data = []
        
        # [新增] 統一設定本次批次的「擷取時間」
        capture_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for item in raw_data:
            # [清洗 1] 日期標準化: "3 天前" -> "2023-12-05"
            std_date = parse_relative_date(item['date_raw'])
            
            # [清洗 2] 文字清洗: 移除前後空白/換行 (符合流程圖 "移除空白" 要求)
            clean_title = item['title'].strip()
            clean_desc = item.get('description', '').strip()
            
            # 整理符合要求的六大欄位:
            # 1. 來源網站 (source)
            # 2. 標題 (title)
            # 3. 發布日期 (publish_date)
            # 4. 內文摘要/重點 (description)
            # 5. 原始連結 (url)
            # 6. 擷取時間 (captured_at) - [新增]
            cleaned_data.append({
                'title': clean_title,
                'url': item['url'],
                'publish_date': std_date,
                'source': item['source'],
                'description': clean_desc,
                'captured_at': capture_time 
            })

        # 4. 寫入資料庫 (Insert & Deduplicate)
        db = Database()
        new_count = db.insert_news(cleaned_data)
        logger.info(f"階段一結束。資料庫新增: {new_count} 筆。")


    def process_form_filling_job():
        """
        [Phase 2] 自動填表流程
        對應流程圖: 檢查狀態 'N' -> 填寫 Google 表單 -> 成功更新 'Y' / 失敗記數
        """
        logger.info("=== 階段二: 檢查待填寫資料 (Status='N') ===")
        db = Database()
        
        # 5. 從 DB 撈出所有 Status = 'N' 的資料
        pending_tasks = db.get_pending_news()
        
        if not pending_tasks:
            logger.info("沒有新資料需要填寫 (All caught up)。")
            return

        logger.info(f"發現 {len(pending_tasks)} 筆待處理任務，準備開始填表...")

        # 初始化填表器 (建議在迴圈外初始化 driver，這裡為求簡單每次重啟)
        # 若要優化效能，可將 FormFiller 放在迴圈外，但需確保它能處理多筆提交
        
        for task in pending_tasks:
            news_id = task['id']
            title = task['title']
            logger.info(f"正在處理任務 ID:{news_id} | 標題: {title[:20]}...")

            filler = None
            try:
                # --- 6. 執行填表邏輯 (正式版) ---
                filler = FormFiller() # 初始化瀏覽器
                is_success = filler.fill_form(task) # 執行自動填寫
                
                if is_success:
                    # 7. 成功流程: 更新狀態為 'Y'
                    db.update_status(news_id, 'Y')
                    logger.info(f"-> 任務成功 (ID {news_id})")
                else:
                    # 失敗流程
                    raise Exception("Google 表單提交驗證失敗 (找不到成功訊息)")

            except Exception as e:
                logger.error(f"-> 任務失敗 (ID {news_id}): {e}")
                # 失敗迴圈: 記數 +1，若超過 3 次則標記為 'E'
                db.record_failure(news_id)
            finally:
                # 確保每次填完都關閉瀏覽器 (避免記憶體洩漏)
                if filler and hasattr(filler, 'driver'):
                    try:
                        filler.driver.quit()
                    except:
                        pass

    def main():
        try:
            # 為了確保 DB 容器已完全啟動
            time.sleep(2)
            
            # 執行完整工作流
            process_scraping_job()
            process_form_filling_job()
            
            logger.info("=== 所有自動化作業執行完畢 ===")
            
        except Exception as e:
            logger.critical(f"主程式發生未預期崩潰: {e}")

    if __name__ == "__main__":
        main()

5.在 Docker 裡面測試爬蟲
  docker exec -it asus_news_worker python app/main.py
  應該會看到 Log 顯示類似： [DB] 批次作業結束: 輸入 9 筆 -> 實際新增 8 筆 (重複 1 筆)
  這就代表那 8 筆成功寫入，而重複的 1 筆被安全地忽略了。

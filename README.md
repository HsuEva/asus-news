ASUS Router Security News Automation  
這是一個端到端的資安新聞自動化蒐集系統。  
專案目標是從多個來源（Google News、官方公告、資安論壇）爬取 ASUS Router 相關資安威脅，經過清洗與去重後存入 MySQL，最後自動填寫至 Google 表單以進行通報。  

🌟 專案亮點  
本專案包含許多針對 瀏覽器自動化 (Browser Automation) 的進階工程實踐：  
1. 全 Selenium 架構：搜尋與內文閱讀皆採用 Selenium，並實作 Anti-Detect 機制繞過網站防護。  
2. 高穩定性設計 (Resilience)：  
   Eager Loading 策略：大幅縮短頁面載入等待時間，防止爬蟲卡死。  
   Driver 自動復活：偵測到底層連線 (HTTPConnectionPool) 錯誤時，會自動重啟瀏覽器，實現無人值守運行。  
3.記憶體管理：實作 gc.collect() 與主動關閉 Driver，使用參數防止 Docker 記憶體崩潰，防止 Docker OOM。  
4.精準過濾：內建多語系關鍵字過濾器，確保新聞與「ASUS」及「Router/資安」高度相關。  
5.智慧填表：使用 JavaScript Injection 技術，解決 Google 表單輸入框不可互動 (Not Interactable) 的問題。  

🛠 技術堆疊 (Tech Stack)  
```text
**Language**: Python 3.9+  
**Database**: MySQL 8.0 (Dockerized)  
**Core Library**: Selenium WebDriver (Headless Chrome)  
**Infrastructure**: Docker & Docker Compose  
**Features**: Multi-source Scraping (Google News EN/TW, Official Sites)  
              Timezone Correction (UTC+8)  
              Automatic Log Rotation (日誌輪替，按日儲存)  
              404 & PDF Detection (無效連結過濾)  
```

📂 專案結構  
```text
asus-news/
├── app/
│   ├── main.py             # 主程式 (負責排程、多源搜尋邏輯)
│   ├── scraper.py          # 爬蟲核心 (含反偵測、重啟機制、Eager模式)
│   ├── form_filler.py      # 填表機器人 (含 JS 注入、時區校正)
│   ├── database.py         # 資料庫操作 (含去重邏輯)
│   ├── logger.py           # 日誌模組 (支援輪替與雙重輸出)
│   └── utils.py            # 工具包 (日期解析)
├── db/
│   └── init.sql            # 資料庫初始化腳本
├── logs/                   # 執行日誌 (自動生成，按日輪替)
├── .env                    # 環境變數設定 (需自行建立)
├── docker-compose.yml      # 容器編排設定 (含記憶體優化)
├── Dockerfile              # Python 環境定義
└── requirements.txt        # 套件清單
```

=========================================================================================
🚀 **環境建置 (Windows 開發環境)**  
※如果你是第一次在 Windows 上執行Cursor、Python、Docker，請依照以下步驟設定環境。  

**第 0 階段：安裝編輯器 (Cursor、Docker、Python)**  
1.下載 Cursor 作為程式碼編輯器  
  前往 Cursor 官網，下載安裝檔。  
  執行安裝程式，並依照指示完成安裝。  

2.下載Docker  
  前往 Docker 官網，下載安裝檔。  
  執行安裝程式，並依照指示完成安裝。  

3.開啟 Cursor 的終端機，檢查python是否已安裝  
  ```bash
  python --version 或 py --version 或 python3 --version  
  ```

4.下載與安裝python  
  a.前往 Python 官網下載頁面。  
  b.點擊黃色按鈕 Download Python 3.9。  
    ※執行下載的安裝檔 (⚠️ 重要)  
    務必勾選最下方的 ☑️ Add Python.exe to PATH (將 Python 加入環境變數)。  
  c.點選 Install Now 完成安裝。  

5.打開 Cursor  
  點擊左側邊欄的「方塊圖示」 (Extensions)。  
  搜尋 Python。  
  找到由 Microsoft 開發的那個（通常下載量最高），點擊 Install。 (這個套件會幫你做語法高亮、程式碼補全、還能幫你選虛擬環境)  

6.安裝完成後回到步驟1，檢查是否安裝成功，安裝成功後，接續7.開啟專案資料夾。  

7.開啟專案資料夾  
  在電腦桌面或你習慣的地方，建立一個新資料夾，命名為 
  ```bash
  asus-news
  ```
  。  
  在 Cursor 中，點選 
  ```bash
  File -> Open Folder
  ```
  ，選擇這個資料夾。  

------------------------------------------------------------------------------------------------
**第 1 階段：建立虛擬環境 (Virtual Environment)** - 為避免影響電腦其他專案，需要建立一個獨立的環境。  
1.開啟 Cursor 的終端機  
  使用快捷鍵 
  ```bash
  Ctrl + ` 
  ```
  開啟終端機。  
  確保終端機路徑是在這個專案的資料夾底下。  

2.請依序輸入以下指令：  
  Windows:  
  (1). 建立虛擬環境 (只需做一次)  
       ```bash
       python -m venv .venv  
       ```

  (2). 啟動虛擬環境 (每次重開 Cursor 都要確認前面有 (.venv) 字樣，通常 Cursor 會自動偵測)  
       ```bash
       .venv\Scripts\activate  
       ```

註:  
Q:如果遇到.venv\Scripts\activate錯誤為Windows PowerShell 安全性限制問題  
A:解決方法  
  步驟 1：修改執行權限  
  ```bash
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser  
  ```
  步驟 2：權限改好後，再執行一次原本的指令  
💡如何確認成功？ 看到 Terminal 的最前面出現了綠色或白色的 (.venv) 字樣  

------------------------------------------------------------------------------------------------
**第 2 階段：驗證與安裝依賴**  
```bash
1.在 Cursor 左側檔案總管按右鍵 -> New File -> 命名為 requirements.txt。  
```
2.貼上以下內容:  
  ```text
  requests>=2.31.0
  beautifulsoup4>=4.12.0
  selenium>=4.16.0
  webdriver-manager>=4.0.1
  mysql-connector-python>=8.2.0
  python-dotenv>=1.0.0
  pandas>=2.1.0
  ```

3.回到終端機，輸入安裝指令：  
  ```bash
  pip install -r requirements.txt
```

------------------------------------------------------------------------------------------------
**第 3 階段：Docker 化**  
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
        title NVARCHAR(255) NOT NULL,
        publish_date DATE NOT NULL,
        url NVARCHAR(2048) NOT NULL,
        source NVARCHAR(100),
        
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

    📊 資料庫 news_Schema
    欄位	        類型	    說明
    id	            INT	        Primary Key
    title	        NVARCHAR    新聞標題
    url	            NVARCHAR	原始連結
    publish_date	DATE	    發布日期 (標準化 YYYY-MM-DD)
    source	        NVARCHAR    來源分類 (如: Google News (TW))
    description	    TEXT	    內文摘要 (優先使用內文，備用 Google Snippet)
    status	        CHAR(1)	    N(新), Y(完), E(錯)
    fail_count	    INT	        失敗重試次數
    created_at	    TIMESTAMP	擷取時間 (UTC，填表時會自動轉 +8)

  (4)建立 docker-compose.yml  
    ```text
    version: '3.8'
    services:
    # 1. MySQL 資料庫服務
    mysql-db:
        image: mysql:8.0
        container_name: asus_news_db
        restart: always
        environment:
        MYSQL_ROOT_PASSWORD: mysecretpassword
        MYSQL_DATABASE: security_news
        MYSQL_USER: scraper_user
        MYSQL_PASSWORD: scraper_password
        # --- [新增這行] 強制伺服器端使用 UTF-8 編碼 ---
        command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
        # ---------------------------------------------
        ports:
        - "3306:3306"
        volumes:
        - db_data:/var/lib/mysql
        - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
        networks:
        - scraper_network
        healthcheck:
        test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
        interval: 10s
        timeout: 5s
        retries: 5

    # 2. Python 應用程式服務
    app:
        build: .
        container_name: asus_news_worker
        depends_on:
        mysql-db:
            condition: service_healthy
        # --- [關鍵修正] ---
        # 使用 env_file 直接載入 .env 檔案中的所有變數
        # 這樣 Python 才能讀取到 GOOGLE_FORM_URL
        env_file:
        - .env
        # ----------------
        volumes:
        - .:/app
        networks:
        - scraper_network
        # 保持容器開啟，方便開發
        # 原本是: command: tail -f /dev/null
        command: python app/main.py

    volumes:
    db_data:

    networks:
    scraper_network:
        driver: bridge
    ```

  (5)建立 Dockerfile (docker-compose.yml 裡面參照了 build: .，需要一個 Dockerfile 才能跑)  
     a.在專案根目錄建立 Dockerfile。  
     b.在Dockerfile貼上以下內容：  
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
     
     c.在.env貼上以下內容，做環境設定  
        # --- 資料庫連線設定 (必須與 docker-compose.yml 一致) ---
        # 注意: 在 Docker 內部互連時，HOST 必須是 docker-compose 裡的 service name (mysql-db)
        # 若是從本機執行 python (非 Docker)，則需改為 localhost
        DB_HOST=mysql-db
        DB_PORT=3306
        DB_USER=scraper_user
        DB_PASSWORD=scraper_password
        DB_NAME=security_news

        # --- Google 表單設定 ---
        # 請將此網址替換為您實際要自動填寫的 Google Form 網址
        GOOGLE_FORM_URL=https://docs.google.com/forms/d/e/1FAIpQLScUld1s4B_RNVnCqSmK_dzgC7fS0cNrZZxAAIrwmyGZdqS7Yg/viewform?usp=publish-editor

        # --- 開發環境設定 ---
        # 解決 Cursor/VSCode 找不到模組 (reportMissingImports) 的問題
        # 讓 Python 知道 app 資料夾也是模組來源
        PYTHONPATH=app

     d.啟動 Docker Desktop  

     e.打開終端機，重設連線  
       ```bash
       docker context use default
       ```

     f.打開終端機，嘗試連線  
       ```bash
       docker ps
       ```

     g.打開終端機，執行會自動建置包含 Chrome 的 Python 環境以及初始化 MySQL 資料庫  
       ```bash
       docker-compose up -d --build
       ```

     h.打開終端機，查看現在的狀態  
       ```bash
       docker ps
       ```
       ```text
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
       ```
**=========================================================================================**
🚀 **撰寫爬蟲程式建置 (Windows 開發環境)**  

**第 1 階段：建立專案結構**  
1.在根目錄下建立app 資料夾  

2.在app資料夾下，建立以下檔案  
  ```text
    asus-news/
    ├── app/                    # 核心應用程式邏輯
    │   ├── __init__.py
    │   ├── main.py             # 程式進入點 (Entry Point)
    │   ├── scraper.py          # 爬蟲邏輯 (Requests/BS4)
    │   ├── utils.py            # 工具包
    │   ├── database.py         # 資料庫操作 (MySQL 連線與 CRUD)
    │   ├── form_filler.py      # 自動填表邏輯 (Selenium)
    │── └── logger.py           # 日誌設定 (Logging)
  ```
------------------------------------------------------------------------------------------------
**第 2 階段：撰寫程式碼**  

⚙️ 程式碼核心邏輯說明  
```text
Phase 1: 爬蟲與資料清洗  
多源排程：系統依序執行以下搜尋任務：  
Google News (EN): 針對國際資安新聞。  
Google News (TW): 針對台灣在地報導。  
官方資源: 針對 site:asus.com。  
資安通報: 針對 bleepingcomputer 等權威網站。  
深度閱讀：進入新聞頁面抓取內文。若遇到 404 或 PDF，會自動標記並跳過或使用備用摘要。  
過濾機制：檢查標題與內文是否包含 ASUS 且同時包含 Router 或 Security 相關關鍵字 (支援中英)。  
去重入庫：使用 INSERT IGNORE 與 Unique Key (Title + Date) 防止重複資料寫入 MySQL。  

Phase 2: 自動填表  
狀態讀取：從資料庫撈取狀態為 N (New) 的資料。  
時區校正：將資料庫的 UTC 時間轉換為台灣時間 (UTC+8)。  
智慧填寫：使用 JavaScript 直接對 DOM 元素賦值，繞過 Selenium send_keys 可能失敗的限制。  
狀態更新：填寫成功後將狀態更新為 Y，失敗超過 3 次則標記為 E。  
```

1.請將以下內容複製到 app/scraper.py  
```text
    import logging
    import time
    import random
    import re
    from typing import List, Dict, Optional
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from urllib3.exceptions import MaxRetryError, NewConnectionError
    from webdriver_manager.chrome import ChromeDriverManager
    from logger import logger

    class NewsScraper:
        def __init__(self):
            self.driver = None
            self._init_driver()

        def _init_driver(self):
            """初始化或重啟 Driver"""
            if self.driver:
                try: self.driver.quit()
                except: pass
            
            logger.info("啟動 Chrome Driver (V14 Final)...")
            self.driver = self._setup_driver()

        def _setup_driver(self) -> webdriver.Chrome:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new") 
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # [關鍵優化] Eager 模式：HTML 下載完就不等圖片/廣告
            chrome_options.page_load_strategy = 'eager'
            
            # 記憶體優化
            chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # 反爬蟲偽裝
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 設定較短的超時，避免卡死
            driver.set_page_load_timeout(20)
            driver.set_script_timeout(20)
            
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver

        def close(self):
            try:
                if self.driver:
                    self.driver.quit()
                    logger.info("爬蟲已結束並關閉")
            except:
                pass

        def is_relevant(self, title: str, content: str = "") -> bool:
            """中英文關鍵字過濾"""
            text_to_check = (title + " " + content).lower()
            if "asus" not in text_to_check and "華碩" not in text_to_check:
                return False
            
            router_keywords = ["router", "rt-", "gt-", "zenwifi", "aimesh", "tuf gaming", "rog rapture", "路由器", "分享器", "網通", "wifi"]
            security_keywords = ["security", "vulnerability", "cve", "exploit", "hack", "patch", "firmware", "backdoor", "botnet", "malware", "cyber", "attack", "warn", "alert", "risk", "資安", "漏洞", "駭客", "攻擊", "更新", "修補", "韌體", "後門", "惡意", "殭屍", "安全", "風險"]
            
            has_router = any(kw in text_to_check for kw in router_keywords)
            has_security = any(kw in text_to_check for kw in security_keywords)
            
            return has_router or has_security

        def read_article_content(self, url: str) -> str:
            if url.lower().endswith('.pdf'): return "SKIP_PDF"
            
            # 最多重試 1 次 (遇到 Driver 死掉時重啟)
            for attempt in range(2):
                try:
                    if not self.driver: self._init_driver()

                    logger.info(f"正在閱讀內文: {url[:50]}...")
                    
                    try:
                        self.driver.get(url)
                    except TimeoutException:
                        try: self.driver.execute_script("window.stop();")
                        except: pass
                    
                    time.sleep(random.uniform(1.0, 2.0))

                    # --- [關鍵修正] 錯誤頁面檢測 ---
                    try:
                        page_title = self.driver.title.lower()
                        # 1. 擴充錯誤關鍵字清單
                        error_keywords = [
                            "404", "not found", "page not found", "找不到網頁", "無法顯示網頁", 
                            "article not found", "error 404", "sorry", "access denied", 
                            "forbidden", "讀取失敗", "無法載入", "site can't be reached", 
                            "refused to connect", "bad gateway", "service unavailable"
                        ]
                        
                        # 2. 檢查標題
                        if any(kw in page_title for kw in error_keywords):
                            logger.warning(f"偵測到錯誤標題 ({page_title})，立即跳過: {url}")
                            return "SKIP_ERROR"
                        
                        # 3. 檢查頁面內容開頭
                        body_elem = self.driver.find_element(By.TAG_NAME, "body")
                        body_start = body_elem.text[:500].lower()
                        
                        if any(kw in body_start for kw in error_keywords):
                            logger.warning(f"偵測到錯誤內容 (如 404/Sorry)，立即跳過: {url}")
                            return "SKIP_ERROR"
                    except:
                        pass
                    # -------------------------------------

                    paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                    content = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 30]
                    if content: return " ".join(content)[:300] + "..."

                    try:
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        clean_text = " ".join(body.text.split())
                        if len(clean_text) > 50: return clean_text[:300] + "..."
                    except: pass
                    
                    return "無法提取有效文字"

                except Exception as e:
                    error_msg = str(e)
                    if "HTTPConnectionPool" in error_msg or "refused" in error_msg or "invalid session" in error_msg:
                        logger.warning(f"偵測到瀏覽器崩潰，正在重啟 Driver...")
                        self._init_driver()
                        time.sleep(2)
                        continue 
                    
                    logger.warning(f"閱讀失敗: {error_msg[:50]}")
                    return "SKIP_ERROR" # 發生異常也直接跳過，不要存
            
            return "SKIP_ERROR"

        def scrape_google_search(self, query: str, source_category: str, search_type: str = 'news', lang: str = 'en') -> List[Dict]:
            results = []
            try:
                if not self.driver: self._init_driver()

                base_url = "https://www.google.com/search?q={}&hl={}"
                
                if search_type == 'news':
                    url = base_url.format(query, lang) + "&tbm=nws&tbs=qdr:m6"
                else:
                    url = base_url.format(query, lang) + "&tbs=qdr:y"

                logger.info(f"[{source_category} | {lang}] 前往搜尋: {url}")
                
                try:
                    self.driver.get(url)
                except:
                    try: self.driver.execute_script("window.stop();")
                    except: pass

                time.sleep(3)

                for _ in range(2):
                    try:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                    except: 
                        self._init_driver()
                        break

                try:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "search")))
                except: pass

                if search_type == 'news':
                    items = self.driver.find_elements(By.CSS_SELECTOR, "div.SoaBEf")
                    if not items: items = self.driver.find_elements(By.CSS_SELECTOR, "div.MjjYud")
                else:
                    items = self.driver.find_elements(By.CSS_SELECTOR, "div.g")

                logger.info(f"[{source_category}] 找到 {len(items)} 筆原始資料")

                valid_count = 0
                for item in items:
                    try:
                        if search_type == 'news':
                            title_elem = item.find_element(By.CSS_SELECTOR, "div[role='heading']")
                        else:
                            title_elem = item.find_element(By.TAG_NAME, "h3")
                        
                        link_elem = item.find_element(By.TAG_NAME, "a")
                        link = link_elem.get_attribute("href")
                        title = title_elem.text

                        snippet = ""
                        try:
                            desc_elem = item.find_element(By.CSS_SELECTOR, ".GI74Re, .VwiC3b")
                            snippet = desc_elem.text
                        except: pass

                        if not self.is_relevant(title, snippet):
                            continue

                        date_str = "Today"
                        try:
                            date_elem = item.find_element(By.CSS_SELECTOR, ".OSrXXb span, .MUxGbd, .LEwnzc span") 
                            date_str = date_elem.text
                        except: pass

                        results.append({
                            "title": title,
                            "url": link,
                            "date_raw": date_str,
                            "source": source_category,
                            "description": snippet
                        })
                        valid_count += 1
                    except:
                        continue
                
                logger.info(f"[{source_category}] 保留 {valid_count} 筆有效資料")

            except Exception as e:
                logger.error(f"[{source_category}] 搜尋錯誤: {e}")
                self._init_driver()
            
            return results
```
2.請將以下內容複製到 app/utils.py，建立日期處理工具  
```text
    import re
    from datetime import datetime, timedelta

    def parse_relative_date(date_str: str) -> str:
        """
        將 Google News 的時間字串 (支援英文與中文格式) 
        轉換為標準日期格式 (YYYY-MM-DD)。
        """
        today = datetime.now()
        date_str = date_str.strip()
        
        try:
            # --- 英文格式處理 (English) ---
            
            # 處理 "3 days ago", "5 mins ago", "2 weeks ago"
            if 'ago' in date_str.lower():
                # 提取數字
                num_match = re.search(r'(\d+)', date_str)
                number = int(num_match.group(1)) if num_match else 0
                
                if 'min' in date_str or 'hour' in date_str:
                    return today.strftime("%Y-%m-%d")
                elif 'day' in date_str:
                    dt = today - timedelta(days=number)
                    return dt.strftime("%Y-%m-%d")
                elif 'week' in date_str:
                    dt = today - timedelta(weeks=number)
                    return dt.strftime("%Y-%m-%d")
                elif 'month' in date_str:
                    dt = today - timedelta(days=number*30)
                    return dt.strftime("%Y-%m-%d")

            # 處理 "Yesterday"
            if 'Yesterday' in date_str:
                dt = today - timedelta(days=1)
                return dt.strftime("%Y-%m-%d")

            # 處理絕對日期 "Jul 19, 2025", "July 19, 2025", "19 July 2025"
            # 嘗試多種英文日期格式
            for fmt in ["%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # --- 中文格式處理 (Chinese) ---
            
            if "年" in date_str and "月" in date_str:
                dt = datetime.strptime(date_str, "%Y年%m月%d日")
                return dt.strftime("%Y-%m-%d")

            days_match = re.search(r'(\d+)\s*天前', date_str)
            if days_match:
                days = int(days_match.group(1))
                dt = today - timedelta(days=days)
                return dt.strftime("%Y-%m-%d")

            weeks_match = re.search(r'(\d+)\s*週前', date_str)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                dt = today - timedelta(weeks=weeks)
                return dt.strftime("%Y-%m-%d")
                
            if "昨天" in date_str:
                dt = today - timedelta(days=1)
                return dt.strftime("%Y-%m-%d")

            # 若都無法解析，回傳今天 (但也印出錯誤以便除錯)
            # print(f"Warning: 無法解析日期 '{date_str}'，預設為今天")
            return today.strftime("%Y-%m-%d")

        except Exception as e:
            print(f"日期解析失敗: {date_str}, 錯誤: {e}")
            return today.strftime("%Y-%m-%d")
```

3.請將以下內容複製到 app/main.py，更新主程式  
```text
    import logging
    import time
    import os
    import gc
    from datetime import datetime, timedelta, timezone
    from scraper import NewsScraper
    from database import Database
    from utils import parse_relative_date
    from form_filler import FormFiller
    from logger import logger

    # 多源搜尋設定
    SEARCH_CONFIGS = [
        {
            "category": "Google News (EN)",
            "query": "ASUS router security",
            "type": "news",
            "lang": "en"
        },
        {
            "category": "Google News (TW)",
            "query": "華碩 路由器 資安",
            "type": "news",
            "lang": "zh-TW"
        },
        {
            "category": "官方資源",
            "query": "site:asus.com security router",
            "type": "web",
            "lang": "en"
        },
        {
            "category": "資安通報", 
            "query": "site:bleepingcomputer.com OR site:thehackernews.com ASUS",
            "type": "news",
            "lang": "en"
        }
    ]

    def process_scraping_job():
        logger.info("=== 階段一: 雙語多源爬蟲啟動 ===")
        scraper = NewsScraper()
        
        try:
            all_news_data = []
            
            for config in SEARCH_CONFIGS:
                logger.info(f"執行任務: {config['category']}...")
                
                raw_data = scraper.scrape_google_search(
                    query=config['query'],
                    source_category=config['category'],
                    search_type=config['type'],
                    lang=config['lang'] 
                )
                
                all_news_data.extend(raw_data[:5])
                time.sleep(2)

            if not all_news_data:
                logger.warning("未找到任何資料。")
                return

            logger.info(f"搜尋完成，共 {len(all_news_data)} 筆，開始閱讀內文...")
            
            cleaned_data = []
            tw_tz = timezone(timedelta(hours=8))
            capture_time = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')

            for item in all_news_data:
                deep_content = scraper.read_article_content(item['url'])
                
                if deep_content in ["SKIP_404", "SKIP_PDF", "SKIP_ERROR","drifted off-grid","Page Not Found!","SORRY","Sorry! Page not found"]:
                    logger.warning(f"跳過無效/錯誤連結: {item['title'][:20]}...")
                    continue
                
                final_desc = "無摘要"
                if deep_content and len(deep_content) > 30 and "失敗" not in deep_content:
                    final_desc = deep_content
                elif item.get('description'):
                    final_desc = f"[Google摘要] {item['description']}"
                
                std_date = parse_relative_date(item['date_raw'])
                
                cleaned_data.append({
                    'title': item['title'].strip(),
                    'url': item['url'],
                    'publish_date': std_date,
                    'source': item['source'],
                    'description': final_desc,
                    'captured_at': capture_time 
                })

            if cleaned_data:
                db = Database()
                new_count = db.insert_news(cleaned_data)
                logger.info(f"階段一結束。資料庫實際新增: {new_count} 筆。")
            else:
                logger.warning("階段一結束。沒有有效資料可寫入。")
            
        except Exception as e:
            logger.error(f"爬蟲階段發生錯誤: {e}")
        finally:
            scraper.close()
            del scraper
            gc.collect()

    def process_form_filling_job():
        logger.info("=== 階段二: 填寫表單 (Status='N') ===")
        db = Database()
        pending_tasks = db.get_pending_news()
        
        # 統計變數
        total_tasks = 0
        success_count = 0
        fail_count = 0
        
        if not pending_tasks:
            logger.info("沒有待處理資料。")
            return total_tasks, success_count, fail_count

        total_tasks = len(pending_tasks)
        logger.info(f"發現 {total_tasks} 筆任務，啟動填表機器人...")
        
        for i, task in enumerate(pending_tasks):
            news_id = task['id']
            title = task['title']
            logger.info(f"[{i+1}/{total_tasks}] 填寫中: {title[:15]}...")

            filler = None
            try:
                filler = FormFiller()
                is_success = filler.fill_form(task)
                
                if is_success:
                    db.update_status(news_id, 'Y')
                    logger.info(f"-> 成功 (ID {news_id})")
                    success_count += 1
                else:
                    raise Exception("提交失敗")

            except Exception as e:
                logger.error(f"-> 失敗 (ID {news_id}): {e}")
                db.record_failure(news_id)
                fail_count += 1
            finally:
                if filler:
                    try: filler.driver.quit()
                    except: pass
                del filler
                gc.collect()
                time.sleep(3)
                
        return total_tasks, success_count, fail_count

    def main():
        logger.info("=== 系統啟動：進入自動化排程模式 ===")
        # 加入 while True 讓它變成無窮迴圈
        while True:
            try:
                time.sleep(2)
                process_scraping_job()
                gc.collect()
                time.sleep(2)
                
                # 接收回傳的統計數據
                total, success, fail = process_form_filling_job()
                
                logger.info("=== 全部完成 ===")
                # 顯示統計結果
                logger.info(f"執行統計: 總共 {total} 筆 | 成功: {success} 筆 | 失敗: {fail} 筆")
                
            except Exception as e:
                logger.critical(f"主程式崩潰: {e}")
                
            # 設定下次執行的等待時間 (目前設定為 24 小時 = 86400 秒)
            wait_seconds = 86400 
            logger.info(f"進入待機模式，{wait_seconds/3600} 小時後將再次執行...")
            time.sleep(wait_seconds)

    if __name__ == "__main__":
        main()
```

4.請將以下內容複製到 app/database.py，更新資料庫模組  
```text
    import mysql.connector
    import os
    import logging
    from typing import List, Dict, Optional
    from logger import logger

    # 設定 logger
    # logger = logging.getLogger(__name__)

    class Database:
        def __init__(self):
            self.config = {
                'user': os.getenv('DB_USER', 'scraper_user'),
                'password': os.getenv('DB_PASSWORD', 'scraper_password'),
                'host': os.getenv('DB_HOST', 'mysql-db'),
                'database': os.getenv('DB_NAME', 'security_news'),
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                # ==========================================
                # 關鍵修正：必須設為 False，否則重複資料會導致全部回滾
                # ==========================================
                'raise_on_warnings': False,  
                'autocommit': False 
            }

        def get_connection(self):
            """建立並回傳資料庫連線"""
            conn = mysql.connector.connect(**self.config)
            
            try:
                cursor = conn.cursor()
                cursor.execute("SET NAMES utf8mb4;")
                cursor.execute("SET CHARACTER SET utf8mb4;")
                cursor.execute("SET character_set_connection=utf8mb4;")
                cursor.close()
            except:
                pass
            # ==============================
            
            return conn

        def insert_news(self, news_list: List[Dict]) -> int:
            if not news_list:
                return 0

            inserted_count = 0
            conn = None
            cursor = None
            
            try:
                conn = self.get_connection()
                cursor = conn.cursor()

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
                        item.get('description', '')
                    )
                    cursor.execute(sql, val)
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                
                # 這一行是將資料寫入硬碟的關鍵
                conn.commit()
                logger.info(f"[DB] 批次作業結束: 輸入 {len(news_list)} 筆 -> 實際新增 {inserted_count} 筆")

            except mysql.connector.Error as err:
                # 只有當發生 "嚴重錯誤" (如連線斷掉) 時才 rollback
                # 因為 raise_on_warnings=False，重複資料不會跑進這裡
                logger.error(f"[DB Error] 寫入失敗: {err}")
                if conn:
                    conn.rollback()  # <--- 你的資料就是在這裡消失的
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
```

5.請將以下內容複製到 app/form_filler.py，更新Google Form 填表器  
```text
    import logging
    import os
    import time
    from datetime import datetime, timedelta
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from logger import logger

    class FormFiller:
        def __init__(self):
            self.form_url = os.getenv('GOOGLE_FORM_URL')
            if not self.form_url:
                raise ValueError("環境變數 GOOGLE_FORM_URL 未設定！")
            
            self.driver = self._setup_driver()

        def _setup_driver(self) -> webdriver.Chrome:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new") 
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--window-size=1920,1080")
            
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver

        def _smart_fill(self, element, value):
            """嘗試多種方式填入數值"""
            try:
                element.clear()
                element.send_keys(value)
            except Exception:
                try:
                    element.click()
                    element.send_keys(value)
                except:
                    self.driver.execute_script("""
                        arguments[0].value = arguments[1];
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """, element, value)

        def fill_form(self, data: dict) -> bool:
            try:
                logger.info(f"前往表單: {self.form_url}")
                self.driver.get(self.form_url)
                
                try:
                    WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"]')))
                except:
                    logger.warning("表單載入似乎超時，但嘗試繼續尋找輸入框...")

                # 多重定位策略
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input.whsOnd")
                if not inputs:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                if not inputs:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[aria-label]")

                textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')

                logger.info(f"偵測到 {len(inputs)} 個輸入框")

                if len(inputs) >= 5:
                    # 1. 標題
                    self._smart_fill(inputs[0], data['title'])
                    # 2. 連結
                    self._smart_fill(inputs[1], data['url'])
                    # 3. 發布日期
                    self._smart_fill(inputs[2], str(data['publish_date']))
                    # 4. 來源
                    self._smart_fill(inputs[3], data['source'])

                    # 5. 擷取時間
                    raw_time = data.get('created_at') or data.get('captured_at')
                    if not raw_time: raw_time = datetime.now()
                    if isinstance(raw_time, str):
                        try: raw_time = datetime.strptime(raw_time, '%Y-%m-%d %H:%M:%S')
                        except: raw_time = datetime.now()
                    tw_time = raw_time + timedelta(hours=8)
                    self._smart_fill(inputs[4], tw_time.strftime('%Y-%m-%d %H:%M:%S'))
                    
                    # 6. 摘要
                    if textareas and 'description' in data:
                        desc = data['description'][:800] 
                        self._smart_fill(textareas[0], desc)
                    
                    logger.info("欄位填寫完畢，嘗試提交...")
                    
                    # 提交按鈕
                    submit_btn = None
                    btn_xpaths = [
                        "//div[@role='button']//span[text()='提交']",
                        "//div[@role='button']//span[text()='Submit']",
                        "//span[contains(text(), '提交')]/ancestor::div[@role='button']",
                        "//span[contains(text(), 'Submit')]/ancestor::div[@role='button']"
                    ]
                    
                    for xpath in btn_xpaths:
                        candidates = self.driver.find_elements(By.XPATH, xpath)
                        if candidates:
                            submit_btn = candidates[0]
                            break

                    if submit_btn:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                        
                        # --- [修正重點] 放寬成功驗證 ---
                        try:
                            # 嘗試等待成功訊息
                            wait = WebDriverWait(self.driver, 5)
                            wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "已記錄") or contains(text(), "recorded") or contains(text(), "response")]')))
                            logger.info("✅ 偵測到成功頁面文字")
                            return True
                        except:
                            # 如果等不到文字，檢查網址是否改變 (Google Form 提交後網址會變)
                            current_url = self.driver.current_url
                            if "formResponse" in current_url or "viewform" not in current_url:
                                logger.info("⚠️ 未偵測到成功文字，但網址已變更，視為提交成功")
                                return True
                            else:
                                # 真的失敗了，截圖留底
                                logger.warning("❌ 提交似乎沒反應，截圖檢查")
                                self.driver.save_screenshot(f"submit_fail_{int(time.time())}.png")
                                return False # 這裡還是回傳 False，讓主程式重試，或者您可以改成 True 賭一把
                    else:
                        logger.error("找不到提交按鈕")
                        return False
                else:
                    logger.error(f"❌ 填表失敗: 找不到足夠的輸入框 (預期 5 個，只找到 {len(inputs)} 個)。")
                    return False

            except Exception as e:
                logger.error(f"❌ 填表過程發生異常: {str(e)[:100]}")
                return False
            finally:
                try:
                    self.driver.quit()
                except:
                    pass
```

6.請將以下內容複製到 app/logger.py，更新日誌設定模組  
```text
    import logging
    import os
    import sys
    from logging.handlers import TimedRotatingFileHandler
    from datetime import datetime

    # 定義日誌資料夾
    LOG_DIR = "logs"
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # 定義日誌格式
    FORMATTER_STRING = "%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    class LoggerSetup:
        def __init__(self):
            self.logger = logging.getLogger("AsusNewsBot")
            self.logger.setLevel(logging.INFO)
            
            # 防止重複添加 Handler (避免 Log 重複印出)
            if not self.logger.handlers:
                self._add_console_handler()
                self._add_file_handler()

        def _add_console_handler(self):
            """新增終端機輸出"""
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(FORMATTER_STRING, datefmt=DATE_FORMAT)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        def _add_file_handler(self):
            """新增檔案輸出 (每天輪替，檔名包含日期)"""
            # 為了讓檔名一開始就包含日期，我們在初始化時就設定好基礎檔名
            # 例如: logs/app_2023-12-06.log
            current_date = datetime.now().strftime("%Y-%m-%d")
            filename = os.path.join(LOG_DIR, f"app_{current_date}.log")
            
            # 使用 TimedRotatingFileHandler
            # when="midnight": 每天午夜輪替
            # interval=1: 每 1 天
            # backupCount=7: 保留最近 7 個檔案
            # encoding="utf-8": 確保中文不亂碼
            file_handler = TimedRotatingFileHandler(
                filename, when="midnight", interval=1, backupCount=7, encoding="utf-8"
            )
            
            # 設定輪替後的檔名後綴格式 (雖然我們基礎檔名已有日期，但這是輪替機制的標準設定)
            file_handler.suffix = "%Y-%m-%d.log" 
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(FORMATTER_STRING, datefmt=DATE_FORMAT)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        def get_logger(self):
            return self.logger

    # 初始化並匯出 logger 實例
    # 其他檔案只需: from logger import logger 即可使用
    logger = LoggerSetup().get_logger()
```

7.執行  
  a.在 Docker 裡面手動測試爬蟲  
    ```bash
    docker exec -it asus_news_worker python app/main.py  
    ```
    最後會看到 Log 顯示：  === 全部完成 ===  

  b.自動化執行，程式自動跑起來  
    ```bash
    docker-compose up  
    ```

  註:  
  1.若要開發者進入手動執行，docker-compose.yml中改(command: tail -f /dev/null)後，手動執行docker exec -it asus_news_worker python app/main.py。  
  2.如果是自動化系統，應該是設定為執行 Python，預期 docker-compose up 後程式就會自動跑起來，因此docker-compose.yml中設定(command: python app/main.py)。  

8.可以查看 Docker 內部日誌，請在終端機輸入  
  ```bash
  docker logs -f asus_news_worker
  ```

**=========================================================================================**
🚀 **查詢結果**  
有不同方法可查詢結果  
1. 至Google Form表單回應中查看  

2. 進入 MySQL 互動介面查詢  
   (1).請在 Terminal 執行，進入容器並登入 MySQL  
       ```bash
       docker exec -it asus_news_db mysql -u root -p
       ```
       系統會提示輸入密碼，請輸入"密碼"

   (2)看到 mysql> 提示符號後，複製以下指令，切換資料庫  
      ```bash
      USE security_news;
      ```

   (3)下指令，我要用UTF-8看  
      ```bash
      SET NAMES utf8mb4;
      ```

   (4)下 SQL 語法，查看新聞資料 (檢查爬蟲成果)  
      ```bash
      SELECT id, title, source, created_at FROM news ORDER BY id;
      ```

   (5)離開  
      ```bash
      exit;
      ```
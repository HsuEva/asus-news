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
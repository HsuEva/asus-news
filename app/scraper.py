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
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 記憶體優化
        chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 反爬蟲偽裝
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        logger.info("正在初始化全能爬蟲 (Multi-Language Support)...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.set_page_load_timeout(30)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def close(self):
        try:
            self.driver.quit()
            logger.info("爬蟲已結束並關閉")
        except:
            pass

    def is_relevant(self, title: str, content: str = "") -> bool:
        """
        [核心過濾器] 判斷新聞是否真的與 ASUS Router 資安相關
        支援中英文關鍵字匹配。
        """
        text_to_check = (title + " " + content).lower()
        
        # 1. 必須包含 ASUS (華碩)
        if "asus" not in text_to_check and "華碩" not in text_to_check:
            return False
            
        # 2. 必須包含路由器相關字詞 (產品名或 Router)
        # [修正] 加入中文關鍵字
        router_keywords = [
            "router", "rt-", "gt-", "zenwifi", "aimesh", "tuf gaming", "rog rapture", 
            "路由器", "分享器", "網通設備"
        ]
        has_router = any(kw in text_to_check for kw in router_keywords)
        
        # 3. 必須包含資安相關字詞
        # [修正] 加入中文關鍵字
        security_keywords = [
            "security", "vulnerability", "cve", "exploit", "hack", "patch", "firmware", 
            "backdoor", "botnet", "malware", "cyber", "attack",
            "資安", "漏洞", "駭客", "攻擊", "更新", "修補", "韌體", "後門", "惡意軟體", "殭屍網路", "安全"
        ]
        has_security = any(kw in text_to_check for kw in security_keywords)
        
        # 嚴格模式：必須同時滿足 (ASUS) AND (Router相關) AND (資安相關)
        is_valid = has_router and has_security
        
        if not is_valid:
            logger.debug(f"過濾掉無關新聞: {title}")
            
        return is_valid

    def read_article_content(self, url: str) -> str:
        if url.lower().endswith('.pdf'): return "PDF 文件連結"
        try:
            logger.info(f"正在閱讀內文: {url[:50]}...")
            try:
                self.driver.get(url)
            except TimeoutException:
                self.driver.execute_script("window.stop();")
            
            time.sleep(random.uniform(1.5, 3.0))

            # 策略 A: 標準段落
            paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
            content = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 30]
            if content: return " ".join(content)[:300] + "..."

            # 策略 B: Body 文字
            body = self.driver.find_element(By.TAG_NAME, "body")
            clean_text = " ".join(body.text.split())
            if len(clean_text) > 50: return clean_text[:300] + "..."
            
            return "無法提取有效文字"
        except Exception as e:
            return "讀取失敗"

    def scrape_google_search(self, query: str, source_category: str, search_type: str = 'news') -> List[Dict]:
        results = []
        try:
            # 為了提高準確度，我們在搜尋詞中強制加入 "router"
            if "router" not in query.lower() and "華碩" not in query:
                query += " router"

            # [重要] 移除 hl=en，改為 hl=zh-TW 或是移除該參數以適應多語言
            # 如果只想找中文新聞，可以設為 hl=zh-TW，若要通吃建議移除 hl 參數讓 Google 自動判斷 IP
            # 但為了 utils.py 的日期解析 (目前支援中英文)，我們先移除 hl=en 讓它自然呈現
            base_url = "https://www.google.com/search?q={}"
            if search_type == 'news':
                url = base_url.format(query) + "&tbm=nws&tbs=qdr:m6"
            else:
                url = base_url.format(query) + "&tbs=qdr:y"

            logger.info(f"[{source_category}] 前往搜尋: {url}")
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "search")))

            if search_type == 'news':
                items = self.driver.find_elements(By.CSS_SELECTOR, "div.SoaBEf")
                if not items: items = self.driver.find_elements(By.CSS_SELECTOR, "div.MjjYud")
            else:
                items = self.driver.find_elements(By.CSS_SELECTOR, "div.g")

            logger.info(f"[{source_category}] 原始搜尋結果: {len(items)} 筆")

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

                    # 抓摘要
                    snippet = ""
                    try:
                        desc_elem = item.find_element(By.CSS_SELECTOR, ".GI74Re, .VwiC3b")
                        snippet = desc_elem.text
                    except: pass

                    # --- [關鍵] 執行中英文混合過濾 ---
                    if not self.is_relevant(title, snippet):
                        continue
                    # -------------------------

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
            
            logger.info(f"[{source_category}] 過濾後有效資料: {valid_count} 筆")

        except Exception as e:
            logger.error(f"[{source_category}] 搜尋錯誤: {e}")
        
        return results
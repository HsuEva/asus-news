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
        
        # --- [V3 強化版] 反爬蟲與穩定性設定 ---
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 關鍵 1: 隱藏 "自動化測試軟體控制中" 的特徵
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 關鍵 2: 偽裝 User-Agent (更真實的版本)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        logger.info("正在初始化 Chrome Driver (V3 Anti-Detect)...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 關鍵 3: 修改 navigator.webdriver 屬性 (讓 Google 抓不到是 Selenium)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def scrape_google_news(self, keyword: str = "ASUS router security") -> List[Dict]:
        results = []
        try:
            # 加上 hl=en 確保介面語言統一，減少 CSS Selector 失效機率
            url = f"https://www.google.com/search?q={keyword}&tbm=nws&tbs=qdr:m6&hl=en"
            logger.info(f"前往 URL: {url}")
            
            self.driver.get(url)
            
            # 隨機延遲
            time.sleep(random.uniform(3, 6))

            # 嘗試處理 "同意 Cookies" 彈窗 (如果是歐盟IP或某些情況會跳出)
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if "Accept" in btn.text or "Agree" in btn.text:
                        btn.click()
                        time.sleep(2)
                        break
            except:
                pass

            # 放寬等待條件：只要有任何搜尋結果容器出現即可
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "search"))
            )

            # 抓取新聞卡片 (嘗試多種 Selector 以防 Google 改版)
            articles = self.driver.find_elements(By.CSS_SELECTOR, "div.SoaBEf")
            if not articles:
                # 備用 Selector
                articles = self.driver.find_elements(By.CSS_SELECTOR, "div.MjjYud")

            logger.info(f"找到 {len(articles)} 篇相關新聞")

            for article in articles:
                try:
                    # 使用相對路徑找標題
                    title_elem = article.find_element(By.CSS_SELECTOR, "div[role='heading']")
                    link_elem = article.find_element(By.TAG_NAME, "a")
                    
                    try:
                        date_elem = article.find_element(By.CSS_SELECTOR, ".OSrXXb span")
                        date_str = date_elem.text
                    except:
                        date_str = "Today" # 找不到日期就預設今天

                    # 嘗試抓摘要
                    try:
                        desc_elem = article.find_element(By.CSS_SELECTOR, ".GI74Re")
                        description = desc_elem.text
                    except:
                        description = ""

                    title = title_elem.text
                    link = link_elem.get_attribute("href")

                    if "ASUS" in title.upper() or "華碩" in title:
                        results.append({
                            "title": title,
                            "url": link,
                            "date_raw": date_str,
                            "source": "Google News",
                            "description": description
                        })
                except Exception as e:
                    continue

        except Exception as e:
            logger.error(f"爬蟲執行期間發生錯誤: {e}")
            # 發生錯誤時截圖，這在 Docker 環境除錯非常重要
            try:
                self.driver.save_screenshot("scraper_error.png")
            except:
                pass
            
        finally:
            try:
                self.driver.quit()
            except:
                pass
        
        return results
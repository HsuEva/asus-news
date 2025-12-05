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

logger = logging.getLogger(__name__)

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
        
        # --- [記憶體優化關鍵參數] ---
        chrome_options.add_argument("--blink-settings=imagesEnabled=false") # 不載入圖片
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 反偵測
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def _smart_fill(self, element, value):
        try:
            element.clear()
            element.send_keys(value)
        except Exception:
            self.driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, element, value)

    def fill_form(self, data: dict) -> bool:
        try:
            self.driver.get(self.form_url)
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"]')))

            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input.whsOnd")
            if not inputs:
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')

            if len(inputs) >= 5:
                self._smart_fill(inputs[0], data['title'])
                self._smart_fill(inputs[1], data['url'])
                self._smart_fill(inputs[2], str(data['publish_date']))
                self._smart_fill(inputs[3], data['source'])

                # 時區校正 (UTC -> UTC+8)
                raw_time = data.get('created_at') or data.get('captured_at')
                if not raw_time: raw_time = datetime.now()
                if isinstance(raw_time, str):
                    try: raw_time = datetime.strptime(raw_time, '%Y-%m-%d %H:%M:%S')
                    except: raw_time = datetime.now()

                tw_time = raw_time + timedelta(hours=8)
                self._smart_fill(inputs[4], tw_time.strftime('%Y-%m-%d %H:%M:%S'))
                
                if textareas and 'description' in data:
                    desc = data['description'][:800] 
                    self._smart_fill(textareas[0], desc)
                
                # 提交
                submit_btn = None
                candidates = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[text()='提交' or text()='Submit']")
                if candidates:
                    submit_btn = candidates[0].find_element(By.XPATH, "./../..")
                else:
                    submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and (descendant::span[text()='提交'] or descendant::span[text()='Submit'])]")

                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", submit_btn)
                
                wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "已記錄") or contains(text(), "recorded") or contains(text(), "response")]')))
                return True
            else:
                logger.error(f"欄位不足: {len(inputs)}")
                return False

        except Exception as e:
            logger.error(f"填表失敗: {str(e)[:100]}")
            return False
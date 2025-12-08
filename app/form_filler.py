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
import logging
import os
import time
from datetime import datetime
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
            raise ValueError("環境變數 GOOGLE_FORM_URL 未設定！請檢查 .env 檔案。")
        
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        """初始化 Selenium Driver (針對 Docker 環境優化)"""
        chrome_options = Options()
        # 使用新版 headless 模式，穩定性較高
        chrome_options.add_argument("--headless=new") 
        # 解決 Linux 容器權限問題
        chrome_options.add_argument("--no-sandbox")
        # 解決共享記憶體不足導致的崩潰
        chrome_options.add_argument("--disable-dev-shm-usage")
        # 設定視窗大小，避免 RWD 隱藏元素
        chrome_options.add_argument("--window-size=1920,1080")
        # 禁用 GPU (伺服器環境不需要)
        chrome_options.add_argument("--disable-gpu")
        
        # 偽裝 User-Agent，避免 Google 表單拒絕存取
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def fill_form(self, data: dict) -> bool:
        """
        自動填寫 Google 表單
        :param data: 包含 title, url, publish_date, source, description, created_at 的字典
        :return: Boolean (True=成功, False=失敗)
        """
        try:
            logger.info(f"正在前往 Google 表單: {self.form_url}")
            self.driver.get(self.form_url)
            
            # 等待表單載入 (等待第一個問題出現)
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"]')))

            # --- 定位輸入欄位 ---
            # Google 表單通常使用 input[type="text"] 作為簡答題
            inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
            
            # Google 表單通常使用 textarea 作為段落 (摘要)
            textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')

            # 檢查欄位數量是否足夠 (根據您的需求，至少要有 5 個簡答題 + 1 個段落)
            # 順序假設: 1.標題, 2.連結, 3.日期, 4.來源, 5.擷取時間
            if len(inputs) >= 5:
                # 1. 填寫標題
                inputs[0].clear()
                inputs[0].send_keys(data['title'])
                
                # 2. 填寫連結
                inputs[1].clear()
                inputs[1].send_keys(data['url'])
                
                # 3. 填寫發布日期 (轉為字串)
                inputs[2].clear()
                inputs[2].send_keys(str(data['publish_date']))
                
                # 4. 填寫新聞來源
                inputs[3].clear()
                inputs[3].send_keys(data['source'])

                # 5. 填寫擷取時間 (created_at 是資料庫自動產生的時間)
                # 如果資料庫取出的 data 包含 created_at (datetime 物件)，轉為字串
                capture_time = data.get('created_at') or data.get('captured_at') or datetime.now()
                inputs[4].clear()
                inputs[4].send_keys(str(capture_time))
                
                # 6. 填寫內文摘要 (如果有的話)
                if textareas and 'description' in data:
                    textareas[0].clear()
                    # 限制摘要長度，避免 Google 表單報錯
                    desc_text = data['description'][:500] if data['description'] else "無摘要"
                    textareas[0].send_keys(desc_text)
                
                logger.info("欄位填寫完成，準備提交...")
                
                # --- 點擊提交按鈕 ---
                # 尋找文字為 "提交" (中文) 或 "Submit" (英文) 的按鈕
                submit_button = self.driver.find_element(By.XPATH, '//span[text()="提交" or text()="Submit"]')
                # 使用 JavaScript 點擊，避開可能被遮擋的問題
                self.driver.execute_script("arguments[0].click();", submit_button)
                
                # --- 驗證是否成功 ---
                # 提交後通常會出現 "您的回應已記錄" 或 "response has been recorded"
                wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "已記錄") or contains(text(), "recorded")]')))
                logger.info("表單提交驗證成功！")
                return True
                
            else:
                logger.error(f"填表失敗: 找不到足夠的輸入框 (預期 5 個，找到 {len(inputs)} 個)。請檢查表單題目順序。")
                return False

        except Exception as e:
            logger.error(f"填表過程發生錯誤: {e}")
            # 發生錯誤時截圖，方便除錯 (會儲存在 Docker 容器內)
            try:
                filename = f"error_screenshot_{int(time.time())}.png"
                self.driver.save_screenshot(filename)
                logger.info(f"已儲存錯誤截圖: {filename}")
            except:
                pass
            return False
        finally:
            # 關閉瀏覽器釋放記憶體
            try:
                self.driver.quit()
            except:
                pass
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
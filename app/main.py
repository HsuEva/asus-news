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

# logging.basicConfig(
#     level=logging.INFO, 
#     format='%(asctime)s - [%(levelname)s] - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# logger = logging.getLogger(__name__)

# 多源搜尋設定
# 注意：這裡雖然移除了 lang 參數，但透過調整 query 關鍵字
# 依然可以搜尋到不同語言的結果 (例如搜尋中文關鍵字就會找到中文新聞)
SEARCH_CONFIGS = [
    {
        "category": "Google News (EN)",
        "query": "ASUS router security", # 英文關鍵字 -> 傾向找英文結果
        "type": "news"
    },
    {
        "category": "Google News (TW)",
        "query": "華碩 路由器 資安", # 中文關鍵字 -> 傾向找中文結果
        "type": "news"
    },
    {
        "category": "官方資源",
        "query": "site:asus.com security router",
        "type": "web"
    },
    {
        "category": "資安通報", 
        "query": "site:bleepingcomputer.com OR site:thehackernews.com ASUS",
        "type": "news"
    }
]

def process_scraping_job():
    logger.info("=== 階段一: 雙語多源爬蟲啟動 ===")
    scraper = NewsScraper()
    
    try:
        all_news_data = []
        
        for config in SEARCH_CONFIGS:
            logger.info(f"執行任務: {config['category']}...")
            
            # [修正重點] 呼叫時移除 lang 參數
            # 這樣就不會觸發 TypeError，因為舊版 scraper 本來就不收這個參數
            raw_data = scraper.scrape_google_search(
                query=config['query'],
                source_category=config['category'],
                search_type=config['type']
                # lang=config['lang']  <-- 已移除此行
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

        db = Database()
        new_count = db.insert_news(cleaned_data)
        logger.info(f"階段一結束。資料庫實際新增: {new_count} 筆。")
        
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
    
    if not pending_tasks:
        logger.info("沒有待處理資料。")
        return

    logger.info(f"發現 {len(pending_tasks)} 筆任務，啟動填表機器人...")
    
    for i, task in enumerate(pending_tasks):
        news_id = task['id']
        title = task['title']
        logger.info(f"[{i+1}/{len(pending_tasks)}] 填寫中: {title[:15]}...")

        filler = None
        try:
            filler = FormFiller()
            is_success = filler.fill_form(task)
            
            if is_success:
                db.update_status(news_id, 'Y')
                logger.info(f"-> 成功 (ID {news_id})")
            else:
                raise Exception("提交失敗")

        except Exception as e:
            logger.error(f"-> 失敗 (ID {news_id}): {e}")
            db.record_failure(news_id)
        finally:
            if filler:
                try: filler.driver.quit()
                except: pass
            del filler
            gc.collect()
            time.sleep(3)

def main():
    try:
        time.sleep(2)
        process_scraping_job()
        gc.collect()
        time.sleep(2)
        process_form_filling_job()
        logger.info("=== 全部完成 ===")
    except Exception as e:
        logger.critical(f"主程式崩潰: {e}")

if __name__ == "__main__":
    main()
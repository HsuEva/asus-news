import logging
import time
import os
import gc
import threading  # 新增: 用於計時器
import sys        # 新增: 用於強制退出
from datetime import datetime, timedelta, timezone
from scraper import NewsScraper
from database import Database
from utils import parse_relative_date
from form_filler import FormFiller
from logger import logger

# --- 設定逾時時間 (秒) ---
# 設定為 300 秒 (5分鐘)，如果超過這個時間還沒跑完，視為卡死
JOB_TIMEOUT_SECONDS = 300 

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

def force_exit_handler():
    """
    當超時發生時的處理函式。
    直接使用 os._exit(1) 強制殺死所有執行緒與進程。
    """
    logger.critical(f"⚠️ 偵測到任務執行超過 {JOB_TIMEOUT_SECONDS} 秒，判定為卡死。")
    logger.critical("💀 正在強制結束程式 (Force Kill)，等待 Docker 自動重啟...")
    # os._exit 不會觸發清理 (finally)，是目前解決 Driver 卡死的唯一手段
    os._exit(1)

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
                # 確保去空白
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

def run_cycle_with_watchdog():
    """
    執行一次完整的爬蟲與填表循環，並加上逾時監控。
    """
    # 1. 啟動計時器 (Watchdog)
    # 如果這個計時器倒數結束，就會執行 force_exit_handler 殺死程式
    timer = threading.Timer(JOB_TIMEOUT_SECONDS, force_exit_handler)
    timer.start()
    
    try:
        # 執行主要任務
        time.sleep(2)
        process_scraping_job()
        gc.collect()
        time.sleep(2)
        
        total, success, fail = process_form_filling_job()
        
        logger.info("=== 全部完成 ===")
        logger.info(f"執行統計: 總共 {total} 筆 | 成功: {success} 筆 | 失敗: {fail} 筆")
        
    finally:
        # 2. 任務如果正常結束，必須取消計時器，否則它會在背景繼續倒數然後殺死程式
        timer.cancel()

def main():
    logger.info("=== 系統啟動：進入自動化排程模式 ===")
    
    # while True:
    try:
        # 使用帶有監控機制的函式來執行任務
        run_cycle_with_watchdog()
            
    except Exception as e:
        logger.critical(f"主程式崩潰 (Exception): {e}")
        # 如果是嚴重錯誤，也可以選擇直接重啟 Docker
        # os._exit(1)
            
    # 設定下次執行的等待時間 (目前設定為 24 小時 = 86400 秒)
    # wait_seconds = 86400 
    # logger.info(f"進入待機模式，{wait_seconds/3600} 小時後將再次執行...")
    # time.sleep(wait_seconds)

if __name__ == "__main__":
    main()
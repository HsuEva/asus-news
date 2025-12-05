import mysql.connector
import os
import logging
from database import Database

# 設定簡易 Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection_and_insert():
    logger.info(">>> 開始執行資料庫連線測試 (Test Mode)")
    
    # 1. 測試環境變數
    db_host = os.getenv('DB_HOST')
    logger.info(f"目前設定的 DB Host: {db_host}")
    
    db = Database()
    
    try:
        # 2. 測試連線
        conn = db.get_connection()
        logger.info("✅ 資料庫連線成功！")
        
        # 3. 測試寫入一筆假資料
        cursor = conn.cursor()
        
        # 準備一筆絕對不會重複的測試資料
        test_title = "System Check: Database Connection Test"
        test_date = "2029-01-01" # 未來的日期，確保唯一
        
        logger.info(f"正在嘗試寫入測試資料: {test_title}...")
        
        sql = """
        INSERT IGNORE INTO news (title, url, publish_date, source, description, status, fail_count)
        VALUES (%s, 'http://test.com', %s, 'System', 'Test Description', 'N', 0)
        """
        
        cursor.execute(sql, (test_title, test_date))
        
        # 4. 強制 Commit (關鍵)
        conn.commit()
        logger.info("✅ Commit 指令已執行。")
        
        # 5. 馬上讀取出來驗證
        cursor.execute(f"SELECT id, title, status FROM news WHERE publish_date = '{test_date}'")
        result = cursor.fetchone()
        
        if result:
            logger.info(f"🎉 驗證成功！資料已存在於資料庫中: {result}")
        else:
            logger.error("❌ 驗證失敗！資料寫入後 Commit 了，但讀取不到 (可能是 INSERT IGNORE 跳過了？)")

    except mysql.connector.Error as err:
        logger.error(f"❌ 資料庫錯誤: {err}")
    except Exception as e:
        logger.error(f"❌ 未預期錯誤: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            logger.info("連線已關閉。")

if __name__ == "__main__":
    test_connection_and_insert()
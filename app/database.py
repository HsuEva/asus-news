import mysql.connector
import os
import logging
from typing import List, Dict, Optional

# 設定 logger
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.config = {
            'user': os.getenv('DB_USER', 'scraper_user'),
            'password': os.getenv('DB_PASSWORD', 'scraper_password'),
            'host': os.getenv('DB_HOST', 'mysql-db'),
            'database': os.getenv('DB_NAME', 'security_news'),
            # ==========================================
            # 關鍵修正：必須設為 False，否則重複資料會導致全部回滾
            # ==========================================
            'raise_on_warnings': False,  
            'autocommit': False 
        }

    def get_connection(self):
        """建立並回傳資料庫連線"""
        return mysql.connector.connect(**self.config)

    def insert_news(self, news_list: List[Dict]) -> int:
        if not news_list:
            return 0

        inserted_count = 0
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            sql = """
            INSERT IGNORE INTO news (title, url, publish_date, source, description, status, fail_count)
            VALUES (%s, %s, %s, %s, %s, 'N', 0)
            """

            for item in news_list:
                val = (
                    item['title'],
                    item['url'],
                    item['publish_date'],
                    item['source'],
                    item.get('description', '')
                )
                cursor.execute(sql, val)
                
                if cursor.rowcount > 0:
                    inserted_count += 1
            
            # 這一行是將資料寫入硬碟的關鍵
            conn.commit()
            logger.info(f"[DB] 批次作業結束: 輸入 {len(news_list)} 筆 -> 實際新增 {inserted_count} 筆")

        except mysql.connector.Error as err:
            # 只有當發生 "嚴重錯誤" (如連線斷掉) 時才 rollback
            # 因為 raise_on_warnings=False，重複資料不會跑進這裡
            logger.error(f"[DB Error] 寫入失敗: {err}")
            if conn:
                conn.rollback()  # <--- 你的資料就是在這裡消失的
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        
        return inserted_count

    def get_pending_news(self) -> List[Dict]:
        """
        流程圖步驟 5: 獲取所有狀態為 'N' (New) 的資料，準備進行填表
        """
        conn = None
        cursor = None
        results = []
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True) # 回傳字典格式，方便存取欄位
            
            # 依照日期排序，舊的新聞先處理
            sql = "SELECT * FROM news WHERE status = 'N' ORDER BY publish_date ASC"
            cursor.execute(sql)
            results = cursor.fetchall()
            
        except mysql.connector.Error as err:
            logger.error(f"[DB Error] 讀取待處理資料失敗: {err}")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        return results

    def update_status(self, news_id: int, status: str):
        """
        流程圖步驟 7: 填表成功後，更新狀態 (例如變更為 'Y')
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            sql = "UPDATE news SET status = %s WHERE id = %s"
            cursor.execute(sql, (status, news_id))
            conn.commit()
            logger.info(f"[DB] 新聞 ID {news_id} 狀態更新為: '{status}'")
            
        except mysql.connector.Error as err:
            logger.error(f"[DB Error] 更新狀態失敗: {err}")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def record_failure(self, news_id: int):
        """
        流程圖失敗迴圈邏輯: 
        1. 失敗次數 (fail_count) + 1
        2. 若失敗次數 >= 3，將 status 設為 'E' (Error/放棄)
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. 增加失敗次數
            sql_update = "UPDATE news SET fail_count = fail_count + 1 WHERE id = %s"
            cursor.execute(sql_update, (news_id,))
            
            # 2. 檢查目前失敗次數
            sql_check = "SELECT fail_count FROM news WHERE id = %s"
            cursor.execute(sql_check, (news_id,))
            result = cursor.fetchone()
            
            if result:
                current_fail_count = result[0]
                logger.warning(f"[DB] 新聞 ID {news_id} 失敗次數增加為: {current_fail_count}")
                
                # 3. 判斷是否超過閾值 (例如 3 次)
                if current_fail_count >= 3:
                    sql_mark_error = "UPDATE news SET status = 'E' WHERE id = %s"
                    cursor.execute(sql_mark_error, (news_id,))
                    logger.error(f"[DB] 新聞 ID {news_id} 失敗次數過多 (>=3)，標記為 Error (E)")
            
            conn.commit()
            
        except mysql.connector.Error as err:
            logger.error(f"[DB Error] 紀錄失敗次數錯誤: {err}")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
import re
from datetime import datetime, timedelta

def parse_relative_date(date_str: str) -> str:
    """
    將 Google News 的相對時間 (e.g., '3 天前', '1 週前') 
    轉換為標準日期格式 (YYYY-MM-DD)。
    """
    today = datetime.now()
    
    try:
        # 去除前後空白
        date_str = date_str.strip()

        # 處理 "2025年5月28日" 這種絕對日期
        if "年" in date_str and "月" in date_str:
            dt = datetime.strptime(date_str, "%Y年%m月%d日")
            return dt.strftime("%Y-%m-%d")

        # 處理 "X 天前"
        days_match = re.search(r'(\d+)\s*天前', date_str)
        if days_match:
            days = int(days_match.group(1))
            dt = today - timedelta(days=days)
            return dt.strftime("%Y-%m-%d")

        # 處理 "X 週前"
        weeks_match = re.search(r'(\d+)\s*週前', date_str)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            dt = today - timedelta(weeks=weeks)
            return dt.strftime("%Y-%m-%d")

        # 處理 "X 小時前" (視為今天)
        hours_match = re.search(r'(\d+)\s*小時前', date_str)
        if hours_match:
            return today.strftime("%Y-%m-%d")
            
        # 處理 "昨天"
        if "昨天" in date_str:
            dt = today - timedelta(days=1)
            return dt.strftime("%Y-%m-%d")

        # 若都無法解析，回傳今天 (或你可以選擇拋出錯誤)
        return today.strftime("%Y-%m-%d")

    except Exception as e:
        print(f"日期解析失敗: {date_str}, 錯誤: {e}")
        return today.strftime("%Y-%m-%d")
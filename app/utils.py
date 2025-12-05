import re
from datetime import datetime, timedelta

def parse_relative_date(date_str: str) -> str:
    """
    將 Google News 的時間字串 (支援英文與中文格式) 
    轉換為標準日期格式 (YYYY-MM-DD)。
    """
    today = datetime.now()
    date_str = date_str.strip()
    
    try:
        # --- 英文格式處理 (English) ---
        
        # 處理 "3 days ago", "5 mins ago", "2 weeks ago"
        if 'ago' in date_str.lower():
            # 提取數字
            num_match = re.search(r'(\d+)', date_str)
            number = int(num_match.group(1)) if num_match else 0
            
            if 'min' in date_str or 'hour' in date_str:
                return today.strftime("%Y-%m-%d")
            elif 'day' in date_str:
                dt = today - timedelta(days=number)
                return dt.strftime("%Y-%m-%d")
            elif 'week' in date_str:
                dt = today - timedelta(weeks=number)
                return dt.strftime("%Y-%m-%d")
            elif 'month' in date_str:
                dt = today - timedelta(days=number*30)
                return dt.strftime("%Y-%m-%d")

        # 處理 "Yesterday"
        if 'Yesterday' in date_str:
            dt = today - timedelta(days=1)
            return dt.strftime("%Y-%m-%d")

        # 處理絕對日期 "Jul 19, 2025", "July 19, 2025", "19 July 2025"
        # 嘗試多種英文日期格式
        for fmt in ["%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # --- 中文格式處理 (Chinese) ---
        
        if "年" in date_str and "月" in date_str:
            dt = datetime.strptime(date_str, "%Y年%m月%d日")
            return dt.strftime("%Y-%m-%d")

        days_match = re.search(r'(\d+)\s*天前', date_str)
        if days_match:
            days = int(days_match.group(1))
            dt = today - timedelta(days=days)
            return dt.strftime("%Y-%m-%d")

        weeks_match = re.search(r'(\d+)\s*週前', date_str)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            dt = today - timedelta(weeks=weeks)
            return dt.strftime("%Y-%m-%d")
            
        if "昨天" in date_str:
            dt = today - timedelta(days=1)
            return dt.strftime("%Y-%m-%d")

        # 若都無法解析，回傳今天 (但也印出錯誤以便除錯)
        # print(f"Warning: 無法解析日期 '{date_str}'，預設為今天")
        return today.strftime("%Y-%m-%d")

    except Exception as e:
        print(f"日期解析失敗: {date_str}, 錯誤: {e}")
        return today.strftime("%Y-%m-%d")
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# 定義日誌資料夾
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 定義日誌格式
FORMATTER_STRING = "%(asctime)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class LoggerSetup:
    def __init__(self):
        self.logger = logging.getLogger("AsusNewsBot")
        self.logger.setLevel(logging.INFO)
        
        # 防止重複添加 Handler (避免 Log 重複印出)
        if not self.logger.handlers:
            self._add_console_handler()
            self._add_file_handler()

    def _add_console_handler(self):
        """新增終端機輸出"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(FORMATTER_STRING, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self):
        """新增檔案輸出 (每天輪替，檔名包含日期)"""
        # 為了讓檔名一開始就包含日期，我們在初始化時就設定好基礎檔名
        # 例如: logs/app_2023-12-06.log
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(LOG_DIR, f"app_{current_date}.log")
        
        # 使用 TimedRotatingFileHandler
        # when="midnight": 每天午夜輪替
        # interval=1: 每 1 天
        # backupCount=7: 保留最近 7 個檔案
        # encoding="utf-8": 確保中文不亂碼
        file_handler = TimedRotatingFileHandler(
            filename, when="midnight", interval=1, backupCount=7, encoding="utf-8"
        )
        
        # 設定輪替後的檔名後綴格式 (雖然我們基礎檔名已有日期，但這是輪替機制的標準設定)
        file_handler.suffix = "%Y-%m-%d.log" 
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(FORMATTER_STRING, datefmt=DATE_FORMAT)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

# 初始化並匯出 logger 實例
# 其他檔案只需: from logger import logger 即可使用
logger = LoggerSetup().get_logger()
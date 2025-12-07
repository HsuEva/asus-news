-- db/init.sql

-- 1. 建立並使用資料庫
CREATE DATABASE IF NOT EXISTS security_news;
USE security_news;

-- 2. 建立新聞資料表
CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publish_date DATE NOT NULL,
    url VARCHAR(2048) NOT NULL,
    source VARCHAR(100),
    
    -- 新增: 新聞摘要 (對應爬蟲的 description)
    description TEXT,
    
    -- 流程圖邏輯核心欄位:
    -- status: 'N'=新資料(New), 'Y'=已填表(Yes), 'E'=錯誤(Error)
    status CHAR(1) DEFAULT 'N' NOT NULL,
    
    -- fail_count: 紀錄填表失敗次數 (流程圖: 失敗超過3次 -> E)
    fail_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 去重機制: 同一天、同標題的新聞視為重複，拒絕寫入
    UNIQUE KEY unique_news_check (title, publish_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

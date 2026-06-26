-- MySQL Database Setup for AI ISP Chatbot
-- Run this script to create the database and tables.

CREATE DATABASE IF NOT EXISTS isp_chatbot
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE isp_chatbot;

-- Create application user
CREATE USER IF NOT EXISTS 'chatbot_user'@'localhost' IDENTIFIED BY 'chatbot_pass';
GRANT ALL PRIVILEGES ON isp_chatbot.* TO 'chatbot_user'@'localhost';
FLUSH PRIVILEGES;

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) DEFAULT NULL,
    current_intent VARCHAR(100) DEFAULT NULL,
    metadata JSON DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_user_id (user_id),
    INDEX idx_last_activity (last_activity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    metadata JSON DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36),
    user_id VARCHAR(100),
    intent VARCHAR(100),
    services_used JSON DEFAULT NULL,
    latency_ms FLOAT DEFAULT 0,
    token_count INT DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_intent (intent),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Logs table (optional — for persistent log storage)
CREATE TABLE IF NOT EXISTS application_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL,
    logger_name VARCHAR(100),
    message TEXT,
    trace_id VARCHAR(36),
    session_id VARCHAR(36),
    user_id VARCHAR(100),
    extra JSON DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_level (log_level),
    INDEX idx_trace_id (trace_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

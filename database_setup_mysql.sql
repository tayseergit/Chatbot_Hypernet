-- ============================================================
-- Chatbot Hypernet — MySQL Database Setup (for XAMPP / phpMyAdmin)
-- ============================================================

CREATE DATABASE IF NOT EXISTS chatbot_hypernet
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE chatbot_hypernet;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- TABLE: sessions
-- ============================================================
DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions (
    id          INT           NOT NULL AUTO_INCREMENT,
    session_id  VARCHAR(100)  NOT NULL UNIQUE,
    user_id     VARCHAR(100)  NOT NULL,
    customer_id VARCHAR(100)  DEFAULT NULL,
    is_active   TINYINT(1)    NOT NULL DEFAULT 1,
    authed      TINYINT(1)    NOT NULL DEFAULT 0,
    auth_state  VARCHAR(50)   NOT NULL DEFAULT 'UNAUTHENTICATED',
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_sessions_session_id (session_id),
    INDEX idx_sessions_user_id    (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: messages
-- ============================================================
DROP TABLE IF EXISTS messages;
CREATE TABLE messages (
    id          INT           NOT NULL AUTO_INCREMENT,
    session_id  VARCHAR(100)  NOT NULL,
    sender      VARCHAR(50)   NOT NULL COMMENT 'user or bot',
    content     TEXT          NOT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_messages_session_id (session_id),
    CONSTRAINT fk_messages_session
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: agent_action_logs
-- ============================================================
DROP TABLE IF EXISTS agent_action_logs;
CREATE TABLE agent_action_logs (
    id             INT           NOT NULL AUTO_INCREMENT,
    session_id     VARCHAR(100)  NOT NULL,
    customer_id    VARCHAR(100)  DEFAULT NULL,
    intent         VARCHAR(100)  DEFAULT NULL,
    action_type    VARCHAR(50)   NOT NULL COMMENT 'INTENT_DECISION | CRM_TOOL | RAG_SEARCH | PERMISSION_DENIED',
    tool_name      VARCHAR(100)  DEFAULT NULL,
    parameters     JSON          DEFAULT NULL,
    status         VARCHAR(20)   NOT NULL DEFAULT 'SUCCESS' COMMENT 'SUCCESS | FAILED | DENIED',
    result_summary TEXT          DEFAULT NULL,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_action_logs_session_id  (session_id),
    INDEX idx_action_logs_customer_id (customer_id),
    INDEX idx_action_logs_intent      (intent),
    INDEX idx_action_logs_action_type (action_type),
    INDEX idx_action_logs_created_at  (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: agent_permissions
-- ============================================================
DROP TABLE IF EXISTS agent_permissions;
CREATE TABLE agent_permissions (
    id           INT           NOT NULL AUTO_INCREMENT,
    tool_name    VARCHAR(100)  NOT NULL UNIQUE,
    display_name VARCHAR(200)  NOT NULL,
    description  TEXT          DEFAULT NULL,
    is_enabled   TINYINT(1)    NOT NULL DEFAULT 1,
    category     VARCHAR(50)   NOT NULL DEFAULT 'CRM_TOOL' COMMENT 'CRM_TOOL | SERVICE | GLOBAL',
    risk_level   VARCHAR(20)   NOT NULL DEFAULT 'MEDIUM' COMMENT 'LOW | MEDIUM | HIGH | CRITICAL',
    updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by   VARCHAR(100)  DEFAULT 'system',
    PRIMARY KEY (id),
    INDEX idx_permissions_tool_name (tool_name),
    INDEX idx_permissions_category  (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


SET FOREIGN_KEY_CHECKS = 1;


-- ============================================================
-- SEED: Default Permissions
-- ============================================================

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level) VALUES
('GLOBAL_AGENT',         'Global Agent Switch',       'Master kill switch — disabling this blocks ALL agent actions immediately.',                      1, 'GLOBAL',   'CRITICAL'),
('CRM',                  'CRM Service',               'Master switch for all CRM operations. Disabling blocks every CRM tool.',                          1, 'SERVICE',  'HIGH'),
('RAG',                  'RAG Knowledge Base',        'Knowledge base search service for answering general ISP questions.',                              1, 'SERVICE',  'LOW'),
('get_balance',          'Check Balance',             'Retrieves the customer account balance from CRM.',                                                1, 'CRM_TOOL', 'LOW'),
('get_current_package',  'Get Current Package',       'Fetches the customer active subscription package details.',                                       1, 'CRM_TOOL', 'LOW'),
('get_customer_info',    'Get Customer Info',         'Retrieves full customer profile and account information from CRM.',                               1, 'CRM_TOOL', 'MEDIUM'),
('open_ticket',          'Open Support Ticket',       'Creates a new support ticket on behalf of the customer in the CRM system.',                      1, 'CRM_TOOL', 'MEDIUM'),
('check_extend_status',  'Check Bill Extension',      'Checks whether the customer is eligible for a bill extension.',                                   1, 'CRM_TOOL', 'MEDIUM'),
('get_available_packages','Get Available Packages',   'Lists all available upgrade or subscription packages for the customer.',                          1, 'CRM_TOOL', 'LOW'),
('check_phone_number',   'Verify Phone Number',       'Authenticates the customer by matching their phone number against the CRM records.',              1, 'CRM_TOOL', 'HIGH');

-- ============================================================
-- END OF SETUP
-- Import via phpMyAdmin: Database > Import > choose this file
-- ============================================================

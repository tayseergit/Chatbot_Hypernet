-- ============================================================
-- Chatbot Hypernet — Complete Database Setup
-- Generated from SQLAlchemy models
-- Tables: sessions, messages, agent_action_logs, agent_permissions
-- ============================================================

-- Drop existing tables (order matters — FK constraints)
DROP TABLE IF EXISTS agent_action_logs;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS agent_permissions;


-- ============================================================
-- TABLE: sessions
-- Stores user session state and authentication info
-- ============================================================
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL UNIQUE,           -- e.g. telegram chat_id as string
    user_id     TEXT    NOT NULL,                  -- platform user identifier
    customer_id TEXT    DEFAULT NULL,              -- CRM customer ID (set after auth)
    is_active   INTEGER NOT NULL DEFAULT 1,        -- 1 = active, 0 = closed
    authed      INTEGER NOT NULL DEFAULT 0,        -- 1 = authenticated with phone
    auth_state  TEXT    NOT NULL DEFAULT 'UNAUTHENTICATED',  -- UNAUTHENTICATED | AWAITING_PHONE | AUTHENTICATED
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    DEFAULT NULL
);

CREATE INDEX idx_sessions_session_id  ON sessions(session_id);
CREATE INDEX idx_sessions_user_id     ON sessions(user_id);


-- ============================================================
-- TABLE: messages
-- Stores full conversation history per session
-- ============================================================
CREATE TABLE messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL REFERENCES sessions(session_id),
    sender      TEXT    NOT NULL,                  -- 'user' or 'bot'
    content     TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_messages_session_id ON messages(session_id);


-- ============================================================
-- TABLE: agent_action_logs
-- Audit trail of every action the agent takes
-- ============================================================
CREATE TABLE agent_action_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT    NOT NULL,
    customer_id    TEXT    DEFAULT NULL,
    intent         TEXT    DEFAULT NULL,           -- e.g. 'check_balance', 'open_ticket'
    action_type    TEXT    NOT NULL,               -- 'INTENT_DECISION' | 'CRM_TOOL' | 'RAG_SEARCH' | 'PERMISSION_DENIED'
    tool_name      TEXT    DEFAULT NULL,           -- e.g. 'get_balance', 'rag_service', 'intent_classifier'
    parameters     TEXT    DEFAULT NULL,           -- JSON string of tool inputs
    status         TEXT    NOT NULL DEFAULT 'SUCCESS',  -- 'SUCCESS' | 'FAILED' | 'DENIED'
    result_summary TEXT    DEFAULT NULL,           -- JSON string of result / error
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_action_logs_session_id   ON agent_action_logs(session_id);
CREATE INDEX idx_action_logs_customer_id  ON agent_action_logs(customer_id);
CREATE INDEX idx_action_logs_intent       ON agent_action_logs(intent);
CREATE INDEX idx_action_logs_action_type  ON agent_action_logs(action_type);
CREATE INDEX idx_action_logs_created_at   ON agent_action_logs(created_at);


-- ============================================================
-- TABLE: agent_permissions
-- Single source of truth for what the agent is allowed to do.
-- Admins toggle these from the dashboard.
-- ============================================================
CREATE TABLE agent_permissions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name    TEXT    NOT NULL UNIQUE,          -- must match code (ToolExecutor / service names)
    display_name TEXT    NOT NULL,                 -- human-readable name shown in dashboard
    description  TEXT    DEFAULT NULL,             -- what this tool does
    is_enabled   INTEGER NOT NULL DEFAULT 1,       -- 1 = allowed, 0 = blocked
    category     TEXT    NOT NULL DEFAULT 'CRM_TOOL',  -- 'CRM_TOOL' | 'SERVICE' | 'GLOBAL'
    risk_level   TEXT    NOT NULL DEFAULT 'MEDIUM',    -- 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_by   TEXT    DEFAULT 'system'
);

CREATE INDEX idx_permissions_tool_name ON agent_permissions(tool_name);
CREATE INDEX idx_permissions_category  ON agent_permissions(category);


-- ============================================================
-- SEED: Default Permissions
-- All tools start ENABLED. Admin can disable from dashboard.
-- ============================================================

-- GLOBAL control — master kill switch for the entire agent
INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'GLOBAL_AGENT',
    'Global Agent Switch',
    'Master kill switch — disabling this blocks ALL agent actions immediately. Use in emergencies only.',
    1, 'GLOBAL', 'CRITICAL'
);

-- SERVICE level — broad service toggles
INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'CRM',
    'CRM Service',
    'Master switch for all CRM operations. Disabling blocks every CRM tool regardless of individual settings.',
    1, 'SERVICE', 'HIGH'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'RAG',
    'RAG Knowledge Base',
    'Knowledge base search service. Used for answering general ISP questions from the knowledge base.',
    1, 'SERVICE', 'LOW'
);

-- CRM TOOLS — individual tool control
INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'get_balance',
    'Check Balance',
    'Retrieves the customer account balance from CRM.',
    1, 'CRM_TOOL', 'LOW'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'get_current_package',
    'Get Current Package',
    'Fetches the customer active subscription package details.',
    1, 'CRM_TOOL', 'LOW'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'get_customer_info',
    'Get Customer Info',
    'Retrieves full customer profile and account information from CRM.',
    1, 'CRM_TOOL', 'MEDIUM'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'open_ticket',
    'Open Support Ticket',
    'Creates a new support ticket on behalf of the customer in the CRM system.',
    1, 'CRM_TOOL', 'MEDIUM'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'check_extend_status',
    'Check Bill Extension Status',
    'Checks whether the customer is eligible for a bill extension.',
    1, 'CRM_TOOL', 'MEDIUM'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'get_available_packages',
    'Get Available Packages',
    'Lists all available upgrade or subscription packages for the customer.',
    1, 'CRM_TOOL', 'LOW'
);

INSERT INTO agent_permissions (tool_name, display_name, description, is_enabled, category, risk_level)
VALUES (
    'check_phone_number',
    'Verify Phone Number',
    'Authenticates the customer by matching their phone number against the CRM records.',
    1, 'CRM_TOOL', 'HIGH'
);

-- ============================================================
-- END OF SETUP
-- Run: sqlite3 chatbot.db < database_setup.sql
-- ============================================================

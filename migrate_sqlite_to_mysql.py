import sqlite3
import pymysql

print("Connecting to SQLite...")
sqlite_conn = sqlite3.connect("chatbot_db.sqlite")
sqlite_cursor = sqlite_conn.cursor()

print("Connecting to MySQL (isp_chatbot)...")
mysql_conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="isp_chatbot",
    port=3306,
    autocommit=True
)
mysql_cursor = mysql_conn.cursor()

# 1. Sessions
print("\n--- Migrating Sessions ---")
sqlite_cursor.execute("SELECT id, session_id, user_id, customer_id, is_active, authed, auth_state, created_at, updated_at, user_name FROM sessions")
sessions = sqlite_cursor.fetchall()
for s in sessions:
    print(f"Migrating session: {s[1]} - {s[9]}")
    mysql_cursor.execute("""
        INSERT INTO sessions (id, session_id, user_id, customer_id, is_active, authed, auth_state, created_at, updated_at, user_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            user_name = VALUES(user_name),
            customer_id = VALUES(customer_id),
            authed = VALUES(authed),
            auth_state = VALUES(auth_state),
            updated_at = VALUES(updated_at)
    """, s)

# 2. Messages
print("\n--- Migrating Messages ---")
sqlite_cursor.execute("SELECT id, session_id, sender, content, created_at FROM messages")
messages = sqlite_cursor.fetchall()
print(f"Found {len(messages)} messages in SQLite")
for m in messages:
    mysql_cursor.execute("""
        INSERT INTO messages (id, session_id, sender, content, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            content = VALUES(content)
    """, m)

# 3. Action Logs
print("\n--- Migrating Agent Action Logs ---")
sqlite_cursor.execute("SELECT id, session_id, action_type, tool_name, intent, status, parameters, result_summary, created_at FROM agent_action_logs")
logs = sqlite_cursor.fetchall()
print(f"Found {len(logs)} action logs in SQLite")
for l in logs:
    mysql_cursor.execute("""
        INSERT INTO agent_action_logs (id, session_id, action_type, tool_name, intent, status, parameters, result_summary, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status)
    """, l)

print("\n--- Verification in MySQL ---")
for t in ['sessions', 'messages', 'agent_action_logs', 'agent_permissions']:
    mysql_cursor.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"MySQL isp_chatbot.{t}: {mysql_cursor.fetchone()[0]} rows")

sqlite_conn.close()
mysql_conn.close()
print("\nMigration completed successfully!")

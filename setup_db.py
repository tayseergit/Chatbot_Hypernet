import sqlite3

db_path = 'chatbot.db'
sql_path = 'database_setup.sql'

with open(sql_path, 'r', encoding='utf-8') as f:
    sql = f.read()

conn = sqlite3.connect(db_path)
conn.executescript(sql)
conn.close()
print('Database created successfully!')

conn2 = sqlite3.connect(db_path)
cur = conn2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print('Tables:')
for row in cur.fetchall():
    print(f'  - {row[0]}')

cur2 = conn2.execute("SELECT tool_name, is_enabled, category, risk_level FROM agent_permissions")
print('\nPermissions seeded:')
for row in cur2.fetchall():
    status = 'ON' if row[1] else 'OFF'
    print(f'  [{status}] {row[0]} ({row[2]}, {row[3]})')

conn2.close()

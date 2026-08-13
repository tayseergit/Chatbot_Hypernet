import pymysql

conn = pymysql.connect(host='localhost', user='root', password='', port=3306, autocommit=True)
cur = conn.cursor()

cur.execute("CREATE DATABASE IF NOT EXISTS isp_chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
print("Database 'isp_chatbot' ready.")

cur.execute("CREATE USER IF NOT EXISTS 'chatbot_user'@'localhost' IDENTIFIED BY 'chatbot_pass'")
cur.execute("GRANT ALL PRIVILEGES ON isp_chatbot.* TO 'chatbot_user'@'localhost'")
cur.execute("FLUSH PRIVILEGES")
print("User 'chatbot_user' created and granted access.")

conn.close()
print("All done!")

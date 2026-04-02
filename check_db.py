import sqlite3

# 连接数据库
conn = sqlite3.connect('word_wearch.db')
c = conn.cursor()

# 查看数据库中的表
print("数据库中的表:")
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
for table in tables:
    print(f"- {table[0]}")

# 关闭连接
conn.close()

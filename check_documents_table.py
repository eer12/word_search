import sqlite3

# 连接数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 检查documents表的结构
print("documents表结构：")
c.execute('PRAGMA table_info(documents);')
rows = c.fetchall()
for row in rows:
    print(row)

# 检查documents表的内容
print("\ndocuments表内容：")
c.execute('SELECT * FROM documents LIMIT 5;')
rows = c.fetchall()
for row in rows:
    print(row)

# 关闭数据库连接
conn.close()
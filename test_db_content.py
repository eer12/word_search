import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 检查数据库中是否包含逗号和句号
print("检查数据库中包含逗号和句号的内容：")
c.execute('SELECT file_id, content FROM file_content_fts WHERE content LIKE "%，%" OR content LIKE "%.%" OR content LIKE "%。%" LIMIT 3')
results = c.fetchall()

for i, row in enumerate(results):
    file_id, content = row
    print(f"\n文件ID: {file_id}")
    print(f"内容片段: {content[:300]}...")

# 关闭连接
conn.close()

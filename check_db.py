import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 查询file_content_fts表的内容
print("检查file_content_fts表中的内容格式：")
c.execute('SELECT content FROM file_content_fts LIMIT 5')
results = c.fetchall()

for i, row in enumerate(results):
    print(f"\n记录 {i+1}:")
    content = row[0]
    print(f"内容长度: {len(content)}")
    print(f"前200字符: {content[:200]}...")
    print(f"是否包含标点符号: {'，' in content or '.' in content or '。' in content}")

# 关闭连接
conn.close()

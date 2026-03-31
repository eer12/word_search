import sqlite3

# 连接数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 先从现有的file_content_fts表中获取内容
content_data = []
try:
    c.execute('SELECT content, file_id FROM file_content_fts;')
    content_data = c.fetchall()
    print(f"从现有表中获取了 {len(content_data)} 条记录")
except sqlite3.OperationalError:
    print("file_content_fts表不存在，跳过获取内容")

# 删除现有的FTS5表
c.execute('DROP TABLE IF EXISTS file_content_fts;')

# 重新创建FTS5表，使用默认的分词器
c.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts USING fts5(
        content,                -- 全文内容
        file_id                -- 关联的文档ID
    )
''')

# 重新插入数据
for data in content_data:
    content, file_id = data
    if content:
        c.execute('INSERT INTO file_content_fts (content, file_id) VALUES (?, ?)', (content, file_id))

# 提交事务
conn.commit()

# 测试搜索
print("测试搜索'高质量'：")
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH '高质量';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0][:100]}...")

# 测试搜索'质量'：
print("\n测试搜索'质量'：")
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH '质量';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0][:100]}...")

# 关闭数据库连接
conn.close()

print("\nFTS5表已重新创建并插入数据")
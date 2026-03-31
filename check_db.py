import sqlite3

# 连接数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 检查file_content_fts表的结构
print("file_content_fts表结构：")
c.execute('PRAGMA table_info(file_content_fts);')
rows = c.fetchall()
for row in rows:
    print(row)

# 检查file_content_fts表的内容
print("\nfile_content_fts表内容：")
c.execute('SELECT * FROM file_content_fts;')
rows = c.fetchall()
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0]}")

# 测试直接搜索，不使用分词
print("\n测试直接搜索'高质量'（不使用分词）：")
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH '高质量';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0][:100]}...")

# 测试搜索'质量'
print("\n测试搜索'质量'：")
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH '质量';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0][:100]}...")

# 关闭数据库连接
conn.close()
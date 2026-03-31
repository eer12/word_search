import sqlite3

# 连接数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 测试使用LIKE语句搜索
print("测试使用LIKE语句搜索'高质量'：")
c.execute("SELECT * FROM file_content_fts WHERE content LIKE '%高质量%';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0]}")

# 测试使用LIKE语句搜索'高质量发展'：
print("\n测试使用LIKE语句搜索'高质量发展'：")
c.execute("SELECT * FROM file_content_fts WHERE content LIKE '%高质量发展%';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0]}")

# 检查file_content_fts表的内容
print("\nfile_content_fts表内容：")
c.execute('SELECT * FROM file_content_fts;')
rows = c.fetchall()
print(f"表中有 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0]}")

# 关闭数据库连接
conn.close()

print("\n测试完成")
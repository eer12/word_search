import sqlite3

# 连接数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 读取测试文档内容
with open('test_document.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 插入测试文档到documents表
c.execute(
    'INSERT INTO documents (file_name, file_path, file_size, issuing_unit, remark) VALUES (?, ?, ?, ?, ?)',
    ('test_document.txt', 'test_document.txt', len(content), '测试单位', '测试文档')
)
document_id = c.lastrowid

# 插入内容到file_content_fts表
c.execute(
    'INSERT INTO file_content_fts (content, file_id) VALUES (?, ?)',
    (content, document_id)
)

# 提交事务
conn.commit()

# 测试搜索
print("测试搜索'高质量'：")
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH '高质量';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0]}")

# 测试搜索'高质量发展'：
print("\n测试搜索'高质量发展'：")
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH '高质量发展';")
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0]}")

# 关闭数据库连接
conn.close()

print("\n测试文档已插入并测试搜索功能")
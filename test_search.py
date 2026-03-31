import sqlite3

# 连接数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 查询documents表的内容
print("\ndocuments表内容：")
c.execute('SELECT * FROM documents LIMIT 5;')
rows = c.fetchall()
for row in rows:
    print(f"id: {row[0]}, file_name: {row[1]}")

# 查询file_content_fts表的内容
print("\nfile_content_fts表内容：")
c.execute('SELECT * FROM file_content_fts LIMIT 5;')
rows = c.fetchall()
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0][:100]}...")

# 测试搜索'高质量'
print("\n测试搜索'高质量'：")
# 对搜索词进行分词
import jieba
seg_list = jieba.cut('高质量')
seg_keyword = ' '.join(seg_list)
print(f"分词结果: {seg_keyword}")

# 测试SQL查询
c.execute("SELECT * FROM file_content_fts WHERE file_content_fts MATCH ?;", (seg_keyword,))
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"file_id: {row[1]}, content: {row[0][:100]}...")

# 测试完整的搜索查询
print("\n测试完整的搜索查询：")
sql = '''
    SELECT d.*, MAX(c.name) as category_name 
    FROM documents d
    LEFT JOIN document_categories dc ON d.id = dc.document_id
    LEFT JOIN categories c ON dc.category_id = c.id
    WHERE d.is_delete = 0 AND d.id IN (SELECT file_id FROM file_content_fts WHERE file_content_fts MATCH ?)
    GROUP BY d.id
    ORDER BY d.upload_time DESC 
    LIMIT 10 OFFSET 0
'''
c.execute(sql, (seg_keyword,))
rows = c.fetchall()
print(f"找到 {len(rows)} 条记录")
for row in rows:
    print(f"id: {row[0]}, file_name: {row[1]}")

# 关闭数据库连接
conn.close()
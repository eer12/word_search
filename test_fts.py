import sqlite3

# 连接到数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 测试FTS5搜索
print("测试FTS5搜索:")

# 直接在file_content_fts表上测试
print("\n直接在file_content_fts表上测试:")
test_keywords = ["金融", "上海", "国际"]
for keyword in test_keywords:
    print(f"\n搜索关键词: {keyword}")
    c.execute('SELECT file_id, content FROM file_content_fts WHERE file_content_fts MATCH ?', (keyword,))
    results = c.fetchall()
    print(f"  找到 {len(results)} 个结果")
    for result in results:
        print(f"    文件ID: {result[0]}")

# 测试不同的搜索语法
print("\n测试不同的搜索语法:")
test_queries = [
    "金融",
    "上海",
    "国际金融",
    "金融 OR 上海"
]
for query in test_queries:
    print(f"\n搜索查询: {query}")
    c.execute('SELECT file_id, content FROM file_content_fts WHERE file_content_fts MATCH ?', (query,))
    results = c.fetchall()
    print(f"  找到 {len(results)} 个结果")

# 查看file_content_fts表的完整内容
print("\nfile_content_fts表的完整内容:")
c.execute('SELECT file_id, content FROM file_content_fts')
content = c.fetchone()
if content:
    print(f"文件ID: {content[0]}")
    print(f"内容前200字符: {content[1][:200]}...")

# 关闭连接
conn.close()
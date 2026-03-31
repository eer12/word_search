import sqlite3

# 连接到数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 检查documents表中的数据
print("documents表中的数据:")
c.execute("SELECT id, file_name, upload_time FROM documents")
documents = c.fetchall()
print(f"共 {len(documents)} 个文档")
for doc in documents:
    print(f"  ID: {doc[0]}, 文件名: {doc[1]}, 上传时间: {doc[2]}")

# 检查file_content_fts表中的数据
print("\nfile_content_fts表中的数据:")
c.execute("SELECT file_id, content FROM file_content_fts")
fts_data = c.fetchall()
print(f"共 {len(fts_data)} 条全文检索记录")
for data in fts_data[:3]:  # 只显示前3条
    print(f"  文件ID: {data[0]}, 内容预览: {data[1][:100]}...")

# 测试搜索功能
print("\n测试搜索功能:")
test_keywords = ["星展银行", "郑州市", "金融"]
for keyword in test_keywords:
    print(f"\n搜索关键词: {keyword}")
    c.execute('''
        SELECT DISTINCT documents.id, documents.file_name 
        FROM documents 
        JOIN file_content_fts ON documents.id = file_content_fts.file_id 
        WHERE file_content_fts MATCH ? AND documents.is_delete = 0 
        ORDER BY documents.upload_time DESC
    ''', (keyword,))
    results = c.fetchall()
    print(f"  找到 {len(results)} 个结果")
    for result in results:
        print(f"    ID: {result[0]}, 文件名: {result[1]}")

# 关闭连接
conn.close()
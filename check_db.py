import sqlite3

# 连接到数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 查询file_content_fts表中的所有数据
print("file_content_fts表中的数据：")
c.execute('SELECT rowid, * FROM file_content_fts')
rows = c.fetchall()
for row in rows:
    print(f"Row ID: {row[0]}, Content: {row[1][:200]}..., File ID: {row[2]}")

# 查询documents表中的对应文件信息
print("\ndocuments表中的文件信息：")
c.execute('SELECT id, file_name, file_path FROM documents')
doc_rows = c.fetchall()
for doc_row in doc_rows:
    print(f"ID: {doc_row[0]}, File Name: {doc_row[1]}, File Path: {doc_row[2]}")

# 查询特定行的数据
print("\n查询第14行数据：")
c.execute('SELECT rowid, * FROM file_content_fts WHERE rowid = 14')
row14 = c.fetchone()
if row14:
    print(f"Row ID: {row14[0]}, Content: {row14[1][:500]}..., File ID: {row14[2]}")
else:
    print("未找到第14行数据")

conn.close()
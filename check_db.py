import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'document_search.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 查看file_content_fts表的结构
print("file_content_fts表的结构：")
c.execute('PRAGMA table_info(file_content_fts)')
columns = c.fetchall()
for column in columns:
    print(f"Column ID: {column[0]}, Name: {column[1]}, Type: {column[2]}, Not Null: {column[3]}, Default: {column[4]}, Primary Key: {column[5]}")

# 查询file_content_fts表
print("\nfile_content_fts表中的数据：")
c.execute('SELECT * FROM file_content_fts')
rows = c.fetchall()
print(f"总共有 {len(rows)} 行数据")
for i, row in enumerate(rows):
    print(f"\nRow {i+1}:")
    print(f"  数据: {row}")
    print(f"  长度: {len(row)}")
    for j, value in enumerate(row):
        print(f"  列 {j}: {value}")

# 查询documents表
print("\ndocuments表中的文件信息：")
c.execute('SELECT id, file_name, file_path FROM documents')
doc_rows = c.fetchall()
for doc_row in doc_rows:
    print(f"ID: {doc_row[0]}, File Name: {doc_row[1]}, File Path: {doc_row[2]}")

# 关闭连接
conn.close()
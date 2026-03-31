import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 查询分类表
print("检查分类表结构:")
c.execute("PRAGMA table_info(categories)")
columns = c.fetchall()
for column in columns:
    print(f"列名: {column[1]}, 类型: {column[2]}")

print("\n检查分类数据:")
c.execute("SELECT * FROM categories")
categories = c.fetchall()
if categories:
    print(f"共找到 {len(categories)} 个分类:")
    for category in categories:
        print(f"ID: {category[0]}, 名称: {category[1]}, 描述: {category[2]}")
else:
    print("分类表为空")

# 关闭连接
conn.close()
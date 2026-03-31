import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 测试不同的搜索词
search_terms = [
    "金融委员会办公室",
    "陕金办发〔2025〕90号",
    "各设区市、杨凌示范区",
    "全面贯彻落实中央金融工作会议"
]

print("测试修改后的搜索功能：")
for term in search_terms:
    print(f"\n搜索词: {term}")
    
    # 构建LIKE查询参数
    like_param = '%' + term + '%'
    
    # 执行搜索
    c.execute('SELECT file_id FROM file_content_fts WHERE content LIKE ?', (like_param,))
    results = c.fetchall()
    print(f"匹配到的文件数: {len(results)}")
    if results:
        print(f"文件ID: {[r[0] for r in results]}")

# 关闭连接
conn.close()

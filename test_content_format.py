import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 检查数据库中的实际内容格式
print("检查数据库中的实际内容格式：")
c.execute('SELECT file_id, content FROM file_content_fts LIMIT 1')
result = c.fetchone()

if result:
    file_id, content = result
    print(f"文件ID: {file_id}")
    print(f"内容前500字符: {content[:500]}")
    print(f"内容类型: {type(content)}")
    print(f"内容长度: {len(content)}")
    print(f"是否包含空格: {' ' in content}")
    
    # 测试不同的搜索方式
    test_terms = [
        "金融 委员会 办公室",  # 包含空格的分词形式
        "陕金 办发 〔 2025 〕 90 号",  # 包含空格的分词形式
        "各 设区 市 、 杨凌 示范区",  # 包含空格的分词形式
        "全面 贯彻落实 中央 金融 工作 会议"  # 包含空格的分词形式
    ]
    
    print("\n测试包含空格的搜索词：")
    for term in test_terms:
        like_param = '%' + term + '%'
        c.execute('SELECT file_id FROM file_content_fts WHERE content LIKE ?', (like_param,))
        results = c.fetchall()
        print(f"搜索词: {term} -> 匹配到的文件数: {len(results)}")

# 关闭连接
conn.close()

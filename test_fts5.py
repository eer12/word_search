import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('documents.db')
c = conn.cursor()

# 测试不同的搜索词
search_terms = [
    "包含逗号的句子",
    "包含逗号的句子，",
    "句子。测试",
    "包含逗号和句号的句子，测试"
]

print("测试FTS5 MATCH搜索结果：")
for term in search_terms:
    print(f"\n搜索词: {term}")
    
    # 分词处理
    try:
        import jieba
        seg_list = jieba.cut(term)
        seg_term = ' '.join(seg_list)
        print(f"分词后: {seg_term}")
        
        # 执行搜索
        c.execute('SELECT file_id FROM file_content_fts WHERE file_content_fts MATCH ?', (seg_term,))
        results = c.fetchall()
        print(f"匹配到的文件数: {len(results)}")
        if results:
            print(f"文件ID: {[r[0] for r in results]}")
    except Exception as e:
        print(f"搜索出错: {e}")

# 关闭连接
conn.close()

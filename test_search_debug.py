#!/usr/bin/env python3
"""
测试搜索逻辑，验证为什么"精准滴灌"搜索不到
"""
import sqlite3
import jieba

DB_PATH = 'document_search.db'

def test_search():
    """测试搜索逻辑"""
    keyword = "精准滴灌"
    
    # 对搜索词进行分词
    seg_list = jieba.cut(keyword)
    seg_query = ' '.join(seg_list)
    print(f"搜索词: {keyword}")
    print(f"分词结果: {seg_query}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查数据库中是否有包含"精准滴灌"的内容
    c.execute("SELECT file_id, content FROM file_content_fts WHERE content LIKE ?", ('%' + seg_query + '%',))
    results = c.fetchall()
    print(f"\n使用分词后的查询 '%{seg_query}%' 找到 {len(results)} 条记录")
    
    # 显示前几条结果
    for i, (file_id, content) in enumerate(results[:3]):
        print(f"\n记录 {i+1} (file_id={file_id}):")
        print(f"内容前200字符: {content[:200]}")
    
    # 检查数据库中是否有包含"精准"的内容
    c.execute("SELECT file_id, content FROM file_content_fts WHERE content LIKE ?", ('%精准%',))
    results = c.fetchall()
    print(f"\n\n使用 '%精准%' 找到 {len(results)} 条记录")
    
    # 检查数据库中是否有包含"滴灌"的内容
    c.execute("SELECT file_id, content FROM file_content_fts WHERE content LIKE ?", ('%滴灌%',))
    results = c.fetchall()
    print(f"使用 '%滴灌%' 找到 {len(results)} 条记录")
    
    # 检查数据库中所有内容
    c.execute("SELECT COUNT(*) FROM file_content_fts")
    total = c.fetchone()[0]
    print(f"\n数据库中共有 {total} 条记录")
    
    # 显示一条示例记录
    c.execute("SELECT file_id, content FROM file_content_fts LIMIT 1")
    result = c.fetchone()
    if result:
        file_id, content = result
        print(f"\n示例记录 (file_id={file_id}):")
        print(f"内容前500字符: {content[:500]}")
    
    conn.close()

if __name__ == '__main__':
    test_search()

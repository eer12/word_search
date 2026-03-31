import os
import sqlite3
from datetime import datetime
from app import extract_text_from_wps

# 测试WPS文件上传和文本提取
def test_upload_wps():
    # 选择一个OLE格式的WPS文件进行测试
    wps_file = 'C:\\backup\\wps\\1774954096.434202_关于打造国际化金融服务业开发区的汇报.wps（0807）.wps'
    if not os.path.exists(wps_file):
        print(f"WPS文件不存在: {wps_file}")
        return
    
    print(f"测试WPS文件: {wps_file}")
    
    # 提取文本
    content = extract_text_from_wps(wps_file)
    print(f"\n提取内容长度: {len(content)}")
    print(f"提取内容前300字符: {content[:300]}...")
    print(f"提取内容是否为路径: {'WPS文件:' in content}")
    
    # 检查是否成功提取了有意义的文本
    if 'WPS文件:' in content:
        print("\n❌ 失败: 未能提取到有效文本，只得到了文件路径")
        return
    
    # 模拟上传过程
    filename = os.path.basename(wps_file)
    filepath = wps_file
    file_size = os.path.getsize(wps_file)
    
    # 连接数据库
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    
    # 插入文档信息
    c.execute(
        'INSERT INTO documents (file_name, file_path, file_size, issuing_unit, remark) VALUES (?, ?, ?, ?, ?)',
        (filename, filepath, file_size, '', '')
    )
    document_id = c.lastrowid
    print(f"\n插入文档ID: {document_id}")
    
    # 插入分类关联
    c.execute(
        'INSERT INTO document_categories (document_id, category_id) VALUES (?, ?)',
        (document_id, 1)
    )
    
    # 插入全文检索表
    if content:
        try:
            import jieba
            # 使用jieba进行分词
            seg_list = jieba.cut(content)
            # 将分词结果用空格连接
            seg_content = ' '.join(seg_list)
            print(f"分词后内容长度: {len(seg_content)}")
            print(f"分词后内容前300字符: {seg_content[:300]}...")
            c.execute(
                'INSERT INTO file_content_fts (content, file_id) VALUES (?, ?)',
                (seg_content, document_id)
            )
            print("\n✅ 成功: 文本已提取并存储到数据库")
        except ImportError:
            # 如果jieba未安装，直接使用原内容
            c.execute(
                'INSERT INTO file_content_fts (content, file_id) VALUES (?, ?)',
                (content, document_id)
            )
    
    conn.commit()
    conn.close()
    print("测试完成")

if __name__ == '__main__':
    test_upload_wps()

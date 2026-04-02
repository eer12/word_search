#!/usr/bin/env python3
"""
测试PDF处理功能和日志输出
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_processor import extract_text_from_pdf

def test_pdf_processing():
    """
    测试PDF处理功能和日志输出
    """
    test_pdf_path = 'c:\\Users\\ADMIN\\Documents\\trae_projects\\word_wearch\\test.pdf'
    print(f"=== 测试PDF处理: {test_pdf_path} ===")
    
    content, is_watermark_file, content_valid = extract_text_from_pdf(test_pdf_path)
    
    print(f"测试结果:")
    print(f"内容长度: {len(content) if content else 0}")
    print(f"是否为水印文件: {is_watermark_file}")
    print(f"内容是否有效: {content_valid}")
    print(f"提取的内容: {content}")
    
    # 检查日志文件是否生成
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    log_file = os.path.join(log_dir, 'pdf_processor.log')
    if os.path.exists(log_file):
        print(f"\n日志文件已生成: {log_file}")
        # 读取日志文件内容
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            print("\n日志内容:")
            print(log_content)
    else:
        print(f"\n日志文件未生成: {log_file}")

if __name__ == '__main__':
    test_pdf_processing()

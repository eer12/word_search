#!/usr/bin/env python3
"""
测试IDE环境下的日志输出
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接测试print语句
print("=== 测试print语句输出 ===")
print("这是一条测试print语句")

# 测试logging模块
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
print("\n=== 测试logging模块输出 ===")
logger.info("这是一条测试logger.info语句")
logger.error("这是一条测试logger.error语句")

# 测试PDF处理器
print("\n=== 测试PDF处理器 ===")
test_pdf_path = 'c:\\Users\\ADMIN\\Documents\\trae_projects\\word_wearch\\test.pdf'
print(f"测试PDF路径: {test_pdf_path}")

from pdf_processor import extract_text_from_pdf
print("调用extract_text_from_pdf...")
content, is_watermark_file, content_valid = extract_text_from_pdf(test_pdf_path)

print("\n=== 测试结果 ===")
print(f"内容长度: {len(content) if content else 0}")
print(f"是否为水印文件: {is_watermark_file}")
print(f"内容是否有效: {content_valid}")

print("\n=== 测试完成 ===")

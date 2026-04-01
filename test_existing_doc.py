#!/usr/bin/env python3
# 测试现有doc文件的文本提取功能

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_text_from_doc

# 测试文件路径（使用backup/docx目录下存在的doc文件）
test_file = r"c:\Users\ADMIN\Documents\trae_projects\word_wearch\backup\docx\1775030683.850678_【省调研】金融岛调研汇报8.12.doc"

print("测试现有doc文件文本提取功能...")
print(f"测试文件: {test_file}")

# 检查文件是否存在
if not os.path.exists(test_file):
    print(f"错误: 文件 {test_file} 不存在")
    sys.exit(1)

# 提取文本
try:
    text = extract_text_from_doc(test_file)
    print("\n提取的文本:")
    print("=" * 50)
    print(text)
    print("=" * 50)
    print(f"文本长度: {len(text)} 字符")
    print("测试成功!")
except Exception as e:
    print(f"测试失败: {e}")

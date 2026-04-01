#!/usr/bin/env python3
# 测试doc文件文本提取功能

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_text_from_doc

# 测试文件路径
test_file = "test_document.doc"

# 创建一个简单的测试doc文件（这里我们只是创建一个空文件，实际测试时需要使用真实的doc文件）
# 注意：实际测试时，你需要替换为一个真实的doc文件路径

print("测试doc文件文本提取功能...")
print(f"测试文件: {test_file}")

# 检查文件是否存在
if not os.path.exists(test_file):
    print(f"错误: 文件 {test_file} 不存在，请创建一个测试doc文件")
    print("或者修改test_file变量为一个真实的doc文件路径")
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

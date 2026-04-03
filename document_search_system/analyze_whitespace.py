#!/usr/bin/env python3
"""
分析文本中的空白字符，确定其具体类型
"""

def analyze_text(text):
    """分析文本中的每个字符"""
    print(f"原始文本: {text}")
    print(f"文本长度: {len(text)}")
    print("\n字符分析:")
    
    for i, char in enumerate(text):
        print(f"位置 {i}: '{char}' - 编码: {ord(char)} - 十六进制: {hex(ord(char))}")

    # 特别检查"精准滴 灌"中间的字符
    test_text = "精准滴 灌"
    print(f"\n\n测试文本: {test_text}")
    print("字符分析:")
    for i, char in enumerate(test_text):
        print(f"位置 {i}: '{char}' - 编码: {ord(char)} - 十六进制: {hex(ord(char))}")

    # 测试不同的正则表达式
    import re
    print("\n\n正则表达式测试:")
    
    # 测试各种空白字符处理
    test_cases = [
        (r'\s+', '\s+ (标准空白字符)'),
        (r'[\s\u00A0]', '[\s\u00A0] (标准空白 + 不间断空格)'),
        (r'[\s\u00A0\u2000-\u200A\u2028\u2029]', '扩展空白字符集'),
        (r'\W+', '\W+ (非单词字符)'),
    ]
    
    for pattern, description in test_cases:
        result = re.sub(pattern, 'X', test_text)
        print(f"{description}: {result}")

if __name__ == '__main__':
    # 测试示例
    test_text = "精准滴 灌我区外贸等实体企业"
    analyze_text(test_text)

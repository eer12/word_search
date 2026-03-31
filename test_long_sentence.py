import jieba

# 测试分词处理
test_sentences = [
    "这是一个包含逗号的句子，测试搜索功能。",
    "这是一个包含句号的句子。测试搜索功能",
    "这是一个包含逗号和句号的句子，测试搜索功能。"
]

print("测试分词处理结果：")
for sentence in test_sentences:
    print(f"\n原始句子: {sentence}")
    seg_list = jieba.cut(sentence)
    seg_content = ' '.join(seg_list)
    print(f"分词结果: {seg_content}")
    print(f"是否包含标点符号: {'，' in seg_content or '.' in seg_content or '。' in seg_content}")

# 测试搜索词处理
print("\n\n测试搜索词处理：")
search_terms = [
    "包含逗号的句子，",
    "句子。测试",
    "包含逗号和句号的句子，测试"
]

for term in search_terms:
    print(f"\n原始搜索词: {term}")
    seg_list = jieba.cut(term)
    seg_term = ' '.join(seg_list)
    print(f"分词结果: {seg_term}")

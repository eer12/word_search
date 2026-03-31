import os
import sys

# 测试修复后的WPS文件提取
def test_wps_extraction():
    # 选择出现乱码的WPS文件进行测试
    wps_file = 'C:\\backup\\wps\\1774956119.325876_"十五五"金融怎么干(1).wps'
    if not os.path.exists(wps_file):
        print(f"WPS文件不存在: {wps_file}")
        # 尝试使用其他文件
        wps_files = [f for f in os.listdir('C:\\backup\\wps') if f.endswith('.wps')]
        if wps_files:
            wps_file = os.path.join('C:\\backup\\wps', wps_files[-1])
            print(f"使用备选文件: {wps_file}")
        else:
            print("没有找到WPS文件")
            return
    
    print(f"测试文件: {wps_file}")
    print(f"文件存在: {os.path.exists(wps_file)}")
    print(f"文件大小: {os.path.getsize(wps_file)} 字节")
    
    # 导入extract_text_from_wps函数
    sys.path.insert(0, os.path.dirname(__file__))
    from app import extract_text_from_wps
    
    # 提取文本
    print("\n开始提取文本...")
    content = extract_text_from_wps(wps_file)
    print(f"\n提取内容长度: {len(content)}")
    print(f"提取内容前300字符: {content[:300]}...")
    print(f"提取内容是否为路径: {'WPS文件:' in content}")
    
    # 检查结果
    if 'WPS文件:' in content:
        print("\n❌ 失败: 未能提取到有效文本，只得到了文件路径")
    else:
        print("\n✅ 成功: 成功提取到文本内容")

if __name__ == '__main__':
    test_wps_extraction()

import os
import sys
from app import extract_text_from_wps, WPS_AVAILABLE

# 测试WPS文件提取
def test_wps_extraction():
    # 遍历wps文件夹中的所有文件
    wps_folder = os.path.join('C:\\backup', 'wps')
    if not os.path.exists(wps_folder):
        print(f"WPS文件夹不存在: {wps_folder}")
        return
    
    print(f"WPS库是否可用: {WPS_AVAILABLE}")
    print(f"测试WPS文件提取，文件夹: {wps_folder}")
    
    for filename in os.listdir(wps_folder):
        if filename.endswith('.wps'):
            filepath = os.path.join(wps_folder, filename)
            print(f"\n测试文件: {filename}")
            print(f"文件路径: {filepath}")
            
            # 提取文本
            text = extract_text_from_wps(filepath)
            print(f"提取结果长度: {len(text)}")
            print(f"提取结果前200字符: {text[:200]}...")
            print(f"是否为路径字符串: {'WPS文件:' in text}")

if __name__ == '__main__':
    test_wps_extraction()

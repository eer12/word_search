import olefile
import struct
import os

def analyze_wps_file(filepath):
    """分析WPS文件结构"""
    print(f"分析文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    
    if not olefile.isOleFile(filepath):
        print("不是OLE文件")
        return
    
    ole = olefile.OleFileIO(filepath)
    print(f"文件包含的流: {ole.listdir()}")
    
    # 尝试读取WordDocument流
    if 'WordDocument' in ole.listdir():
        print("\n=== WordDocument流分析 ===")
        stream = ole.openstream('WordDocument')
        data = stream.read()
        print(f"流大小: {len(data)} 字节")
        print(f"前200字节 (hex): {data[:200].hex()}")
        
        # 查找中文字符 (GBK编码的中文字符通常在0xB0-0xF7范围内)
        chinese_chars = []
        i = 0
        while i < len(data) - 1:
            # 尝试GBK解码
            if 0x81 <= data[i] <= 0xFE:
                try:
                    char = data[i:i+2].decode('gbk')
                    if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
                        chinese_chars.append(char)
                        if len(chinese_chars) > 500:
                            break
                    i += 2
                    continue
                except:
                    pass
            i += 1
        
        if chinese_chars:
            print(f"\n提取的中文字符: {''.join(chinese_chars[:200])}")
    
    # 尝试读取1Table或0Table流
    for table_name in ['1Table', '0Table']:
        if table_name in ole.listdir():
            print(f"\n=== {table_name}流分析 ===")
            stream = ole.openstream(table_name)
            data = stream.read()
            print(f"流大小: {len(data)} 字节")
            print(f"前100字节 (hex): {data[:100].hex()}")
    
    # 尝试读取Data流
    if 'Data' in ole.listdir():
        print("\n=== Data流分析 ===")
        stream = ole.openstream('Data')
        data = stream.read()
        print(f"流大小: {len(data)} 字节")
        
        # 尝试查找文本
        try:
            text = data.decode('gbk', errors='ignore')
            # 过滤出可打印字符和中文字符
            import re
            text = re.sub(r'[^\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef\s\w]', '', text)
            if text.strip():
                print(f"GBK解码文本: {text[:500]}")
        except Exception as e:
            print(f"解码失败: {e}")
    
    ole.close()

if __name__ == '__main__':
    # 列出WPS文件夹中的所有文件
    wps_folder = 'C:\\backup\\wps'
    for filename in os.listdir(wps_folder):
        if filename.endswith('.wps'):
            filepath = os.path.join(wps_folder, filename)
            print(f"\n{'='*60}")
            analyze_wps_file(filepath)
            print(f"{'='*60}")

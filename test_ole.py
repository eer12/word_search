import olefile
import os
import sys

# 测试文件
filepath = 'C:\\backup\\wps\\1774954096.434202_关于打造国际化金融服务业开发区的汇报.wps（0807）.wps'

print(f"测试文件: {filepath}", flush=True)
print(f"文件存在: {os.path.exists(filepath)}", flush=True)

try:
    is_ole = olefile.isOleFile(filepath)
    print(f"是否是OLE文件: {is_ole}", flush=True)
    
    if is_ole:
        print("正在打开OLE文件...", flush=True)
        ole = olefile.OleFileIO(filepath)
        streams = ole.listdir()
        print(f"文件包含的流: {streams}", flush=True)
        
        # 尝试从WordDocument流中提取文本
        if 'WordDocument' in streams:
            print("找到WordDocument流，正在读取...", flush=True)
            stream = ole.openstream('WordDocument')
            data = stream.read()
            print(f"WordDocument流大小: {len(data)} 字节", flush=True)
            
            # 查找GBK编码的中文字符
            text_parts = []
            i = 0
            while i < len(data) - 1:
                # GBK编码的中文字符第一个字节在0x81-0xFE范围内
                if 0x81 <= data[i] <= 0xFE:
                    try:
                        char = data[i:i+2].decode('gbk')
                        if '\u4e00' <= char <= '\u9fff':  # 中文字符
                            text_parts.append(char)
                            i += 2
                            continue
                    except:
                        pass
                # 英文和数字
                elif 32 <= data[i] <= 126:
                    text_parts.append(chr(data[i]))
                    i += 1
                    continue
                i += 1
            
            text = ''.join(text_parts)
            print(f"提取的文本长度: {len(text)}", flush=True)
            print(f"提取的文本前200字符: {text[:200]}", flush=True)
        else:
            print("未找到WordDocument流", flush=True)
        
        ole.close()
        print("OLE文件已关闭", flush=True)
    else:
        print("不是OLE文件", flush=True)
except Exception as e:
    print(f"错误: {e}", flush=True)
    import traceback
    traceback.print_exc()
    
print("测试完成", flush=True)

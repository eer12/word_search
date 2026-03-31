"""
WPS文件文本提取模块
支持新旧两种格式的WPS文件：
- 新格式（类似DOCX的ZIP格式）
- 旧格式（OLE格式）
"""

import os
import re
import subprocess
import tempfile

# 尝试导入可选依赖库
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

try:
    import mammoth
    MAMMOTH_AVAILABLE = True
except ImportError:
    MAMMOTH_AVAILABLE = False

try:
    import olefile
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False

try:
    import win32com.client
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False


def extract_text_from_wps(filepath):
    """
    从WPS文件中提取文本内容
    
    尝试多种方法提取文本，按优先级排序：
    1. python-docx（新格式WPS文件）
    2. docx2txt（新格式WPS文件）
    3. mammoth（新格式WPS文件）
    4. olefile（旧格式OLE文件）
    5. antiword（外部工具）
    6. catdoc（外部工具）
    7. pandoc（外部工具）
    8. Windows COM接口（最可靠的方法）
    
    Args:
        filepath: WPS文件路径
        
    Returns:
        提取的文本内容，如果所有方法都失败则返回文件路径字符串
    """
    text = ''
    
    print(f"开始处理WPS文件: {filepath}")
    
    # 方法1: 尝试使用python-docx（新格式WPS文件）
    if DOCX_AVAILABLE:
        try:
            doc = Document(filepath)
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            text = '\n'.join(text_parts)
            if len(text.strip()) > 50:
                print(f"方法1成功: 使用python-docx提取文本，长度: {len(text)}")
                return text
        except Exception as e:
            print(f"方法1失败: python-docx无法处理: {e}")
    else:
        print("方法1: python-docx库未安装")
    
    # 方法2: 尝试使用docx2txt（新格式WPS文件）
    if DOCX2TXT_AVAILABLE:
        try:
            text = docx2txt.process(filepath)
            if len(text.strip()) > 50:
                print(f"方法2成功: 使用docx2txt提取文本，长度: {len(text)}")
                return text
        except Exception as e:
            print(f"方法2失败: docx2txt无法处理: {e}")
    else:
        print("方法2: docx2txt库未安装")
    
    # 方法3: 尝试使用mammoth（新格式WPS文件）
    if MAMMOTH_AVAILABLE:
        try:
            with open(filepath, 'rb') as f:
                result = mammoth.extract_raw_text(f)
                text = result.value
                if len(text.strip()) > 50:
                    print(f"方法3成功: 使用mammoth提取文本，长度: {len(text)}")
                    return text
        except Exception as e:
            print(f"方法3失败: mammoth无法处理: {e}")
    else:
        print("方法3: mammoth库未安装")
    
    # 方法4: 处理OLE格式的WPS文件（旧格式）
    if OLEFILE_AVAILABLE:
        text = _extract_from_ole(filepath)
        if text:
            return text
    else:
        print("方法4: olefile库未安装")
    
    # 方法5: 尝试使用antiword（外部工具）
    try:
        result = subprocess.run(['antiword', filepath], capture_output=True, text=True, timeout=10)
        if result.stdout.strip() and len(result.stdout.strip()) > 50:
            print(f"方法5成功: 使用antiword提取文本，长度: {len(result.stdout)}")
            return result.stdout
    except Exception as e:
        print(f"方法5失败: antiword无法使用: {e}")
    
    # 方法6: 尝试使用catdoc（外部工具）
    try:
        result = subprocess.run(['catdoc', filepath], capture_output=True, text=True, timeout=10)
        if result.stdout.strip() and len(result.stdout.strip()) > 50:
            print(f"方法6成功: 使用catdoc提取文本，长度: {len(result.stdout)}")
            return result.stdout
    except Exception as e:
        print(f"方法6失败: catdoc无法使用: {e}")
    
    # 方法7: 尝试使用pandoc（外部工具）
    try:
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp_name = temp.name
        result = subprocess.run(['pandoc', filepath, '-o', temp_name], capture_output=True, text=True, timeout=10)
        with open(temp_name, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        os.unlink(temp_name)
        if len(text.strip()) > 50:
            print(f"方法7成功: 使用pandoc提取文本，长度: {len(text)}")
            return text
    except Exception as e:
        print(f"方法7失败: pandoc无法使用: {e}")
    
    # 方法8: 使用Windows COM接口（最可靠的方法）
    if WIN32COM_AVAILABLE:
        text = _extract_from_com(filepath)
        if text:
            return text
    else:
        print("方法8: win32com库未安装")
    
    # 所有方法都失败
    print("所有方法都失败，无法提取WPS文件文本")
    return f"WPS文件: {os.path.basename(filepath)}"


def _extract_from_ole(filepath):
    """
    从OLE格式的WPS文件中提取文本
    
    Args:
        filepath: WPS文件路径
        
    Returns:
        提取的文本内容，如果提取失败或质量不佳则返回None
    """
    try:
        if not olefile.isOleFile(filepath):
            print("不是OLE文件")
            return None
            
        ole = olefile.OleFileIO(filepath)
        
        # 获取所有流的列表（处理嵌套列表格式）
        streams = ole.listdir()
        stream_names = [s[0] if isinstance(s, list) else s for s in streams]
        print(f"OLE文件包含的流: {stream_names}")
        
        # 尝试从WordDocument流中提取文本
        if 'WordDocument' not in stream_names:
            print("未找到WordDocument流")
            ole.close()
            return None
            
        print("找到WordDocument流，正在提取文本...")
        stream = ole.openstream('WordDocument')
        data = stream.read()
        print(f"WordDocument流大小: {len(data)} 字节")
        
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
        print(f"从OLE提取的原始文本长度: {len(text)}")
        
        # 清理文本
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(?<![\u4e00-\u9fff])[a-zA-Z](?![\u4e00-\u9fff])', '', text)
        
        # 检查文本质量
        if _check_text_quality(text):
            print(f"方法4成功: 从OLE格式提取文本，长度: {len(text)}")
            ole.close()
            return text
        else:
            print(f"方法4: 提取的文本质量不佳（可能是乱码），尝试其他方法")
            ole.close()
            return None
            
    except Exception as e:
        print(f"方法4失败: OLE处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def _check_text_quality(text):
    """
    检查提取的文本质量
    
    检查条件：
    1. 文本长度 > 50
    2. 中文比例 > 30%
    3. 至少有3组连续的中文字符
    4. 至少有5个标点符号
    5. 乱码字符比例 < 10%
    
    Args:
        text: 待检查的文本
        
    Returns:
        如果文本质量合格返回True，否则返回False
    """
    if len(text.strip()) <= 50:
        return False
    
    total_chars = len(text.strip())
    
    # 检查中文比例
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
    if chinese_ratio <= 0.3:
        return False
    
    # 检查连续中文字符
    consecutive_chinese = len(re.findall(r'[\u4e00-\u9fff]{3,}', text))
    if consecutive_chinese < 3:
        return False
    
    # 检查标点符号
    punctuation_count = len(re.findall(r'[，。！？；：""''（）《》【】、]', text))
    if punctuation_count < 5:
        return False
    
    # 检查乱码字符
    garbled_chars = len(re.findall(r'[欹増擭褢崌膲瞺亯齎蟸豐蛻筽啒遅貜枑枺銐淾刧鷁褃癳鴙悢昩閑嵮媁痵僗軴弸詋孾刄肙蹚魐瀀錧鱊藌頞]', text))
    garbled_ratio = garbled_chars / total_chars if total_chars > 0 else 0
    if garbled_ratio >= 0.1:
        return False
    
    print(f"文本质量检查通过: 中文比例{chinese_ratio:.2%}, 连续中文字符组数{consecutive_chinese}, "
          f"标点符号数{punctuation_count}, 乱码比例{garbled_ratio:.2%}")
    return True


def _extract_from_com(filepath):
    """
    使用Windows COM接口从WPS文件中提取文本
    
    这是最可靠的方法，但需要Windows系统和Microsoft Word
    
    Args:
        filepath: WPS文件路径
        
    Returns:
        提取的文本内容，如果提取失败则返回None
    """
    word_app = None
    doc = None
    
    try:
        print("方法8: 尝试使用Windows COM接口...")
        
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 尝试使用Word应用程序打开WPS文件
        word_app = win32com.client.Dispatch("Word.Application")
        word_app.Visible = False
        word_app.DisplayAlerts = False
        
        print(f"Word应用程序已启动，正在打开文件: {filepath}")
        
        # 打开文档
        doc = word_app.Documents.Open(filepath)
        
        # 提取文本
        text = doc.Content.Text
        
        print(f"成功提取文本，长度: {len(text)}")
        
        # 关闭文档
        try:
            doc.Close(SaveChanges=False)
        except:
            pass
        doc = None
        
        # 退出Word应用
        try:
            word_app.Quit()
        except:
            pass
        word_app = None
        
        # 释放COM
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        
        if len(text.strip()) > 50:
            print(f"方法8成功: 使用Windows COM提取文本，长度: {len(text)}")
            return text
        else:
            return None
            
    except Exception as e:
        print(f"方法8失败: Windows COM无法使用: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 确保资源被释放
        try:
            if doc:
                doc.Close(SaveChanges=False)
        except:
            pass
        try:
            if word_app:
                word_app.Quit()
        except:
            pass
        try:
            pythoncom.CoUninitialize()
        except:
            pass


# 如果直接运行此文件，进行测试
if __name__ == '__main__':
    import sys
    
    # 测试文件路径
    test_file = r'C:\backup\wps\1774956119.325876_"十五五"金融怎么干(1).wps'
    
    if os.path.exists(test_file):
        print(f"测试文件: {test_file}")
        content = extract_text_from_wps(test_file)
        print(f"\n提取结果:\n{content[:500]}...")
    else:
        print(f"测试文件不存在: {test_file}")
        print("请提供有效的WPS文件路径进行测试")

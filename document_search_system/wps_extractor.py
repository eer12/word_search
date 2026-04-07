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
    4. LibreOffice（跨平台，支持新旧格式）
    5. Windows COM接口（最可靠的方法）
    
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
    
    # 方法4: 尝试使用LibreOffice转换为HTML，然后提取文本
    try:
        # 导入LibreOffice转换函数
        from .utils import convert_with_libreoffice, extract_text_from_html
        html_content = convert_with_libreoffice(filepath, 'html')
        if html_content:
            # 从HTML中提取纯文本
            text = extract_text_from_html(html_content)
            if text and len(text.strip()) > 50:
                print(f"方法4成功: 使用LibreOffice提取文本，长度: {len(text)}")
                return text
    except Exception as e:
        print(f"方法4失败: LibreOffice无法使用: {e}")

    # 方法5: 使用Windows COM接口（最可靠的方法）
    if WIN32COM_AVAILABLE:
        text = _extract_from_com(filepath)
        if text:
            return text
    else:
        print("方法5: win32com库未安装")
    
    # 所有方法都失败
    print("所有方法都失败，无法提取WPS文件文本")
    return f"WPS文件: {os.path.basename(filepath)}"





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
        print("方法5: 尝试使用Windows COM接口...")
        
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
            print(f"方法5成功: 使用Windows COM提取文本，长度: {len(text)}")
            return text
        else:
            return None
            
    except Exception as e:
        print(f"方法5失败: Windows COM无法使用: {e}")
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

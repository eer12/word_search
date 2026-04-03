import PyPDF2
from .pdf_ocr import ocr_pdf_file

def check_watermark(text):
    """
    检查文本是否为水印
    
    Args:
        text: 待检查的文本
    
    Returns:
        bool: 是否为水印
    """
    if not text:
        return False
    
    # 检查是否包含水印特征
    watermark_features = [
        '禁止传输涉密文件'
    ]
    
    # 统计水印特征出现的次数
    watermark_count = 0
    for feature in watermark_features:
        watermark_count += text.count(feature)
    
    # 检查是否重复出现相同的水印信息
    lines = text.strip().split('\n')
    unique_lines = set(lines)
    
    # 如果水印特征出现次数较多，或者大部分行都是重复的，认为是水印
    if watermark_count >= 3 or (len(lines) > 3 and len(unique_lines) < len(lines) * 0.3):
        print("检测到水印信息")
        return True
    
    return False

def extract_text_from_pdf(filepath):
    """
    从PDF文件中提取文本
    先尝试使用普通方法读取，失败后使用OCR
    
    Args:
        filepath: PDF文件路径
    
    Returns:
        tuple: (提取的文本, 是否为水印文件, 内容是否有效)
    """
    content = ''
    is_watermark_file = False
    content_valid = True
    
    # 1. 先尝试使用普通方法读取PDF
    print(f"尝试使用普通方法读取PDF文件: {filepath}")
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            if text and len(text.strip()) > 10:
                print(f"普通方法读取成功，提取内容长度: {len(text)}")
                # 检查普通方法读取的数据是否为水印
                is_watermark = check_watermark(text)
                if is_watermark:
                    print("普通方法读取到水印，尝试使用OCR")
                    # 普通方法读取到水印，使用OCR
                    ocr_content = ocr_pdf_file(filepath)
                    if ocr_content and len(ocr_content.strip()) > 10:
                        print(f"OCR识别成功，提取内容长度: {len(ocr_content)}")
                        content = ocr_content
                    else:
                        print("OCR识别也失败")
                        content_valid = False
                else:
                    content = text
            else:
                print("普通方法读取失败，尝试使用OCR")
                # 2. 普通方法失败，使用OCR
                try:
                    ocr_content = ocr_pdf_file(filepath)
                    if ocr_content and len(ocr_content.strip()) > 10:
                        print(f"OCR识别成功，提取内容长度: {len(ocr_content)}")
                        content = ocr_content
                    else:
                        print("OCR识别也失败")
                        content_valid = False
                except Exception as e:
                    print(f"OCR处理失败: {e}")
                    content_valid = False
    except Exception as e:
        print(f"普通方法读取PDF失败: {e}")
        # 普通方法失败，使用OCR
        try:
            ocr_content = ocr_pdf_file(filepath)
            if ocr_content and len(ocr_content.strip()) > 10:
                print(f"OCR识别成功，提取内容长度: {len(ocr_content)}")
                content = ocr_content
            else:
                print("OCR识别也失败")
                content_valid = False
        except Exception as e:
            print(f"OCR处理失败: {e}")
            content_valid = False
    
    # 3. 检查是否只提取到了水印信息
    if content:
        # 处理多余的空格和换行符，确保分词正确
        # 去除连续的空白字符（包括空格、换行符、制表符等），保留单个空格
        import re
        # 首先将所有空白字符替换为普通空格
        content = re.sub(r'[\s\u00A0\u2000-\u200A\u2028\u2029]', ' ', content)
        # 然后去除连续的空格
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 使用check_watermark函数检查是否为水印
        if check_watermark(content):
            print("PDF文件只提取到水印信息")
            content_valid = False
            # 标记为水印文件
            is_watermark_file = True

    return content, is_watermark_file, content_valid

import os
import tempfile
import fitz  # PyMuPDF
import traceback

os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# 尝试导入PaddleOCR
PaddleOCR = None
try:
    from paddleocr import PaddleOCR
except ImportError:
    print("警告: PaddleOCR模块未找到，OCR功能将不可用")

def ocr_pdf_file(pdf_path):
    """
    使用PaddleOCR识别PDF文件中的文本
    """
    print(f"开始OCR识别PDF文件: {pdf_path}")
    try:
        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            print(f"文件不存在: {pdf_path}")
            return ''
        
        # 检查文件大小
        file_size = os.path.getsize(pdf_path)
        print(f"PDF文件大小: {file_size} 字节")
        
        # 检查PaddleOCR是否可用
        if PaddleOCR is None:
            print("错误: PaddleOCR模块未找到，OCR功能不可用")
            return ''
        
        # 初始化PaddleOCR
        print("初始化PaddleOCR...")
        ocr = PaddleOCR(
            use_textline_orientation=True, 
            lang='ch', 
            enable_mkldnn=False,      # <--- 加上这个，强制关闭MKLDNN加速
            det_model_dir=None,  # 使用默认模型
            rec_model_dir=None,  # 使用默认模型
            cls_model_dir=None   # 使用默认模型
        )
        print("PaddleOCR初始化完成")
        
        # 将PDF转换为图像
        print("开始将PDF转换为图像...")
        images = []
        try:
            # 使用PyMuPDF打开PDF文件
            pdf_doc = fitz.open(pdf_path)
            print(f"PDF文件共 {pdf_doc.page_count} 页")
            
            # 遍历每一页
            for page_num in range(pdf_doc.page_count):
                print(f"处理第 {page_num+1} 页...")
                # 获取页面
                page = pdf_doc.load_page(page_num)
                # 1. 定义缩放倍数 (1.0 相当于 72 DPI, 0.5 相当于 36 DPI)
                zoom = 1.0 
                # 2. 创建矩阵对象
                mat = fitz.Matrix(zoom, zoom)
                # 3. 使用矩阵生成图片
                pix = page.get_pixmap(matrix=mat)

                  # 生成临时文件路径
                temp_image_path = tempfile.mktemp(suffix='.jpg')
                # 如果上面没卡死，这里就会打印出来
                print(f"### 临时文件路径: {temp_image_path} ###")
                # 保存图像
                pix.save(temp_image_path)
                images.append((temp_image_path, page_num+1))
            
        except Exception as e:
            print(f"PDF转换失败: {e}")
            traceback.print_exc()
            return ''
        
        # 存储所有页面的识别结果
        all_text = []
        
        # 对每一页进行OCR识别
        for temp_image_path, page_num in images:
            
            try:
                # --- 修改点 1: 使用 predict() 替代 ocr() ---
                result = ocr.predict(temp_image_path)
                print(f"第 {page_num} 页OCR识别完成")
                
                # --- 修改点 2: 适配新的结果格式 ---
                page_text = []
                if result:
                    # 遍历每一页的结果 (result 是一个列表)
                    for page_res in result:
                        # 获取当前页的所有识别文本和坐标
                        rec_texts = page_res.get('rec_texts', [])
                        # 直接将所有文本添加到页面文本列表中
                        page_text.extend(rec_texts)
                
                # 将页面文本添加到总结果中
                all_text.extend(page_text)
                print(f"第 {page_num} 页提取到 {len(page_text)} 行文本")

            except Exception as e:
                print(f"处理第 {page_num} 页时出错: {e}")
                print(f"错误类型: {type(e).__name__}")
            finally:
                # 删除临时文件
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
        #print(f"OCR原始结果: {all_text}")
        # 将所有识别的文本直接连接，不添加空格
        final_text = ''.join(all_text)
        
        # 处理多余的空格和换行符，确保分词正确
        # 去除连续的空白字符（包括空格、换行符、制表符等），保留单个空格
        import re
        # 首先将所有空白字符替换为普通空格
        final_text = re.sub(r'[\s\u00A0\u2000-\u200A\u2028\u2029]', ' ', final_text)
        # 然后去除连续的空格
        final_text = re.sub(r'\s+', ' ', final_text).strip()
        # 在pdf_ocr.py中添加调试信息
        print(f"OCR识别完成，总文本长度: {len(final_text)}")
        print(f"识别结果前400字符: {final_text[:400]}...")
        return final_text
    except Exception as e:
        print(f"OCR识别失败: {e}")
        traceback.print_exc()
        return ''
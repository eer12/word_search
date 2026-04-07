"""
通用工具模块
包含各种辅助函数，如文件转换、文本处理等
"""

import os
import subprocess
import tempfile

def convert_with_libreoffice(filepath, output_format='html'):
    """
    使用LibreOffice将文件转换为指定格式
    
    Args:
        filepath: 输入文件路径
        output_format: 输出格式，默认为html
        
    Returns:
        转换后的文件内容，如果转换失败则返回None
    """
    try:
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 构建输出文件路径
            base_name = os.path.basename(filepath)
            name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(temp_dir, f"{name_without_ext}.{output_format}")
            
            # 构建LibreOffice命令
            # 使用无头模式运行LibreOffice
            if os.name == 'nt':
                # Windows系统
                libreoffice_cmd = 'soffice'
            else:
                # Linux系统
                libreoffice_cmd = 'libreoffice'
            
            cmd = [
                libreoffice_cmd,
                '--headless',
                '--convert-to',
                output_format,
                '--outdir',
                temp_dir,
                filepath
            ]
            
            print(f"执行LibreOffice转换命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"LibreOffice转换输出: {result.stdout}")
            print(f"LibreOffice转换错误: {result.stderr}")
            
            # 检查转换是否成功
            if result.returncode == 0 and os.path.exists(output_file):
                # 读取转换后的文件内容
                with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return content
            else:
                print(f"LibreOffice转换失败，返回码: {result.returncode}")
                return None
    except Exception as e:
        print(f"使用LibreOffice转换文件失败: {e}")
        return None

def extract_text_from_html(html_content):
    """
    从HTML内容中提取纯文本
    
    Args:
        html_content: HTML内容
        
    Returns:
        提取的纯文本
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        print(f"从HTML提取文本失败: {e}")
        return None
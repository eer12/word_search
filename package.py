#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

# 打包脚本

def clean_dist():
    """清理之前的打包文件"""
    dist_dir = 'dist'
    build_dir = 'build'
    egg_info_dir = None
    
    # 查找 egg_info 目录
    for item in os.listdir('.'):
        if item.endswith('.egg-info'):
            egg_info_dir = item
            break
    
    # 删除目录
    if os.path.exists(dist_dir):
        print(f"清理目录: {dist_dir}")
        shutil.rmtree(dist_dir)
    
    if os.path.exists(build_dir):
        print(f"清理目录: {build_dir}")
        shutil.rmtree(build_dir)
    
    if egg_info_dir and os.path.exists(egg_info_dir):
        print(f"清理目录: {egg_info_dir}")
        shutil.rmtree(egg_info_dir)

def update_setup():
    """更新 setup.py 文件"""
    setup_content = """
from setuptools import setup, find_packages
import os

# 打包配置
setup(
    name='document-search-system',
    version='1.0',
    packages=find_packages(),
    url='',
    license='',
    author='',
    author_email='',
    description='文档搜索系统',
    # 包含的文件
    data_files=[
        ('templates', [os.path.join('templates', f) for f in os.listdir('templates') if f.endswith('.html')]),
        ('views', [os.path.join('views', f) for f in os.listdir('views') if f.endswith('.ejs')]),
        ('', ['requirements.txt', 'install.py', 'start.py', 'app.py', 'config.py', 'launch.py', 'launch_gui.py', 'run_production.py', 'wps_extractor.py', 'analyze_wps.py'])
    ],
    # 依赖项
    install_requires=[
        'Flask',
        'PyPDF2',
        'python-docx',
        'pytesseract',
        'Pillow',
        'pdf2image',
        'waitress',
        'jieba',
        'mammoth',
        'olefile',
        'docx2txt',
        'pywin32'
    ],
    # 入口点
    entry_points={
        'console_scripts': [
            'document-search=start:main'
        ]
    }
)
"""
    
    with open('setup.py', 'w', encoding='utf-8') as f:
        f.write(setup_content.strip())
    print("已更新 setup.py 文件")

def run_packaging():
    """执行打包命令"""
    try:
        print("开始打包项目...")
        result = subprocess.run([sys.executable, 'setup.py', 'bdist_wheel'], 
                              capture_output=True, text=True, check=True)
        print("打包成功！")
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("警告:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"打包过程中发生错误: {e}")
        return False

def check_output():
    """检查打包结果"""
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        print("\n打包文件:")
        for item in os.listdir(dist_dir):
            item_path = os.path.join(dist_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path) / (1024 * 1024)  # 转换为 MB
                print(f"- {item} ({size:.2f} MB)")
    else:
        print("未找到打包文件")

def main():
    """主函数"""
    print("=== 文档搜索系统打包脚本 ===")
    
    # 步骤 1: 清理之前的打包文件
    clean_dist()
    
    # 步骤 2: 更新 setup.py 文件
    update_setup()
    
    # 步骤 3: 执行打包命令
    success = run_packaging()
    
    # 步骤 4: 检查打包结果
    if success:
        check_output()
        print("\n打包完成！")
        print("\n使用方法:")
        print("1. 安装包: pip install dist/document_search_system-1.0-py3-none-any.whl")
        print("2. 运行系统: document-search")
    else:
        print("\n打包失败，请检查错误信息")

if __name__ == "__main__":
    main()

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
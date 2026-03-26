from setuptools import setup
import os

# 打包配置
setup(
    name='document-search-system',
    version='1.0',
    packages=[''],
    url='',
    license='',
    author='',
    author_email='',
    description='文档搜索系统',
    # 包含的文件
    data_files=[
        ('templates', [os.path.join('templates', f) for f in os.listdir('templates') if f.endswith('.html')]),
        ('', ['requirements.txt', 'install.py', 'start.py'])
    ],
    # 依赖项
    install_requires=[
        'Flask',
        'PyPDF2',
        'python-docx',
        'mysql-connector-python',
        'pytesseract',
        'Pillow',
        'pdf2image'
    ]
)

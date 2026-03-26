import os

# 系统配置
class Config:
    # 默认上传目录
    UPLOAD_FOLDER = r'F:\backup'
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc', 'wps'}
    
    # MySQL数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'document_search'
    }
    
    # 系统默认设置
    DEFAULT_CATEGORY_ID = 1
    
    # 关键词提取配置
    MIN_KEYWORD_LENGTH = 3
    MAX_KEYWORD_LENGTH = 100
    
    # 文件编码配置
    FILE_ENCODING = 'utf-8'

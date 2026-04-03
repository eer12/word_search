import os
import sys

# 获取应用程序所在目录
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # 打包环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 全局BASE_DIR变量，保持向后兼容
BASE_DIR = get_base_dir()

# 系统配置
class Config:

    # 密码验证配置
    ENABLE_AUTH = True  # 是否启用密码验证
    USER_PASSWORD = 'user123'  # 用户密码
    ADMIN_PASSWORD = 'qk1230'  # 管理员密码
    
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc', 'wps', 'txt', 'xlsx', 'xls'}
    
    # 系统默认设置
    DEFAULT_CATEGORY_ID = 1
    
    # 关键词提取配置
    MIN_KEYWORD_LENGTH = 3
    MAX_KEYWORD_LENGTH = 100
    
    # 文件编码配置
    FILE_ENCODING = 'utf-8'
    
    
    # 动态计算的属性
    @classmethod
    def get_upload_folder(cls):
        return os.path.join(get_base_dir(), 'backup')
    
    @classmethod
    def get_db_path(cls):
        return os.path.join(get_base_dir(), 'document_search.db')
    
    # 确保目录存在
    @classmethod
    def ensure_directories(cls):
        upload_folder = cls.get_upload_folder()
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        if not os.path.exists(os.path.join(get_base_dir(), 'logs')):
            os.makedirs(os.path.join(get_base_dir(), 'logs'))

# 添加类属性，确保向后兼容
Config.UPLOAD_FOLDER = property(lambda self: Config.get_upload_folder())
Config.DB_PATH = property(lambda self: Config.get_db_path())

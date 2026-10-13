import os
import sys
import json

# 获取应用程序所在目录
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # 打包环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 用户设置文件路径
def get_settings_path():
    return os.path.join(get_base_dir(), 'settings.json')

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
        """默认上传目录：安装目录下的 backup 文件夹"""
        return os.path.join(get_base_dir(), 'backup')

    @classmethod
    def get_db_path(cls):
        return os.path.join(get_base_dir(), 'document_search.db')

    @classmethod
    def load_settings(cls):
        """从 settings.json 读取持久化设置，返回上传目录"""
        default = cls.get_upload_folder()
        try:
            path = get_settings_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved = data.get('upload_folder')
                    if saved and os.path.isabs(saved):
                        return saved
        except Exception:
            pass
        return default

    @classmethod
    def save_upload_folder(cls, upload_folder):
        """将上传目录保存到 settings.json"""
        try:
            path = get_settings_path()
            data = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data['upload_folder'] = upload_folder
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # 确保目录存在
    @classmethod
    def ensure_directories(cls):
        upload_folder = cls.load_settings()
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        if not os.path.exists(os.path.join(get_base_dir(), 'logs')):
            os.makedirs(os.path.join(get_base_dir(), 'logs'))

# 全局BASE_DIR变量，保持向后兼容
BASE_DIR = get_base_dir()

# 添加类属性：优先从持久化文件加载，回退到默认值
Config.UPLOAD_FOLDER = Config.load_settings()
Config.DB_PATH = Config.get_db_path()

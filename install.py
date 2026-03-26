import os
import subprocess
import sys
import time
import zipfile
import shutil

# MySQL配置
# 使用相对路径，确保在打包后能正确找到MySQL
MYSQL_INSTALL_PATH = os.path.join(os.getcwd(), "mysql")
MYSQL_DATA_PATH = os.path.join(MYSQL_INSTALL_PATH, "data")
MYSQL_BIN_PATH = os.path.join(MYSQL_INSTALL_PATH, "bin")
MYSQL_PORT = "3306"
MYSQL_ROOT_PASSWORD = "123456"

# 检查本地MySQL
def check_local_mysql():
    print("正在检查本地MySQL...")
    try:
        # 检查MySQL目录是否存在
        if not os.path.exists(MYSQL_INSTALL_PATH):
            print(f"错误: MySQL目录不存在，请确保MySQL在路径: {MYSQL_INSTALL_PATH}")
            return False
        
        # 检查MySQL可执行文件是否存在
        mysql_exe = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
        if not os.path.exists(mysql_exe):
            print("错误: MySQL可执行文件不存在，请确保MySQL安装正确")
            return False
        
        print("本地MySQL检查成功")
        return True
    except Exception as e:
        print(f"检查MySQL失败: {e}")
        return False

# 配置MySQL
def configure_mysql():
    print("正在配置MySQL...")
    try:
        # 初始化数据目录
        if not os.path.exists(MYSQL_DATA_PATH):
            print("初始化MySQL数据目录...")
            init_cmd = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
            subprocess.check_call([init_cmd, "--initialize-insecure"])
            print("数据目录初始化成功")
        
        # 启动MySQL服务
        print("启动MySQL服务...")
        start_cmd = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
        subprocess.Popen([start_cmd, "--console"])
        time.sleep(5)  # 等待服务启动
        print("MySQL服务启动成功")
        
        # 设置root密码
        print("设置MySQL root密码...")
        mysql_cmd = os.path.join(MYSQL_BIN_PATH, "mysql.exe")
        sql_commands = [
            f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{MYSQL_ROOT_PASSWORD}';",
            "FLUSH PRIVILEGES;"
        ]
        for cmd in sql_commands:
            subprocess.check_call([mysql_cmd, "-u", "root", "-p", MYSQL_ROOT_PASSWORD, "-e", cmd])
        print("MySQL配置成功")
        return True
    except Exception as e:
        print(f"MySQL配置失败: {e}")
        return False

# 安装依赖
def install_dependencies():
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装成功")
    except Exception as e:
        print(f"依赖安装失败: {e}")
        return False
    return True

# 初始化数据库
def init_database():
    print("正在初始化数据库...")
    try:
        # 导入应用程序的数据库初始化函数
        import app
        # 修改配置为使用内置MySQL
        app.DB_CONFIG['host'] = 'localhost'
        app.DB_CONFIG['user'] = 'root'
        app.DB_CONFIG['password'] = MYSQL_ROOT_PASSWORD
        app.DB_CONFIG['database'] = 'document_search'
        # 调用初始化函数
        app.init_db()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False
    return True

# 让用户选择安装目录
def select_install_directory():
    print("请选择安装目录:")
    print("1. 默认目录 (当前目录)")
    print("2. 自定义目录")
    choice = input("请输入选择 (1/2): ")
    
    if choice == "1":
        return os.getcwd()
    elif choice == "2":
        custom_dir = input("请输入自定义目录路径: ")
        # 确保目录存在
        if not os.path.exists(custom_dir):
            os.makedirs(custom_dir)
        return custom_dir
    else:
        print("无效选择，使用默认目录")
        return os.getcwd()

# 主安装函数
def main():
    print("=== 文档搜索系统安装程序 ===")
    
    # 让用户选择安装目录
    install_dir = select_install_directory()
    print(f"安装目录: {install_dir}")
    
    # 检查本地MySQL
    if not check_local_mysql():
        print("安装失败，请检查错误信息")
        return False
    
    # 配置MySQL
    if not configure_mysql():
        print("安装失败，请检查错误信息")
        return False
    
    # 安装依赖
    if not install_dependencies():
        print("安装失败，请检查错误信息")
        return False
    
    # 初始化数据库
    if not init_database():
        print("安装失败，请检查错误信息")
        return False
    
    print("\n=== 安装成功 ===")
    print(f"您可以在 {install_dir} 目录中运行 launch.exe 启动应用程序")
    return True

if __name__ == "__main__":
    main()

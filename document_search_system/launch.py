import os
import subprocess
import sys
import time
import traceback

# 获取当前目录
CURRENT_DIR = os.getcwd()

# 确保日志目录存在
LOG_DIR = os.path.join(CURRENT_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, "launch.log")

# 日志函数
def log(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

# MySQL配置
MYSQL_INSTALL_PATH = os.path.join(CURRENT_DIR, "mysql")
MYSQL_BIN_PATH = os.path.join(MYSQL_INSTALL_PATH, "bin")
MYSQL_ROOT_PASSWORD = "123456"

# 应用程序配置
APP_DIR = CURRENT_DIR

# 启动MySQL服务
def start_mysql_service():
    log("正在启动MySQL服务...")
    try:
        # 检查MySQL目录是否存在
        if not os.path.exists(MYSQL_INSTALL_PATH):
            log(f"错误: MySQL目录不存在: {MYSQL_INSTALL_PATH}")
            return False
        
        if not os.path.exists(MYSQL_BIN_PATH):
            log(f"错误: MySQL bin目录不存在: {MYSQL_BIN_PATH}")
            return False
        
        # 检查MySQL可执行文件是否存在
        mysql_cmd = os.path.join(MYSQL_BIN_PATH, "mysql.exe")
        if not os.path.exists(mysql_cmd):
            log(f"错误: mysql.exe不存在: {mysql_cmd}")
            return False
        
        mysqld_cmd = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
        if not os.path.exists(mysqld_cmd):
            log(f"错误: mysqld.exe不存在: {mysqld_cmd}")
            return False
        
        # 检查MySQL是否已启动
        result = subprocess.run([mysql_cmd, "-u", "root", f"--password={MYSQL_ROOT_PASSWORD}", "-e", "SELECT 1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            log("MySQL服务已启动")
            return True
        
        # 启动MySQL服务
        # 使用--initialize-insecure参数初始化数据目录
        log("初始化MySQL数据目录...")
        init_result = subprocess.run([mysqld_cmd, "--initialize-insecure"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if init_result.returncode != 0:
            log(f"初始化数据目录失败: {init_result.stderr}")
        
        # 启动MySQL
        log("启动MySQL服务...")
        subprocess.Popen([mysqld_cmd, "--console"])
        time.sleep(5)  # 等待服务启动
        
        # 再次检查服务是否启动
        result = subprocess.run([mysql_cmd, "-u", "root", f"--password={MYSQL_ROOT_PASSWORD}", "-e", "SELECT 1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            log("MySQL服务启动成功")
            return True
        else:
            log(f"MySQL服务启动失败: {result.stderr}")
            return False
    except Exception as e:
        log(f"启动MySQL服务失败: {e}")
        log(traceback.format_exc())
        return False

# 启动应用程序
def start_app():
    log("正在启动文档搜索系统...")
    try:
        # 导入应用程序
        sys.path.insert(0, APP_DIR)
        log(f"APP_DIR: {APP_DIR}")
        log(f"sys.path: {sys.path}")
        
        # 检查app.py是否存在
        app_path = os.path.join(APP_DIR, "app.py")
        if not os.path.exists(app_path):
            log(f"错误: app.py不存在: {app_path}")
            return False
        
        # 检查run_production.py是否存在
        production_script = os.path.join(APP_DIR, "run_production.py")
        if os.path.exists(production_script):
            # 使用生产环境脚本启动
            log("使用生产环境服务器启动应用...")
            # 导入生产环境脚本并运行
            from . import run_production
        else:
            # 备用方案：直接运行Flask应用
            log("未找到生产环境脚本，使用Flask内置服务器启动...")
            from . import app
            # 修改配置为使用本地MySQL
            app.DB_CONFIG['host'] = 'localhost'
            app.DB_CONFIG['user'] = 'root'
            app.DB_CONFIG['password'] = MYSQL_ROOT_PASSWORD
            app.DB_CONFIG['database'] = 'document_search'
            # 启动应用程序
            log("启动Flask应用...")
            app.app.run(debug=False, port=3000)
    except Exception as e:
        log(f"启动失败: {e}")
        log(traceback.format_exc())
        return False
    return True

# 主函数
def main():
    log("=== 文档搜索系统启动程序 ===")
    log(f"当前目录: {CURRENT_DIR}")
    
    # 启动MySQL服务
    if not start_mysql_service():
        log("启动失败，请检查MySQL服务")
        return
    
    # 启动应用程序
    start_app()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"主函数错误: {e}")
        log(traceback.format_exc())
        # 等待用户按回车键
        input("按回车键退出...")

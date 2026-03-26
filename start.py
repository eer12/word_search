import os
import subprocess
import sys
import time

# MySQL配置
# 使用相对路径，确保在打包后能正确找到MySQL
MYSQL_INSTALL_PATH = os.path.join(os.getcwd(), "mysql")
MYSQL_BIN_PATH = os.path.join(MYSQL_INSTALL_PATH, "bin")
MYSQL_ROOT_PASSWORD = "123456"

# 启动MySQL服务
def start_mysql_service():
    print("正在启动MySQL服务...")
    try:
        # 检查MySQL是否已启动
        mysql_cmd = os.path.join(MYSQL_BIN_PATH, "mysql.exe")
        result = subprocess.run([mysql_cmd, "-u", "root", "-p", MYSQL_ROOT_PASSWORD, "-e", "SELECT 1"], capture_output=True, text=True)
        if result.returncode == 0:
            print("MySQL服务已启动")
            return True
        
        # 启动MySQL服务
        start_cmd = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
        subprocess.Popen([start_cmd, "--console"])
        time.sleep(5)  # 等待服务启动
        
        # 再次检查服务是否启动
        result = subprocess.run([mysql_cmd, "-u", "root", "-p", MYSQL_ROOT_PASSWORD, "-e", "SELECT 1"], capture_output=True, text=True)
        if result.returncode == 0:
            print("MySQL服务启动成功")
            return True
        else:
            print("MySQL服务启动失败")
            return False
    except Exception as e:
        print(f"启动MySQL服务失败: {e}")
        return False

# 启动应用程序
def start_app():
    print("正在启动文档搜索系统...")
    try:
        # 导入应用程序
        import app
        # 修改配置为使用内置MySQL
        app.DB_CONFIG['host'] = 'localhost'
        app.DB_CONFIG['user'] = 'root'
        app.DB_CONFIG['password'] = MYSQL_ROOT_PASSWORD
        app.DB_CONFIG['database'] = 'document_search'
        # 启动应用程序
        app.app.run(debug=False, port=3000)
    except Exception as e:
        print(f"启动失败: {e}")
        return False
    return True

# 主函数
def main():
    print("=== 文档搜索系统启动程序 ===")
    
    # 启动MySQL服务
    if not start_mysql_service():
        print("启动失败，请检查MySQL服务")
        return
    
    # 启动应用程序
    start_app()

if __name__ == "__main__":
    main()

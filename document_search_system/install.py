import os
import subprocess
import sys
import shutil

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
        # 调用初始化函数（使用SQLite）
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
    
    # 安装依赖
    if not install_dependencies():
        print("安装失败，请检查错误信息")
        return False
    
    # 初始化数据库
    if not init_database():
        print("安装失败，请检查错误信息")
        return False
    
    print("\n=== 安装成功 ===")
    print(f"您可以在 {install_dir} 目录中运行 launch.py 启动应用程序")
    return True

if __name__ == "__main__":
    main()

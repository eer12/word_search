import os
import sys
# 运行命令
# python setup.py bdist_wheel
# 启动应用程序
def start_app():
    print("正在启动文档搜索系统...")
    try:
        # 导入应用程序
        from . import app
        # 启动应用程序
        app.app.run(host='0.0.0.0', debug=True, port=3000)
    except Exception as e:
        print(f"启动失败: {e}")
        return False
    return True

# 主函数
def main():
    print("=== 文档搜索系统启动程序 ===")
    
    # 启动应用程序
    start_app()

if __name__ == "__main__":
    main()

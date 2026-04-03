import os
import sys

# 启动应用程序
def start_app():
    print("正在启动文档搜索系统...")
    try:
        # 导入应用程序
        import app
        # 启动应用程序
        app.app.run(debug=False, port=3000)
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

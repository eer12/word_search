import os
import sys

# 添加当前目录到Python搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app

if __name__ == '__main__':
    print("启动生产环境服务器...")
    try:
        # 初始化数据库
        print("初始化数据库...")
        app.init_db()
        print("数据库初始化成功")
        
        # 尝试使用Waitress WSGI服务器
        from waitress import serve
        print("使用Waitress WSGI服务器")
        print("服务地址: http://0.0.0.0:8080")
        # 使用Waitress运行Flask应用
        # host='0.0.0.0'表示监听所有网络接口
        # threads=4表示使用4个线程处理请求
        serve(app.app, host='0.0.0.0', port=8080, threads=4)
    except ImportError:
        # 如果Waitress不可用，回退到Flask内置服务器
        print("Waitress模块不可用，回退到Flask内置服务器")
        print("服务地址: http://0.0.0.0:8080")
        app.app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print(f"启动服务器失败: {e}")
        import traceback
        traceback.print_exc()
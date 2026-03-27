import os
import sys

# 添加当前目录到Python搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app

if __name__ == '__main__':
    print("启动生产环境服务器...")
    try:
        # 尝试使用Waitress WSGI服务器
        from waitress import serve
        print("使用Waitress WSGI服务器")
        print("服务地址: http://0.0.0.0:8082")
        # 使用Waitress运行Flask应用
        # host='0.0.0.0'表示监听所有网络接口
        # port=8082表示使用8082端口
        # threads=4表示使用4个线程处理请求
        serve(app.app, host='0.0.0.0', port=8082, threads=4)
    except ImportError:
        # 如果Waitress不可用，回退到Flask内置服务器
        print("Waitress模块不可用，回退到Flask内置服务器")
        print("服务地址: http://0.0.0.0:8082")
        app.app.run(host='0.0.0.0', port=8082, debug=False)
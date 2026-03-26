from waitress import serve
import app

if __name__ == '__main__':
    print("启动生产环境服务器...")
    print("使用Waitress WSGI服务器")
    print("服务地址: http://0.0.0.0:8080")
    # 使用Waitress运行Flask应用
    # host='0.0.0.0'表示监听所有网络接口
    # port=8080表示使用8080端口
    # threads=4表示使用4个线程处理请求
    serve(app.app, host='0.0.0.0', port=8080, threads=4)
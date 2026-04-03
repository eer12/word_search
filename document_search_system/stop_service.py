import os
import subprocess
import sys
import time

def stop_service():
    """停止文档搜索系统服务"""
    print("正在停止文档搜索系统服务...")
    
    # 检查并停止所有相关进程
    try:
        # 查找Python进程
        print("查找Python进程...")
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, timeout=5)
        
        if 'python.exe' in result.stdout:
            print("发现Python进程，正在停止...")
            # 停止所有Python进程
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            print("Python进程已停止")
        else:
            print("未发现Python进程")
        
        # 检查并停止其他可能的进程
        print("检查其他相关进程...")
        processes = ['waitress-serve.exe', 'flask.exe']
        for process in processes:
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process}'], 
                                  capture_output=True, text=True, timeout=5)
            if process in result.stdout:
                print(f"发现{process}进程，正在停止...")
                subprocess.run(['taskkill', '/F', '/IM', process], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                print(f"{process}进程已停止")
        
        # 检查端口是否已释放
        print("检查端口8080是否已释放...")
        time.sleep(2)
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            if result != 0:
                print("端口8080已释放，服务已停止")
            else:
                print("端口8080仍被占用，可能需要手动停止服务")
        except Exception as e:
            print(f"检查端口时出错: {e}")
            
        print("服务停止完成！")
        
    except Exception as e:
        print(f"停止服务时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    stop_service()
    # 等待用户按任意键退出
    input("按任意键退出...")
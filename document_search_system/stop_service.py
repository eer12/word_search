import os
import subprocess
import sys
import time


def find_pids_on_port(port=8080):
    """查找监听指定端口的进程PID集合"""
    pids = set()
    try:
        result = subprocess.run(['netstat', '-ano'],
                                capture_output=True, text=True, timeout=5)
        suffix = ':' + str(port)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[0].upper() == 'TCP' \
                    and parts[3].upper() == 'LISTENING' \
                    and parts[1].endswith(suffix):
                pid_str = parts[-1]
                if pid_str.isdigit():
                    pids.add(int(pid_str))
    except Exception as e:
        print(f"查询端口监听进程失败: {e}")
    return pids


def stop_service():
    """停止文档搜索系统服务（按8080端口精确定位服务进程）"""
    print("正在停止文档搜索系统服务...")

    # 收集要停止的进程PID：端口监听进程 + PID文件记录的进程
    kill_pids = find_pids_on_port(8080)

    pid_file = None
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        pid_file = os.path.join(base_dir, "server.pid")
        if os.path.exists(pid_file):
            with open(pid_file, "r", encoding="utf-8") as f:
                pid_text = f.read().strip()
            if pid_text.isdigit():
                kill_pids.add(int(pid_text))
    except Exception as e:
        print(f"读取PID文件失败: {e}")

    if not kill_pids:
        print("未发现在8080端口运行的服务进程，服务可能已经停止")
    else:
        for pid in kill_pids:
            if pid == os.getpid():
                continue
            print(f"正在停止服务器进程，PID: {pid}")
            # /T 连同子进程一起结束，/F 强制结束
            result = subprocess.run(
                ['taskkill', '/T', '/F', '/PID', str(pid)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5)
            if result.returncode == 0:
                print(f"进程 {pid} 已停止")
            else:
                print(f"进程 {pid} 停止失败: {result.stderr.strip()}")

    # 清理PID文件
    if pid_file:
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except Exception:
            pass

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


if __name__ == "__main__":
    try:
        stop_service()
    except Exception as e:
        print(f"停止服务时出错: {e}")
        import traceback
        traceback.print_exc()
    # 等待用户按任意键退出
    input("按任意键退出...")

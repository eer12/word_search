import os
import subprocess
import sys
import time
import traceback

# pywebview：用于内嵌浏览器窗口
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

# 获取应用程序所在目录
if getattr(sys, 'frozen', False):
    # 打包环境
    CURRENT_DIR = os.path.dirname(sys.executable)
    if r'AppData\Local\Temp' in CURRENT_DIR:
        if os.path.exists(os.path.join(os.getcwd(), "app.py")):
            CURRENT_DIR = os.getcwd()
        else:
            for root, dirs, files in os.walk(os.getcwd()):
                if "app.py" in files:
                    CURRENT_DIR = root
                    break
else:
    CURRENT_DIR = os.getcwd()

# 确保日志目录存在
LOG_DIR = os.path.join(CURRENT_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, "launch.log")

# 应用程序配置
APP_DIR = CURRENT_DIR

# 服务器以独立进程方式运行时使用的隐藏启动参数
SERVER_ARG = "--run-server"
# Windows 进程创建标志：分离进程 + 新进程组 + 无窗口
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000

# 服务器进程PID记录文件（供停止工具精确定位）
PID_FILE = os.path.join(CURRENT_DIR, "server.pid")
# 服务器运行日志
SERVER_LOG = os.path.join(LOG_DIR, "server.log")


def log(message):
    """写入启动日志"""
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def is_port_open(port=8080):
    """检测端口是否已被监听"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        return sock.connect_ex(('localhost', port)) == 0
    finally:
        sock.close()


def build_child_env():
    """构造子进程环境变量：剔除PyInstaller引导器的内部变量。
    否则子进程（同一exe的第二实例）会复用启动器的 _MEI 临时目录，
    启动器退出时目录因被子进程占用而删除失败，弹出警告框。"""
    child_env = dict(os.environ)
    for key in list(child_env.keys()):
        if key.startswith('_PYI_') or key.startswith('_MEIPASS') \
                or key.startswith('_MEI'):
            child_env.pop(key, None)
    return child_env


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
    except Exception:
        pass
    return pids


def run_server_mode():
    """独立服务器进程入口：运行生产环境服务器，阻塞直到服务退出。
    由启动器以分离进程方式通过 SERVER_ARG 参数拉起，不显示界面。"""
    original_cwd = os.getcwd()
    try:
        os.chdir(APP_DIR)
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass
        log_f = open(SERVER_LOG, "a", encoding="utf-8")
        log_f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"服务器进程启动，PID: {os.getpid()}\n")
        log_f.flush()
        sys.stdout = log_f
        sys.stderr = log_f
        production_script = os.path.join(APP_DIR, "run_production.py")
        if not os.path.exists(production_script) and hasattr(sys, '_MEIPASS'):
            production_script = os.path.join(sys._MEIPASS, "run_production.py")
        import runpy
        runpy.run_path(production_script, run_name='__main__')
    except Exception:
        try:
            traceback.print_exc()
        except Exception:
            pass
    finally:
        try:
            if os.path.exists(PID_FILE):
                with open(PID_FILE, "r", encoding="utf-8") as f:
                    if f.read().strip() == str(os.getpid()):
                        os.remove(PID_FILE)
        except Exception:
            pass
        try:
            os.chdir(original_cwd)
        except Exception:
            pass


class DownloadApi:
    """pywebview JS API：处理内嵌浏览器中的文件下载和新窗口打开。
    在JS中通过 window.pywebview.api.xxx() 调用。"""

    def open_in_new_window(self, url_path):
        """在新的pywebview窗口中打开页面，实现类似多标签页的效果。"""
        try:
            url = f'http://localhost:8080{url_path}'
            webview.create_window(
                title='文档查看',
                url=url,
                width=1000,
                height=700,
                min_size=(600, 400),
                js_api=DownloadApi()
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def download_file(self, file_id, file_name):
        """显示保存对话框，从Flask服务器下载文件并保存到用户选择的位置。"""
        import urllib.request
        import tempfile
        import shutil

        if not file_name:
            file_name = ''
        file_name = str(file_name)

        try:
            ext = os.path.splitext(file_name)[1].lower()
            if ext:
                file_types = (f'文件 (*{ext})',)
            else:
                file_types = ()

            save_path = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=file_name,
                file_types=file_types
            )
            if not save_path:
                return {'success': False, 'error': '用户取消保存'}

            if ext and not save_path.lower().endswith(ext):
                save_path = save_path + ext

            url = f'http://localhost:8080/download-file/{file_id}'
            tmp_path = tempfile.NamedTemporaryFile(delete=False).name
            urllib.request.urlretrieve(url, tmp_path)

            shutil.copy2(tmp_path, save_path)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            return {'success': True, 'path': save_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def launch_server_process():
    """启动服务器进程（非阻塞），返回 Popen 对象或 None（端口已占用）。"""
    if is_port_open(8080):
        log("检测到8080端口已有服务在运行，直接打开浏览器")
        return None

    log("正在启动服务器进程...")
    boot_log = open(os.path.join(LOG_DIR, "server_boot.log"), "ab")
    proc = subprocess.Popen(
        [sys.executable, SERVER_ARG],
        cwd=APP_DIR,
        env=build_child_env(),
        stdin=subprocess.DEVNULL,
        stdout=boot_log,
        stderr=subprocess.STDOUT,
        close_fds=True,
        creationflags=DETACHED_PROCESS
                    | CREATE_NEW_PROCESS_GROUP
                    | CREATE_NO_WINDOW
    )
    boot_log.close()
    log(f"服务器进程已启动，PID: {proc.pid}")
    return proc


def stop_server():
    """停止服务器进程（按端口和PID文件精确定位）"""
    kill_pids = find_pids_on_port(8080)
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r", encoding="utf-8") as f:
                pid_text = f.read().strip()
            if pid_text.isdigit():
                kill_pids.add(int(pid_text))
    except Exception:
        pass
    for pid in kill_pids:
        if pid == os.getpid():
            continue
        try:
            log(f"正在停止服务器进程，PID: {pid}")
            subprocess.run(
                ['taskkill', '/T', '/F', '/PID', str(pid)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5)
        except Exception as e:
            log(f"停止进程 {pid} 失败: {e}")
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass


# 加载页 HTML：启动期间显示进度条，服务器就绪后由 pywebview 跳转到主页
LOADING_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { height:100%; overflow:hidden; }
body {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    background:linear-gradient(135deg,#0d1b2a,#1b4965,#2b6e8c);
    font-family:"Microsoft YaHei","Segoe UI",sans-serif;
}
.logo { width:64px; height:64px; margin-bottom:24px; }
.app-title { color:#fff; font-size:26px; font-weight:600; margin-bottom:8px; }
.app-sub { color:rgba(255,255,255,0.5); font-size:13px; margin-bottom:40px; }
.progress-wrap { width:320px; }
.progress-track {
    height:6px; background:rgba(255,255,255,0.15); border-radius:3px; overflow:hidden;
}
.progress-fill {
    height:100%; width:0%; border-radius:3px;
    background:linear-gradient(90deg,#4fc3f7,#29b6f6);
    transition:width 0.3s ease;
}
.progress-row {
    display:flex; justify-content:space-between; align-items:center;
    margin-top:10px;
}
.progress-pct { color:rgba(255,255,255,0.85); font-size:13px; font-weight:600; }
.progress-msg { color:rgba(255,255,255,0.5); font-size:12px; }
.error-box {
    display:none; margin-top:24px; padding:16px 24px; border-radius:8px;
    background:rgba(244,67,54,0.15); border:1px solid rgba(244,67,54,0.4);
    color:#ef9a9a; font-size:13px; max-width:340px; text-align:center; line-height:1.6;
}
</style>
</head>
<body>
  <svg class="logo" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M6 2h8l4 4v16H6V2z" stroke="#4fc3f7" stroke-width="1.5"
          stroke-linejoin="round" fill="rgba(79,195,247,0.1)"/>
    <path d="M14 2v4h4" stroke="#4fc3f7" stroke-width="1.5"
          stroke-linejoin="round" fill="none"/>
    <path d="M9 11h6M9 14.5h6M9 18h4" stroke="#4fc3f7" stroke-width="1.3"
          stroke-linecap="round"/>
  </svg>
  <div class="app-title">文档本地存储检索工具</div>
  <div class="app-sub">v1.2</div>
  <div class="progress-wrap">
    <div class="progress-track"><div class="progress-fill" id="bar"></div></div>
    <div class="progress-row">
      <span class="progress-msg" id="msg">正在启动服务...</span>
      <span class="progress-pct" id="pct">0%</span>
    </div>
  </div>
  <div class="error-box" id="err"></div>
<script>
function updateProgress(pct, msg) {
    var bar = document.getElementById('bar');
    var pctEl = document.getElementById('pct');
    var msgEl = document.getElementById('msg');
    bar.style.width = pct + '%';
    pctEl.textContent = Math.round(pct) + '%';
    if (msg) msgEl.textContent = msg;
}
function showError(msg) {
    var err = document.getElementById('err');
    err.textContent = msg;
    err.style.display = 'block';
    document.getElementById('bar').style.width = '100%';
    document.getElementById('bar').style.background = '#ef5350';
    document.getElementById('pct').textContent = '启动失败';
    document.getElementById('msg').textContent = '';
}
</script>
</body>
</html>
"""


def main():
    """主入口：启动服务器 → 显示加载页 → 服务器就绪后跳转主页 → 关闭后停止服务器。"""
    if not WEBVIEW_AVAILABLE:
        import tkinter.messagebox as mb
        try:
            mb.showinfo("提示",
                        "pywebview未安装，请用浏览器访问 http://localhost:8080")
        except Exception:
            pass
        return

    # 非阻塞启动服务器进程
    launch_server_process()

    # 先用加载页创建窗口，js_api 绑定到窗口（后续 load_url 切换页面不影响桥接）
    log("正在打开加载页...")
    window = webview.create_window(
        title='文档本地存储检索工具1.2',
        html=LOADING_HTML,
        width=1200,
        height=800,
        min_size=(800, 600),
        js_api=DownloadApi()
    )

    def on_loaded():
        """后台线程：轮询端口、更新进度条，就绪后跳转到主页。"""
        progress = 0
        server_ready = False
        for i in range(150):            # 最多等待 30 秒
            if is_port_open(8080):
                server_ready = True
                break
            progress = min(progress + 1.2, 90)
            try:
                window.evaluate_js(
                    f'updateProgress({progress:.1f}, "正在启动服务...")')
            except Exception:
                pass
            time.sleep(0.2)

        if not server_ready:
            log("服务器启动超时")
            try:
                window.evaluate_js(
                    'showError("服务器启动超时，请检查日志：'
                    + SERVER_LOG.replace('\\', '/') + '")')
            except Exception:
                pass
            time.sleep(5)
            try:
                window.destroy()
            except Exception:
                pass
            return

        # 服务器就绪，进度跳到 100%
        log("服务器启动成功，端口8080已监听，正在加载主页...")
        try:
            window.evaluate_js('updateProgress(100, "加载完成")')
        except Exception:
            pass
        time.sleep(0.4)
        # 跳转到真正的应用页面
        window.load_url('http://localhost:8080')

    # webview.start() 阻塞主线程；func 在后台线程执行端口轮询
    webview.start(func=on_loaded)
    # 窗口关闭后停止服务器
    log("内嵌浏览器窗口已关闭，正在停止服务器...")
    stop_server()


if __name__ == "__main__":
    # 独立服务器进程模式：由主进程以分离进程方式拉起，
    # 不显示界面、不参与单实例锁，直接阻塞运行服务器
    if SERVER_ARG in sys.argv:
        run_server_mode()
        sys.exit(0)

    # 单实例锁：防止重复启动
    import tempfile
    import ctypes

    lock_file = os.path.join(tempfile.gettempdir(), "launch_gui.lock")

    def is_process_running(pid):
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False

    try:
        with open(lock_file, "x") as f:
            f.write(str(os.getpid()))
        main()
    except FileExistsError:
        try:
            with open(lock_file, "r") as f:
                pid_str = f.read().strip()
            pid = int(pid_str)
            if is_process_running(pid):
                import tkinter.messagebox as mb
                try:
                    mb.showinfo("提示", "应用程序已经在运行中")
                except Exception:
                    pass
            else:
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
                main()
        except (ValueError, OSError, Exception):
            try:
                os.remove(lock_file)
            except Exception:
                pass
            main()
    finally:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception:
                pass

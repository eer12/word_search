import os
import subprocess
import sys
import time
import traceback
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

# pywebview：用于内嵌浏览器窗口
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

# 获取应用程序所在目录
if getattr(sys, 'frozen', False):
    # 打包环境
    # 对于PyInstaller打包的应用，sys.executable指向可执行文件
    # 但在某些情况下，它可能指向临时目录中的文件
    # 所以我们需要确保获取的是实际的安装目录
    CURRENT_DIR = os.path.dirname(sys.executable)
    # 检查是否在临时目录中
    if r'AppData\Local\Temp' in CURRENT_DIR:
        # 如果在临时目录中，使用可执行文件的实际目录
        # 对于PyInstaller打包的应用，我们可以通过sys._MEIPASS获取临时目录
        # 但我们需要找到实际的安装目录
        # 尝试从命令行参数中获取安装目录
        import os
        # 检查当前目录是否有app.py文件
        if os.path.exists(os.path.join(os.getcwd(), "app.py")):
            CURRENT_DIR = os.getcwd()
        else:
            # 尝试查找包含app.py的目录
            for root, dirs, files in os.walk(os.getcwd()):
                if "app.py" in files:
                    CURRENT_DIR = root
                    break
else:
    # 开发环境
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
        # 记录服务进程PID，供停止工具定位
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass
        # 该进程无控制台，把输出重定向到日志文件
        log_f = open(SERVER_LOG, "a", encoding="utf-8")
        log_f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"服务器进程启动，PID: {os.getpid()}\n")
        log_f.flush()
        sys.stdout = log_f
        sys.stderr = log_f
        # 定位生产环境脚本：优先安装目录，其次打包内建资源
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
        # 仅清理本进程写入的PID文件
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
                # 子窗口同样挂载JS桥接：保证窗内下载弹原生保存框、
                # 继续查看文件时仍可弹出内嵌窗口而非系统浏览器
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

        # 确保file_name是字符串
        if not file_name:
            file_name = ''
        file_name = str(file_name)

        try:
            # 根据扩展名构造文件类型过滤器
            ext = os.path.splitext(file_name)[1].lower()
            if ext:
                file_types = (f'文件 (*{ext})',)
            else:
                file_types = ()

            # 显示原生保存对话框，预填文件名
            save_path = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=file_name,
                file_types=file_types
            )
            if not save_path:
                return {'success': False, 'error': '用户取消保存'}

            # 确保保存路径有扩展名（用户可能没输入）
            if ext and not save_path.lower().endswith(ext):
                save_path = save_path + ext

            # 从Flask服务器下载文件到临时文件
            url = f'http://localhost:8080/download-file/{file_id}'
            tmp_path = tempfile.NamedTemporaryFile(delete=False).name
            urllib.request.urlretrieve(url, tmp_path)

            # 复制到用户选择的位置
            shutil.copy2(tmp_path, save_path)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            return {'success': True, 'path': save_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class LaunchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("文档搜索系统启动器")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        self.title_label = ttk.Label(self.main_frame, text="文档搜索系统", font=("微软雅黑", 16, "bold"))
        self.title_label.pack(pady=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备启动...")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var, font=("微软雅黑", 12))
        self.status_label.pack(pady=10)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(self.main_frame, width=70, height=15)
        self.log_text.pack(pady=10, fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 按钮框架
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(self.btn_frame, text="启动服务", command=self.start_services, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(self.btn_frame, text="停止服务", command=self.stop_services, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.exit_btn = ttk.Button(self.btn_frame, text="退出", command=self.exit_app, width=15)
        self.exit_btn.pack(side=tk.RIGHT, padx=10)
        
        # 服务进程
        self.app_process = None
        self.running = False
        
        # 自动启动服务
        self.start_services()
    
    def log(self, message):
        """记录日志"""
        try:
            print(message)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
            
            # 更新GUI日志
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            # 防止日志记录导致无限循环
            print(f"日志记录失败: {e}")
    

    
    def start_app_service(self):
        """启动应用程序服务"""
        self.log("正在启动文档搜索系统...")
        try:
            # 检查run_production.py是否存在
            production_script = os.path.join(APP_DIR, "run_production.py")
            self.log(f"检查生产环境脚本: {production_script}")
            if os.path.exists(production_script):
                self.log(f"生产环境脚本存在: {production_script}")
                # 使用生产环境脚本启动
                self.log("使用生产环境服务器启动应用...")
                # 构建启动命令
                # 当应用被打包为可执行文件时，sys.executable指向的是打包后的可执行文件
                # 我们需要找到真实的Python解释器，或者使用不同的方式运行脚本
                if getattr(sys, 'frozen', False):
                    # 可执行文件环境：以“独立分离进程”重新启动自身来运行服务器。
                    # 分离进程不属于启动器，启动器退出（20秒自动关闭）后
                    # 服务器进程仍然存活，http://localhost:8080 可继续访问。
                    if is_port_open(8080):
                        self.log("检测到8080端口已有服务在运行，无需重复启动")
                        self.app_process = None
                        return True
                    self.log("检测到可执行文件环境，以独立后台进程方式启动服务器")
                    boot_log = open(os.path.join(LOG_DIR, "server_boot.log"), "ab")
                    self.app_process = subprocess.Popen(
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
                    self.log(f"服务器进程已启动，PID: {self.app_process.pid}")

                else:
                    # 开发环境
                    python_exe = sys.executable
                    self.log(f"Python解释器: {python_exe}")
                    startup_cmd = [python_exe, production_script]
                    self.log(f"启动命令: {' '.join(startup_cmd)}")
                    self.log(f"工作目录: {APP_DIR}")
                    # 在后台启动应用，捕获输出
                    self.app_process = subprocess.Popen(
                        startup_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=APP_DIR
                    )
                    self.log(f"应用进程已启动，PID: {self.app_process.pid}")
                    # 启动一个线程来读取输出
                    threading.Thread(target=self.read_process_output, args=(self.app_process,)).start()
                
                # 等待服务启动并验证
                self.log("等待应用服务启动...")
                for i in range(30):  # 最多等待30秒
                    time.sleep(1)
                    # 检查进程是否还在运行（仅在非打包环境）
                    if self.app_process is not None:
                        if self.app_process.poll() is not None:
                            self.log(f"应用服务进程已退出，退出码: {self.app_process.returncode}")
                            # 尝试读取剩余的输出
                            try:
                                stdout, stderr = self.app_process.communicate(timeout=2)
                                if stdout:
                                    self.log(f"进程 stdout: {stdout.strip()}")
                                if stderr:
                                    self.log(f"进程 stderr: {stderr.strip()}")
                            except:
                                pass
                            return False
                    # 检查端口是否已监听
                    try:
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', 8080))
                        sock.close()
                        if result == 0:
                            self.log("应用服务启动成功，端口8080已监听")
                            return True
                        else:
                            self.log(f"端口8080未监听，连接结果: {result}")
                    except Exception as e:
                        self.log(f"检查端口时出错: {e}")
                
                self.log("应用服务启动超时，端口8080未监听")
                # 检查进程状态（仅在非打包环境）
                if self.app_process is not None:
                    if self.app_process.poll() is not None:
                        self.log(f"进程已退出，退出码: {self.app_process.returncode}")
                    else:
                        self.log("进程仍在运行，但端口未监听")
                        # 尝试读取输出
                        try:
                            # 非阻塞读取
                            import select
                            rlist, _, _ = select.select([self.app_process.stdout, self.app_process.stderr], [], [], 1)
                            for f in rlist:
                                if f == self.app_process.stdout:
                                    line = f.readline()
                                    if line:
                                        self.log(f"进程 stdout: {line.strip()}")
                                elif f == self.app_process.stderr:
                                    line = f.readline()
                                    if line:
                                        self.log(f"进程 stderr: {line.strip()}")
                        except:
                            pass
                else:
                    self.log("服务器进程未持有句柄，无法检查进程状态")
                return False
            else:
                # 备用方案：直接运行Flask应用
                self.log("未找到生产环境脚本，使用Flask内置服务器启动...")
                app_script = os.path.join(APP_DIR, "app.py")
                self.log(f"检查Flask应用脚本: {app_script}")
                if os.path.exists(app_script):
                    self.log(f"Flask应用脚本存在: {app_script}")
                    # 构建启动命令
                    startup_cmd = [sys.executable, app_script]
                    self.log(f"启动命令: {' '.join(startup_cmd)}")
                    self.log(f"工作目录: {APP_DIR}")
                    # 在后台启动应用，捕获输出
                    self.app_process = subprocess.Popen(
                        startup_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=APP_DIR
                    )
                    self.log(f"应用进程已启动，PID: {self.app_process.pid}")
                    # 启动一个线程来读取输出
                    threading.Thread(target=self.read_process_output, args=(self.app_process,)).start()
                    
                    # 等待服务启动并验证
                    self.log("等待应用服务启动...")
                    for i in range(30):  # 最多等待30秒
                        time.sleep(1)
                        # 检查进程是否还在运行
                        if self.app_process.poll() is not None:
                            self.log(f"应用服务进程已退出，退出码: {self.app_process.returncode}")
                            # 尝试读取剩余的输出
                            try:
                                stdout, stderr = self.app_process.communicate(timeout=2)
                                if stdout:
                                    self.log(f"进程 stdout: {stdout.strip()}")
                                if stderr:
                                    self.log(f"进程 stderr: {stderr.strip()}")
                            except:
                                pass
                            return False
                        # 检查端口是否已监听
                        try:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1)
                            result = sock.connect_ex(('localhost', 8080))
                            sock.close()
                            if result == 0:
                                self.log("应用服务启动成功，端口8080已监听")
                                return True
                            else:
                                self.log(f"端口未监听，连接结果: {result}")
                        except Exception as e:
                            self.log(f"检查端口时出错: {e}")
                    
                    self.log("应用服务启动超时，端口0未监听")
                    # 检查进程状态
                    if self.app_process.poll() is not None:
                        self.log(f"进程已退出，退出码: {self.app_process.returncode}")
                    else:
                        self.log("进程仍在运行，但端口未监听")
                        # 尝试读取输出
                        try:
                            # 非阻塞读取
                            import select
                            rlist, _, _ = select.select([self.app_process.stdout, self.app_process.stderr], [], [], 1)
                            for f in rlist:
                                if f == self.app_process.stdout:
                                    line = f.readline()
                                    if line:
                                        self.log(f"进程 stdout: {line.strip()}")
                                elif f == self.app_process.stderr:
                                    line = f.readline()
                                    if line:
                                        self.log(f"进程 stderr: {line.strip()}")
                        except:
                            pass
                    return False
                else:
                    self.log(f"错误: app.py不存在: {app_script}")
                    return False
        except Exception as e:
            self.log(f"启动应用服务失败: {e}")
            self.log(traceback.format_exc())
            return False
    
    def read_process_output(self, process):
        """读取进程输出"""
        try:
            while process.poll() is None:
                # 读取 stdout
                stdout_line = process.stdout.readline()
                if stdout_line:
                    line = stdout_line.strip()
                    if line:
                        self.log(line)
                # 读取 stderr
                stderr_line = process.stderr.readline()
                if stderr_line:
                    line = stderr_line.strip()
                    if line:
                        self.log(f"错误: {line}")
                # 避免无限循环，添加短暂休眠
                time.sleep(0.1)
            
            # 读取剩余输出
            stdout_remaining = process.stdout.read()
            if stdout_remaining:
                remaining = stdout_remaining.strip()
                if remaining:
                    self.log(remaining)
            stderr_remaining = process.stderr.read()
            if stderr_remaining:
                remaining = stderr_remaining.strip()
                if remaining:
                    self.log(f"错误: {remaining}")
            
            # 检查进程退出码
            if process.returncode != 0:
                self.log(f"应用服务异常退出，退出码: {process.returncode}")
                # 重新启用启动按钮
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("应用服务异常退出"))
        except Exception as e:
            self.log(f"读取进程输出失败: {e}")
            # 避免无限循环，不记录traceback
            self.log("读取进程输出时发生异常")
    
    def start_services(self):
        """启动所有服务"""
        def start_thread():
            try:
                self.status_var.set("正在启动服务...")
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.DISABLED)
                
                # 启动应用服务
                if not self.start_app_service():
                    self.status_var.set("应用服务启动失败")
                    self.start_btn.config(state=tk.NORMAL)
                    return
                
                self.status_var.set("服务启动成功")
                self.log("服务已成功启动，访问地址: http://localhost:8080")
                self.running = True
                self.stop_btn.config(state=tk.NORMAL)

                # 服务器就绪后打开内嵌浏览器窗口
                if WEBVIEW_AVAILABLE:
                    self.log("正在打开内嵌浏览器窗口...")
                    # 在主线程中执行（webview必须在主线程运行）
                    self.root.after(0, self._open_webview)
                else:
                    # pywebview未安装，回退到20秒后自动关闭
                    self.log("pywebview未安装，启动器将在20秒后自动关闭")
                    self.log("请用浏览器访问 http://localhost:8080")
                    def auto_close():
                        self.root.quit()
                    self.root.after(20000, auto_close)
            except Exception as e:
                self.log(f"启动服务失败: {e}")
                self.status_var.set("服务启动异常")
                self.start_btn.config(state=tk.NORMAL)
        
        # 在后台线程中启动服务
        threading.Thread(target=start_thread).start()
    
    def stop_services(self):
        """停止所有服务"""
        def stop_thread():
            self.status_var.set("正在停止服务...")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            
            # 停止应用服务（服务器是独立进程，按端口/PID精确定位，
            # 不能再像以前那样杀掉机器上所有 python.exe）
            stopped = False
            kill_pids = find_pids_on_port(8080)
            # 补充 PID 文件中记录的服务进程
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
                    self.log(f"正在停止服务器进程，PID: {pid}")
                    kill_result = subprocess.run(
                        ['taskkill', '/T', '/F', '/PID', str(pid)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, timeout=5)
                    if kill_result.returncode == 0:
                        stopped = True
                except Exception as e:
                    self.log(f"停止进程 {pid} 失败: {e}")
            # 兜底：终止启动器持有的进程句柄
            if self.app_process and self.app_process.poll() is None:
                try:
                    self.log("终止启动器持有的服务器进程...")
                    self.app_process.terminate()
                    self.app_process.wait(timeout=3)
                    stopped = True
                except Exception:
                    try:
                        self.app_process.kill()
                        self.app_process.wait()
                        stopped = True
                    except Exception:
                        pass
            # 清理PID文件
            try:
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
            except Exception:
                pass

            if stopped:
                self.log("应用服务已停止")
            else:
                self.log("未发现正在运行的应用服务")
            self.status_var.set("服务已停止")
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
        
        # 在后台线程中停止服务
        threading.Thread(target=stop_thread).start()
    
    def _open_webview(self):
        """关闭tkinter窗口，打开pywebview内嵌浏览器窗口。
        webview窗口关闭后，停止服务器再退出。"""
        try:
            # 先隐藏tkinter窗口
            self.root.withdraw()
            # 创建webview窗口，传入JS API用于文件下载
            webview.create_window(
                title='文档本地存储检索工具1.2',
                url='http://localhost:8080',
                width=1200,
                height=800,
                min_size=(800, 600),
                js_api=DownloadApi()
            )
            # webview.start() 阻塞主线程，直到窗口关闭
            webview.start()
            # webview窗口关闭后，停止服务器
            self.log("内嵌浏览器窗口已关闭，正在停止服务器...")
            self._stop_server_process()
            self.root.quit()
        except Exception as e:
            self.log(f"打开内嵌浏览器失败: {e}")
            self.log(traceback.format_exc())
            # 回退：显示tkinter窗口
            self.root.deiconify()

    def _stop_server_process(self):
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
                self.log(f"正在停止服务器进程，PID: {pid}")
                subprocess.run(
                    ['taskkill', '/T', '/F', '/PID', str(pid)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=5)
            except Exception as e:
                self.log(f"停止进程 {pid} 失败: {e}")
        # 兜底：终止启动器持有的进程句柄
        if self.app_process and self.app_process.poll() is None:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=3)
            except Exception:
                try:
                    self.app_process.kill()
                    self.app_process.wait()
                except Exception:
                    pass
        # 清理PID文件
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass

    def exit_app(self):
        """退出应用"""
        # 只关闭启动器窗口，不停止服务：
        # 打包环境中服务运行在独立分离进程里，启动器退出后仍继续提供服务
        self.root.quit()

if __name__ == "__main__":
    # 独立服务器进程模式：由启动器以分离进程方式拉起，
    # 不显示界面、不参与单实例锁，直接阻塞运行服务器
    if SERVER_ARG in sys.argv:
        run_server_mode()
        sys.exit(0)

    # 防止重复启动
    import os
    import tempfile
    import ctypes
    
    # 创建一个锁文件，防止重复启动
    lock_file = os.path.join(tempfile.gettempdir(), "launch_gui.lock")
    
    def is_process_running(pid):
        """检查Windows进程是否存在"""
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except:
            return False
    
    try:
        # 尝试创建锁文件
        with open(lock_file, "x") as f:
            f.write(str(os.getpid()))
        
        # 运行应用
        root = tk.Tk()
        app = LaunchGUI(root)
        root.mainloop()
    except FileExistsError:
        # 如果锁文件已存在，检查是否有正在运行的实例
        try:
            with open(lock_file, "r") as f:
                pid_str = f.read().strip()
            pid = int(pid_str)
            
            # 检查进程是否存在（使用Windows API）
            if is_process_running(pid):
                print("应用程序已经在运行中")
                # 显示提示对话框
                try:
                    import tkinter.messagebox as messagebox
                    messagebox.showinfo("提示", "应用程序已经在运行中")
                except:
                    pass
            else:
                # 进程不存在，删除锁文件并重新启动
                try:
                    os.remove(lock_file)
                except:
                    pass
                # 重新启动应用
                root = tk.Tk()
                app = LaunchGUI(root)
                root.mainloop()
        except (ValueError, OSError, Exception) as e:
            # 读取或检查失败，删除锁文件并重新启动
            try:
                os.remove(lock_file)
            except:
                pass
            # 重新启动应用
            root = tk.Tk()
            app = LaunchGUI(root)
            root.mainloop()
    finally:
        # 退出时删除锁文件
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except:
                pass
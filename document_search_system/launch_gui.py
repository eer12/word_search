import os
import subprocess
import sys
import time
import traceback
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

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
                    # 可执行文件环境
                    self.log("检测到可执行文件环境，使用线程方式运行脚本")
                    # 在打包环境中，直接使用线程方式运行脚本，不依赖外部Python解释器
                    def run_script():
                        try:
                            import runpy
                            import os
                            # 保存原始工作目录
                            original_cwd = os.getcwd()
                            # 设置工作目录为APP_DIR
                            os.chdir(APP_DIR)
                            self.log(f"使用runpy运行脚本: {production_script}")
                            self.log(f"工作目录: {os.getcwd()}")
                            # 运行脚本
                            runpy.run_path(production_script, run_name='__main__')
                            # 恢复原始工作目录
                            os.chdir(original_cwd)
                        except Exception as e:
                            self.log(f"运行脚本失败: {e}")
                            import traceback
                            self.log(traceback.format_exc())
                    # 启动新线程运行脚本
                    threading.Thread(target=run_script, daemon=True).start()
                    # 由于我们在当前进程中运行脚本，没有单独的进程
                    # 所以我们设置app_process为None，使用端口检查来判断服务是否启动
                    self.app_process = None
                    self.log("脚本已在后台线程中启动")

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
                    self.log("打包环境: 脚本在后台线程中运行，无法检查进程状态")
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
                
                # 20秒后自动关闭窗口
                self.log("启动器将在20秒后自动关闭...")
                def auto_close():
                    self.log("自动关闭启动器窗口")
                    self.root.quit()
                
                # 设置20秒定时器
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
            
            # 停止应用服务
            if self.app_process:
                try:
                    self.log("停止应用服务...")
                    self.app_process.terminate()
                    try:
                        self.app_process.wait(timeout=3)
                        self.log("应用服务已停止")
                    except subprocess.TimeoutExpired:
                        self.log("应用服务未响应，强制停止...")
                        self.app_process.kill()
                        self.app_process.wait()
                        self.log("应用服务已强制停止")
                except Exception as e:
                    self.log(f"停止应用服务失败: {e}")
            else:
                # 打包环境，脚本在后台线程中运行
                # 由于使用了daemon=True，主线程退出时后台线程会自动退出
                self.log("打包环境: 应用服务在后台线程中运行，将随主线程退出而停止")
            

            
            # 确保所有相关进程都已停止
            try:
                self.log("检查并清理残留进程...")
                # 查找并停止所有python进程（运行run_production.py或app.py的）
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True, timeout=5)
                if 'python.exe' in result.stdout:
                    self.log("发现残留的Python进程，正在停止...")
                    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            except Exception as e:
                self.log(f"清理残留进程失败: {e}")
            
            self.status_var.set("服务已停止")
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
        
        # 在后台线程中停止服务
        threading.Thread(target=stop_thread).start()
    
    def exit_app(self):
        """退出应用"""
        # 直接退出应用，不停止服务
        # 在打包环境中，服务在后台独立进程中运行，不会随启动器退出而停止
        # 即使在开发环境中，服务在后台线程中运行，使用了daemon=True，主线程退出时后台线程会自动退出
        self.root.quit()

if __name__ == "__main__":
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
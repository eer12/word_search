import os
import subprocess
import sys
import time
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes

# 检查是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# MySQL配置
# 获取当前脚本所在目录
import sys
import os

# 确定MySQL安装路径
if getattr(sys, 'frozen', False):
    # 打包后的环境
    base_dir = os.path.dirname(sys.executable)
    # 检查当前目录下的mysql目录
    MYSQL_INSTALL_PATH = os.path.join(base_dir, "mysql")
    # 如果不存在，检查PyInstaller的临时目录结构
    if not os.path.exists(MYSQL_INSTALL_PATH):
        # 检查当前目录的所有子目录，寻找mysql
        for root, dirs, files in os.walk(base_dir):
            if "mysql" in dirs:
                MYSQL_INSTALL_PATH = os.path.join(root, "mysql")
                break
else:
    # 开发环境
    # 首先检查当前目录下的mysql目录
    MYSQL_INSTALL_PATH = os.path.join(os.getcwd(), "mysql")
    # 如果不存在，检查上级目录
    if not os.path.exists(MYSQL_INSTALL_PATH):
        parent_dir = os.path.dirname(os.getcwd())
        parent_mysql_path = os.path.join(parent_dir, "mysql")
        if os.path.exists(parent_mysql_path):
            MYSQL_INSTALL_PATH = parent_mysql_path

MYSQL_DATA_PATH = os.path.join(MYSQL_INSTALL_PATH, "data")
MYSQL_BIN_PATH = os.path.join(MYSQL_INSTALL_PATH, "bin")
MYSQL_PORT = "3306"
MYSQL_ROOT_PASSWORD = "123456"

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文档搜索系统安装程序")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 设置图标（如果有）
        # self.root.iconbitmap("icon.ico")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        self.title_label = ttk.Label(self.main_frame, text="文档搜索系统安装", font=("微软雅黑", 16, "bold"))
        self.title_label.pack(pady=20)
        
        # 安装目录选择
        self.dir_frame = ttk.LabelFrame(self.main_frame, text="安装目录", padding="10")
        self.dir_frame.pack(fill=tk.X, pady=10)
        
        self.dir_var = tk.StringVar(value=os.getcwd())
        self.dir_entry = ttk.Entry(self.dir_frame, textvariable=self.dir_var, width=50)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.browse_btn = ttk.Button(self.dir_frame, text="浏览...", command=self.browse_directory)
        self.browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=20)
        
        # 状态文本
        self.status_var = tk.StringVar(value="准备安装...")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var, wraplength=550)
        self.status_label.pack(pady=10)
        
        # 按钮框架
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=20)
        
        self.install_btn = ttk.Button(self.btn_frame, text="安装", command=self.start_install, width=15)
        self.install_btn.pack(side=tk.LEFT, padx=10)
        
        self.cancel_btn = ttk.Button(self.btn_frame, text="取消", command=self.root.quit, width=15)
        self.cancel_btn.pack(side=tk.RIGHT, padx=10)
    
    def browse_directory(self):
        dir_path = filedialog.askdirectory(title="选择安装目录", initialdir=os.getcwd())
        if dir_path:
            self.dir_var.set(dir_path)
    
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def check_local_mysql(self):
        self.update_status("正在检查本地MySQL...")
        self.update_progress(10)
        try:
            # 检查MySQL目录是否存在
            if not os.path.exists(MYSQL_INSTALL_PATH):
                self.update_status(f"错误: MySQL目录不存在，请确保MySQL在路径: {MYSQL_INSTALL_PATH}")
                return False
            
            # 检查MySQL可执行文件是否存在
            mysql_exe = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
            if not os.path.exists(mysql_exe):
                self.update_status("错误: MySQL可执行文件不存在，请确保MySQL安装正确")
                return False
            
            self.update_status("本地MySQL检查成功")
            self.update_progress(20)
            return True
        except Exception as e:
            self.update_status(f"检查MySQL失败: {e}")
            return False
    
    def configure_mysql(self):
        self.update_status("正在配置MySQL...")
        self.update_progress(30)
        try:
            # 检查MySQL可执行文件
            mysqld_exe = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
            if not os.path.exists(mysqld_exe):
                self.update_status(f"错误: mysqld.exe不存在于路径: {mysqld_exe}")
                return False
            
            # 初始化数据目录
            if not os.path.exists(MYSQL_DATA_PATH):
                self.update_status("初始化MySQL数据目录...")
                init_cmd = mysqld_exe
                try:
                    result = subprocess.run([init_cmd, "--initialize-insecure"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode != 0:
                        self.update_status(f"初始化数据目录失败: {result.stderr.decode('utf-8', errors='ignore')}")
                        return False
                    self.update_status("数据目录初始化成功")
                except Exception as e:
                    self.update_status(f"初始化数据目录异常: {e}")
                    return False
            
            # 创建my.ini配置文件
            self.update_status("创建MySQL配置文件...")
            my_ini_path = os.path.join(MYSQL_INSTALL_PATH, "my.ini")
            my_ini_content = f"""
[mysqld]
basedir={MYSQL_INSTALL_PATH}
datadir={MYSQL_DATA_PATH}
port={MYSQL_PORT}
character-set-server=utf8mb4
default-storage-engine=INNODB

[client]
port={MYSQL_PORT}
default-character-set=utf8mb4
"""
            try:
                with open(my_ini_path, 'w', encoding='utf-8') as f:
                    f.write(my_ini_content)
                self.update_status("配置文件创建成功")
            except Exception as e:
                self.update_status(f"创建配置文件失败: {e}")
                return False
            
            # 先尝试停止可能存在的MySQL服务
            try:
                mysqladmin_exe = os.path.join(MYSQL_BIN_PATH, "mysqladmin.exe")
                if os.path.exists(mysqladmin_exe):
                    self.update_status("停止正在运行的MySQL服务...")
                    subprocess.run([mysqladmin_exe, "-u", "root", "shutdown"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                    time.sleep(2)
            except Exception as e:
                self.update_status(f"停止服务失败: {e}")
            
            # 卸载可能存在的MySQL服务
            try:
                self.update_status("卸载可能存在的MySQL服务...")
                subprocess.run(["sc", "delete", "MySQL80"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(2)
            except Exception as e:
                self.update_status(f"卸载服务失败: {e}")
            
            # 尝试安装MySQL为Windows服务
            service_installed = False
            self.update_status("安装MySQL为Windows服务...")
            try:
                # 使用完整路径安装服务
                install_result = subprocess.run([mysqld_exe, "--install", "MySQL80", f"--defaults-file={my_ini_path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                if install_result.returncode == 0:
                    self.update_status("服务安装成功")
                    time.sleep(2)
                    # 检查服务是否真的安装成功
                    check_result = subprocess.run(["sc", "query", "MySQL80"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                    if "SERVICE_NAME: MySQL80" in check_result.stdout.decode('utf-8', errors='ignore'):
                        service_installed = True
                        self.update_status("服务已成功注册")
                    else:
                        self.update_status("服务注册失败")
                else:
                    self.update_status(f"安装服务失败: {install_result.stderr.decode('utf-8', errors='ignore')}")
            except Exception as e:
                self.update_status(f"安装服务异常: {e}")
            
            # 启动MySQL
            mysql_running = False
            if service_installed:
                # 尝试启动服务
                self.update_status("启动MySQL服务...")
                try:
                    start_result = subprocess.run(["sc", "start", "MySQL80"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                    if start_result.returncode == 0:
                        self.update_status("服务启动成功")
                    else:
                        self.update_status(f"启动服务失败: {start_result.stderr.decode('utf-8', errors='ignore')}")
                        # 尝试使用net命令启动
                        self.update_status("尝试使用net命令启动服务...")
                        net_result = subprocess.run(["net", "start", "MySQL80"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                        if net_result.returncode == 0:
                            self.update_status("net命令启动成功")
                        else:
                            self.update_status(f"net命令启动失败: {net_result.stderr.decode('utf-8', errors='ignore')}")
                            service_installed = False
                except Exception as e:
                    self.update_status(f"启动服务异常: {e}")
                    service_installed = False
            
            # 如果服务安装失败，尝试直接运行mysqld.exe作为后台进程
            if not service_installed:
                self.update_status("服务安装失败，尝试直接运行mysqld.exe...")
                try:
                    # 直接运行mysqld.exe作为后台进程
                    mysqld_process = subprocess.Popen([mysqld_exe, "--defaults-file={my_ini_path}"], creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_status("mysqld.exe已启动")
                    time.sleep(5)
                    # 检查进程是否在运行
                    if mysqld_process.poll() is None:
                        self.update_status("mysqld.exe进程正在运行")
                        mysql_running = True
                    else:
                        self.update_status("mysqld.exe进程启动失败")
                        return False
                except Exception as e:
                    self.update_status(f"直接运行mysqld.exe异常: {e}")
                    return False
            else:
                # 等待服务启动
                self.update_status("等待服务启动...")
                for i in range(10):
                    time.sleep(1)
                    try:
                        service_status = subprocess.run(["sc", "query", "MySQL80"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                        if "RUNNING" in service_status.stdout.decode('utf-8', errors='ignore'):
                            self.update_status("MySQL服务启动成功")
                            mysql_running = True
                            break
                    except:
                        pass
                    if i == 9:
                        self.update_status("MySQL服务启动失败")
                        return False
            
            if not mysql_running:
                self.update_status("MySQL启动失败")
                return False
            
            # 设置root密码
            self.update_status("设置MySQL root密码...")
            mysql_cmd = os.path.join(MYSQL_BIN_PATH, "mysql.exe")
            if not os.path.exists(mysql_cmd):
                self.update_status(f"错误: mysql.exe不存在于路径: {mysql_cmd}")
                return False
            
            # 由于使用了--initialize-insecure，初始密码为空，所以不需要-p参数
            # 先执行密码设置命令
            password_cmd = f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{MYSQL_ROOT_PASSWORD}';"
            try:
                subprocess.check_call([mysql_cmd, "-u", "root", "-e", password_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                self.update_status(f"设置密码失败: {e}")
                return False
            
            # 密码设置成功后，使用新密码执行FLUSH PRIVILEGES命令
            # 使用--password参数而不是-p，避免交互式密码提示
            flush_cmd = "FLUSH PRIVILEGES;"
            try:
                subprocess.check_call([mysql_cmd, "-u", "root", f"--password={MYSQL_ROOT_PASSWORD}", "-e", flush_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                self.update_status(f"刷新权限失败: {e}")
                return False
            
            self.update_status("MySQL配置成功")
            self.update_progress(40)
            return True
        except Exception as e:
            self.update_status(f"MySQL配置失败: {e}")
            return False
    
    def install_dependencies(self):
        self.update_status("正在安装依赖...")
        self.update_progress(50)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            self.update_status("依赖安装成功")
            self.update_progress(60)
            return True
        except Exception as e:
            self.update_status(f"依赖安装失败: {e}")
            return False
    
    def init_database(self):
        self.update_status("正在初始化数据库...")
        self.update_progress(70)
        try:
            # 导入应用程序的数据库初始化函数
            import sys
            import os
            
            # 添加当前目录到Python搜索路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            # 导入app模块
            import app
            # 修改配置为使用本地MySQL
            app.DB_CONFIG['host'] = 'localhost'
            app.DB_CONFIG['user'] = 'root'
            app.DB_CONFIG['password'] = MYSQL_ROOT_PASSWORD
            app.DB_CONFIG['database'] = 'document_search'
            # 调用初始化函数
            app.init_db()
            self.update_status("数据库初始化成功")
            self.update_progress(80)
            return True
        except Exception as e:
            self.update_status(f"数据库初始化失败: {e}")
            return False
    
    def copy_mysql_to_install_dir(self, install_dir):
        """将MySQL复制到安装目录"""
        self.update_status("正在复制MySQL到安装目录...")
        self.update_progress(25)
        try:
            # 目标MySQL目录
            target_mysql_dir = os.path.join(install_dir, "mysql")
            
            # 如果目标目录存在，先删除
            if os.path.exists(target_mysql_dir):
                shutil.rmtree(target_mysql_dir)
            
            # 找到MySQL源目录
            mysql_source_dir = None
            
            # 1. 首先检查PyInstaller的临时目录（_MEIPASS）
            if getattr(sys, 'frozen', False):
                if hasattr(sys, '_MEIPASS'):
                    meipass_dir = sys._MEIPASS
                    self.update_status(f"检查PyInstaller临时目录: {meipass_dir}")
                    meipass_mysql = os.path.join(meipass_dir, "mysql")
                    if os.path.exists(meipass_mysql):
                        self.update_status(f"在MEIPASS中找到MySQL目录: {meipass_mysql}")
                        mysql_source_dir = meipass_mysql
            
            # 2. 尝试使用全局变量
            if not mysql_source_dir:
                self.update_status(f"检查全局变量路径: {MYSQL_INSTALL_PATH}")
                if os.path.exists(MYSQL_INSTALL_PATH):
                    self.update_status(f"全局变量路径存在: {MYSQL_INSTALL_PATH}")
                    mysql_source_dir = MYSQL_INSTALL_PATH
            
            # 3. 在打包环境中寻找MySQL目录
            if not mysql_source_dir and getattr(sys, 'frozen', False):
                # 获取当前可执行文件的目录
                base_dir = os.path.dirname(sys.executable)
                self.update_status(f"打包环境，检查目录: {base_dir}")
                
                # 直接检查当前目录下的mysql文件夹
                current_mysql = os.path.join(base_dir, "mysql")
                if os.path.exists(current_mysql):
                    self.update_status(f"找到MySQL目录: {current_mysql}")
                    mysql_source_dir = current_mysql
                else:
                    # 检查上级目录
                    parent_dir = os.path.dirname(base_dir)
                    parent_mysql = os.path.join(parent_dir, "mysql")
                    if os.path.exists(parent_mysql):
                        self.update_status(f"找到MySQL目录: {parent_mysql}")
                        mysql_source_dir = parent_mysql
                    else:
                        # 搜索当前目录及其子目录
                        self.update_status("搜索当前目录及其子目录...")
                        for root, dirs, files in os.walk(base_dir):
                            self.update_status(f"搜索目录: {root}")
                            if "mysql" in dirs:
                                mysql_source_dir = os.path.join(root, "mysql")
                                self.update_status(f"找到MySQL目录: {mysql_source_dir}")
                                break
            
            # 4. 开发环境，检查当前目录
            if not mysql_source_dir:
                current_dir = os.getcwd()
                self.update_status(f"开发环境，检查当前目录: {current_dir}")
                dev_mysql_path = os.path.join(current_dir, "mysql")
                if os.path.exists(dev_mysql_path):
                    self.update_status(f"开发环境找到MySQL目录: {dev_mysql_path}")
                    mysql_source_dir = dev_mysql_path
                else:
                    # 检查上级目录
                    parent_dir = os.path.dirname(current_dir)
                    parent_mysql = os.path.join(parent_dir, "mysql")
                    if os.path.exists(parent_mysql):
                        self.update_status(f"开发环境找到MySQL目录: {parent_mysql}")
                        mysql_source_dir = parent_mysql
                
            if not mysql_source_dir:
                self.update_status("错误: 找不到MySQL源目录")
                return None
            
            # 复制MySQL目录
            self.update_status(f"开始复制MySQL从 {mysql_source_dir} 到 {target_mysql_dir}")
            shutil.copytree(mysql_source_dir, target_mysql_dir)
            self.update_status("MySQL复制成功")
            self.update_progress(30)
            return target_mysql_dir
        except Exception as e:
            self.update_status(f"复制MySQL失败: {e}")
            return None
    
    def start_install(self):
        # 禁用按钮
        self.install_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        
        # 获取安装目录
        install_dir = self.dir_var.get()
        self.update_status(f"安装目录: {install_dir}")
        
        # 确保安装目录存在
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
        
        # 复制MySQL到安装目录
        target_mysql_dir = self.copy_mysql_to_install_dir(install_dir)
        if not target_mysql_dir:
            messagebox.showerror("安装失败", "复制MySQL失败，请检查错误信息")
            self.install_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.NORMAL)
            return
        
        # 更新MySQL路径为安装目录中的路径
        global MYSQL_INSTALL_PATH, MYSQL_DATA_PATH, MYSQL_BIN_PATH
        MYSQL_INSTALL_PATH = target_mysql_dir
        MYSQL_DATA_PATH = os.path.join(MYSQL_INSTALL_PATH, "data")
        MYSQL_BIN_PATH = os.path.join(MYSQL_INSTALL_PATH, "bin")
        
        # 检查MySQL
        if not self.check_local_mysql():
            messagebox.showerror("安装失败", "MySQL检查失败，请检查错误信息")
            self.install_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.NORMAL)
            return
        
        # 配置MySQL
        if not self.configure_mysql():
            messagebox.showerror("安装失败", "MySQL配置失败，请检查错误信息")
            self.install_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.NORMAL)
            return
        
        # 初始化数据库
        if not self.init_database():
            messagebox.showerror("安装失败", "数据库初始化失败，请检查错误信息")
            self.install_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.NORMAL)
            return
        
        # 复制必要的文件和文件夹到安装目录
        self.update_status("正在复制应用程序文件到安装目录...")
        self.update_progress(85)
        try:
            # 获取源文件目录
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # 打包环境
                source_dir = sys._MEIPASS
                self.update_status(f"打包环境，源目录: {source_dir}")
            else:
                # 开发环境
                source_dir = os.getcwd()
                self.update_status(f"开发环境，源目录: {source_dir}")
            
            # 复制app.py
            app_py = os.path.join(source_dir, "app.py")
            target_app_py = os.path.join(install_dir, "app.py")
            self.update_status(f"尝试复制app.py: {app_py} -> {target_app_py}")
            if os.path.exists(app_py):
                shutil.copy2(app_py, target_app_py)
                self.update_status("app.py复制成功")
            else:
                self.update_status(f"app.py不存在: {app_py}")
            
            # 复制config.py
            config_py = os.path.join(source_dir, "config.py")
            target_config_py = os.path.join(install_dir, "config.py")
            self.update_status(f"尝试复制config.py: {config_py} -> {target_config_py}")
            if os.path.exists(config_py):
                shutil.copy2(config_py, target_config_py)
                self.update_status("config.py复制成功")
            else:
                self.update_status(f"config.py不存在: {config_py}")
            
            # 复制templates文件夹
            templates_dir = os.path.join(source_dir, "templates")
            target_templates_dir = os.path.join(install_dir, "templates")
            self.update_status(f"尝试复制templates: {templates_dir} -> {target_templates_dir}")
            if os.path.exists(templates_dir):
                if os.path.exists(target_templates_dir):
                    shutil.rmtree(target_templates_dir)
                shutil.copytree(templates_dir, target_templates_dir)
                self.update_status("templates复制成功")
            else:
                self.update_status(f"templates不存在: {templates_dir}")
            
            # 复制launch.exe
            launch_exe = os.path.join(source_dir, "launch.exe")
            target_launch_exe = os.path.join(install_dir, "launch.exe")
            self.update_status(f"尝试复制launch.exe: {launch_exe} -> {target_launch_exe}")
            if os.path.exists(launch_exe):
                shutil.copy2(launch_exe, target_launch_exe)
                self.update_status("launch.exe复制成功")
            else:
                self.update_status(f"launch.exe不存在: {launch_exe}")
            
            # 复制run_production.py
            run_production_py = os.path.join(source_dir, "run_production.py")
            target_run_production_py = os.path.join(install_dir, "run_production.py")
            self.update_status(f"尝试复制run_production.py: {run_production_py} -> {target_run_production_py}")
            if os.path.exists(run_production_py):
                shutil.copy2(run_production_py, target_run_production_py)
                self.update_status("run_production.py复制成功")
            else:
                self.update_status(f"run_production.py不存在: {run_production_py}")
            
            self.update_status("应用程序文件复制成功")
        except Exception as e:
            self.update_status(f"复制应用程序文件失败: {e}")
            import traceback
            self.update_status(f"错误详情: {traceback.format_exc()}")
        
        # 完成安装
        self.update_status("安装成功！")
        self.update_progress(100)
        
        # 显示完成消息
        messagebox.showinfo("安装成功", f"文档搜索系统安装成功！\n您可以在 {install_dir} 目录中运行 launch.exe 启动应用程序")
        
        # 退出程序
        self.root.quit()

def main():
    # 检查是否以管理员权限运行
    if not is_admin():
        # 提示用户需要管理员权限
        messagebox.showerror("需要管理员权限", "安装MySQL服务需要管理员权限，请右键点击setup.exe并选择'以管理员身份运行'来启动安装程序")
        # 退出安装程序
        sys.exit()
    
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

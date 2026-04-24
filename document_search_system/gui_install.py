import os
import subprocess
import sys
import time
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox



class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文档搜索系统安装程序 created by kai qiao")
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
            # 直接创建SQLite数据库和表结构，避免导入app模块导致的套娃问题
            import os
            import sqlite3
            
            # 获取安装目录
            install_dir = self.dir_var.get()
            
            # 构建数据库路径
            db_path = os.path.join(install_dir, 'document_search.db')
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # 创建分类表
            c.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建文档表
            c.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    issuing_unit TEXT DEFAULT '',
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_delete INTEGER DEFAULT 0,
                    remark TEXT DEFAULT ''
                )
            ''')
            
            # 创建文档-分类关联表
            c.execute('''
                CREATE TABLE IF NOT EXISTS document_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    UNIQUE (document_id, category_id)
                )
            ''')
            
            # 创建SQLite全文检索表
            c.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts USING fts5(
                    content,                -- 全文内容
                    file_id,                -- 关联的文档ID
                    tokenize=unicode61  -- 使用unicode61分词器
                )
            ''')
            
            # 创建触发器，在文档删除时同时删除全文检索记录
            c.execute('''
                CREATE TRIGGER IF NOT EXISTS documents_delete_trigger
                AFTER DELETE ON documents
                FOR EACH ROW
                BEGIN
                    DELETE FROM file_content_fts WHERE file_id = OLD.id;
                END
            ''')
            
            # 插入默认分类
            c.execute('SELECT COUNT(*) FROM categories')
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO categories (name, description) VALUES (?, ?)', ('默认分类', '系统默认分类'))
                conn.commit()
            
            conn.commit()
            conn.close()
            
            self.update_status("数据库初始化成功")
            self.update_progress(80)
            return True
        except Exception as e:
            self.update_status(f"数据库初始化失败: {e}")
            import traceback
            self.update_status(f"错误详情: {traceback.format_exc()}")
            return False
    
    def copy_mysql_to_install_dir(self, install_dir):
        """由于使用SQLite，不再需要MySQL"""
        self.update_status("正在准备数据库环境...")
        self.update_progress(25)
        # 由于使用SQLite，不需要复制MySQL
        self.update_status("数据库环境准备完成")
        self.update_progress(30)
        return True
    
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
        
        # 准备数据库环境（使用SQLite，不需要MySQL）
        if not self.copy_mysql_to_install_dir(install_dir):
            messagebox.showerror("安装失败", "数据库环境准备失败，请检查错误信息")
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
            
            # 不再复制launch.exe，只保留launch_gui.exe
            
            # 复制run_production.py
            run_production_py = os.path.join(source_dir, "run_production.py")
            target_run_production_py = os.path.join(install_dir, "run_production.py")
            self.update_status(f"尝试复制run_production.py: {run_production_py} -> {target_run_production_py}")
            if os.path.exists(run_production_py):
                shutil.copy2(run_production_py, target_run_production_py)
                self.update_status("run_production.py复制成功")
            else:
                self.update_status(f"run_production.py不存在: {run_production_py}")
            
            # 复制launch_gui.py
            launch_gui_py = os.path.join(source_dir, "launch_gui.py")
            target_launch_gui_py = os.path.join(install_dir, "launch_gui.py")
            self.update_status(f"尝试复制launch_gui.py: {launch_gui_py} -> {target_launch_gui_py}")
            if os.path.exists(launch_gui_py):
                shutil.copy2(launch_gui_py, target_launch_gui_py)
                self.update_status("launch_gui.py复制成功")
            else:
                self.update_status(f"launch_gui.py不存在: {launch_gui_py}")
            
            # 复制文件检索系统启动程序.exe
            launch_gui_exe = os.path.join(source_dir, "文件检索系统启动程序.exe")
            target_launch_gui_exe = os.path.join(install_dir, "文件检索系统启动程序.exe")
            self.update_status(f"尝试复制文件检索系统启动程序.exe: {launch_gui_exe} -> {target_launch_gui_exe}")
            
            # 尝试多个路径查找文件检索系统启动程序.exe
            launch_gui_found = False
            
            # 1. 检查当前source_dir
            if os.path.exists(launch_gui_exe):
                shutil.copy2(launch_gui_exe, target_launch_gui_exe)
                self.update_status("文件检索系统启动程序.exe复制成功")
                launch_gui_found = True
            else:
                # 2. 检查dist目录
                dist_launch_gui_exe = os.path.join(source_dir, "dist", "文件检索系统启动程序.exe")
                if os.path.exists(dist_launch_gui_exe):
                    shutil.copy2(dist_launch_gui_exe, target_launch_gui_exe)
                    self.update_status("从dist目录复制文件检索系统启动程序.exe成功")
                    launch_gui_found = True
                else:
                    # 3. 检查当前可执行文件所在目录
                    if getattr(sys, 'frozen', False):
                        exe_dir = os.path.dirname(sys.executable)
                        exe_dir_launch_gui = os.path.join(exe_dir, "文件检索系统启动程序.exe")
                        if os.path.exists(exe_dir_launch_gui):
                            shutil.copy2(exe_dir_launch_gui, target_launch_gui_exe)
                            self.update_status("从可执行文件目录复制文件检索系统启动程序.exe成功")
                            launch_gui_found = True
                        else:
                            # 4. 检查上级目录
                            parent_dir = os.path.dirname(exe_dir)
                            parent_launch_gui = os.path.join(parent_dir, "文件检索系统启动程序.exe")
                            if os.path.exists(parent_launch_gui):
                                shutil.copy2(parent_launch_gui, target_launch_gui_exe)
                                self.update_status("从上级目录复制文件检索系统启动程序.exe成功")
                                launch_gui_found = True
                            else:
                                # 5. 检查上级目录的dist目录
                                parent_dist_launch_gui = os.path.join(parent_dir, "dist", "文件检索系统启动程序.exe")
                                if os.path.exists(parent_dist_launch_gui):
                                    shutil.copy2(parent_dist_launch_gui, target_launch_gui_exe)
                                    self.update_status("从上级目录的dist目录复制文件检索系统启动程序.exe成功")
                                    launch_gui_found = True
            
            # 复制关闭文件检索系统.exe
            stop_service_exe = os.path.join(source_dir, "关闭文件检索系统.exe")
            target_stop_service_exe = os.path.join(install_dir, "关闭文件检索系统.exe")
            self.update_status(f"尝试复制关闭文件检索系统.exe: {stop_service_exe} -> {target_stop_service_exe}")
            
            # 尝试多个路径查找关闭文件检索系统.exe
            stop_service_found = False
            
            # 1. 检查当前source_dir
            if os.path.exists(stop_service_exe):
                shutil.copy2(stop_service_exe, target_stop_service_exe)
                self.update_status("关闭文件检索系统.exe复制成功")
                stop_service_found = True
            else:
                # 2. 检查dist目录
                dist_stop_service_exe = os.path.join(source_dir, "dist", "关闭文件检索系统.exe")
                if os.path.exists(dist_stop_service_exe):
                    shutil.copy2(dist_stop_service_exe, target_stop_service_exe)
                    self.update_status("从dist目录复制关闭文件检索系统.exe成功")
                    stop_service_found = True
                else:
                    # 3. 检查当前可执行文件所在目录
                    if getattr(sys, 'frozen', False):
                        exe_dir = os.path.dirname(sys.executable)
                        exe_dir_stop_service = os.path.join(exe_dir, "关闭文件检索系统.exe")
                        if os.path.exists(exe_dir_stop_service):
                            shutil.copy2(exe_dir_stop_service, target_stop_service_exe)
                            self.update_status("从可执行文件目录复制关闭文件检索系统.exe成功")
                            stop_service_found = True
                        else:
                            # 4. 检查上级目录
                            parent_dir = os.path.dirname(exe_dir)
                            parent_stop_service = os.path.join(parent_dir, "关闭文件检索系统.exe")
                            if os.path.exists(parent_stop_service):
                                shutil.copy2(parent_stop_service, target_stop_service_exe)
                                self.update_status("从上级目录复制关闭文件检索系统.exe成功")
                                stop_service_found = True
                            else:
                                # 5. 检查上级目录的dist目录
                                parent_dist_stop_service = os.path.join(parent_dir, "dist", "关闭文件检索系统.exe")
                                if os.path.exists(parent_dist_stop_service):
                                    shutil.copy2(parent_dist_stop_service, target_stop_service_exe)
                                    self.update_status("从上级目录的dist目录复制关闭文件检索系统.exe成功")
                                    stop_service_found = True
            
            if not launch_gui_found:
                self.update_status(f"launch_gui.exe不存在，将创建一个临时启动脚本")
                # 创建一个临时启动脚本
                temp_launch_script = os.path.join(install_dir, "launch_gui.py")
                if os.path.exists(temp_launch_script):
                    self.update_status("使用launch_gui.py作为启动脚本")
                else:
                    self.update_status("警告: launch_gui.py也不存在")
            
            self.update_status("应用程序文件复制成功")
        except Exception as e:
            self.update_status(f"复制应用程序文件失败: {e}")
            import traceback
            self.update_status(f"错误详情: {traceback.format_exc()}")
        
        # 完成安装
        self.update_status("安装成功！")
        self.update_progress(100)
        
        # 显示完成消息
        messagebox.showinfo("安装成功", f"文档搜索系统安装成功！\n您可以在 {install_dir} 目录中运行 文件检索系统启动程序.exe 启动应用程序")
        
        # 退出程序
        self.root.quit()

def main():
    # 不需要管理员权限，直接运行
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

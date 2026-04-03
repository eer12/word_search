#!/usr/bin/env python3
"""
打包脚本，用于程序化记录打包步骤
确保所有必要的文件都被正确包含在安装程序中
"""

import os
import subprocess
import shutil
import sys

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 输出目录
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
# MySQL目录
MYSQL_DIR = os.path.join(PROJECT_ROOT, "mysql")

# 确保输出目录存在
if not os.path.exists(DIST_DIR):
    os.makedirs(DIST_DIR)

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    print(f"执行命令: {' '.join(cmd)}")
    # 不捕获输出，直接输出到控制台
    result = subprocess.run(cmd, cwd=cwd)
    print(f"返回码: {result.returncode}")
    return result

def build_launch_gui():
    """打包launch_gui.py"""
    print("\n=== 打包 launch_gui.py ===")
    # 先清理之前的构建结果
    build_dir = os.path.join(PROJECT_ROOT, "build")
    spec_file = os.path.join(PROJECT_ROOT, "文件检索系统启动程序.spec")
    if os.path.exists(build_dir):
        print("清理build目录")
        shutil.rmtree(build_dir)
    if os.path.exists(spec_file):
        print("删除文件检索系统启动程序.spec文件")
        os.remove(spec_file)
    
    # 检查当前目录
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {PROJECT_ROOT}")
    
    # 准备数据文件参数
    data_files = [
        f"{os.path.join(PROJECT_ROOT, 'app.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'config.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'run_production.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'wps_extractor.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'analyze_wps.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'query_db.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'templates')};templates",
        f"{os.path.join(PROJECT_ROOT, '使用说明.txt')};使用说明.txt",
        f"{os.path.join(PROJECT_ROOT, '使用说明.md')};使用说明.md"
    ]
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "文件检索系统启动程序",
        "--windowed",
        "--collect-all", "tkinter",
        "--collect-all", "tcl",
        "--collect-all", "tk",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "flask",
        "--hidden-import", "PyPDF2",
        "--hidden-import", "docx",
        "--hidden-import", "pytesseract",
        "--hidden-import", "PIL",
        "--hidden-import", "pdf2image",
        "--hidden-import", "waitress",
        "--hidden-import", "sqlite3",
        "--hidden-import", "datetime",
        "--hidden-import", "tempfile",
        "--hidden-import", "subprocess",
        "--hidden-import", "re",
        "--hidden-import", "jieba",
        "--hidden-import", "mammoth",
        "--hidden-import", "olefile",
        "--hidden-import", "docx2txt",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "pythoncom",
        "--hidden-import", "win32com.client"
    ]
    
    # 添加数据文件
    for data_file in data_files:
        cmd.extend(["--add-data", data_file])
    
    # 添加主脚本
    cmd.append(os.path.join(PROJECT_ROOT, "launch_gui.py"))
    # 移除pywpsrpc依赖，因为它不存在
    result = run_command(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("打包 launch_gui.py 失败")
        return False
    
    # 检查文件检索系统启动程序.exe是否生成
    launch_gui_exe = os.path.join(PROJECT_ROOT, "dist", "文件检索系统启动程序.exe")
    print(f"检查文件是否存在: {launch_gui_exe}")
    print(f"文件存在: {os.path.exists(launch_gui_exe)}")
    
    # 列出dist目录内容
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    print("\n=== dist目录内容 ===")
    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            file_path = os.path.join(dist_dir, file)
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"- {file} (大小: {size:.2f} MB)")
    else:
        print("dist目录不存在")
    
    if os.path.exists(launch_gui_exe):
        size = os.path.getsize(launch_gui_exe) / (1024 * 1024)  # MB
        print(f"打包 launch_gui.py 成功，生成文件: {launch_gui_exe} (大小: {size:.2f} MB)")
        return True
    else:
        print(f"打包 launch_gui.py 失败，文件 {launch_gui_exe} 不存在")
        return False

def build_stop_service():
    """打包stop_service.py"""
    print("\n=== 打包 stop_service.py ===")
    # 先清理之前的构建结果
    build_dir = os.path.join(PROJECT_ROOT, "build")
    spec_file = os.path.join(PROJECT_ROOT, "关闭文件检索系统.spec")
    if os.path.exists(build_dir):
        print("清理build目录")
        shutil.rmtree(build_dir)
    if os.path.exists(spec_file):
        print("删除关闭文件检索系统.spec文件")
        os.remove(spec_file)
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "关闭文件检索系统",
        "--console",
        "--hidden-import", "socket"
    ]
    
    # 添加主脚本
    cmd.append(os.path.join(PROJECT_ROOT, "stop_service.py"))
    
    # 检查当前目录
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"构建命令: {' '.join(cmd)}")
    
    # 在项目根目录执行命令
    result = run_command(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("打包 stop_service.py 失败")
        return False
    
    # 检查关闭文件检索系统.exe是否生成
    stop_service_exe = os.path.join(PROJECT_ROOT, "dist", "关闭文件检索系统.exe")
    print(f"检查文件是否存在: {stop_service_exe}")
    print(f"文件存在: {os.path.exists(stop_service_exe)}")
    
    # 列出dist目录内容
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    print("\n=== dist目录内容 ===")
    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            file_path = os.path.join(dist_dir, file)
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"- {file} (大小: {size:.2f} MB)")
    else:
        print("dist目录不存在")
    
    if os.path.exists(stop_service_exe):
        size = os.path.getsize(stop_service_exe) / (1024 * 1024)  # MB
        print(f"打包 stop_service.py 成功，生成文件: {stop_service_exe} (大小: {size:.2f} MB)")
        return True
    else:
        print(f"打包 stop_service.py 失败，文件 {stop_service_exe} 不存在")
        return False

def build_gui_install():
    """打包gui_install.py，包含所有必要的文件"""
    print("\n=== 打包 gui_install.py ===")
    # 先清理之前的构建结果
    build_dir = os.path.join(PROJECT_ROOT, "build")
    spec_file = os.path.join(PROJECT_ROOT, "gui_install.spec")
    if os.path.exists(build_dir):
        print("清理build目录")
        shutil.rmtree(build_dir)
    if os.path.exists(spec_file):
        print("删除gui_install.spec文件")
        os.remove(spec_file)
    
    # 准备数据文件参数
    data_files = [
        f"{os.path.join(PROJECT_ROOT, 'app.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'config.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'run_production.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'launch_gui.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'wps_extractor.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'analyze_wps.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'query_db.py')};.",
        f"{os.path.join(PROJECT_ROOT, 'templates')};templates",
        f"{os.path.join(PROJECT_ROOT, 'requirements.txt')};.",
        f"{os.path.join(PROJECT_ROOT, '使用说明.txt')};使用说明.txt",
        f"{os.path.join(PROJECT_ROOT, '使用说明.md')};使用说明.md"
    ]
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "gui_install",
        "--windowed",
        "--collect-all", "tkinter",
        "--collect-all", "tcl",
        "--collect-all", "tk",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "flask",
        "--hidden-import", "PyPDF2",
        "--hidden-import", "docx",
        "--hidden-import", "pytesseract",
        "--hidden-import", "PIL",
        "--hidden-import", "pdf2image",
        "--hidden-import", "waitress",
        "--hidden-import", "sqlite3",
        "--hidden-import", "datetime",
        "--hidden-import", "tempfile",
        "--hidden-import", "subprocess",
        "--hidden-import", "re",
        "--hidden-import", "jieba",
        "--hidden-import", "mammoth",
        "--hidden-import", "olefile",
        "--hidden-import", "docx2txt",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "pythoncom",
        "--hidden-import", "win32com.client"
    ]
    
    # 添加数据文件
    for data_file in data_files:
        cmd.extend(["--add-data", data_file])
    
    # 添加主脚本
    cmd.append(os.path.join(PROJECT_ROOT, "gui_install.py"))
    
    # 检查当前目录
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"构建命令: {' '.join(cmd)}")
    
    # 在项目根目录执行命令
    result = run_command(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("打包 gui_install.py 失败")
        return False
    
    # 检查gui_install.exe是否生成
    gui_install_exe = os.path.join(PROJECT_ROOT, "dist", "gui_install.exe")
    print(f"检查文件是否存在: {gui_install_exe}")
    print(f"文件存在: {os.path.exists(gui_install_exe)}")
    
    # 列出dist目录内容
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    print("\n=== dist目录内容 ===")
    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            file_path = os.path.join(dist_dir, file)
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"- {file} (大小: {size:.2f} MB)")
    else:
        print("dist目录不存在")
    
    if os.path.exists(gui_install_exe):
        size = os.path.getsize(gui_install_exe) / (1024 * 1024)  # MB
        print(f"打包 gui_install.py 成功，生成文件: {gui_install_exe} (大小: {size:.2f} MB)")
        return True
    else:
        print(f"打包 gui_install.py 失败，文件 {gui_install_exe} 不存在")
        return False

def copy_launch_gui_exe():
    """复制文件检索系统启动程序.exe到dist目录"""
    print("\n=== 复制 文件检索系统启动程序.exe ===")
    # pyinstaller默认输出到dist目录
    src = os.path.join(PROJECT_ROOT, "dist", "文件检索系统启动程序.exe")
    dst = os.path.join(DIST_DIR, "文件检索系统启动程序.exe")
    if os.path.exists(src):
        try:
            shutil.copy2(src, dst)
            print(f"成功复制 文件检索系统启动程序.exe 到 {DIST_DIR}")
            return True
        except PermissionError as e:
            print(f"复制文件时出现权限错误: {e}")
            print("文件可能被其他进程占用，尝试使用不同的方法")
            # 尝试使用不同的方法复制
            try:
                # 先删除目标文件（如果存在）
                if os.path.exists(dst):
                    os.remove(dst)
                # 再次尝试复制
                shutil.copy2(src, dst)
                print(f"成功复制 文件检索系统启动程序.exe 到 {DIST_DIR}")
                return True
            except Exception as e:
                print(f"复制失败: {e}")
                # 即使复制失败，也继续执行，因为文件检索系统启动程序.exe已经在dist目录中
                print("警告: 复制失败，但文件检索系统启动程序.exe已经在dist目录中")
                return True
    else:
        print("文件检索系统启动程序.exe 不存在")
        return False

def verify_build():
    """验证构建结果"""
    print("\n=== 验证构建结果 ===")
    files_to_check = [
        "gui_install.exe",
        "文件检索系统启动程序.exe",
        "关闭文件检索系统.exe"
    ]
    
    all_exist = True
    for file_name in files_to_check:
        file_path = os.path.join(DIST_DIR, file_name)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"✓ {file_name} 存在，大小: {size:.2f} MB")
        else:
            print(f"✗ {file_name} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主函数"""
    print("开始打包文档搜索系统...")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"输出目录: {DIST_DIR}")
    # 由于使用SQLite，不再需要MySQL目录
    
    # 先备份dist目录（如果存在）
    backup_dir = os.path.join(PROJECT_ROOT, "dist_backup")
    if os.path.exists(DIST_DIR):
        print(f"备份dist目录到 {backup_dir}")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(DIST_DIR, backup_dir)    
    # 构建gui_install
    if not build_gui_install():
        return 1
    
    # 构建launch_gui
    if not build_launch_gui():
        return 1
    
    # 构建stop_service
    if not build_stop_service():
        return 1
    
    # 验证构建结果
    if not verify_build():
        return 1
    
    print("\n=== 打包完成 ===")
    print(f"您可以在 {DIST_DIR} 目录中找到以下文件:")
    print("- gui_install.exe: 图形化安装程序（使用SQLite数据库）")
    print("- 文件检索系统启动程序.exe: 图形化启动器")
    print("- 关闭文件检索系统.exe: 服务停止工具")
    print("\n安装步骤:")
    print("1. 运行 gui_install.exe")
    print("2. 选择安装目录")
    print("3. 等待安装完成")
    print("4. 在安装目录中运行 文件检索系统启动程序.exe 启动应用")
    print("5. 若需要停止服务，运行 关闭文件检索系统.exe")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

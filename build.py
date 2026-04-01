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
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
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
    if os.path.exists("build"):
        print("清理build目录")
        shutil.rmtree("build")
    if os.path.exists("launch_gui.spec"):
        print("删除launch_gui.spec文件")
        os.remove("launch_gui.spec")
    
    # 检查当前目录
    print(f"当前工作目录: {os.getcwd()}")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "launch_gui",
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
        "launch_gui.py"
    ]
    # 移除pywpsrpc依赖，因为它不存在
    result = run_command(cmd)
    if result.returncode != 0:
        print("打包 launch_gui.py 失败")
        return False
    
    # 检查launch_gui.exe是否生成
    launch_gui_exe = os.path.join("dist", "launch_gui.exe")
    print(f"检查文件是否存在: {launch_gui_exe}")
    print(f"文件存在: {os.path.exists(launch_gui_exe)}")
    
    # 列出dist目录内容
    print("\n=== dist目录内容 ===")
    if os.path.exists("dist"):
        for file in os.listdir("dist"):
            print(f"- {file}")
    else:
        print("dist目录不存在")
    
    if os.path.exists(launch_gui_exe):
        print(f"打包 launch_gui.py 成功，生成文件: {launch_gui_exe}")
        return True
    else:
        print(f"打包 launch_gui.py 失败，文件 {launch_gui_exe} 不存在")
        return False

def build_gui_install():
    """打包gui_install.py，包含所有必要的文件"""
    print("\n=== 打包 gui_install.py ===")
    # 先清理之前的构建结果
    if os.path.exists("build"):
        print("清理build目录")
        shutil.rmtree("build")
    if os.path.exists("gui_install.spec"):
        print("删除gui_install.spec文件")
        os.remove("gui_install.spec")
    
    # 准备数据文件参数
    data_files = [
        f"app.py;.",
        f"config.py;.",
        f"run_production.py;.",
        f"launch_gui.py;.",
        f"wps_extractor.py;.",
        f"analyze_wps.py;.",
        f"query_db.py;.",
        f"templates;templates",
        f"requirements.txt;."
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
        "--hidden-import", "win32con"
    ]
    
    # 添加数据文件
    for data_file in data_files:
        cmd.extend(["--add-data", data_file])
    
    # 添加主脚本
    cmd.append("gui_install.py")
    
    # 检查当前目录
    print(f"当前工作目录: {os.getcwd()}")
    print(f"构建命令: {' '.join(cmd)}")
    
    result = run_command(cmd)
    if result.returncode != 0:
        print("打包 gui_install.py 失败")
        return False
    
    # 检查gui_install.exe是否生成
    gui_install_exe = os.path.join("dist", "gui_install.exe")
    print(f"检查文件是否存在: {gui_install_exe}")
    print(f"文件存在: {os.path.exists(gui_install_exe)}")
    
    # 列出dist目录内容
    print("\n=== dist目录内容 ===")
    if os.path.exists("dist"):
        for file in os.listdir("dist"):
            file_path = os.path.join("dist", file)
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
    """复制launch_gui.exe到dist目录"""
    print("\n=== 复制 launch_gui.exe ===")
    # pyinstaller默认输出到dist目录
    src = os.path.join("dist", "launch_gui.exe")
    dst = os.path.join(DIST_DIR, "launch_gui.exe")
    if os.path.exists(src):
        try:
            shutil.copy2(src, dst)
            print(f"成功复制 launch_gui.exe 到 {DIST_DIR}")
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
                print(f"成功复制 launch_gui.exe 到 {DIST_DIR}")
                return True
            except Exception as e:
                print(f"复制失败: {e}")
                # 即使复制失败，也继续执行，因为launch_gui.exe已经在dist目录中
                print("警告: 复制失败，但launch_gui.exe已经在dist目录中")
                return True
    else:
        print("launch_gui.exe 不存在")
        return False

def verify_build():
    """验证构建结果"""
    print("\n=== 验证构建结果 ===")
    files_to_check = [
        "gui_install.exe",
        "launch_gui.exe"
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
    
    # 构建launch_gui
    if not build_launch_gui():
        return 1
    
    # 备份launch_gui.exe
    launch_gui_exe = os.path.join(DIST_DIR, "launch_gui.exe")
    if os.path.exists(launch_gui_exe):
        backup_launch_gui = os.path.join(PROJECT_ROOT, "launch_gui.exe.backup")
        print(f"备份launch_gui.exe到 {backup_launch_gui}")
        shutil.copy2(launch_gui_exe, backup_launch_gui)
    
    # 构建gui_install
    if not build_gui_install():
        return 1
    
    # 恢复launch_gui.exe
    backup_launch_gui = os.path.join(PROJECT_ROOT, "launch_gui.exe.backup")
    if os.path.exists(backup_launch_gui):
        print(f"恢复launch_gui.exe")
        shutil.copy2(backup_launch_gui, launch_gui_exe)
        os.remove(backup_launch_gui)
    
    # 验证构建结果
    if not verify_build():
        return 1
    
    print("\n=== 打包完成 ===")
    print(f"您可以在 {DIST_DIR} 目录中找到以下文件:")
    print("- gui_install.exe: 图形化安装程序（使用SQLite数据库）")
    print("- launch_gui.exe: 图形化启动器")
    print("\n安装步骤:")
    print("1. 运行 gui_install.exe")
    print("2. 选择安装目录")
    print("3. 等待安装完成")
    print("4. 在安装目录中运行 launch_gui.exe 启动应用")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

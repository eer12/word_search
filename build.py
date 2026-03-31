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
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "launch_gui",
        "--windowed",
        "--collect-all", "tkinter",
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
        "--hidden-import", "pywpsrpc",
        "--hidden-import", "jieba",
        "--hidden-import", "mammoth",
        "launch_gui.py"
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        print("打包 launch_gui.py 失败")
        return False
    print("打包 launch_gui.py 成功")
    return True

def build_gui_install():
    """打包gui_install.py，包含所有必要的文件"""
    print("\n=== 打包 gui_install.py ===")
    
    # 准备数据文件参数
    data_files = [
        f"app.py;.",
        f"config.py;.",
        f"run_production.py;.",
        f"launch_gui.py;.",
        f"templates;templates",
        f"requirements.txt;."
    ]
    
    # 构建命令
    cmd = ["pyinstaller", "--onefile", "--name", "gui_install", "--windowed", "--collect-all", "tkinter", "--hidden-import", "tkinter.ttk", "--hidden-import", "tkinter.filedialog", "--hidden-import", "tkinter.messagebox", "--hidden-import", "flask", "--hidden-import", "PyPDF2", "--hidden-import", "docx", "--hidden-import", "pytesseract", "--hidden-import", "PIL", "--hidden-import", "pdf2image", "--hidden-import", "waitress", "--hidden-import", "sqlite3", "--hidden-import", "datetime", "--hidden-import", "tempfile", "--hidden-import", "subprocess", "--hidden-import", "re", "--hidden-import", "pywpsrpc", "--hidden-import", "jieba", "--hidden-import", "mammoth"]
    
    # 添加数据文件
    for data_file in data_files:
        cmd.extend(["--add-data", data_file])
    
    # 添加主脚本
    cmd.append("gui_install.py")
    
    result = run_command(cmd)
    if result.returncode != 0:
        print("打包 gui_install.py 失败")
        return False
    print("打包 gui_install.py 成功")
    return True

def copy_launch_gui_exe():
    """复制launch_gui.exe到dist目录"""
    print("\n=== 复制 launch_gui.exe ===")
    src = os.path.join(DIST_DIR, "launch_gui.exe")
    dst = os.path.join(DIST_DIR, "launch_gui.exe")
    if os.path.exists(src):
        print(f"launch_gui.exe 已经在 dist 目录中")
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
    
    # 构建launch_gui
    if not build_launch_gui():
        return 1
    
    # 构建gui_install
    if not build_gui_install():
        return 1
    
    # 复制launch_gui.exe
    if not copy_launch_gui_exe():
        return 1
    
    # 验证构建结果
    if not verify_build():
        return 1
    
    print("\n=== 打包完成 ===")
    print(f"您可以在 {DIST_DIR} 目录中找到以下文件:")
    print("- gui_install.exe: 图形化安装程序（包含内置MySQL）")
    print("- launch_gui.exe: 图形化启动器")
    print("\n安装步骤:")
    print("1. 运行 gui_install.exe")
    print("2. 选择安装目录")
    print("3. 等待安装完成")
    print("4. 在安装目录中运行 launch_gui.exe 启动应用")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

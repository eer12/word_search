import os
import subprocess
import time
import ctypes

# 检查是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# MySQL配置
MYSQL_INSTALL_PATH = os.path.join(os.getcwd(), "mysql")
MYSQL_DATA_PATH = os.path.join(MYSQL_INSTALL_PATH, "data")
MYSQL_BIN_PATH = os.path.join(MYSQL_INSTALL_PATH, "bin")
MYSQL_PORT = "3306"
MYSQL_ROOT_PASSWORD = "123456"

print("=== MySQL服务测试脚本 ===")
print(f"是否以管理员权限运行: {'是' if is_admin() else '否'}")
print(f"MySQL安装路径: {MYSQL_INSTALL_PATH}")
print(f"MySQL数据路径: {MYSQL_DATA_PATH}")
print(f"MySQL二进制路径: {MYSQL_BIN_PATH}")

# 检查MySQL可执行文件
mysqld_exe = os.path.join(MYSQL_BIN_PATH, "mysqld.exe")
print(f"\n检查mysqld.exe: {mysqld_exe}")
if os.path.exists(mysqld_exe):
    print("✓ mysqld.exe存在")
else:
    print("✗ mysqld.exe不存在")
    exit(1)

# 检查VC++运行时库
def check_vc_redist():
    print("\n检查VC++运行时库...")
    system32 = os.path.join(os.environ['SystemRoot'], 'System32')
    required_dlls = [
        'vcruntime140.dll',
        'msvcp140.dll',
        'vcruntime140_1.dll'
    ]
    for dll in required_dlls:
        dll_path = os.path.join(system32, dll)
        if os.path.exists(dll_path):
            print(f"✓ {dll} 存在")
        else:
            print(f"✗ {dll} 不存在")

check_vc_redist()

# 初始化数据目录
if not os.path.exists(MYSQL_DATA_PATH):
    print("\n初始化MySQL数据目录...")
    try:
        result = subprocess.run([mysqld_exe, "--initialize-insecure"], capture_output=True, text=True)
        print(f"初始化结果: {'成功' if result.returncode == 0 else '失败'}")
        if result.returncode != 0:
            print(f"错误信息: {result.stderr}")
    except Exception as e:
        print(f"初始化异常: {e}")
        exit(1)
else:
    print("\n数据目录已存在，跳过初始化")

# 创建my.ini配置文件
my_ini_path = os.path.join(MYSQL_INSTALL_PATH, "my.ini")
print(f"\n创建配置文件: {my_ini_path}")
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
    print("✓ 配置文件创建成功")
except Exception as e:
    print(f"✗ 创建配置文件失败: {e}")
    exit(1)

# 停止可能存在的MySQL服务
print("\n停止可能存在的MySQL服务...")
try:
    mysqladmin_exe = os.path.join(MYSQL_BIN_PATH, "mysqladmin.exe")
    if os.path.exists(mysqladmin_exe):
        subprocess.run([mysqladmin_exe, "-u", "root", "shutdown"], capture_output=True, text=True)
    print("✓ 服务停止完成")
except Exception as e:
    print(f"停止服务失败: {e}")

# 卸载可能存在的MySQL服务
print("\n卸载可能存在的MySQL服务...")
try:
    uninstall_result = subprocess.run(["sc", "delete", "MySQL80"], capture_output=True, text=True)
    print(f"卸载结果: {'成功' if uninstall_result.returncode == 0 else '失败'}")
    if uninstall_result.returncode != 0:
        print(f"卸载错误: {uninstall_result.stderr}")
    time.sleep(2)
    print("✓ 服务卸载完成")
except Exception as e:
    print(f"卸载服务失败: {e}")

# 安装MySQL为Windows服务
print("\n安装MySQL为Windows服务...")
try:
    install_result = subprocess.run([mysqld_exe, "--install", "MySQL80", f"--defaults-file={my_ini_path}"], capture_output=True, text=True)
    print(f"安装结果: {'成功' if install_result.returncode == 0 else '失败'}")
    if install_result.returncode != 0:
        print(f"错误信息: {install_result.stderr}")
    else:
        print("✓ 服务安装成功")
    time.sleep(2)
    
    # 检查服务是否真的安装成功
    check_result = subprocess.run(["sc", "query", "MySQL80"], capture_output=True, text=True)
    if "SERVICE_NAME: MySQL80" in check_result.stdout:
        print("✓ 服务已成功注册")
    else:
        print("✗ 服务注册失败")
        print(f"服务检查结果: {check_result.stdout}")
except Exception as e:
    print(f"安装服务异常: {e}")
    exit(1)

# 启动MySQL服务
print("\n启动MySQL服务...")
try:
    start_result = subprocess.run(["sc", "start", "MySQL80"], capture_output=True, text=True)
    print(f"启动结果: {'成功' if start_result.returncode == 0 else '失败'}")
    if start_result.returncode != 0:
        print(f"错误信息: {start_result.stderr}")
        # 尝试使用net命令启动
        print("尝试使用net命令启动...")
        net_result = subprocess.run(["net", "start", "MySQL80"], capture_output=True, text=True)
        print(f"net命令启动结果: {'成功' if net_result.returncode == 0 else '失败'}")
        if net_result.returncode != 0:
            print(f"net命令错误: {net_result.stderr}")
        else:
            print("✓ net命令启动成功")
    else:
        print("✓ 服务启动成功")
except Exception as e:
    print(f"启动服务异常: {e}")

# 等待服务启动
print("\n等待服务启动...")
service_running = False
for i in range(10):
    time.sleep(1)
    try:
        service_status = subprocess.run(["sc", "query", "MySQL80"], capture_output=True, text=True)
        print(f"服务状态输出: {service_status.stdout}")
        if "RUNNING" in service_status.stdout:
            print("✓ MySQL服务正在运行")
            service_running = True
            break
        else:
            print(f"服务状态: {service_status.stdout}")
    except Exception as e:
        print(f"检查服务状态异常: {e}")

if not service_running:
    print("✗ MySQL服务启动失败")
    # 尝试直接运行mysqld.exe
    print("\n尝试直接运行mysqld.exe...")
    try:
        mysqld_process = subprocess.Popen([mysqld_exe, "--defaults-file={my_ini_path}"], creationflags=subprocess.CREATE_NO_WINDOW)
        print("✓ mysqld.exe已启动")
        time.sleep(5)
        # 检查进程是否在运行
        if mysqld_process.poll() is None:
            print("✓ mysqld.exe进程正在运行")
            # 测试连接
            print("\n测试MySQL连接...")
            mysql_cmd = os.path.join(MYSQL_BIN_PATH, "mysql.exe")
            test_result = subprocess.run([mysql_cmd, "-u", "root", "-e", "SELECT VERSION();"], capture_output=True, text=True)
            print(f"连接结果: {'成功' if test_result.returncode == 0 else '失败'}")
            if test_result.returncode == 0:
                print(f"MySQL版本: {test_result.stdout}")
            else:
                print(f"连接错误: {test_result.stderr}")
            # 停止进程
            mysqld_process.terminate()
        else:
            print("✗ mysqld.exe进程启动失败")
    except Exception as e:
        print(f"直接运行mysqld.exe异常: {e}")
    exit(1)

# 测试连接
print("\n测试MySQL连接...")
mysql_cmd = os.path.join(MYSQL_BIN_PATH, "mysql.exe")
try:
    # 由于使用了--initialize-insecure，初始密码为空
    test_result = subprocess.run([mysql_cmd, "-u", "root", "-e", "SELECT VERSION();"], capture_output=True, text=True)
    print(f"连接结果: {'成功' if test_result.returncode == 0 else '失败'}")
    if test_result.returncode == 0:
        print(f"MySQL版本: {test_result.stdout}")
    else:
        print(f"连接错误: {test_result.stderr}")
except Exception as e:
    print(f"连接异常: {e}")

print("\n=== 测试完成 ===")

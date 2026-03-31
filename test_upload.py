import os
import sys
import time

# 测试文件上传
def test_upload():
    # 选择一个WPS文件进行测试
    wps_files = [f for f in os.listdir('C:\\backup\\wps') if f.endswith('.wps')]
    if not wps_files:
        print("没有找到WPS文件")
        return
    
    wps_file = os.path.join('C:\\backup\\wps', wps_files[0])
    print(f"测试上传WPS文件: {wps_file}")
    
    # 导入requests库
    try:
        import requests
    except ImportError:
        print("requests库未安装，使用curl命令上传")
        # 使用curl命令上传
        import subprocess
        
        # 构建curl命令
        curl_command = f'curl -F "document=@{wps_file}" -F "category_id=1" -F "issuing_unit=" -F "remark=" http://127.0.0.1:3000/upload'
        
        print(f"执行命令: {curl_command}")
        
        # 执行命令
        result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
        print(f"命令输出: {result.stdout}")
        print(f"命令错误: {result.stderr}")
        print(f"命令返回码: {result.returncode}")
    else:
        # 使用requests库上传
        print("使用requests库上传")
        
        # 构建表单数据
        files = {
            'document': open(wps_file, 'rb')
        }
        data = {
            'category_id': '1',
            'issuing_unit': '',
            'remark': ''
        }
        
        # 发送POST请求
        try:
            response = requests.post('http://127.0.0.1:3000/upload', files=files, data=data, timeout=30)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}...")
            
            # 检查是否上传成功
            if '文件上传成功' in response.text:
                print("✅ 上传成功")
            else:
                print("❌ 上传失败")
        except Exception as e:
            print(f"上传错误: {e}")
        finally:
            # 关闭文件
            files['document'].close()

if __name__ == '__main__':
    test_upload()

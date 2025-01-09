import importlib.util
import json
import re

# 检查指定的Python包是否已安装
def check_package_installed(package_name):
    # 使用importlib.util.find_spec()函数尝试找到指定包的规格
    package_spec = importlib.util.find_spec(package_name)

    # 如果找到包的规格，则说明包已安装，返回True
    if package_spec is not None:
        return True
    # 否则，包未安装，返回False
    else:
        return False


# 使用正则表达式匹配JSON对象
def getJsonObject(text):
    try:
        json_pattern = r'```ai(.*?)```'
        json_str = re.search(json_pattern, text, re.DOTALL).group(1).strip()

        # 将JSON字符串解析为Python字典
        json_obj = json.loads(json_str)

        # 打印提取到的JSON对象
        return json_obj
    except Exception as e:
        return ''


# 将 content 数据写入到 file_path 文件中。
def write_to_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)  # 修改点
        return "成功"
    except IOError as e:
        return f"写入文件时发生错误: {e}"

#从 TXT 文件中读取 JSON 数据。
def read_json_from_file(file_path):
    try:
        content = read_from_file(file_path)  # 修改点
        if content and len(content) > 0:
            json_data = json.loads(content)  # 修改点
            print(f"已成功从文件 {file_path} 中读取 JSON 数据。")
        else:
            return None
        return json_data
    except json.JSONDecodeError as e:
        return f"JSON 解码错误: {e}"

#从 file_path 文件中读取数据。
def read_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # 修改点
        print(f"已成功从文件 {file_path} 中读取 JSON 数据。")
        return content
    except IOError as e:
        print(f"读取文件时发生错误: {e}")


import subprocess

# 使用subprocess.run执行命令脚本命令
def execute_command(command):
    # 使用subprocess.run执行命令
    try:
        # shell=True允许我们使用shell命令语法
        subprocess.run(command, shell=True, check=True)
        return "命令执行成功"
    except subprocess.CalledProcessError as e:
        return f"命令执行失败: {e}"


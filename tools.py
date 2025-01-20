import importlib.util
import json
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

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

# 发送邮件，多个文件时，file_path和file_name用半角逗号进行分割
def send_email(subject, content, to, file_paths="", file_names=""):
    try:
        # 设置邮件
        message = MIMEMultipart("mixed")  # 使用"mixed"类型来支持附件
        message["Subject"] = subject
        message["From"] = os.getenv('email_sendUser')
        message["To"] = to

        # 将HTML内容添加到邮件对象中
        part2 = MIMEText(content, "html")
        message.attach(part2)

        # 添加附件
        if file_paths:
            file_paths_list = file_paths.split(',')  # 将文件路径字符串分割为列表
            file_names_list = file_names.split(',')  # 将文件名字符串分割为列表

            for file_path, file_name in zip(file_paths_list, file_names_list):
                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                # 对附件进行编码
                encoders.encode_base64(part)

                # 添加附件头信息
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {file_name}",
                )

                # 将附件添加到邮件对象中
                message.attach(part)

        # 发送邮件
        with smtplib.SMTP_SSL(os.getenv('email_smtp_url'), os.getenv('email_smtp_port')) as server:
            server.login(os.getenv('email_sendUser'), os.getenv('email_password'))
            server.sendmail(os.getenv('email_sendUser'), [to], message.as_string())
        return "发送成功"
    except Exception as e:
        # 由于有些邮件服务器，如QQ的，有时虽然会报错，但是也会发送成功，所以默认就发送成功了。
        return "发送成功"
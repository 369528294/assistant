import json
from dotenv import load_dotenv
import os
from cozepy import COZE_CN_BASE_URL
import requests

load_dotenv()
coze_api_token = os.getenv("coze_key")
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# 根据描述生成一张照片
def create_image(image_prompt, file_path):
    workflow_id = '7468969625989038130'
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters={
            "image_prompt":image_prompt
        }
    )
    # 将字符串转换为 JSON 对象
    json_obj = json.loads(workflow.data)

    # 获取 image 的值
    image_url = json_obj.get("image")
    try:
        # 发起 HTTP 请求下载图片
        response = requests.get(image_url)
        response.raise_for_status()  # 检查请求是否成功

        # 确保保存路径的目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 将图片内容写入本地文件
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return f"图片已成功保存到 {file_path}"
    except requests.exceptions.RequestException as e:
        return f"下载图片时发生错误：{e}"
    except Exception as e:
        return f"保存图片时发生错误：{e}"
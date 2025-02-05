import os
import platform

import websocket
import datetime
import hashlib
import base64
import hmac
import json
import time
import ssl
import pyaudio
import threading  # 导入threading模块
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
from dotenv import load_dotenv
import tkinter as tk
import pyautogui
import queue
from websocket import WebSocketConnectionClosedException
import pyperclip

# 定义语音识别的状态
STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2


class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        url = url + '?' + urlencode(v)
        return url


def on_message(ws, message, result_queue):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            print(f"识别结果：{result}")
            result_queue.put(result)  # 将识别结果放入队列
    except Exception as e:
        print("接收到消息时出现异常:", e)


def on_error(ws, error):
    print("### 错误:", error)
    reconnect(ws)


def on_close(ws, a, b):
    if not ws.is_closing:  # 检查是否正在关闭
        print("### 连接已关闭 ###")
        reconnect(ws)
    else:
        print("### 连接已关闭, 不进行重连 ###")
        ws.is_closing = False  # 重置关闭标志


def reconnect(ws):
    """实现 WebSocket 重连机制"""
    print("Attempting to reconnect...")
    ws.close()
    time.sleep(1)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # 再次运行WebSocket


def on_open(ws, wsParam, frame_size=8000, interval=0.04):
    def run(*args):
        status = STATUS_FIRST_FRAME
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=frame_size)
        while True:
            buf = stream.read(frame_size)
            if not buf:
                status = STATUS_LAST_FRAME
            if status == STATUS_FIRST_FRAME:
                d = {"common": wsParam.CommonArgs,
                     "business": wsParam.BusinessArgs,
                     "data": {"status": 0, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                d = json.dumps(d)
                ws.send(d)
                status = STATUS_CONTINUE_FRAME
            elif status == STATUS_CONTINUE_FRAME:
                d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                try:
                    ws.send(json.dumps(d))
                except WebSocketConnectionClosedException:
                    print("WebSocket connection closed. Stopping the stream.")
                    break
            elif status == STATUS_LAST_FRAME:
                d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                try:
                    ws.send(json.dumps(d))
                except WebSocketConnectionClosedException:
                    print("WebSocket connection closed. Stopping the stream.")
                    break  # 如果连接关闭，停止处理
                time.sleep(1)
                break
            time.sleep(interval)
        stream.stop_stream()
        stream.close()
        p.terminate()
        ws.close()

    # 使用 threading.Thread 启动新的线程
    thread = threading.Thread(target=run)
    thread.start()


class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语音识别")
        self.root.geometry("300x200")

        self.is_listening = False  # 是否正在监听
        self.is_closing = False  # 是否正在关闭连接
        self.ws = None
        self.ws_param = None
        self.result_queue = queue.Queue()  # 创建一个队列用于线程间通信

        # 创建开始按钮
        self.start_button = tk.Button(root, text="开始监听", width=20, command=self.toggle_listening)
        self.start_button.pack(pady=20)

        # 创建状态标签
        self.status_label = tk.Label(root, text="状态: 停止", width=20)
        self.status_label.pack(pady=10)

        # 启动主线程更新文本框
        self.update_text_box_thread = threading.Thread(target=self.update_text_box)
        self.update_text_box_thread.daemon = True
        self.update_text_box_thread.start()

    def toggle_listening(self):
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        load_dotenv()
        API_KEY = os.getenv('XF_API_KEY')
        APPID = os.getenv('XF_APPID')
        API_SECRET = os.getenv('XF_API_SECRET')

        self.ws_param = Ws_Param(APPID=APPID, APIKey=API_KEY, APISecret=API_SECRET)
        ws_url = self.ws_param.create_url()

        self.ws = websocket.WebSocketApp(ws_url, on_message=lambda ws, msg: on_message(ws, msg, self.result_queue),
                                         on_error=on_error, on_close=self.on_close)
        self.ws.on_open = lambda ws: on_open(ws, self.ws_param)

        self.status_label.config(text="状态: 监听中")
        self.is_listening = True
        self.start_button.config(text="停止监听")
        threading.Thread(target=self.ws.run_forever, kwargs={'sslopt': {"cert_reqs": ssl.CERT_NONE}}).start()

    def stop_listening(self):
        if self.ws:
            self.is_closing = True  # 设置关闭标志
            self.ws.close()

        self.status_label.config(text="状态: 停止")
        self.is_listening = False
        self.start_button.config(text="开始监听")

    def on_close(self, ws, a, b):
        if not self.is_closing:
            print("### 连接已关闭 ###")
            reconnect(ws)
        else:
            print("### 连接已关闭, 不进行重连 ###")
            self.is_closing = False  # 重置关闭标志

    def update_text_box(self):
        while True:
            if not self.result_queue.empty():
                result = self.result_queue.get()  # 获取识别的文本
                self.root.after(0, self.insert_text, result)  # 在主线程中插入文本

    def insert_text(self, text):
        pyperclip.copy(text)
        self.paste()

    def paste(self):
        """Simulates pressing the paste shortcut (Cmd+V on macOS, Ctrl+V on others)."""
        if platform.system() == "Darwin":  # macOS
            pyautogui.hotkey('command', 'v')
        else:  # Windows/Linux
            pyautogui.hotkey('ctrl', 'v')

    def on_closing(self):
        if self.ws:
            self.ws.close()
        self.root.quit()


if __name__ == "__main__":
    # 创建GUI窗口
    root = tk.Tk()
    app = SpeechToTextApp(root)

    # 设置关闭时的处理函数
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # 启动GUI主循环
    root.mainloop()

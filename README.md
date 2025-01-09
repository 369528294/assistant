# Assistant

[中文文档](README_zh-CN.md)

Maybe this is your assistant to help you to do something with your ideas

## install

config your ai model , you can register an account on [deepseek](https://www.deepseek.com/),and get your [api_key](https://platform.deepseek.com/api_keys) 

```sh
cp .env.example .env
```

config your assistant , and edit it in your config

```sh
cp role.example role.md
```

install packages

```sh
pip install -r requirements.txt
```

## run

```sh
python chat.py
```
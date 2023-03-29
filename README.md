# 使用uiautomator2搭配chatGPT制作的qq群机器人

## 需求背景

图一乐，群友们想体验一下chatGPT，自己刚好有个号有api，单纯玩具

### 优点
+ 基本没有啥封号风险，用的不是qq的协议，纯ui操作
+ 能玩

### 缺点
+ 安装麻烦，得一台手机一直监控群消息
+ 依赖环境多，需要安装uiautomator2，为了记录消息，还得安装redis
+ 速度慢
+ api接口反应也慢

## 安装流程

### 1.需要环境
+ 一台安卓手机，打开adb调试
+ 一台电脑，安装adb，python环境

### 2.运行
```shell
pip3 install -r requirements.txt
```
打开config.ini，按照说明填写配置
```shell
python3 main.py
```

### 最后
uiautomator2 的安装流程请看官方库
https://github.com/openatx/uiautomator2
import time
import uiautomator2 as u2
import redis
import openai
import json
import os
from multiprocessing import Process
from configparser import ConfigParser

# 读取配置文件
cfg = ConfigParser()
cfg.read('config.ini')

os.environ["HTTP_PROXY"] = cfg.get("conf", "proxies")
os.environ["HTTPS_PROXY"] = cfg.get("conf", "proxies")
openai.api_key = cfg.get("conf", "api_key")

red = redis.Redis()
d = u2.connect()
print(d.info)
time.sleep(10)
d.set_fastinput_ime(True)

NICK_NAME = f"@{cfg.get('conf', 'nice_name')}"


class ChatGPT:
    def __init__(self, user: str):
        self.user = f"chatUser:{user}"

    def ask_gpt(self, messages: list):
        # q = "用python实现：提示手动输入3个不同的3位数区间，输入结束后计算这3个区间的交集，并输出结果区间"
        try:
            rsp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return rsp.get("choices")[0]["message"]["content"]
        except Exception:
            return "chatGTGP 接口错误"

    def add_message(self, message: str):
        # 假如对话长度超过5轮，则重制
        if red.llen(self.user) >= 5:
            red.delete(self.user)

        if not red.exists(self.user):
            red.rpush(self.user, json.dumps({"role": "system", "content": "You are a helpful assistant"}, ensure_ascii=False))

        message_dic = {"role": "user", "content": message}
        red.rpush(self.user, json.dumps(message_dic, ensure_ascii=False))

        message_data = red.lrange(self.user, 0, -1)

        return [json.loads(x) for x in message_data]

    def add_answer(self, answer: str):
        answer_dic = {"role": "assistant", "content": answer}
        red.rpush(self.user, json.dumps(answer_dic, ensure_ascii=False))


def header_message():
    """循环处理未处理的信息"""
    while True:
        message = red.lpop("chatMessage")
        if not message:
            time.sleep(1)
            print("*********等待任务*********")
            continue
        message_dic = json.loads(message.decode())
        user: str = message_dic['user']
        message = message_dic['message']

        user_format = user.replace(" ", "*")
        chat = ChatGPT(user=user_format)
        message_data = chat.add_message(message)
        answer = chat.ask_gpt(message_data)
        chat.add_answer(answer)

        d(resourceId="com.tencent.mobileqq:id/input").send_keys(f"@{user} {answer}")
        d(resourceId="com.tencent.mobileqq:id/fun_btn").click()


def get_message():
    while True:
        s = d.xpath('//*[@resource-id="com.tencent.mobileqq:id/listView1"]/android.widget.RelativeLayout').all()
        for one in s:
            try:
                children = one.elem.getchildren()

                if len(children) != 3:
                    if len(children) == 4:
                        children = children[1:]
                    else:
                        continue
                _, linearLayout, textView = children
                header_and_name = linearLayout.getchildren()
                if len(header_and_name) != 2:
                    name = [x for x in linearLayout.getchildren() if x.tag == "android.widget.TextView"]
                    if not name:
                        continue

                    name = name[0] if name else None
                    if name is None:
                        continue
                else:
                    _, name = header_and_name

                if textView.tag == "android.widget.TextView" and name.tag == "android.widget.TextView":
                    message: str = textView.attrib['text'].strip()
                    name_txt = name.attrib['text']

                    # 这里判断是否要放进提问队列里面
                    if message and message.startswith(NICK_NAME):
                        message = message.replace(NICK_NAME, "")
                        if message.strip() != "":
                            message_dic = json.dumps({"user": name_txt, "message": message.strip()}, ensure_ascii=False)

                            # 判断这个人的提问是否重复（页面一直扫描会重复）
                            state = red.sismember('message_check', message_dic)
                            if not state:
                                print("放进队列里准备chatGPT处理")
                                red.sadd("message_check", message_dic)
                                # 放进消息队列里面等待处理
                                red.rpush("chatMessage", message_dic)
            except Exception as e:
                print(e)
                continue


if __name__ == '__main__':

    p = Process(target=get_message, )
    p.start()
    header_message()


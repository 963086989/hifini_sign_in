# -*- coding: utf-8 -*-
"""
cron: 1 0 0 * * *
new Env('HiFiNi');
"""

import json
from sendNotify import send
import requests
import re
import os
import sys
import time
requests.packages.urllib3.disable_warnings()

def getHeader(cookie):
    return  {
                'Cookie': cookie,
                'authority': 'www.hifini.com',
                'accept': 'text/plain, */*; q=0.01',
                'accept-language': 'zh-CN,zh;q=0.9',
                'origin': 'https://www.hifini.com',
                'referer': 'https://www.hifini.com/',
                'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }

def getSign(cookie):
    sign_in_url = "https://www.hifini.com/sg_sign.htm"
    headers = getHeader(cookie)
    rsp = requests.get(url=sign_in_url, headers=headers,
                                timeout=15, verify=False)
    rsp_text = rsp.text.strip()
    pattern = r'var\s+sign\s*=\s*"([a-f0-9]+)";'
    match = re.search(pattern,  rsp_text)

    if match:
        sign_value = match.group(1)
        return sign_value
    else:
        return None 

def start(cookie):
    max_retries = 20
    retries = 0
    msg = ""
    sign = getSign(cookie)
    if sign is None:
        print("签到结果未拿到Sign")
        send("hifini 签到结果 ",  "未拿到Sign")
        return

    while retries < max_retries:
        try:
            msg += "第{}次执行签到\n".format(str(retries+1))
            sign_in_url = "https://www.hifini.com/sg_sign.htm"
            headers = getHeader(cookie)
            
            rsp = requests.post(url=sign_in_url, data={'sign': sign}, headers=headers,
                                timeout=15, verify=False)
            rsp_text = rsp.text.strip()
            # print(rsp_text)
            success = False
            if "今天已经签过啦！" in rsp_text:
                msg += '已经签到过了，不再重复签到!\n'
                success = True
            elif "成功" in rsp_text:
                rsp_json = json.loads(rsp_text)
                msg += rsp_json['message']
                success = True
            elif "503 Service Temporarily" in rsp_text or "502 Bad Gateway" in rsp_text:
                msg += "服务器异常！\n"
            elif "请登录后再签到!" in rsp_text:
                msg += "Cookie没有正确设置！\n"
                success = True
            else:
                msg += "未知异常!\n"
                msg += rsp_text + '\n'

            # rsp_json = json.loads(rsp_text)
            # print(rsp_json['code'])
            # print(rsp_json['message'])
            if success:
                print("签到结果: ",msg)
                send("hifini 签到结果", msg)
                break  # 成功执行签到，跳出循环
            elif retries >= max_retries:
                print("达到最大重试次数，签到失败。")
                send("hifini 签到结果", msg)
                break
            else:
                retries += 1
                print("等待20秒后进行重试...")
                time.sleep(20)
        except Exception as e:
            print("签到失败，失败原因:"+str(e))
            send("hifini 签到结果", str(e))
            retries += 1
            if retries >= max_retries:
                print("达到最大重试次数，签到失败。")
                break
            else:
                print("等待20秒后进行重试...")
                time.sleep(20)

if __name__ == "__main__":
    cookie = os.getenv("HIFINI_COOKIE")
    start(cookie)

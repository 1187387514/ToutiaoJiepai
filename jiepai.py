import requests
import urllib.parse
import re
from bs4 import BeautifulSoup as bs
import json
import traceback
from multiprocessing import Pool
from bs4 import BeautifulSoup as bs
from config import *
import pymongo
import os
import hashlib
#程序用于爬取今日头条街拍图片
client = pymongo.MongoClient(db_url)
mydb = client[db_name]
id = 0

#获取索引网页
def getindex(offset,keyword):
    header = {
              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
              "cookie": """tt_webid=6707125074643944967; WEATHER_CITY=%E5%8C%97%E4%BA%AC; UM_distinctid=16b980f20c1a7-03d67e981415f3-e343166-144000-16b980f20c23b3; tt_webid=6707125074643944967; csrftoken=e21f9bc427534e0eac2fed008ab17b38; CNZZDATA1259612802=872817706-1561621153-https%253A%252F%252Fwww.baidu.com%252F%7C1562231482; __tasessionId=d8w3iejpp1562231797597; s_v_web_id=35699bfca4448493e5037df29181ad34"""
              }
    data = {
            'aid': 24,
            'app_name': 'web_search',
            'offset': offset,
            'format': 'json',
            'keyword': keyword,
            'autoload': 'true',
            'count': 20,
            'en_qc': 1,
            'cur_tab': 1,
            'from': 'search_tab',
            'pd': 'synthesis'
            }
    param = urllib.parse.urlencode(data)
    url = "https://www.toutiao.com/api/search/content/?"+param
    try:
        r = requests.get(url,headers=header)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        print("获取index失败")
        traceback.print_exc()

#解析索引网页
def parseindex(html):
    data = json.loads(html)
    try:
        if data and "data" in data.keys():
            merge = data.get('data')
            for item in merge:
                #print(item.get("share_url"))
                if item and "share_url" in item:
                    yield item.get("share_url")
    except Exception as e:
        print("解析index失败")
        traceback.print_exc()
        pass
    #这里注释的是以正则表达式寻找把结果存在列表的方式
    #r = re.compile(r'share_url":"(.*?)"',re.S)
    #try:
        #urls = re.findall(r,html)
        #print(urls)
        #return urls

h
def getdetail(url):
    header = {
              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
              "cookie": """tt_webid=6707125074643944967; WEATHER_CITY=%E5%8C%97%E4%BA%AC; UM_distinctid=16b980f20c1a7-03d67e981415f3-e343166-144000-16b980f20c23b3; tt_webid=6707125074643944967; csrftoken=e21f9bc427534e0eac2fed008ab17b38; CNZZDATA1259612802=872817706-1561621153-https%253A%252F%252Fwww.baidu.com%252F%7C1562231482; __tasessionId=d8w3iejpp1562231797597; s_v_web_id=35699bfca4448493e5037df29181ad34"""
              }
    try:
        r = requests.get(url,headers=header)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        print("获取detail失败")
        traceback.print_exc()
#获取街拍图片的url以及相关信息
def parse_detail(html,url):
    try:
        soup = bs(html,"html.parser")
        title = soup.find('title')
        print(title)
        r = re.compile(r'JSON.parse\((.*?)\)',re.S)
        find = re.search(r,html)
        if find:
            find2 = find.group(1)
            find3 = find2.replace("\\","")
            r2 = re.compile(r'"url":"(.*?)"',re.S)
            imgs = re.findall(r2,find3)
            for img in imgs:
                content = save_image(img)
                download(content)
            return {"title":title.text,
                    "imgs":imgs,
                    "url":url}
        """通过转换成json来获取url大失败，以后想起来再这样弄吧
        r = re.compile(r'JSON.parse\((.*?)\)',re.S)
        find = re.search(r,html)
        if find:
            find2 = find.group(1)
            find3 = find2.replace("\\","")
            gal = eval(find3)
            if gal and "sub_images" in gal:
                items = gal.get("sub_images")
                imgs = [item.get("url") for item in items]"""
    except:
        print("解析detail失败")
        traceback.print_exc()
#把解析下来的信息保存在mongodb上
def save_mongo(data):
    if mydb[db_table].insert_one(data):
        print("插入mongodb成功")
        return True
    else:
        print("插入mongodb失败")
        return False
#把街拍图片以二进制的形式获取下来
def save_image(url):
    header = {
              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
              "cookie": """tt_webid=6707125074643944967; WEATHER_CITY=%E5%8C%97%E4%BA%AC; UM_distinctid=16b980f20c1a7-03d67e981415f3-e343166-144000-16b980f20c23b3; tt_webid=6707125074643944967; csrftoken=e21f9bc427534e0eac2fed008ab17b38; CNZZDATA1259612802=872817706-1561621153-https%253A%252F%252Fwww.baidu.com%252F%7C1562231482; __tasessionId=d8w3iejpp1562231797597; s_v_web_id=35699bfca4448493e5037df29181ad34"""
              }
    try:
        r = requests.get(url,headers=header)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.content
    except:
        print("获取图片失败")
        traceback.print_exc()
#下载街拍图片到本地
def download(content):
    path = "{}/{}.{}".format(os.getcwd(), hashlib.md5(content).hexdigest(),"jpg")
    if not os.path.exists(path):
        with open(path,"wb") as f:
            f.write(content)

def main(offset,keyword):
    html = getindex(offset,keyword)
    items = parseindex(html)
    for item in items:
        #print(item)
        html3 = getdetail(item)
        img_data = parse_detail(html3,item)
        if img_data:
            #print(type(img_data))
            save_mongo(img_data)
        #print(parse_detail(html3,item))

if __name__ == '__main__':
    for i in range(1,3):
        main(i*20,"街拍")

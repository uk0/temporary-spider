'''
Python版本： 3.7
OS： mac os
owner: zhangjianxin
'''
import asyncio
import base64
import json
import os
import random
import string
import smtplib
import urllib
from email.mime.text import MIMEText
import time
import queue
from encodings.utf_8 import decode

from selenium.webdriver.common.proxy import *
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# https://www.wandoujia.com/category/app
# /html/body/div[2]/ul[1]

CATEGORY_LIST_FILE_NAME = "category_list.txt"
APPINFO_LIST_FILE_NAME = "back_app_info_list.txt"


def getBWbash():
    import requests
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    # 提供添加proxy的能力 ，在浏览器添加 ，无头也可以用，目前测试 上线采用 容器部署 selenium-server 我们远程调用即可。
    proxy = {'address': '127.0.0.1:8178'}

    capabilities = dict(DesiredCapabilities.CHROME)
    capabilities['proxy'] = {'proxyType': 'MANUAL',
                             # 'httpProxy': proxy['address'],
                             # 'ftpProxy': proxy['address'],
                             # 'sslProxy': proxy['address'],
                             'noProxy': '',
                             'class': "org.openqa.selenium.Proxy",
                             'autodetect': False}

    options = webdriver.ChromeOptions()
    #  不加载图片 可能有效。。webp类型的无法阻止
    prefs = {"profile.managed_default_content_settings.images": 2}

    options.add_experimental_option("prefs", prefs)
    wd = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options, desired_capabilities=capabilities)
    return wd


def GetHtml(url):
    wd = getBWbash()
    # wd.implicitly_wait(30)
    wd.get(url)  # 进入界面
    WebDriverWait(wd, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ul.clearfix:nth-child(2)"))
    )
    listDom = wd.find_elements_by_xpath("/html/body/div[2]/ul[1]/li")
    tagIndex = 0;

    result_array = []
    print("长度 = {}".format(len(listDom)))
    for i in listDom:
        result = {}
        tagIndex = tagIndex + 1
        temp_arry = i.find_element_by_xpath("/html/body/div[2]/ul[1]/li[{}]".format(tagIndex))
        temp_item_a = temp_arry.find_element_by_tag_name("a")

        result["href"] = temp_item_a.get_attribute("href")
        result["title"] = temp_item_a.get_attribute("title")

        tag1 = temp_arry.find_element_by_tag_name("div").find_elements_by_tag_name("a")
        data = []
        for child_cate in tag1:
            data.append(
                {"item_href": child_cate.get_attribute("href"), "item_title": child_cate.get_attribute("title")})
        result["item_araray"] = data
        result_array.append(result)
    print(result_array)
    save_json_to_file(result_array)
    wd.quit()


def file_inode():
    if os.path.exists(CATEGORY_LIST_FILE_NAME):
        return True;
    return False


def save_json_to_file(line):
    str = json.dumps(line)
    with open(CATEGORY_LIST_FILE_NAME, 'wa+') as f:
        f.write(bytes(str + '\n', encoding="utf8"))


def get_app_info(appid):
    url = "https://www.wandoujia.com/apps/{}".format(appid)


def download_url_format(appid):
    return "https://www.wandoujia.com/apps/{}/download/dot?ch=detail_normal_dl".format(appid)


def get_category_page_auto_load(url):
    #     //*[@id="j-tag-list"]
    wd = getBWbash()
    # wd.implicitly_wait(30)
    wd.get(url)  # 进入界面
    WebDriverWait(wd, 10).until(
        # 如果10秒内发现这个id就不再等待
        EC.presence_of_element_located((By.XPATH, "//*[@id=\"j-tag-list\"]"))
    )

    while 1:
        print("我准备开始刷新这个页面。")
        js = "var q=document.documentElement.scrollTop=100000"
        wd.execute_script(js)
        wd.find_element_by_xpath("//*[@id=\"j-refresh-btn\"]").click()
        # 三秒点一下更多
        time.sleep(1)
        try:
            if wd.find_element_by_class_name("isEmpty").text != "":
                break
        except Exception:
            print("not found isEmpty class")
            # 测试请打开 这个注释
            # break

    # //*[@id="j-tag-list"]
    j_tag_list = wd.find_element_by_id("j-tag-list").find_elements_by_tag_name("li")
    print("一共有 {} 个APP".format(len(j_tag_list)))

    for app_tag in j_tag_list:
        # 一个info信息
        app_detail = {}
        try:
            app_desc = app_tag.find_element_by_class_name("app-desc")
            a_info_attr = app_tag.find_element_by_class_name("detail-check-btn")

            comment = app_desc.find_element_by_class_name("comment").text
            span_info = app_desc.find_element_by_class_name("meta").find_elements_by_tag_name("span")

            app_title = app_desc.find_element_by_xpath("h2/a")
            app_detail["app_info_url"] = app_title.get_attribute("href")

            app_detail["app_info_name"] = app_title.get_attribute("title")

            app_id = a_info_attr.get_attribute("data-app-id")

            app_detail["app_info_download_url"] = download_url_format(app_id)

            app_detail["app_info_id"] = app_id
            app_detail["app_info_pname"] = a_info_attr.get_attribute("data-app-pname")
            app_detail["app_info_icon"] = a_info_attr.get_attribute("data-app-icon")

            app_detail["app_info_comment"] = comment
            app_detail["app_info_download_count"] = span_info[0].text
            app_detail["app_info_download_length"] = span_info[2].text

            print(app_detail)
            save_data_to_file(app_detail)
        except Exception:
            print("o fuck Exception...")



def save_data_to_file(line):
    str = json.dumps(line)
    with open(APPINFO_LIST_FILE_NAME, 'a+') as f:
        f.write(str + "\n")


def read_category_list():
    f = open(CATEGORY_LIST_FILE_NAME)
    lines = f.read()
    return json.loads(lines)


def ReadFile():
    if file_inode():
        # 拿到所有的类别
        list = read_category_list()
        for item_araray in list:
            for item in item_araray["item_araray"]:
                #  加载信息
                get_category_page_auto_load(item["item_href"])
                # 测试
                # time.sleep(1000)


    else:
        GetHtml("https://www.wandoujia.com/category/app")


if __name__ == '__main__':
    ReadFile()

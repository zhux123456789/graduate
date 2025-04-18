# -*- coding: utf-8 -*-
from selenium import webdriver
import time
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import csv
import re
def clean_text(text):
    """清洗文本数据"""
    if not text:
        return None
    text = re.sub(r'<[^>]+>', '', text)    # 去除HTML标签
    text = re.sub(r'http\S+|www\.\S+', '', text)    # 去除URL
    text = re.sub(r'[\r\n\t]+', ' ', text)  # 替换换行符
    text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)  # 匹配所有非字母数字汉字空格的字符
    text = re.sub(r'\s{2,}', ' ', text)  # 合并多个空格
    text = text.strip()    # 去除首尾空白
    return text if text else None
def start():
    a = Options()
    a.add_argument('--no-sandbox')
    a.add_experimental_option('detach', True)
    driver = webdriver.Edge(service=Service('msedgedriver.exe'), options=a)
    driver.get('https://movie.douban.com/subject/27606065/comments?status=P')
    return driver
# 表头定义
headers = ["原始评论", "清洗后评论"]
with open("result_selenium.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    driver = start()
    page_num = 0
    while True:
        page_num += 1
        driver.implicitly_wait(5)
        time.sleep(2)
        li_list = driver.find_elements(By.XPATH, '//*[@id="comments"]/div')
        for i in li_list[:-1]:
            try:
                raw_comment = i.find_element(By.XPATH, './/div[2]/p').text
                cleaned_comment = clean_text(raw_comment)
                if cleaned_comment:
                    writer.writerow([raw_comment, cleaned_comment])
            except Exception:
                continue
        # 检查是否有下一页
        next_buttons = driver.find_elements(By.XPATH, '//*[@id="paginator"]/a[contains(text(),"后页")]')
        if not next_buttons:
            break
        try:
            next_buttons[0].click()
        except Exception:
            break
driver.quit()
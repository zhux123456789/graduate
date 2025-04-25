# -*- coding: utf-8 -*-
from selenium import webdriver
import time
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import csv
import re
from typing import Dict

def clean_text(text):
    """清洗文本数据"""
    if not text:
        return None
    text = re.sub(r'<[^>]+>', '', text)  # 去除HTML标签
    text = re.sub(r'http\S+|www\.\S+', '', text)  # 去除URL
    text = re.sub(r'[\r\n\t]+', ' ', text)  # 替换换行符
    text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)  # 匹配所有非字母数字汉字空格的字符
    text = re.sub(r'\s{2,}', ' ', text)  # 合并多个空格
    text = text.strip()  # 去除首尾空白
    return text if text else None
class DoubanCrawler:
    def __init__(self):
        self.options = Options()
        self.options.add_argument('--no-sandbox')
        self.options.add_experimental_option('detach', True)
        self.driver = webdriver.Edge(service=Service('msedgedriver.exe'), options=self.options)

        # 性能统计
        self.total_requests = 0
        self.successful_requests = 0
        self.total_response_time = 0.0
        self.request_stats = []     #记录每次请求的详细数据
        self.page_load_times = []   #记录每个页面的加载时间

    def start(self, url):
        """启动浏览器并访问初始URL"""
        self.total_requests += 1
        start_time = time.time()
        try:
            self.driver.get(url)
            load_time = time.time() - start_time
            self.successful_requests += 1
            self.total_response_time += load_time
            self.request_stats.append({
                'url': url,
                'status': 'success',
                'duration': round(load_time, 2)
            })
            self.page_load_times.append(load_time)
            return True
        except Exception as e:
            self.request_stats.append({
                'url': url,
                'status': 'failed',
                'duration': round(time.time() - start_time, 2),
                'error': str(e)
            })
            return False

    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计摘要"""
        stats = {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'min_response_time': 0.0,
            'max_response_time': 0.0
        }
        if self.total_requests > 0:
            stats['success_rate'] = round(
                self.successful_requests / self.total_requests * 100, 2
            )
        if self.successful_requests > 0:
            stats['avg_response_time'] = round(
                self.total_response_time / self.successful_requests, 2
            )
            stats['min_response_time'] = round(min(self.page_load_times), 2)
            stats['max_response_time'] = round(max(self.page_load_times), 2)
        return stats

    def crawl(self, start_url):
        """主爬取流程"""
        # 表头定义
        headers = ["原始评论", "清洗后评论"]
        with open("result_selenium_model.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            if not self.start(start_url):
                return
            page_num = 0
            while True:
                page_num += 1
                self.driver.implicitly_wait(5)
                time.sleep(2)
                # 记录页面加载开始时间
                page_start = time.time()

                try:
                    li_list = self.driver.find_elements(By.XPATH, '//*[@id="comments"]/div')
                    for i in li_list[:-1]:
                        try:
                            raw_comment = i.find_element(By.XPATH, './/div[2]/p').text
                            cleaned_comment = clean_text(raw_comment)
                            if cleaned_comment:
                                writer.writerow([raw_comment, cleaned_comment])
                        except Exception:
                            continue

                    # 记录成功的页面处理
                    self.request_stats.append({
                        'url': self.driver.current_url,
                        'status': 'processed',
                        'duration': round(time.time() - page_start, 2)
                    })

                    # 检查是否有下一页
                    next_buttons = self.driver.find_elements(By.XPATH,'//*[@id="paginator"]/a[contains(text(),"后页")]')
                    if not next_buttons:
                        break

                    # 记录下一页点击
                    self.total_requests += 1
                    click_start = time.time()
                    try:
                        next_buttons[0].click()
                        click_time = time.time() - click_start
                        self.successful_requests += 1
                        self.total_response_time += click_time
                        self.request_stats.append({
                            'url': 'next_page_click',
                            'status': 'success',
                            'duration': round(click_time, 2)
                        })
                    except Exception as e:
                        self.request_stats.append({
                            'url': 'next_page_click',
                            'status': 'failed',
                            'duration': round(time.time() - click_start, 2),
                            'error': str(e)
                        })
                        break

                except Exception as e:
                    self.request_stats.append({
                        'url': self.driver.current_url,
                        'status': 'failed',
                        'duration': round(time.time() - page_start, 2),
                        'error': str(e)
                    })
                    break

    def close(self):
        """关闭浏览器"""
        self.driver.quit()


if __name__ == "__main__":
    crawler = DoubanCrawler()
    try:
        crawler.crawl('https://movie.douban.com/subject/27606065/comments?status=P')
    finally:
        # 输出性能摘要
        stats = crawler.get_performance_stats()
        print("\n=== 性能统计 ===")
        print(f"总请求次数: {stats['total_requests']}")
        print(f"成功请求次数: {stats['successful_requests']}")
        print(f"请求成功率: {stats['success_rate']}%")
        print(f"平均响应时间: {stats['avg_response_time']}秒")
        print(f"最短响应时间: {stats['min_response_time']}秒")
        print(f"最长响应时间: {stats['max_response_time']}秒")

        # 保存详细统计
        with open("selenium_stats.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'status', 'duration', 'error'])
            writer.writeheader()
            writer.writerows(crawler.request_stats)

        crawler.close()
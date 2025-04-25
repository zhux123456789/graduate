# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import csv
import re
from typing import List, Dict, Optional
from datetime import datetime


class WebCrawler:
    """网络爬虫核心类，包含数据清洗和性能统计功能"""

    def __init__(self):
        """初始化爬虫配置"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
        }
        self.request_interval = 0 # 每次请求之间的固定间隔(秒)
        self.start_time = None  # 爬虫启动时间
        self.end_time = None  # 爬虫结束时间

        # 性能统计变量
        self.total_requests = 0  # 总请求次数
        self.successful_requests = 0  # 成功次数
        self.total_response_time = 0.0  # 总成功时间，计算平均响应时间
        self.request_stats = []  # 存储每次请求的详细数据

    def clean_text(self, text: str) -> str:
        """清洗文本数据"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def fetch_page(self, url: str) -> Optional[str]:
        """获取网页内容并记录性能指标"""
        self.total_requests += 1
        start_time = time.time()
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            # 编码检测
            if 'charset' in response.headers.get('content-type', '').lower():
                response.encoding = re.search(
                    r'charset=([\w-]+)',
                    response.headers['content-type'],
                    re.IGNORECASE
                ).group(1)
            else:
                response.encoding = response.apparent_encoding
            # 记录成功指标
            duration = time.time() - start_time
            self.successful_requests += 1
            self.total_response_time += duration
            self.request_stats.append({
                'url': url,
                'status': 'success',  # 状态
                'duration': round(duration, 2)  # 耗时
            })
            return response.text
        except requests.exceptions.RequestException as e:
            # 记录失败指标
            duration = time.time() - start_time
            self.request_stats.append({
                'url': url,
                'status': 'failed',
                'duration': round(duration, 2),
                'error': str(e)
            })
            return None

    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计摘要"""
        stats = {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'min_response_time': 0.0,
            'max_response_time': 0.0,
            'total_runtime': 0.0,
            'total_sleep_time': 0.0,
            'sleep_percentage': 0.0
        }

        if self.start_time and self.end_time:
            stats['total_runtime'] = round(self.end_time - self.start_time, 2)

        if self.total_requests > 0:
            stats['success_rate'] = round(
                self.successful_requests / self.total_requests * 100, 2
            )
            # 计算总休眠时间 (每次请求后休眠，除了最后一次)
            stats['total_sleep_time'] = round(
                (self.total_requests - 1) * self.request_interval, 2
            )
            if stats['total_runtime'] > 0:
                stats['sleep_percentage'] = round(
                    stats['total_sleep_time'] / stats['total_runtime'] * 100, 2
                )

        if self.successful_requests > 0:
            stats['avg_response_time'] = round(
                self.total_response_time / self.successful_requests, 2
            )
            successful_durations = [r['duration'] for r in self.request_stats if r['status'] == 'success']
            stats['min_response_time'] = round(min(successful_durations), 2)
            stats['max_response_time'] = round(max(successful_durations), 2)

        return stats

    def parse_html(self, html: str):
        """解析HTML内容"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for item in soup.find_all('div', class_="comment-item"):
            try:
                raw_content = item.find('span', class_='short').text
                cleaned_content = self.clean_text(raw_content)
                if cleaned_content:
                    results.append({
                        'raw_content': raw_content,
                        'cleaned_content': cleaned_content
                    })
            except:
                continue
        return results

    def save_data(self, data, filename: str = 'result_request_model.csv'):
        """保存数据到CSV"""
        if not data:
            return
        fieldnames = ['raw_content', 'cleaned_content']
        try:
            with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerows(data)
        except:
            pass

    def save_stats(self, filename: str = 'stats_request.csv'):
        """保存详细请求统计"""
        if not self.request_stats:
            return
        fieldnames = ['url', 'status', 'duration', 'error']
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.request_stats)
        except:
            pass

    def crawl(self, start_url: str):
        """主爬取流程"""
        self.start_time = time.time()
        current_url = start_url
        while current_url:
            html = self.fetch_page(current_url)
            if html:
                data = self.parse_html(html)
                self.save_data(data)
                soup = BeautifulSoup(html, 'html.parser')
                next_link = soup.find('a', class_='next')
                if next_link and 'href' in next_link.attrs:
                    current_url = 'https://movie.douban.com/subject/35603727/comments' + next_link['href']
                    # 在每次请求后休眠，除了最后一次
                    if current_url:
                        time.sleep(self.request_interval)
                else:
                    current_url = None
        self.end_time = time.time()


if __name__ == '__main__':
    crawler = WebCrawler()
    start_url = 'https://movie.douban.com/subject/35603727/comments?status=P'
    try:
        crawler.crawl(start_url)
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
        print(f"总运行时间: {stats['total_runtime']}秒")
        print(f"总休眠时间: {stats['total_sleep_time']}秒")
        print(f"休眠时间占比: {stats['sleep_percentage']}%")

        # 保存详细统计
        crawler.save_stats()
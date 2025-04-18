# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import csv
import logging
import re
from typing import List, Dict, Optional

# 配置日志记录系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class WebCrawler:
    """网络爬虫核心类，包含数据清洗功能"""

    def __init__(self):
        """初始化爬虫配置"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
        }
        self.request_interval = 2
        self.proxies = None
        self.max_retries = 3  # 最大重试次数

    def clean_text(self, text: str) -> str:
        """
        清洗文本数据
        Args:
            text: 需要清洗的原始文本
        Returns:
            str: 清洗后的文本
        """
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)        # 去除HTML标签
        text = re.sub(r'[\r\n\t]+', ' ', text)        # 去除特殊字符
        text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)  # 匹配所有非字母数字汉字空格的字符
        text = re.sub(r'\s{2,}', ' ', text)  # 合并多个空格
        text = text.strip()        # 去除首尾空白
        text = text.replace('\u3000', ' ').replace('\xa0', ' ')        # 替换不常见字符
        return text

    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取指定URL的网页内容
        Args:
            url: 要请求的网页URL
        Returns:
            str: 成功返回网页HTML内容，失败返回None
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=10
                )
                response.raise_for_status()

                # 更精确的编码检测
                if 'charset' in response.headers.get('content-type', '').lower():
                    response.encoding = re.search(
                        r'charset=([\w-]+)',
                        response.headers['content-type'],
                        re.IGNORECASE
                    ).group(1)
                else:
                    response.encoding = response.apparent_encoding

                return response.text
            except requests.exceptions.RequestException as e:
                logging.warning(f"请求失败(尝试 {attempt + 1}/{self.max_retries}): {url} - {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # 指数退避
                continue
        logging.error(f"请求最终失败: {url}")
        return None

    def parse_html(self, html: str) -> List[Dict]:
        """
        解析HTML内容并提取结构化数据
        Args:
            html: 需要解析的HTML字符串
        Returns:
            List[Dict]: 包含提取数据的字典列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for item in soup.find_all('div', class_="comment-item"):
            try:
                # 提取原始数据
                raw_content = item.find('span', class_='short').text

                # 数据清洗
                cleaned_content = self.clean_text(raw_content)
                # 跳过空评论
                if not cleaned_content:
                    continue

                # 构建数据字典（包含原始和清洗后内容）
                data = {
                    'raw_content': raw_content,
                    'cleaned_content': cleaned_content,
                }
                results.append(data)

            except Exception as e:
                logging.warning(f"解析异常: {str(e)}")
                continue
        return results

    def save_data(self, data: List[Dict], filename: str = 'result_request.csv'):
        """
        将清洗后的数据保存到CSV文件
        Args:
            data: 要保存的数据列表（字典格式）
            filename: 保存文件名
        """
        if not data:
            logging.info("没有有效数据需要保存")
            return

        # 定义CSV字段顺序（包含原始和清洗后字段）
        fieldnames = ['raw_content', 'cleaned_content']

        try:
            # 检查文件是否存在以决定是否写入表头
            write_header = not self._file_exists(filename)

            with open(filename, 'a', newline='', encoding='utf-8-sig') as f:  # utf-8-sig处理Excel兼容问题
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if write_header:
                    writer.writeheader()

                writer.writerows(data)
                logging.info(f"成功保存 {len(data)} 条数据到 {filename}")

        except Exception as e:
            logging.error(f"保存数据失败: {str(e)}")

    def _file_exists(self, filename: str) -> bool:
        """检查文件是否存在且不为空"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                # 尝试读取第一行
                f.readline()
                return True
        except (FileNotFoundError, IOError):
            return False

    def crawl(self, start_url: str):
        """
        爬虫主控制流程
        Args:
            start_url: 起始URL
        """
        current_url = start_url
        while current_url:
            logging.info(f"开始处理页面: {current_url}")

            # 获取页面内容
            html = self.fetch_page(current_url)
            if not html:
                break

            # 解析并保存数据
            data = self.parse_html(html)
            self.save_data(data)

            # 查找下一页
            soup = BeautifulSoup(html, 'html.parser')
            next_link = soup.find('a', class_='next')

            if next_link and 'href' in next_link.attrs:
                current_url = 'https://movie.douban.com/subject/35603727/comments' + next_link['href']
                time.sleep(self.request_interval)
            else:
                current_url = None

        logging.info("爬取任务完成")


if __name__ == '__main__':
    # 创建爬虫实例
    crawler = WebCrawler()

    # 开始爬取
    start_url = 'https://movie.douban.com/subject/35603727/comments?status=P'
    crawler.crawl(start_url)
import requests
import threading
from queue import Queue
from bs4 import BeautifulSoup
import time
import csv
import random
import re  # 新增导入re模块


# ================== 代理池部分 ==================
class ProxyPool:
    def __init__(self):
        self.API_URL = "https://dps.kdlapi.com/api/getdps/?secret_id=oqjf2rg0ohkjq5fne3up&signature=umo268qrc72jx2lqf7yrthcakypsgr98&num=3&pt=1&format=text&sep=1"
        self.USERNAME = "d2183389021"
        self.PASSWORD = "231wtih8"
        self.proxy_queue = Queue()
        self.THREAD_COUNT = 5

    def fetch_proxies(self):
        """获取代理列表"""
        try:
            print("正在从代理API获取代理IP...")
            response = requests.get(self.API_URL, timeout=10)
            if response.status_code == 200:
                proxies = [{
                    "http": f"http://{self.USERNAME}:{self.PASSWORD}@{ip}/",
                    "https": f"http://{self.USERNAME}:{self.PASSWORD}@{ip}/"
                } for ip in response.text.strip().split('\n') if ip]
                print(f"成功获取 {len(proxies)} 个代理IP")
                return proxies
            print("获取代理失败: 状态码", response.status_code)
            return []
        except Exception as e:
            print("获取代理异常:", str(e))
            return []

    def init_proxy_pool(self):
        """初始化代理池"""
        proxies = self.fetch_proxies()
        if not proxies:
            raise Exception("获取代理失败")
        for p in proxies:
            self.proxy_queue.put(p)
        print("代理池初始化完成")


# ================== 爬虫部分 ==================
class DoubanCrawler:
    def __init__(self, proxy_pool):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Core/1.94.249.400 QQBrowser/12.5.5659.400',
            'cookie': '_TDID_CK=1744910449602; 6333762c95037d16=llodr4gW7Y2OsfnhfKcguS5DvhDJknivL2RToqF1OtzhWETUha6WYRDQ7Z38uxtxyF%2Bd2yYzJ1agaZlMwTmwhOu2etpxKD%2BN0Fl5BWdXgWygqZjEMbZSfJOIxlLZrdmjC00aLFEBF4hBbRi8SljE%2FqmcWsKjtL1qXI4fXkDhBPTWKBg%2FmgkFLmLhkQ7tUsU03NfqchKHduGXgDqf9pDcSwcXJQilLC1SiBbIJVrXk4ta1uoJzps7Z4CeYZAD6dSBtuf%2B2iTSMev0bCX9Ykfj137RoYJC7EDL0ToS6WpkqG4dpBX%2BOtVmhw%3D%3D; bid=7fJOYgrbJHI; _pk_id.100001.4cf6=27bd481415e42dbf.1742379762.; ll="118200"; _vwo_uuid_v2=DC7A0101853C609944DCA618C5C7C731E|dd905dd5ea7f07427f2d0502ea746342; __yadk_uid=LMBd8SyR8PheeTNhDKf8uLz75nAOGyYy; push_noty_num=0; push_doumail_num=0; __utmv=30149280.28004; __utma=30149280.1024150468.1742379762.1744728782.1744908847.14; __utmc=30149280; __utmz=30149280.1744908847.14.9.utmcsr=cn.bing.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt=1; dbcl2="280044689:kFqoWMd7nnc"; ck=fGWy; __utmt_douban=1; __utma=223695111.665774635.1742379762.1744728782.1744910439.14; __utmb=223695111.0.10.1744910439; __utmc=223695111; __utmz=223695111.1744910439.14.10.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1744910439%2C%22https%3A%2F%2Fwww.douban.com%2F%22%5D; _pk_ses.100001.4cf6=1; frodotk_db="db29954f297708d1917cbfed7c651a73"; __utmb=30149280.6.10.1744908847'
        }
        self.request_interval = 3
        self.proxy_pool = proxy_pool
        self.lock = threading.Lock()
        self.url_lock = threading.Lock()

    def fetch_page(self, url):
        """使用代理获取页面"""
        proxy = self.proxy_pool.proxy_queue.get()
        try:
            print(f"使用代理: {proxy['http']}")

            response = requests.get(
                url,
                headers=self.headers,
                proxies=proxy,
                timeout=15
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"爬取失败: {str(e)}")
            return None
        finally:
            self.proxy_pool.proxy_queue.put(proxy)
            # 随机延迟，避免固定频率
            time.sleep(self.request_interval + random.uniform(0, 1.5))

    def parse_html(self, html):
        """解析豆瓣评论"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        comments = soup.find_all('div', attrs={"class": "comment-item"})
        print(f"找到 {len(comments)} 条评论")

        for item in comments:
            try:
                data = {
                    'content': item.find('span', attrs={'class': 'short'}).text.strip(),
                    # 'rating': item.find('span', attrs={'class': 'rating'}).get('title', '无评分'),
                    # 'time': item.find('span', attrs={'class': 'comment-time'}).text.strip()
                }
                print(f"评论内容: {data['content']}")
                # print(f"评分: {data['rating']}, 时间: {data['time']}")
                print("-" * 50)
                results.append(data)
            except Exception as e:
                print(f"解析评论失败: {str(e)}")
                continue
        return results

    def clean_text(self, text):
        """清洗文本数据，去除无关字符和格式"""
        if not text:
            return None
        text = re.sub(r'<[^>]+>', '', text)  # 去除HTML标签
        text = re.sub(r'http\S+|www\.\S+', '', text)  # 去除URL链接
        text = re.sub(r'[\r\n\t]+', ' ', text)  # 替换换行符和制表符为空格
        text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)  # 只保留字母、数字、汉字和空格
        text = re.sub(r'\s{2,}', ' ', text)  # 合并多个连续空格
        text = text.strip()  # 去除首尾空白字符
        return text if text else None  # 返回有效文本或None

    def save_data(self, data, filename='result_request.csv'):
        """线程安全的保存方法，同时保存原始数据和清洗后的数据"""
        with self.lock:
            # 处理每条数据，添加清洗后的内容
            processed_data = []
            for item in data:
                cleaned_item = item.copy()  # 创建副本避免修改原始数据
                # 清洗content字段
                cleaned_item['cleaned_content'] = self.clean_text(item['content'])
                processed_data.append(cleaned_item)

            # 定义CSV文件的字段名
            fieldnames = ['content', 'cleaned_content']

            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if f.tell() == 0:  # 如果是新文件，写入表头
                    writer.writeheader()
                writer.writerows(processed_data)

            print(f"已保存 {len(processed_data)} 条数据到 {filename}，包含原始内容和清洗后内容")

    def get_all_page_urls(self, start_url):
        """获取所有分页URL"""
        print("\n开始收集所有分页URL...")
        urls = [start_url]
        current_url = start_url
        page_count = 1
        while True:
            html = self.fetch_page(current_url)
            if not html:
                print(f"无法获取页面内容，终止收集")
                break
            next_url = self.extract_next_url(current_url, html)
            if not next_url:
                print("没有找到下一页链接，终止收集")
                break
            if next_url in urls:
                print("下一页URL已存在，终止收集")
                break
            urls.append(next_url)
            current_url = next_url
            page_count += 1
            time.sleep(self.request_interval + random.uniform(0, 2))

        print(f"\n共收集到 {len(urls)} 个分页URL:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
        return urls

    def extract_next_url(self, current_url, html):
        """从parse_html中获取的数据爬取出下一页的URL"""
        soup = BeautifulSoup(html, 'html.parser')
        try:
            next_page = soup.find('a', class_='next')['href']
            next_url = requests.compat.urljoin(current_url, next_page)
            print(f"找到下一页URL: {next_url}")
            return next_url
        except Exception as e:
            print(f"提取下一页URL失败: {str(e)}")
            return None

    def worker(self, thread_id, url_list):
        """工作线程处理分配的URL列表"""
        print(f"\n线程 {thread_id} 启动，分配了 {len(url_list)} 个URL:")
        for i, url in enumerate(url_list, 1):
            print(f"线程 {thread_id} 处理第 {i}/{len(url_list)} 个URL: {url}")

            html = self.fetch_page(url)
            if html:
                data = self.parse_html(html)
                if data:
                    self.save_data(data)
                    print(f"线程 {thread_id} 已从 {url} 爬取 {len(data)} 条数据")

            # 随机延迟，避免固定频率
            time.sleep(self.request_interval + random.uniform(0, 1))
        print(f"\n线程 {thread_id} 已完成所有任务")


# ================== 主程序 ==================
if __name__ == '__main__':
    try:
        # 初始化代理池
        print("初始化代理池...")
        proxy_pool = ProxyPool()
        proxy_pool.init_proxy_pool()

        # 创建爬虫实例
        print("\n创建爬虫实例...")
        crawler = DoubanCrawler(proxy_pool)
        start_url = 'https://movie.douban.com/subject/35603727/comments?status=P'
        print(f"起始URL: {start_url}")

        # 第一步：获取所有分页URL
        all_urls = crawler.get_all_page_urls(start_url)
        if not all_urls:
            raise Exception("未获取到任何分页URL")

        # 第二步：分配URL给各线程
        print(f"\n将 {len(all_urls)} 个URL分配给 {proxy_pool.THREAD_COUNT} 个线程...")
        threads = []
        chunk_size = len(all_urls) // proxy_pool.THREAD_COUNT + 1

        for i in range(proxy_pool.THREAD_COUNT):
            start = i * chunk_size
            end = (i + 1) * chunk_size
            thread_urls = all_urls[start:end]

            if not thread_urls:
                print(f"线程 {i + 1} 没有分配到URL，跳过")
                continue

            print(f"线程 {i + 1} 分配到 {len(thread_urls)} 个URL")
            t = threading.Thread(
                target=crawler.worker,
                args=(i + 1, thread_urls)
            )
            t.start()
            threads.append(t)
            time.sleep(1 + random.uniform(0, 1))  # 避免同时发起请求

        # 等待所有线程完成
        print("\n等待所有线程完成...")
        for t in threads:
            t.join()

    except Exception as e:
        print(f"\n程序异常终止: {str(e)}")
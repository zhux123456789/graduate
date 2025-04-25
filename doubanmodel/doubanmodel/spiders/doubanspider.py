from typing import Iterable
from ..items import DoubanItem
import scrapy
from scrapy import Request
import time
from collections import defaultdict


class DoubanSpiderSpider(scrapy.Spider):
    name = 'doubanspider'
    allowed_domains = ['movie.douban.com']

    # Initialize statistics
    def __init__(self, *args, **kwargs):
        super(DoubanSpiderSpider, self).__init__(*args, **kwargs)
        self.stats = defaultdict(int)
        self.response_times = []
        self.start_time = time.time()

    def start_requests(self) -> Iterable[Request]:
        # Your existing cookie and header setup
        cookie_str = 'bid=j5GxGkea1xY; ll="118200"; _pk_id.100001.4cf6=4b7169ae9091b92d.1741676850.; push_doumail_num=0; push_noty_num=0; __yadk_uid=9YMMvEi9PMt2bPkAN9QpgviGHHf23C1j; _vwo_uuid_v2=DA43E21C0F8B41C25531D1CFE741208CB|fc0f776385df39e7280b682ef520dedf; __utmv=30149280.28004; __utma=30149280.2115326024.1741676810.1745196734.1745247083.24; __utmc=30149280; __utmz=30149280.1745247083.24.10.utmcsr=sogou.com|utmccn=(referral)|utmcmd=referral|utmcct=/link; __utmt=1; __utmb=30149280.1.10.1745247083; __utma=223695111.1719922726.1741676850.1745196736.1745247090.21; __utmb=223695111.0.10.1745247090; __utmc=223695111; __utmz=223695111.1745247090.21.9.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1745247090%2C%22https%3A%2F%2Fwww.douban.com%2F%22%5D; _pk_ses.100001.4cf6=1; ap_v=0,6.0; 6333762c95037d16=VZ7%2BDNdd4ReIlIX4p0WQ7tTCi6ZCcSBNC22%2BtdTt253f889LAnKWl6Tqpd7Ef9mhFT06Mxj6JSt9JOwO5cPmFw5%2FfY%2BpWSDqzM3u9a0jJw03GBkK6EQ2494WFF9Sdi9lCTx%2B22rVbPaWbcboVsafx356riCaljUdE2eong3yQHdcgEFxdyI2FN3dGV24anFOXUU7NqD%2BUyzog%2BQdYKBu%2FgL3%2FhjeUWv7Nm13ucnjjG13KRNo3%2B0%2F%2BU3idOTZQCLrVTry9tSbNQmf8YyRgobMUrWOJDsH4qQ01%2FhzBvG5cy09Yhznafec6g%3D%3D; _TDID_CK=1745247091571'
        cookies = {}
        for cookie in cookie_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value.strip()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Core/1.94.249.400 QQBrowser/12.5.5659.400',
            'Referer': 'https://movie.douban.com/',
            'Host': 'movie.douban.com'
        }

        # Track initial request
        self.stats['total_requests'] += 1
        yield Request(
            url='https://movie.douban.com/subject/30290253/comments',
            cookies=cookies,
            headers=headers,
            callback=self.parse,
            meta={'request_start': time.time()}
        )

    def parse(self, response):
        # Track response time
        request_time = time.time() - response.meta['request_start']
        self.response_times.append(request_time)

        # Check for anti-scraping
        if "sec.douban.com" in response.url:
            self.stats['failed_requests'] += 1
            self.logger.error("触发反爬验证！请更新 Cookie 或使用代理")
            return

        self.stats['successful_requests'] += 1

        # Your existing parsing logic
        movie_list = response.xpath('//div[@class="mod-bd"]//div')
        for i_item in movie_list:
            douban_item = DoubanItem()
            douban_item['movie_comment'] = i_item.xpath(
                './/div[@class="comment"]//p[@class="comment-content"]//span[@class="short"]//text()').extract_first()
            yield douban_item

        # Parse next page
        next_link = response.xpath('.//div[@id="paginator"]//a[@class="next"]//@href').extract()
        if next_link:
            self.stats['total_requests'] += 1
            yield scrapy.Request(
                "https://movie.douban.com/subject/30290253/comments" + next_link[0],
                callback=self.parse,
                meta={'request_start': time.time()}
            )

    def closed(self, reason):
        # Calculate statistics when spider closes
        total_time = time.time() - self.start_time
        stats = {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats.get('successful_requests', 0),
            'failed_requests': self.stats.get('failed_requests', 0),
            'total_time': round(total_time, 2)
        }

        if self.response_times:
            stats.update({
                'avg_response_time': round(sum(self.response_times) / len(self.response_times), 2),
                'min_response_time': round(min(self.response_times), 2),
                'max_response_time': round(max(self.response_times), 2),
                'success_rate': round(stats['successful_requests'] / stats['total_requests'] * 100, 2)
            })

        # Print statistics
        print("\n=== 性能统计 ===")
        print(f"总请求次数: {stats['total_requests']}")
        print(f"成功请求次数: {stats['successful_requests']}")
        print(f"失败请求次数: {stats['failed_requests']}")
        print(f"请求成功率: {stats.get('success_rate', 0)}%")
        print(f"平均响应时间: {stats.get('avg_response_time', 0)}秒")
        print(f"最短响应时间: {stats.get('min_response_time', 0)}秒")
        print(f"最长响应时间: {stats.get('max_response_time', 0)}秒")
        print(f"总运行时间: {stats['total_time']}秒")
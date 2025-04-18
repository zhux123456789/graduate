from typing import Iterable


from douban.items import DoubanItem
import scrapy
from scrapy import Request


class DoubanSpiderSpider(scrapy.Spider):
    name = 'douban_spider'
    allowed_domains = ['movie.douban.com']

    # 不再使用 start_urls，改用自定义请求
    def start_requests(self) -> Iterable[Request]:
        # 需要从浏览器获取最新的 bid 值（关键！）
        cookie_str = 'bid=j5GxGkea1xY; ll="118200"; _pk_id.100001.4cf6=4b7169ae9091b92d.1741676850.; push_noty_num=0; push_doumail_num=0; __yadk_uid=9YMMvEi9PMt2bPkAN9QpgviGHHf23C1j; _vwo_uuid_v2=DA43E21C0F8B41C25531D1CFE741208CB|fc0f776385df39e7280b682ef520dedf; __utmv=30149280.28004; __utmz=30149280.1744717785.16.5.utmcsr=sogou.com|utmccn=(referral)|utmcmd=referral|utmcct=/link; __utma=30149280.2115326024.1741676810.1744730915.1744736561.18; __utma=223695111.1719922726.1741676850.1744730915.1744736584.16; __utmz=223695111.1744736584.16.5.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; ap_v=0,6.0; dbcl2="280044689:oEghxgZRoV4"; ck=vkEp; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1744868015%2C%22https%3A%2F%2Fopen.weixin.qq.com%2F%22%5D; _pk_ses.100001.4cf6=1; frodotk_db="de6529a1efd2f6739b2f7ce5cf78e359"'
        # 转换为字典
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

        # 初始请求需要携带 cookies 和 headers
        yield Request(
            url='https://movie.douban.com/subject/30290253/comments',
            cookies=cookies,
            headers=headers,
            callback=self.parse
        )

    # 默认解析方法
    def parse(self, response):
        # 检查是否被重定向到验证页
        if "sec.douban.com" in response.url:
            self.logger.error("触发反爬验证！请更新 Cookie 或使用代理")
            return
        movie_list = response.xpath('//div[@class="mod-bd"]//div')
        for i_item in movie_list:
            # 创建DoubanItem类，写详细的XPath并进行数据解析
            douban_item = DoubanItem()
            # 获取电影名
            douban_item['movie_comment'] = i_item.xpath(
                './/div[@class="comment"]//p[@class="comment-content"]//span[@class="short"]//text()').extract_first()

            # 将数据yield到piplines里面
            yield douban_item  # 进入到pipelines

        # 解析下一页规则，取后页的XPath
        next_link = response.xpath('.//div[@id="paginator"]//a[@class="next"]//@href').extract()
        if next_link:  # 判断是否到最后一页
            next_link = next_link[0]
            yield scrapy.Request("https://movie.douban.com/subject/30290253/comments"+next_link, callback=self.parse)

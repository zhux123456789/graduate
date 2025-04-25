from typing import Iterable
from doubanf.douban.items import DoubanItem
import scrapy
from scrapy import Request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class DoubanSpiderSpider(scrapy.Spider):
    name = 'douban_spider'
    allowed_domains = ['movie.douban.com']

    def __init__(self, *args, **kwargs):
        super(DoubanSpiderSpider, self).__init__(*args, **kwargs)
        # 初始化Selenium浏览器驱动
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)

        # 设置浏览器cookie
        self.driver.get("https://movie.douban.com")
        cookie_str = 'bid=7fJOYgrbJHI; _pk_id.100001.4cf6=27bd481415e42dbf.1742379762.; ll="118200"; _vwo_uuid_v2=DC7A0101853C609944DCA618C5C7C731E|dd905dd5ea7f07427f2d0502ea746342; __yadk_uid=LMBd8SyR8PheeTNhDKf8uLz75nAOGyYy; push_noty_num=0; push_doumail_num=0; __utmv=30149280.28004; ap_v=0,6.0; __utma=30149280.1024150468.1742379762.1745246659.1745257202.19; __utmc=30149280; __utmz=30149280.1745257202.19.13.utmcsr=ntp.msn.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt_douban=1; __utmb=30149280.1.10.1745257202; __utma=223695111.665774635.1742379762.1745246659.1745257202.19; __utmb=223695111.0.10.1745257202; __utmc=223695111; __utmz=223695111.1745257202.19.14.utmcsr=ntp.msn.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1745257204%2C%22https%3A%2F%2Fntp.msn.cn%2F%22%5D; _pk_ses.100001.4cf6=1'
        for cookie in cookie_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                self.driver.add_cookie({'name': name.strip(), 'value': value.strip()})

    def start_requests(self) -> Iterable[Request]:
        # 使用Selenium处理页面，不再需要直接发送Request
        url = 'https://movie.douban.com/subject/30290253/comments'
        yield Request(url=url, callback=self.parse_with_selenium)

    def parse_with_selenium(self, response):
        # 使用Selenium加载页面
        self.driver.get(response.url)

        # 检查是否被重定向到验证页
        if "sec.douban.com" in self.driver.current_url:
            self.logger.error("触发反爬验证！请更新Cookie")
            return

        # 等待评论加载完成
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="comment-item"]'))
            )
        except Exception as e:
            self.logger.error(f"等待评论加载超时: {str(e)}")
            return

        # 滚动页面以加载更多内容（如果需要）
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 使用Selenium解析数据
        comments = self.driver.find_elements(By.XPATH, '//div[@class="comment-item"]')
        for comment in comments:
            douban_item = DoubanItem()
            try:
                content = comment.find_element(By.XPATH, './/span[@class="short"]').text
                douban_item['movie_comment'] = content
                yield douban_item
            except Exception as e:
                self.logger.error(f"解析评论出错: {str(e)}")
                continue

        # 处理下一页
        try:
            next_button = self.driver.find_element(By.XPATH, '//a[@class="next"]')
            if next_button:
                next_url = next_button.get_attribute('href')
                if next_url:
                    yield Request(url=next_url, callback=self.parse_with_selenium)
        except Exception as e:
            self.logger.error(f"找不到下一页按钮: {str(e)}")

    def closed(self, reason):
        # 爬虫关闭时退出浏览器
        self.driver.quit()
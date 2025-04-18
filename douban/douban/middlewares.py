# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from twisted.internet import error
import requests
from scrapy import signals
import logging
from urllib.parse import urlparse
import time
import random
from twisted.web._newclient import ResponseNeverReceived


class ProxyMiddleware:
    """
    动态代理中间件（自动更换IP并打印到控制台）
    功能：管理代理IP池，自动为每个请求分配不同代理
    """

    def __init__(self, proxy_api, proxy_user, proxy_pass):
        self.proxy_api = proxy_api  # 代理IP获取接口地址
        self.proxy_user = proxy_user  # 代理服务用户名
        self.proxy_pass = proxy_pass  # 代理服务密码
        self.current_proxy = None  # 当前使用的代理配置缓存
        self.proxy_pool = []  # 可用的代理IP列表池
        self.proxy_index = 0  # 当前使用的代理索引（实现轮询）

    @classmethod
    def from_crawler(cls, crawler):     # Scrapy标准初始化方法
        proxy_api = crawler.settings.get('PROXY_API_URL')  # 从配置读取API地址
        proxy_user = crawler.settings.get('PROXY_USER')  # 从配置读取用户名
        proxy_pass = crawler.settings.get('PROXY_PASSWORD')  # 从配置读取密码

        middleware = cls(proxy_api, proxy_user, proxy_pass)  # 创建中间件实例
        crawler.signals.connect(middleware.spider_opened, signals.spider_opened)  # 注册爬虫启动信号
        return middleware  # 返回中间件实例

    def spider_opened(self, spider):
        """爬虫启动时初始化代理池"""
        self.refresh_proxy_pool()  # 首次加载代理IP池

    def refresh_proxy_pool(self):
        """从API接口刷新代理IP池"""
        try:
            response = requests.get(self.proxy_api)  # 请求代理API
            self.proxy_pool = [ip.strip() for ip in response.text.split('\n') if ip.strip()]  # 解析IP列表
            self.proxy_index = 0  # 重置轮询索引
            print(f"\n[Proxy] 已刷新代理池，获取到 {len(self.proxy_pool)} 个IP")  # 打印
        except Exception as e:
            print(f"\n[Proxy Error] 刷新代理池失败: {str(e)}")  # 异常处理

    def get_next_proxy(self):
        """获取下一个可用代理IP（轮询机制）"""
        if not self.proxy_pool:  # 代理池为空时
            self.refresh_proxy_pool()  # 尝试刷新
            if not self.proxy_pool:  # 仍然为空则返回None
                return None
        proxy_ip = self.proxy_pool[self.proxy_index % len(self.proxy_pool)]  # 轮询获取IP
        self.proxy_index += 1  # 索引递增
        if self.proxy_index % 10 == 0:  # 每10次请求刷新代理池
            self.refresh_proxy_pool()
        print(f"\033[94m[Proxy] 使用代理: \033[93m{proxy_ip}\033[0m")  # 彩色打印代理信息
        return {  # 返回格式化代理配置
            "http": f"http://{self.proxy_user}:{self.proxy_pass}@{proxy_ip}",
            "https": f"http://{self.proxy_user}:{self.proxy_pass}@{proxy_ip}"
        }

    def process_request(self, request, spider):
        """处理每个请求（核心方法）"""
        self.current_proxy = self.get_next_proxy()  # 获取新代理
        if not self.current_proxy:  # 无可用代理时
            print("\033[91m[Proxy Error] 无可用代理IP!\033[0m")  # 打印红色错误
            return

        scheme = 'https' if request.url.startswith('https') else 'http'  # 识别协议类型
        request.meta['proxy'] = self.current_proxy[scheme]  # 设置代理
        request.headers['Proxy-Authorization'] = f'Basic {self.proxy_user}:{self.proxy_pass}'  # 认证头
        request.meta['proxy_info'] = self.current_proxy  # 保存代理信息


class CustomRetryMiddleware:
    """增强版重试中间件（核心功能注释）"""

    def __init__(self, settings):
        # 初始化重试配置参数
        self.max_retry_times = settings.getint('RETRY_TIMES', 3)  # 最大重试次数（默认3次）
        retry_codes = settings.getlist('RETRY_HTTP_CODES',
                                       [500, 502, 503, 504, 400, 403, 404, 408, 429])  # 需要重试的HTTP状态码
        self.retry_http_codes = set(int(x) for x in retry_codes)  # 转换为集合提高查询效率
        self.retry_exceptions = (error.TimeoutError, error.TCPTimedOutError,  # 需要重试的异常类型
                                 error.ConnectionLost, ResponseNeverReceived)
        self.retry_delay = settings.getfloat('RETRY_DELAY', 1)  # 基础重试延迟（秒）

    @classmethod
    def from_crawler(cls, crawler):    # Scrapy标准初始化方法
        return cls(crawler.settings)  # 从crawler配置创建实例

    def process_response(self, request, response, spider):       # 响应处理入口
        if request.meta.get('dont_retry', False):  # 检查是否标记不重试
            return response
        # 状态码重试逻辑
        if response.status in self.retry_http_codes:  # 匹配需要重试的状态码
            return self._handle_failure(request, f"HTTP {response.status}", spider)  # 调用统一失败处理
        return response  # 正常响应直接返回

    def process_exception(self, request, exception, spider):
        # 异常处理入口
        if isinstance(exception, self.retry_exceptions):  # 匹配需要重试的异常类型
            return self._handle_failure(request, str(exception), spider)  # 调用统一失败处理
        return None  # 其他异常不处理

    def _handle_failure(self, request, reason, spider):
        # 统一失败处理方法
        proxy = request.meta.get('proxy', '无代理')  # 提取代理信息
        # 打印红色错误日志（包含失败原因和代理信息）
        print(f"\033[91m[FAIL] 请求失败 ({reason}) | 代理: {proxy.split('@')[-1] if '@' in proxy else proxy}\033[0m")

        retries = request.meta.get('retry_times', 0) + 1  # 计算当前重试次数

        if retries <= self.max_retry_times:  # 判断是否超过最大重试次数
            delay = self.retry_delay * (1 + random.random())  # 计算随机延迟时间（1-2倍基础延迟）
            # 打印黄色重试提示（包含延迟时间和重试计数）
            print(f"\033[93m[RETRY] 将在 {delay:.1f}s 后重试 ({retries}/{self.max_retry_times})\033[0m")
            time.sleep(delay)  # 执行延迟

            # 尝试获取新代理（需配合ProxyMiddleware使用）
            proxy_middleware = spider.crawler.engine.downloader.middleware.middlewares[0]
            if hasattr(proxy_middleware, 'get_proxy'):
                proxy_middleware.get_proxy()

            # 创建重试请求（保留原请求参数）
            retry_req = request.copy()
            retry_req.meta['retry_times'] = retries  # 更新重试次数
            retry_req.dont_filter = True  # 避免去重过滤
            return retry_req  # 返回新请求

        # 超过最大重试次数时打印红色终止提示
        print(f"\033[91m[ABORT] 放弃重试 (已达最大重试次数 {self.max_retry_times})\033[0m")
        return None  # 终止重试

    def _retry(self, request, reason, spider):
        # 基础重试逻辑
        retries = request.meta.get('retry_times', 0) + 1   # 获取当前已重试次数（从request.meta中读取，默认0）+1得到新次数
        if retries <= self.max_retry_times:
            retryreq = request.copy()        # 克隆原始请求（避免修改原始请求对象）
            retryreq.meta['retry_times'] = retries     # 更新重试次数到新请求的meta中
            retryreq.dont_filter = True     # 禁用去重过滤（确保重试请求不会被过滤系统拦截）
            return retryreq       # 返回新构造的重试请求（Scrapy会重新调度该请求
        spider.logger.error(f"Gave up retrying {request.url} (failed {retries} times): {reason}")



class DoubanSpiderMiddleware:# 爬虫中间件基类，用于处理爬虫的输入输出
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()  # 创建中间件实例
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)  # 连接spider_opened信号
        return s  # 返回中间件实例
    def process_spider_input(self, response, spider):# 处理进入爬虫的响应对象
        return None        # 返回None表示继续处理，抛出异常则停止处理

    def process_spider_output(self, response, result, spider):        # 处理爬虫返回的结果
        # 必须返回Request或Item对象的可迭代对象
        for i in result:  # 默认实现：原样返回所有结果
            yield i

    def process_spider_exception(self, response, exception, spider):      # 处理爬虫处理过程中抛出的异常
        pass  # 默认不处理任何异常

    def process_start_requests(self, start_requests, spider):  # 处理爬虫的初始请求
        # 必须只返回Request对象(不能返回Item)
        for r in start_requests:  # 默认实现：原样返回所有初始请求
            yield r

    def spider_opened(self, spider):  # 爬虫启动时调用的信号处理器
        spider.logger.info("Spider opened: %s" % spider.name)  # 记录爬虫启动日志


class DoubanDownloaderMiddleware:  # 下载器中间件基类，用于处理请求和响应
    @classmethod
    def from_crawler(cls, crawler):     # Scrapy框架创建中间件的工厂方法
        s = cls()  # 创建中间件实例
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)  # 连接爬虫启动信号
        return s  # 返回中间件实例

    def process_request(self, request, spider):   # 处理每个经过下载器的请求
        return None  # 默认不修改请求

    def process_response(self, request, response, spider):    # 处理下载器返回的响应
        return response  # 默认原样返回响应

    def process_exception(self, request, exception, spider):     # 处理下载过程中出现的异常
        pass  # 默认不处理异常

    def spider_opened(self, spider):  # 爬虫启动时的信号处理
        spider.logger.info("Spider opened: %s" % spider.name)  # 记录爬虫启动日志
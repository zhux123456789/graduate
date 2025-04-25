# Scrapy settings for douban project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "douban"

SPIDER_MODULES = ["douban.spiders"]
NEWSPIDER_MODULE = "douban.spiders"

# 代理配置
PROXY_API_URL = "https://dps.kdlapi.com/api/getdps/?secret_id=oqjf2rg0ohkjq5fne3up&signature=umo268qrc72jx2lqf7yrthcakypsgr98&num=3&pt=1&sep=1"
PROXY_USER = "d2183389021"
PROXY_PASSWORD = "231wtih8"

# 下载器中间件配置
DOWNLOADER_MIDDLEWARES = {
    'douban.middlewares.ProxyMiddleware': 100,  # 优先级要高
    'douban.middlewares.CustomRetryMiddleware': 550,  # 在RetryMiddleware之前
    'scrapy.middlewares.retry.RetryMiddleware': None,  # 禁用默认的RetryMiddleware
    'douban.middlewares.DoubanDownloaderMiddleware': 543,  # 原有的中间件
}

# 重试配置
RETRY_TIMES = 3  # 重试次数
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408]  # 需要重试的状态码


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Core/1.94.249.400 QQBrowser/12.5.5659.400'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "douban.middlewares.DoubanSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# 启用中间件


# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'douban.pipelines.CsvPipeline': 300
}
DOWNLOAD_DELAY = 3  # 设置每个请求之间的时间间隔
RANDOMIZE_DOWNLOAD_DELAY = True


# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
# 允许的域名
ALLOWED_DOMAIN = ['movie.douban.com', 'sec.douban.com']

# 禁用OffsiteMiddleware（不推荐）
# SPIDER_MIDDLEWARES = {
#    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,
# }

# 添加必要的请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'Referer': 'https://movie.douban.com'
}

# 启用Cookies
COOKIES_ENABLED = True
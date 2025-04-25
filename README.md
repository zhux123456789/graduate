项目简介
这是一个基于 Python 的多功能豆瓣数据采集系统，包含 Scrapy、Requests 和 Selenium 三种实现方案，适用于不同场景的数据采集需求。

功能模块
1. Scrapy 爬虫 (/douban)
完整实现了 Scrapy 爬虫框架，包含以下组件：

spiders/douban_spider.py - 核心爬虫逻辑

items.py - 数据字段定义

pipelines.py - 数据处理和存储

settings.py - 爬虫配置

特点：

自动翻页功能

数据持久化存储

支持 CSV 和 Excel 格式输出

完善的异常处理机制

2. Requests 实现方案
提供两种 Requests 实现方式：

模块	描述	特点
request-model	基础实现	简单易用，适合初学者
request-ip-agent	高级实现	支持代理IP池和多线程
3. Selenium 实现方案
提供两种浏览器自动化方案：

模块	描述	特点
selenium-model	基础实现	标准浏览器操作
selenium-behavior	高级实现	模拟人类操作行为
使用说明
环境要求
Python 3.8+

Edge 浏览器

匹配的 msedgedriver

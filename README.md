# 网络爬虫项目集

包含使用Scrapy、Requests和Selenium实现的豆瓣数据爬取工具

## 文件说明

### Scrapy系列
- `doubanf`: Scrapy与Selenium整合版
- `douban-model`: 豆瓣性能测试文件

### Requests系列
- `request-model`: Requests性能测试文件
- `request-ip-agent`: 增加代理IP池和多线程优化的版本

### Selenium系列
- `selenium-model`: Selenium性能测试文件
- `selenium-behavior`: 模拟人类操作行为(随机滚动/停顿等)

## 功能说明

- 支持自动翻页功能
- 数据持久化存储
- 注意IP代理（重要注意事项可见）
-`doubanf`爬取用selenium，处理用scrapy框架

## 数据输出

所有爬虫结果均保存为CSV格式文件，包含：
- 原始爬取数据
- 清洗后的规整数据

## 重要注意事项

### 浏览器驱动
- 必须确保`msedgedriver.exe`与本地Edge浏览器版本匹配
  - 版本不匹配会导致运行失败
  - 浏览器更新后需重新下载对应版本的驱动

### Cookie维护
- 需要定期更换有效的Cookie
  - 使用登录后的Cookie可爬取全部页数
  - 未登录状态仅能获取前5页数据

### User-Agent设置
- 若被网站拦截，需更换用户代理列表中的值

### 代理IP配置
- 当前使用付费代理IP(有效期至2025年6月)
- 剩余可用IP数量：100+
- 到期或耗尽后需手动更新代理池配置

## !!!一定要手动更新cookie和user-agent

> 本项目为个人学习用途，欢迎指正交流！

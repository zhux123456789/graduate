import scrapy
class DoubanItem(scrapy.Item):
    # serial_number = scrapy.Field()  # 序号
    movie_comment = scrapy.Field()  # 电评价

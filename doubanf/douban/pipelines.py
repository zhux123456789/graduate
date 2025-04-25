import xlwt
import re
from scrapy.exceptions import DropItem


class CsvPipeline:
    def __init__(self):
        self.book = xlwt.Workbook(encoding='utf-8')
        self.sheet = self.book.add_sheet('comment')
        headers = ['原始评论', '清洗后评论']  # 增加清洗后评论列
        for col, header in enumerate(headers):
            self.sheet.write(0, col, header)
        self.row = 1

    def clean_comment(self, text):
        """清洗评论文本"""
        if not text:
            return None

        # 基础清洗
        text = re.sub(r'<[^>]+>', '', text)  # 去除HTML标签
        text = re.sub(r'[\r\n\t]+', ' ', text)  # 替换换行符
        text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)  # 匹配所有非字母数字汉字空格的字符
        text = re.sub(r'\s{2,}', ' ', text)  # 合并多个空格
        text = text.strip()  # 去除首尾空白
        return text if text else None

    def process_item(self, item, spider):
        raw_comment = item.get('movie_comment')
        if not raw_comment:
            raise DropItem("Missing comment in item")

        # 清洗数据
        cleaned_comment = self.clean_comment(raw_comment)
        if not cleaned_comment:  # 如果清洗后为空则丢弃
            raise DropItem("Empty comment after cleaning")

        # 写入原始和清洗后数据
        self.sheet.write(self.row, 0, raw_comment)
        self.sheet.write(self.row, 1, cleaned_comment)
        self.row += 1
        return item

    def close_spider(self, spider):
        self.book.save('result_scrapy.csv')  # 修改文件名以区分
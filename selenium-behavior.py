# 导入必要的库
from selenium import webdriver  # 主浏览器自动化库
import time  # 时间控制
import random  # 随机数生成
from selenium.webdriver.edge.options import Options  # Edge浏览器配置
from selenium.webdriver.edge.service import Service  # Edge浏览器服务
from selenium.webdriver.common.by import By  # 元素定位方式
from selenium.webdriver.common.action_chains import ActionChains  # 鼠标动作链
from selenium.webdriver.common.keys import Keys  # 键盘按键
import csv  # CSV文件操作
import re  # 正则表达式


def clean_text(text):
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


def random_sleep(min_sec=0.5, max_sec=3):
    """生成随机等待时间，模拟人类操作间隔"""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_scroll(driver):
    """模拟人类滚动行为"""
    try:
        # 获取视口尺寸和页面总高度
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_pos = 0

        while current_pos < scroll_height:
            # 计算安全的滚动距离
            scroll_step = min(
                random.randint(200, 800),
                scroll_height - current_pos  # 确保不会滚动超过页面底部
            )
            current_pos += scroll_step

            # 20%概率向上滚动
            if random.random() > 0.8 and current_pos > viewport_height:
                scroll_back = min(
                    random.randint(200, 500),
                    current_pos  # 确保不会回滚到页面顶部以上
                )
                current_pos -= scroll_back
                driver.execute_script(f"window.scrollTo(0, {current_pos});")
            else:
                driver.execute_script(f"window.scrollTo(0, {current_pos});")

            random_sleep(0.2, 1.5)

            # 安全的鼠标移动（限制在视口范围内）
            if random.random() > 0.6:
                try:
                    max_x = viewport_width - 10
                    max_y = viewport_height - 10
                    offset_x = random.randint(-50, 50)
                    offset_y = random.randint(-50, 50)

                    # 确保移动后不会超出边界
                    ActionChains(driver).move_by_offset(
                        max(-max_x, min(offset_x, max_x)),
                        max(-max_y, min(offset_y, max_y))
                    ).perform()
                except Exception as e:
                    print(f"鼠标移动时的小错误: {str(e)}")
                    continue

    except Exception as e:
        print(f"滚动时发生错误: {str(e)}")
        # 出错时执行安全回退的滚动
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
def human_like_click(driver, element):
    """模拟人类点击元素的随机行为"""
    try:
        # 先移动鼠标到元素
        ActionChains(driver).move_to_element(element).perform()
        random_sleep(0.5, 1.5)  # 随机等待后再点击

        # 30%概率使用双击代替单击
        if random.random() > 0.7:
            ActionChains(driver).double_click(element).perform()
        else:
            element.click()
    except Exception:
        # 如果常规点击失败，改用JavaScript点击
        driver.execute_script("arguments[0].click();", element)


def start():
    """初始化浏览器并设置反检测参数"""
    options = Options()
    options.add_argument('--no-sandbox')  # 禁用沙盒模式
    # 反自动化检测参数
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 设置随机窗口大小
    width = random.randint(1200, 1920)
    height = random.randint(800, 1080)
    options.add_argument(f'--window-size={width},{height}')

    # 启动Edge浏览器
    driver = webdriver.Edge(service=Service('msedgedriver.exe'), options=options)

    # 随机等待1-3秒后访问目标页面
    random_sleep(1, 3)
    driver.get('https://movie.douban.com/subject/27606065/comments?status=P')
    return driver


# CSV文件设置
headers = ["原始评论", "清洗后评论"]  # 定义CSV表头
with open("result_selenium.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)  # 写入表头

    driver = start()  # 启动浏览器
    page_num = 0  # 页码计数器

    try:
        while True:
            page_num += 1
            print(f"正在处理第 {page_num} 页...")

            # 模拟人类滚动页面
            human_like_scroll(driver)
            random_sleep(1, 2)  # 滚动后随机等待

            # 定位所有评论元素
            li_list = driver.find_elements(By.XPATH, '//*[@id="comments"]/div')

            # 处理每条评论（排除最后一个可能的分页元素）
            for i in li_list[:-1]:
                try:
                    # 平滑滚动到评论位置
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", i)
                    random_sleep(0.3, 1)  # 滚动后短暂停顿

                    # 提取并清洗评论内容
                    raw_comment = i.find_element(By.XPATH, './/div[2]/p').text
                    cleaned_comment = clean_text(raw_comment)

                    if cleaned_comment:  # 只保存有效评论
                        writer.writerow([raw_comment, cleaned_comment])
                        csvfile.flush()  # 立即写入磁盘
                except Exception as e:
                    print(f"处理评论时出错: {str(e)}")
                    continue

            # 检查是否有"后页"按钮
            next_buttons = driver.find_elements(By.XPATH, '//*[@id="paginator"]/a[contains(text(),"后页")]')
            if not next_buttons:
                print("没有找到下一页按钮，爬取结束")
                break

            try:
                # 滚动到分页区域
                paginator = driver.find_element(By.ID, 'paginator')
                driver.execute_script("arguments[0].scrollIntoView();", paginator)
                random_sleep(1, 2)

                # 人类化点击下一页
                human_like_click(driver, next_buttons[0])
                random_sleep(2, 5)  # 等待新页面加载

                # 20%概率模拟"后退-前进"操作
                if random.random() > 0.8:
                    driver.back()  # 返回上一页
                    random_sleep(1, 3)
                    driver.forward()  # 前进回当前页
                    random_sleep(1, 3)

            except Exception as e:
                print(f"翻页时出错: {str(e)}")
                break
    finally:
        # 最终确保浏览器关闭
        driver.quit()
        print("爬取完成，浏览器已关闭")
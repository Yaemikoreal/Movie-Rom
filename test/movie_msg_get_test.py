import os
from time import sleep

from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

# 获取当前脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 获取当前脚本所在目录的上一层目录
script_dir = os.path.dirname(script_dir)
# 构建数据库文件的路径
driver_path = os.path.join(script_dir, r"edgedriver/msedgedriver.exe")
# 反检测设置 #
edge_options = Options()
# 开启开发者模式
edge_options.add_experimental_option('excludeSwitches', ['enable-automation'])
# 禁用启用Blink运行时的功能
edge_options.add_argument('--disable-blink-features=AutomationControlled')
# # 使用无头模式
# edge_options.add_argument('--headless')
# # 禁用GPU，防止无头模式出现莫名的BUG
# edge_options.add_argument('--disable-gpu')
# 创建 Edge WebDriver 的 Service
service = Service(driver_path)
# 创建Edge WebDriver
driver = webdriver.Edge(service=service, options=edge_options)

# 要搜索的电影名称
movie_name = '周处除三害'
url = f"https://search.douban.com/movie/subject_search?search_text={movie_name}"

# 打开页面
driver.get(url)
sleep(0.5)
# 等待页面加载完成（可以根据具体情况调整等待时间）
driver.implicitly_wait(5)

# 获取页面源码
html = driver.page_source

# 解析页面内容
soup = BeautifulSoup(html, 'html.parser')
print(soup)
# 处理搜索结果
# 在这里可以编写代码来提取和处理搜索结果信息

# # 关闭浏览器
# driver.quit()

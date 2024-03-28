import random
import re
import time
import os
from PIL import Image
import requests
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
import pandas as pd
from bs4 import BeautifulSoup
from data_entry.CalculateUserMsg import CalculateUserMsg
from data_entry.DataGetComment import DataGetComment
from data_entry.PublicFunctions import PublicFunctions
from algo.MyDecorator import timer

'''
该脚本用于:
    获取电影的subject_id以及标签和一些基础信息
'''


class DataMovieMsgGetter:
    def __init__(self, *args, **kwargs):
        self.User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
        # 公共函数
        self.pf = PublicFunctions()
        self.dgc = DataGetComment()
        # 数据库路径
        self.db_path = self.pf.path_get()
        #
        self.edge_options = self.set_edge_options()
        self.service = self.set_service()
        #
        self.movie_msg_list = []
        # movie_data_comment
        self.movie_data_comment_df = self.pf.read_table_all("movie_data_comment")
        # 原有的movie_msg表信息
        self.movie_msg_df = self.pf.read_table_all("movie_msg")

    def read_movie_data_comment_df(self):
        # 电影名单
        movie_data_comment_name_list = self.movie_data_comment_df['movie_name'].unique().tolist()
        movie_msg_name_list = self.movie_msg_df['movie_name'].unique().tolist()
        # 找出movie_data_comment_name_list有而movie_msg_name_list没有的值,得到即为需要更新的电影列表
        result_list = [value for value in movie_data_comment_name_list if value not in movie_msg_name_list]
        # # top250电影
        # movie_data_top250_df = self.pf.read_table_all("movie_data_top250")
        # result_list = movie_data_top250_df['电影名字'].unique().tolist()
        return result_list

    def set_edge_options(self):
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
        return edge_options

    def set_service(self):
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录的上一层目录
        script_dir = os.path.dirname(script_dir)
        # 构建数据库文件的路径
        driver_path = os.path.join(script_dir, r"edgedriver/msedgedriver.exe")
        # 创建 Edge WebDriver 的 Service
        service = Service(driver_path)
        return service

    def get_movie_msg_all(self, movie_name):
        # 创建Edge WebDriver
        driver = webdriver.Edge(service=self.service, options=self.edge_options)
        url = f"https://search.douban.com/movie/subject_search?search_text={movie_name}"
        # 打开页面
        driver.get(url)
        time.sleep(1)
        # 等待页面加载完成（可以根据具体情况调整等待时间）
        driver.implicitly_wait(4)
        # 获取页面源码
        html = driver.page_source
        # 解析页面内容
        soup = BeautifulSoup(html, 'html.parser')
        # 关闭浏览器
        driver.quit()
        return soup

    def calculate_movie_msg(self, soup):
        movie_title = soup.find('div', id="wrapper")
        if movie_title is None:
            return None
        movie_title = movie_title.find('div', class_="root")
        # 图片路径获取
        movie_img_title = movie_title.find('a', class_="cover-link")

        if movie_img_title:
            # 查找包含图片的标签
            img_tag = movie_img_title.find('img')
            # 提取src属性的值
            img_src = img_tag['src']
            print("提取到的src路径信息为:", img_src)
        else:
            img_src = None
            print("未找到包含图片的标签")

        # 电影信息获取
        movie_title = movie_title.find_all('div', class_="detail")
        if not movie_title:
            return None
        first_movie = movie_title[0]
        movie_tag = first_movie.find('a', class_="title-text")
        # 电影名称以及发表年份
        movie_name = movie_tag.text
        # 提取 subject_id
        data_moreurl = movie_tag['data-moreurl']
        if data_moreurl:
            # 从字符串中提取 subject_id 的值
            subject_id = data_moreurl.split("subject_id:'")[1].split("'")[0]
        else:
            subject_id = None
        # rating评分
        rating_element = first_movie.find('span', class_="rating_nums")
        if rating_element is not None:
            rating = rating_element.text
            # 处理评分数据
        else:
            rating = None
        # 评分人数
        rating_people = first_movie.find('span', class_="pl")
        if rating_people is not None:
            rating_people = rating_people.text
        else:
            rating_people = None
        # movie_label
        movie_labels = first_movie.find('div', class_="meta abstract").text
        # movie_actors
        movie_actors = first_movie.find('div', class_="meta abstract_2").text
        movie_msg_dt = {
            "subject_id": subject_id,
            "movie_name": movie_name,
            "average_score": rating,
            "rating_people": rating_people,
            "movie_labels": movie_labels,
            "movie_actors": movie_actors,
            "movie_img_src": img_src
        }
        return movie_msg_dt

    def determine(self, movie_name):
        # 判断该电影是否需要进行数据补充
        result = False
        filtered_df = self.movie_msg_df[(self.movie_msg_df['movie_name'] == movie_name)]
        # 如果筛选后的 DataFrame 为空时则需要对其进行数据获取
        if filtered_df.empty:
            result = True
        return result

    def constitute_movie_duration(self, movie):
        # movie_duration(电影时长)
        movie_labels = movie.get('movie_labels')
        movie_duration = re.search(r'\b\d+\s*分钟\b', movie_labels)
        if movie_duration:
            movie_duration = movie_duration.group(0)
            # 从原始字符串中删除分钟数信息
            movie_labels = re.sub(r'\b\d+\s*分钟\b', '', movie_labels)
        else:
            movie_duration = None
        return movie_duration, movie_labels

    def constitute_movie_name_year(self, movie):
        # 获取出电影名称以及演出年份
        movie_name = movie.get('movie_name')
        movie_year = re.search(r'\((\d{4})\)$', movie_name)
        movie_year = movie_year.group(1)
        if not movie_year:
            movie_year = None
        movie_name = re.sub(r'\s*\(\d{4}\)', '', movie_name)
        return movie_name, movie_year

    def constitute_rating_people(self, movie):
        # 处理出电影点评人数
        rating_people = movie.get('rating_people')
        # 去除括号
        if rating_people is None:
            return rating_people
        rating_people = rating_people.strip('()')
        return rating_people

    def movie_msg_df_constitute(self, movie, movie_name_real):
        # 数据整理
        movie_name, movie_year = self.constitute_movie_name_year(movie)
        rating_people = self.constitute_rating_people(movie)
        movie_duration, movie_labels = self.constitute_movie_duration(movie)
        # rating（电影评分）
        rating = movie.get('average_score')
        # subject_id(豆瓣索引ID)
        subject_id = movie.get('subject_id')
        # 电影演员
        movie_actors = movie.get('movie_actors')
        # 图片路径
        movie_img = movie.get('movie_img_src')
        movie_msg_dt_2 = {
            "movie_name": [movie_name_real],
            "movie_name_notes": [movie_name],
            "movie_year": [movie_year],
            "average_score": [rating],
            "rating_people": [rating_people],
            "movie_labels": [movie_labels],
            "movie_actors": [movie_actors],
            "movie_duration": [movie_duration],
            "subject_id": [subject_id],
            "movie_img": [movie_img]
        }
        movie_msg_df = pd.DataFrame(movie_msg_dt_2)
        return movie_msg_df

    def movie_name_list_detection(self, movie_name_list):
        if len(movie_name_list) == 0:
            log_content = "没有电影需要获取其详细信息!"
            print(log_content)
            # 日志信息写入
            self.pf.write_sqlite_db_log(bug_level="INFO", movie_name=None, log_content=log_content)
            return False
        return True

    def resize_image(self, image_path, target_width=216, target_height=308):
        # 调整图片大小
        img = Image.open(image_path)
        resized_img = img.resize((target_width, target_height))
        return resized_img

    def movie_img_get(self, movie_msg_dt):
        # 图片使用subject_id进行索引
        movie_name = movie_msg_dt.get('movie_name')
        subject_id = movie_msg_dt.get('subject_id')
        img_src = movie_msg_dt.get('movie_img_src')
        if subject_id is None:
            return None
        # 获取当前脚本的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 上一层目录，即保存图片的目录
        save_dir = os.path.abspath(os.path.join(script_dir, os.pardir, "static", "img"))

        # 本地保存文件名
        file_name = f"{subject_id}.jpg"
        # 完整的本地保存路径
        img_local_filename = os.path.join(save_dir, file_name)

        # 发送请求获取图片内容
        response = requests.get(img_src)
        if response.status_code == 200:
            # 保存原始图片到本地
            with open(img_local_filename, 'wb') as f:
                f.write(response.content)

            # 调整图片大小
            resized_img = self.resize_image(img_local_filename)
            resized_img.save(img_local_filename)

            print(f"电影<{movie_name}>图片已成功保存并调整大小到: {img_local_filename}")
            movie_msg_dt['movie_img_src'] = f"{subject_id}.jpg"
        else:
            print(f"电影<{movie_name}>无法下载图片!!!")
            movie_msg_dt['movie_img_src'] = None

        return movie_msg_dt

    def get_movie_all_msg(self, movie_name):
        # 读取电影信息核心函数
        soup = self.get_movie_msg_all(movie_name)
        movie_msg_dt = self.calculate_movie_msg(soup)
        if movie_msg_dt is not None:
            # 获取图片
            movie_msg_dt1 = self.movie_img_get(movie_msg_dt)
            if movie_msg_dt1 is not None:
                # 整合数据信息
                movie_msg_df = self.movie_msg_df_constitute(movie_msg_dt1, movie_name)
                self.pf.write_sqlite_db(movie_msg_df, 'movie_msg')
                print(f"电影<{movie_name}>的相关数据已经写入表中")
            else:
                print(f"电影<{movie_name}>的subject_id为空！！！")
        else:
            log_content = f"电影<{movie_name}>未查询到相关内容结果！"
            print(log_content)
            # 日志信息写入
            self.pf.write_sqlite_db_log(bug_level="WARNING", movie_name=movie_name, log_content=log_content)

    @timer
    def calculate_movie(self):
        movie_name_list = self.read_movie_data_comment_df()
        # 如果movie_name_list为空，则不进行后续操作
        movie_name_list_status = self.movie_name_list_detection(movie_name_list)
        if not movie_name_list_status:
            return
        # 对列表名称进行遍历，同时将电影内容获取并写入
        for movie_name in movie_name_list:
            result_status = self.determine(movie_name)
            # result_status为True时说明表中没有对应值
            if result_status:
                self.get_movie_all_msg(movie_name)
                time.sleep(random.randint(1, 3))
            else:
                print(f"电影<{movie_name}>在表中已有数据！")
            print("------------------------------------")

    def calculate(self):
        self.calculate_movie()


def main(**kwargs):
    obj = DataMovieMsgGetter(**kwargs)
    obj.calculate()
    # 同步表信息
    obs = CalculateUserMsg()
    obs.calculate()


def main_test():
    main()


if __name__ == '__main__':
    main_test()

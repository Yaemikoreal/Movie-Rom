import os
import random
import sqlite3
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from algo.MyDecorator import timer
from data_entry.DataMovieMsgGetter import DataMovieMsgGetter
from data_entry.PublicFunctions import PublicFunctions
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

"""
对没有图片的电影进行图片信息获取
"""

class MovieImgGetter:
    def __init__(self):
        self.img_getter = 1
        # 公共函数
        self.pf = PublicFunctions()
        self.movie_msgget = DataMovieMsgGetter()
        # 原有的movie_msg表信息
        self.movie_msg_df = self.pf.read_table_all("movie_msg")
        #
        self.edge_options = self.set_edge_options()
        self.service = self.set_service()
        # 数据库路径
        self.db_path = self.pf.path_get()

    def read_movie_data_comment_df(self):
        # 提取'movie_img'列中值为None的行，这说明这部电影并没有获取到对应的图片信息
        new_data_df = self.movie_msg_df[self.movie_msg_df['movie_img'].isnull()]
        movie_name_list = new_data_df['movie_name'].tolist()
        return movie_name_list

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

    def update_movie_msg(self, movie_img_src, movie_subject_id):
        # 更新movie_msg表
        conn = sqlite3.connect(self.db_path)
        table_name = "movie_msg"
        # 执行更新操作
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET movie_img = ? WHERE subject_id = ?", (movie_img_src, movie_subject_id))
        conn.commit()
        conn.close()

    def get_movie_all_msg(self, movie_name):
        # 读取电影信息核心函数
        soup = self.get_movie_msg_all(movie_name)
        movie_msg_dt = self.movie_msgget.calculate_movie_msg(soup)
        if movie_msg_dt is not None:
            # 获取图片到Img
            movie_msg_dt1 = self.movie_msgget.movie_img_get(movie_msg_dt)
            if movie_msg_dt1 is not None:
                # 更新表信息
                movie_img_src = movie_msg_dt1.get("movie_img_src")
                movie_subject_id = movie_msg_dt1.get("subject_id")
                self.update_movie_msg(movie_img_src, movie_subject_id)
                print(f"电影<{movie_name}>的图片已经获取到并写入表中！！！")
            else:
                print(f"电影<{movie_name}>的subject_id为空！！！")
        else:
            print(f"<{movie_name}>没有获取到对应图片！！！")

    @timer
    def calculate_movie(self):
        # 获取没有图片信息的电影名单
        movie_name_list = self.read_movie_data_comment_df()
        for movie_name in movie_name_list:
            self.get_movie_all_msg(movie_name)
        print("电影图片更新完毕！！！")


def main():
    obj = MovieImgGetter()
    obj.calculate_movie()


def main_test():
    main()


if __name__ == "__main__":
    main_test()

import os
import sqlite3

import requests
import parsel
from sqlalchemy import create_engine
import pandas as pd
from bs4 import BeautifulSoup

from algo.my_decorator import timer

'''
1、明确需求:
    爬取豆瓣最受欢迎的影评（会每日更新）
'''


class DataGetComment:
    def __init__(self):
        self.User_Agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0')
        self.is_write = 1
        self.rating_score_dt = {
            '力荐': 5,
            '推荐': 4,
            '还行': 3,
            '较差': 2,
            '很差': 1
        }
        self.rating_list = ['allstar50 main-title-rating', 'allstar40 main-title-rating',
                            'allstar30 main-title-rating', 'allstar20 main-title-rating',
                            'allstar10 main-title-rating']

    def get_comment(self, status):
        # movie_data_list用于存储所读取的所有电影评论信息
        movie_data_list = []
        if status == 1:
            # 模拟浏览器发送请求
            for page in range(0, 100, 20):
                url = f'https://movie.douban.com/review/best/?start={page}'
                headers = {
                    'User-Agent': self.User_Agent
                }
                response = requests.get(url=url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                # 通过类名查找元素
                soup = soup.find('div', class_='article')
                soup = soup.find('div', class_='review-list chart')
                # 使用 find_all 方法查找所有 data-cid 属性为数字的 div 元素
                div_list = soup.find_all('div', {'data-cid': True})
                for div in div_list:
                    # 电影名字
                    a_tag = div.find('a', class_='subject-img')
                    a_tag = a_tag.find('img')
                    movie_name = a_tag.get('title')
                    # 评论者名称
                    a_tag = div.find('a', class_='name')
                    user_name = a_tag.text.strip()
                    # 评论分数
                    for it in self.rating_list:
                        a_tag = div.find('span', class_=f'{it}')
                        if a_tag is None:
                            continue
                        rating_score = a_tag.get('title')
                    movie_dt = {
                        'user_name': user_name,
                        'movie_name': movie_name,
                        'movie_rating': rating_score
                    }
                    movie_data_list.append(movie_dt)
            movie_data_df = pd.DataFrame(movie_data_list)

            movie_data_df['movie_rating'] = movie_data_df['movie_rating'].replace(self.rating_score_dt)
            return movie_data_df
        else:
            # 模拟浏览器发送请求
            url = 'https://movie.douban.com/review/latest/?app_name=movie'
            headers = {
                'User-Agent': self.User_Agent
            }
            response = requests.get(url=url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            # 通过类名查找元素
            soup = soup.find('div', class_='article')
            soup = soup.find('div', class_='review-list chart')
            # 使用 find_all 方法查找所有 data-cid 属性为数字的 div 元素
            div_list = soup.find_all('div', {'data-cid': True})
            for div in div_list:
                # 电影名字
                a_tag = div.find('a', class_='subject-img')
                a_tag = a_tag.find('img')
                movie_name = a_tag.get('title')
                # 评论者名称
                a_tag = div.find('a', class_='name')
                user_name = a_tag.text.strip()
                # 评论分数
                for it in self.rating_list:
                    a_tag = div.find('span', class_=f'{it}')
                    if a_tag is None:
                        continue
                    rating_score = a_tag.get('title')
                movie_dt = {
                    'user_name': user_name,
                    'movie_name': movie_name,
                    'movie_rating': rating_score
                }
                movie_data_list.append(movie_dt)
            movie_data_df = pd.DataFrame(movie_data_list)
            movie_data_df['movie_rating'] = movie_data_df['movie_rating'].replace(self.rating_score_dt)
            return movie_data_df

    def write_sqlite_db(self, movie_df):
        # 构建数据库文件的路径
        db_path = self.path_get()
        # 创建数据库连接对象
        conn = sqlite3.connect(db_path)
        # 将 DataFrame 写入到已存在的数据库表中
        movie_df.to_sql('movie_data_comment', conn, if_exists='append', index=False)
        # 关闭数据库连接
        conn.close()

    def path_get(self):
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录的上一层目录
        script_dir = os.path.dirname(script_dir)
        # 构建数据库文件的路径
        db_path = os.path.join(script_dir, "MovieData.sqlite")
        return db_path

    def read_movie_data_comment(self, user_name, movie_name):
        # 构建数据库文件的路径
        db_path = self.path_get()
        # 创建数据库连接对象
        conn = sqlite3.connect(db_path)
        # 从数据库中读取表格数据到 DataFrame
        data_df = pd.read_sql_query(
            f"SELECT * FROM movie_data_comment WHERE user_name = '{user_name}' AND movie_name = '{movie_name}' ", conn)
        conn.close()
        return data_df

    def read_id_max(self):
        # 构建数据库文件的路径
        db_path = self.path_get()
        # 创建数据库连接对象
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 执行查询
        cursor.execute("SELECT MAX(id) FROM movie_data_comment")
        max_id = cursor.fetchone()[0]  # 获取查询结果中的最大值
        if max_id is None:
            max_id = 0
        # 关闭数据库连接
        conn.close()
        return max_id

    def filter(self, movie_df):
        max_id = self.read_id_max()
        start_id = max_id + 1
        new_movie_list = []
        count_num = 0
        for index, row in movie_df.iterrows():
            user_name = row['user_name']
            movie_name = row['movie_name']
            rating_score = row['movie_rating']
            data_df = self.read_movie_data_comment(user_name, movie_name)
            if data_df.empty:
                new_movie_dt = {
                    "id": start_id,
                    "user_name": user_name,
                    "movie_name": movie_name,
                    "movie_rating": rating_score
                }
                new_movie_list.append(new_movie_dt)
                start_id += 1
                count_num += 1
        new_movie_df = pd.DataFrame(new_movie_list)
        if new_movie_df.empty:
            print("暂无新影评可获取！")
        else:
            print(f"成功写入{count_num}条新数据！")
        return new_movie_df

    def calculate_movie(self, status):
        movie_df = self.get_comment(status)
        new_movie_df = self.filter(movie_df)
        self.write_sqlite_db(new_movie_df)

    @timer
    def calculate(self):
        # 当status为1时，获取最受欢迎的评论和评分
        self.calculate_movie(status=1)
        # 当status为0时，获取最新的评论和评分
        self.calculate_movie(status=0)


def mian_test():
    obj = DataGetComment()
    obj.calculate()


if __name__ == '__main__':
    mian_test()

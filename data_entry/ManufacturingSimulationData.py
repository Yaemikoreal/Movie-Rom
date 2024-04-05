import os
import requests
import parsel
from sqlalchemy import create_engine
import pandas as pd
from bs4 import BeautifulSoup
import sqlite3
import random

from algo.MyDecorator import timer
from data_entry.CalculateUserMsg import CalculateUserMsg
from data_entry.PublicFunctions import PublicFunctions

"""
该脚本用于生成模拟数据，写入movie_data_comment表，用于协同过滤算法模拟
"""


class ManufacturingSimulationData:
    def __init__(self):
        self.pf = PublicFunctions()
        self.db_path = self.pf.path_get()
        # 用户和电影评分
        self.movie_comments_df = self.pf.read_table_all(read_table='movie_data_comment')
        # 电影信息
        self.movie_df = self.pf.read_table_all(read_table='movie_msg')
        # 用户信息
        self.user_df = self.pf.read_table_all(read_table='user_msg')

    def three_probability_comment(self, movie_name_list, user_name):
        # 逻辑：该方法用于以3%的假定概率来模拟用户对电影的评分，并返回一个模拟评分字典
        one_user_movie_rating_dt = {user_name: []}
        count_num = 0
        for movie_name in movie_name_list:
            # 生成1到len(movie_name_list)之间的随机数
            random_num = random.randint(1, len(movie_name_list))
            # 如果随机数在1到0.03*len(movie_name_list)之间，则返回True，否则返回False
            if random_num <= 0.03 * len(movie_name_list):
                count_num += 1
                print(f"用户{user_name}对{movie_name}")
                one_user_movie_rating_dt[user_name].append(movie_name)
        return one_user_movie_rating_dt

    def read_one_user_msg(self, user_name):
        conn = sqlite3.connect(self.db_path)
        data_df = pd.read_sql_query(
            f"SELECT * FROM user_msg WHERE user_name = '{user_name}'", conn)
        conn.close()
        return data_df

    def check_user_movie_count(self, user_name):
        # 如果该用户的观影量已经大于预想值，则不对其进行模拟数据生成
        one_user_movie_count_msg_df = self.read_one_user_msg(user_name)
        movie_count = one_user_movie_count_msg_df['movie_count'].iloc[0]
        if movie_count >= 5:
            return False
        return True

    def make_data_to_movie_data_comment(self):
        """
        判断逻辑:
            1.判断该用户的观影量是否已经到达预想值阈值;
            2.该方法用于以3%的假定概率来模拟用户对电影的评分，并返回一个模拟评分字典
        :return:
        """
        all_user_movie_lt = []
        user_name_list = self.user_df['user_name'].tolist()
        movie_name_list = self.movie_df['movie_name'].tolist()
        count = 0
        for user_name in user_name_list:
            # 判断该用户的观影量是否已经到达预想值阈值
            status = self.check_user_movie_count(user_name)
            # 如果没有达到，则进行数据生成
            if status:
                count += 1
                one_user_movie_rating_dt = self.three_probability_comment(movie_name_list, user_name)
                all_user_movie_lt.append(one_user_movie_rating_dt)
        print(f"有{count}个用户未到达预想观影量阈值（5），现对其进行数据生成处理！")
        print("----------------------------------------------------------")
        return all_user_movie_lt

    def check_user_movie(self, user_name, movie):
        conn = sqlite3.connect(self.db_path)
        data_df = pd.read_sql_query(
            f"SELECT * FROM movie_data_comment WHERE user_name = '{user_name}' AND movie_name = '{movie}'", conn)
        conn.close()
        # 如果是空的，则说明表里没有该用户对该电影的评价，则返回True表示可以写入
        if data_df.empty:
            return True
        else:
            return False

    def random_rating(self, movie):
        # 查询出当前电影的平均分数
        one_movie_df = self.movie_df[(self.movie_df['movie_name'] == movie)]
        average_score = one_movie_df['average_score'].iloc[0]
        if average_score is None:
            average_rating = random.randint(1, 5)
        else:
            # 根据该电影的平均分数(十分制),随机出一个合理的分数(五分制)
            average_score = round(float(average_score) / 2)
            # 生成一个0到9之间的随机数
            random_number = random.randint(0, 9)
            # 如果随机数是0，返回True；否则返回False
            if random_number == 0:
                if average_score < 3:
                    average_rating = average_score + 2
                else:
                    average_rating = average_score - 2
            else:
                # 随机生成在该范围内的整数
                if average_score == 5:
                    average_rating = random.randint(average_score - 1, average_score)
                elif average_score == 1:
                    average_rating = random.randint(average_score, average_score + 1)
                else:
                    average_rating = random.randint(average_score - 1, average_score + 1)
        print(f"电影<{movie}>模拟评分为<{average_rating}>,实际平均评分值为<{average_score}>")
        return average_rating

    def insert_movie_data_comment(self, user_name, movie_name, movie_rating):
        # 处理用户评分并写入评论表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO movie_data_comment (user_name, movie_name, movie_rating) VALUES (?, ?, ?)',
                       (user_name, movie_name, movie_rating))
        # 提交更改并关闭连接
        conn.commit()
        conn.close()

    def check_user_data(self, all_user_movie_lt):
        count_num = 0
        for it in all_user_movie_lt:
            for user_name, movies in it.items():
                for movie in movies:
                    status = self.check_user_movie(user_name, movie)
                    # True表示可以写入
                    if status:
                        # 根据该电影的平均分数(十分制),随机出一个合理的分数(五分制)
                        average_rating = self.random_rating(movie)
                        count_num += 1
                        # 写入
                        self.insert_movie_data_comment(user_name, movie, average_rating)
                        print(f'<{count_num}>   用户<{user_name}>对电影<{movie}>的模拟评分为<{average_rating}>')
                        print("---------------------------------------------------------------")

        print("---------------------")
        print(f"新写入{count_num}条模拟评论！")

    @timer
    def calculate(self):
        """
        数据生成逻辑:
            1.遍历全部用户和电影名，假设用户有3%的概率会留下评分评论内容;
            2.留下评分内容时，检查该用户是否已经存在对该电影的评分;
            3.在随机拟定评分时，参考该电影的平均评分值.
        :return:
        """
        # 模拟用户评论电影数据生成
        all_user_movie_lt = self.make_data_to_movie_data_comment()
        # 判断处理检查该用户是否已经存在对该电影的评分
        self.check_user_data(all_user_movie_lt)
        # 同步表信息
        obs = CalculateUserMsg()
        obs.calculate()


def main_test():
    obj = ManufacturingSimulationData()
    obj.calculate()


if __name__ == '__main__':
    main_test()

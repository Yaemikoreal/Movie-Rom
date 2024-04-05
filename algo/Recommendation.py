import sqlite3

import pandas as pd

from algo.CollaborativeFiltering import main as collaborative_filtering_main
from data_entry.PublicFunctions import PublicFunctions
from algo.ReadMovieImgRandom import ReadMovieImgRandom

"""
1.根据传来的用户名判断该用户的观影量是否有十个：
    如果有，则直接对其进行推荐计算。
    如果没有，那么让用户对十个精选电影进行评分判断。
"""


class Recommendation:
    def __init__(self):
        # 公共函数
        self.pf = PublicFunctions()
        # 数据库路径
        self.db_path = self.pf.path_get()

    def read_user_msg(self, user_name):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中随机读取六十行数据到 DataFrame
        data_df = pd.read_sql_query(f"SELECT * FROM user_msg WHERE user_name = '{user_name}'", conn)
        conn.close()
        return data_df

    def insert_user_msg(self, user_name):
        # user_msg_df是空的则说明用户在库中没有观影量记录,则让user_msg表中新加入该用户名，同时，观影量设置为0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_msg (user_name, movie_count) VALUES (?, ?)", (user_name, 0))
        # 提交更改并关闭连接
        conn.commit()
        conn.close()

    def insert_movie_data_comment(self, user_name, movie_name, movie_rating):
        # 处理用户评分并写入评论表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO movie_data_comment (user_name, movie_name, movie_rating) VALUES (?, ?, ?)',
                       (user_name, movie_name, movie_rating))
        # 提交更改并关闭连接
        conn.commit()
        conn.close()

    def rating_judgment(self, user_name):
        user_msg_df = self.read_user_msg(user_name)
        # user_msg_df是空的则说明用户在库中没有观影量记录,则让user_msg表中新加入该用户名，同时，观影量设置为0
        if user_msg_df.empty:
            self.insert_user_msg(user_name)
            print(f"用户<{user_name}>已加入user_msg表，观影量设置为：0！")
            return False
            # user_msg_df不为空时，判断其观影量是否大于十，如果大于十，那么直接返回True,小于十时,让用户完成表单,再进行推荐
        else:
            movie_count = user_msg_df['movie_count'][0]
            if movie_count >= 10:
                print(f"用户<{user_name}>观影量大于10！")
                return True

    def read_movie_user_comment(self, user_name):
        # 读取出用户现在的观影数
        conn = sqlite3.connect(self.db_path)
        # 从数据库中随机读取六十行数据到 DataFrame
        data_df = pd.read_sql_query(f"SELECT * FROM movie_data_comment WHERE user_name = '{user_name}'", conn)
        conn.close()
        return data_df

    def update_user_msg(self, user_name, movie_count):
        # 更新user_msg表中该用胡的观影量值
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE user_msg SET movie_count = ? WHERE user_name = ?',
                       (movie_count, user_name))
        # 提交更改并关闭连接
        conn.commit()
        conn.close()

    def insert_user_comment(self, user_name, ratings):
        for movie_name, rating in ratings.items():
            # rating为0则说明用户并没有看过，不做记录
            if rating == "0":
                continue
            self.insert_movie_data_comment(user_name, movie_name, rating)
            print(f"用户{user_name}对电影{movie_name}的评分为{rating}，已经写入！")
        # 读取出用户现在的观影评分总量,更新观影量
        data_df = self.read_movie_user_comment(user_name)
        movie_count = data_df.shape[0]
        self.update_user_msg(user_name, movie_count)

    def calculate(self, data):
        # user_name如名，ratings是用户对十部电影的对应评分
        user_name = data.get('username')
        ratings = data.get('ratings')
        # ratings是空的则说明是加载完成时传递的用户名，进行判断
        if ratings is None:
            status = self.rating_judgment(user_name)
            data["status"] = status
            return data
        # ratings不为空,则说明是用户提交的评分表单,则处理用户评分并写入评论表,并进行推荐计算
        else:
            # 对评论表写入用户评分
            self.insert_user_comment(user_name, ratings)
            data["status"] = True
            return data


def main():
    data = {
        'user_name': '方聿南'
    }
    obj = Recommendation()
    obj.calculate(data)


def main_test():
    main()


if __name__ == '__main__':
    main_test()

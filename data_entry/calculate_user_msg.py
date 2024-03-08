import sqlite3
import pandas as pd
from algo.my_decorator import timer
from data_entry.public_functions import PublicFunctions

"""
该脚本用于:
    1.同步user_msg表中的user_id信息;
    2.同步movie_msg表中的movie_id信息。
"""


class CalculateUserMsg:
    def __init__(self):
        # 初始写入id
        self.start_user_id = 0
        # 记录新的用户列表
        self.movie_msg_list = []
        self.user_msg_list = []
        # 该列表用于更新表中已经存在的电影的评分
        self.user_msg_list_old = []
        # 公共函数
        self.pf = PublicFunctions()
        # 数据库路径
        self.db_path = self.pf.path_get()
        #
        self.movie_comments_df = self.pf.read_table_all('movie_data_comment')

    def inspect_user_name(self, user_name):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中读取表格数据到 DataFrame
        data_df = pd.read_sql_query(
            f"SELECT * FROM user_msg WHERE user_name = '{user_name}'", conn)
        conn.close()
        # 如果data_df为空则说明表中没有该用户信息需要写入
        if data_df.empty:
            return True
        return False

    def inspect_movie_name(self, movie_name):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中读取表格数据到 DataFrame
        data_df = pd.read_sql_query(
            f"SELECT * FROM movie_msg WHERE movie_name = '{movie_name}'", conn)
        conn.close()
        # 如果data_df为空则说明表中没有该电影信息需要写入
        if data_df.empty:
            return True
        return False

    def processing_user_information(self, start_id, user_name_list):
        # 对用户姓名数据进行处理
        for name in user_name_list:
            user_status = self.inspect_user_name(name)
            if user_status:
                start_id += 1
                user_msg_dt = {
                    "user_id": start_id,
                    "user_name": name
                }
                self.user_msg_list.append(user_msg_dt)

    def calculate_user_msg(self):
        # 读取出数据内容
        user_msg_df = self.pf.read_table_all('user_msg')
        # 设置起始 user_id 如果 user_msg_df 为空则使用 self.start_user_id，否则使用 user_msg_df['user_id'].max()
        start_id = self.start_user_id if user_msg_df.empty else user_msg_df['user_id'].max()
        # 获取不重复的 user_name 列并转换为列表
        user_name_list = self.movie_comments_df['user_name'].unique().tolist()
        # 对用户数据进行处理
        self.processing_user_information(start_id, user_name_list)
        user_msg_df = pd.DataFrame(self.user_msg_list)
        # 写入
        self.pf.write_sqlite_db(user_msg_df, 'user_msg')

    def update_movie_msg(self):
        movie_msg_list = self.user_msg_list_old.copy()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for it in movie_msg_list:
            average_score = it.get('average_score')
            movie_name = it.get('movie_name')
            # 使用占位符 ? 来防止 SQL 注入，并指定要更新的列和设置的值
            sql = "UPDATE movie_msg SET average_score = ? WHERE movie_name = ?"
            # 执行 SQL 更新语句
            cursor.execute(sql, (average_score, movie_name))
        # 提交事务
        conn.commit()
        cursor.close()
        conn.close()
        print('Movie_msg表已有电影评分已更新！')

    def processing_movie_information(self, start_id, movie_name_list):
        for movie in movie_name_list:
            movie_status = self.inspect_movie_name(movie)
            # 计算出该电影的平均评分
            filtered_df = self.movie_comments_df[self.movie_comments_df['movie_name'] == movie].copy()
            average_score = filtered_df['movie_rating'].mean()
            average_score = round(average_score, 1)
            start_id += 1
            movie_dt = {
                "movie_id": start_id,
                "movie_name": movie,
                "average_score": average_score
            }
            if movie_status:
                self.movie_msg_list.append(movie_dt)
            else:
                self.user_msg_list_old.append(movie_dt)

    def write_movie_msg(self):
        movie_msg_list = self.user_msg_list.copy()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for it in movie_msg_list:
            movie_id = it.get('movie_id')
            average_score = it.get('average_score')
            movie_name = it.get('movie_name')
            # 使用占位符 ? 来防止 SQL 注入，并指定要更新的列和设置的值
            sql = "INSERT INTO movie_msg (movie_id, average_score, movie_name) VALUES (?, ?, ?);"
            # 执行 SQL 更新语句
            cursor.execute(sql, (movie_id, average_score, movie_name))
        # 提交事务
        conn.commit()
        cursor.close()
        conn.close()
        print('Movie_msg表已更新未有内容！')

    def calculate_movie_msg(self):
        # 读取出数据内容
        movie_msg_df = self.pf.read_table_all('movie_msg')
        # 设置起始 id 如果 movie_msg_df 为空则使用 self.start_user_id，否则使用 movie_msg_df['user_id'].max()
        start_id = self.start_user_id if movie_msg_df.empty else movie_msg_df['movie_id'].max()
        # 获取不重复的 movie_name 列并转换为列表
        movie_name_list = self.movie_comments_df['movie_name'].unique().tolist()
        # 对电影数据进行处理
        self.processing_movie_information(start_id, movie_name_list)
        #  写入
        self.write_movie_msg()
        # 更新已有电影评分数据
        self.update_movie_msg()

    @timer
    def calculate(self):
        # 对user_msg表根据movie_data_comment表数据进行同步更新
        self.calculate_user_msg()
        # 对movie_msg表根据movie_data_comment表数据进行同步更新
        self.calculate_movie_msg()



def main_test():
    obj = CalculateUserMsg()
    obj.calculate()


if __name__ == '__main__':
    main_test()

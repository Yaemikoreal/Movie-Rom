import sqlite3
import pandas as pd
from algo.MyDecorator import timer
from data_entry.PublicFunctions import PublicFunctions

"""
该脚本用于:
    1.同步user_msg表中的user_id信息;
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
        # 用户评论df
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

    @timer
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

    @timer
    def calculate_movie_count(self):
        # 使用 value_counts() 方法计算每个用户名出现的次数
        username_counts = self.movie_comments_df['user_name'].value_counts()
        # 将结果转换为列表套字典的形式
        result_dt = [{'user_name': username, 'movie_count': count} for username, count in username_counts.items()]
        self.insert_movie_count(result_dt)
        print("更新成功！")

    def insert_movie_count(self, result_dt):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # 将数据插入到表格中
        # 更新表格中的数据
        for row in result_dt:
            cursor.execute('UPDATE user_msg SET movie_count = ? WHERE user_name = ?',
                           (row.get('movie_count'), row.get('user_name')))
            print(f"成功更新用户<{row.get('user_name')}>的观影数量为:<{row.get('movie_count')}>")
        # 提交更改并关闭连接
        conn.commit()
        conn.close()

    @timer
    def calculate(self):
        # 对user_msg表根据movie_data_comment表数据进行同步更新
        self.calculate_user_msg()
        # 对user_msg表已有用户添加movie_count计数
        self.calculate_movie_count()


def main_test():
    obj = CalculateUserMsg()
    obj.calculate()


if __name__ == '__main__':
    main_test()

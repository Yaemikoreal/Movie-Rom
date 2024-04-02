import sqlite3
import pandas as pd

from data_entry.PublicFunctions import PublicFunctions

"""
随机读三十个电影信息以供前端页面显示
"""


class ReadMovieImgRandom:
    def __init__(self):
        # 公共函数
        self.pf = PublicFunctions()
        # 数据库路径
        self.db_path = self.pf.path_get()

    def read_movie_img(self):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中随机读取三十行数据到 DataFrame
        data_df = pd.read_sql_query("SELECT * FROM movie_msg ORDER BY RANDOM() LIMIT 60", conn)
        conn.close()
        return data_df

    def process_movie_tags(self, data_df):
        # 处理电影标签
        data_df['new_movie_labels'] = data_df['movie_labels']
        # 使用apply方法结合lambda函数来对'new_movie_labels'列进行处理。split(' / ')会将字符串分割成列表，
        # 只选择列表中索引为 1 到 3 的部分，最后再用'/'.join() 连接起来。这样就能够过滤掉大部分国家信息并保留前三个标签。
        data_df['new_movie_labels'] = data_df['new_movie_labels'].apply(lambda x: ' / '.join(x.split(' / ')[1:4]))
        data_df = data_df[['movie_name', 'new_movie_labels', 'movie_img']]
        # 重命名列
        data_df = data_df.rename(columns={
            'movie_name': 'title',
            'new_movie_labels': 'description',
            'movie_img': 'image'
        })
        return data_df

    def calculate(self):
        data_df = self.read_movie_img()
        # 处理电影标签
        data_df = self.process_movie_tags(data_df)
        return data_df


def main():
    obj = ReadMovieImgRandom()
    obj.calculate()


def main_test():
    main()


if __name__ == '__main__':
    main_test()

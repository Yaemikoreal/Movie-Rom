import random
import sqlite3
import pandas as pd

from data_entry.PublicFunctions import PublicFunctions

"""
1.随机读六十个电影信息以供index页面显示;
2.推荐界面推荐一批用户很有可能看过的电影让其进行评分:
        推荐要素：
            1.从top250电影中抽取，作为这一批电影的大头,占2/3到3/4;
            2.从电影表中抽取，在抽取的时候最新一年的不考虑(原因:太新了，看过的可能性要小一些)
"""


class ReadMovieImgRandom:
    def __init__(self):
        # 公共函数
        self.pf = PublicFunctions()
        # 数据库路径
        self.db_path = self.pf.path_get()
        #  豆瓣top250电影
        self.movie_top250_df_y = self.pf.read_table_all('movie_data_top250')
        # 电影信息df
        self.movie_msg_df = self.pf.read_table_all('movie_msg')

    def read_movie_img(self):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中随机读取六十行数据到 DataFrame
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

    def read_movie_df(self):
        # 排除movie_msg_df中 movie_img 列中为 None 的行
        filtered_df = self.movie_msg_df[self.movie_msg_df["movie_img"].notna()]
        # 在movie_msg中读出top250的电影全部信息,用于用户评分
        movie_top250_list = self.movie_top250_df_y['电影名字'].tolist()
        movie_top250_df = filtered_df[filtered_df["movie_name"].isin(movie_top250_list)]
        movie_not_in_top250_df = filtered_df[~filtered_df["movie_name"].isin(movie_top250_list)]
        return movie_top250_df, movie_not_in_top250_df

    def random_ten_movies(self, movie_top250_df, movie_not_in_top250_df):
        # 从 DataFrame 中随机挑选 random_num 行，从经典电影和新电影中一共提取十二个出来，经典高分电影占6-8个
        random_num = random.randint(6, 8)
        movie_top250_random_df = movie_top250_df.sample(n=random_num)
        new_movie_df = movie_not_in_top250_df.sample(n=12 - random_num)
        # 使用 concat() 函数将两个 DataFrame 合并在一起
        data_df = pd.concat([movie_top250_random_df, new_movie_df])
        return data_df

    def calculate(self, static):
        if static == 'index':
            # 读取出随机六十个电影展示
            data_df = self.read_movie_img()
            # 处理电影标签
            data_df = self.process_movie_tags(data_df)
            return data_df
        elif static == 'recommendation':
            # 将movie_msg表的电影信息分成经典电影和新电影,推荐逻辑为:从top250电影中推荐6-8个，从新电影中提取几个，一共十个
            movie_top250_df, movie_not_in_top250_df = self.read_movie_df()
            data_df = self.random_ten_movies(movie_top250_df, movie_not_in_top250_df)
            # 处理电影标签
            data_df = self.process_movie_tags(data_df)
            return data_df


def main():
    static = 'recommendation'
    obj = ReadMovieImgRandom()
    obj.calculate(static)


def main_test():
    main()


if __name__ == '__main__':
    main_test()

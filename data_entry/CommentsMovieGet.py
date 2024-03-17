import sqlite3
import time

import requests
import pandas as pd
from bs4 import BeautifulSoup
from data_entry.CalculateUserMsg import CalculateUserMsg
from data_entry.DataGetComment import DataGetComment
from data_entry.PublicFunctions import PublicFunctions
from algo.my_decorator import timer

'''
该脚本用于:
    1.爬取豆瓣单部电影的影评(该脚本主要实现),
    2.同步user_msg表中的user_id信息(调用CalculateUserMsg);
    3.同步movie_msg表中的movie_id信息(调用CalculateUserMsg)。
'''


class CommentsMovieGet:
    def __init__(self, *args, **kwargs):
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
        self.rating_list = ['allstar50 rating', 'allstar40 rating',
                            'allstar30 rating', 'allstar20 rating',
                            'allstar10 rating']
        # 公共函数
        self.pf = PublicFunctions()
        self.dgc = DataGetComment()
        # 数据库路径
        self.db_path = self.pf.path_get()
        # 电影名
        self.movie_name = None
        self.movie_data_list = []

    def get_comment(self, subject_id):
        # 打分默认值为还行
        rating_score = "还行"
        # 暂定每部电影100条评论
        page_list = [0, 20, 40, 60, 80]
        for page in page_list:
            # time.sleep(3)
            # 模拟浏览器发送请求
            url = f'https://movie.douban.com/subject/{subject_id}/comments?start={page}&limit=20&status=P&sort=new_score'
            headers = {
                'User-Agent': self.User_Agent
            }
            response = requests.get(url=url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            # if soup is None:
            #     return None
            # 通过类名查找元素
            soup = soup.find('div', id='content')
            if soup is None:
                return None
            # 找到包含电影名的 h1 标签
            movie_name_tag = soup.find('h1')
            # 提取电影名
            movie_name = movie_name_tag.text.strip()
            movie_name = movie_name.replace(" 短评", "")
            self.movie_name = movie_name
            soup = soup.find('div', class_='article')
            soup = soup.find('div', class_='mod-bd')
            # 使用 find_all 方法查找所有 data-cid 属性为数字的 div 元素
            div_list = soup.find_all('div', {'data-cid': True})
            for div in div_list:
                # 评论者名称
                user_id_tag = div.find('a')
                user_name = user_id_tag['title']
                user_name = user_name.replace("'", "")
                # 评论分数
                for it in self.rating_list:
                    a_tag = div.find('span', class_=f'{it}')
                    if a_tag is None:
                        continue
                    rating_score = a_tag.get('title')
                # 短评内容
                comment_tag = div.find('span', class_='short')
                short_commentary = comment_tag.text
                movie_dt = {
                    'user_name': user_name,
                    'movie_name': movie_name,
                    'movie_rating': rating_score,
                    'short_commentary': short_commentary
                }
                self.movie_data_list.append(movie_dt)
        movie_data_df = pd.DataFrame(self.movie_data_list)
        movie_data_df['movie_rating'] = movie_data_df['movie_rating'].replace(self.rating_score_dt)
        return movie_data_df

    def read_movie_data_comment(self, user_name, movie_name):
        conn = sqlite3.connect(self.db_path)
        user_name = fr'{user_name}'
        movie_name = fr'{movie_name}'
        # 从数据库中读取表格数据到 DataFrame
        data_df = pd.read_sql_query(
            f"SELECT * FROM movie_data_comment WHERE user_name = '{user_name}' AND movie_name = '{movie_name}'", conn)
        conn.close()
        return data_df

    def read_id_max(self):
        # 创建数据库连接对象
        conn = sqlite3.connect(self.db_path)
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
            short_commentary = row['short_commentary']
            data_df = self.read_movie_data_comment(user_name, movie_name)
            if data_df.empty:
                print(f"用户<{user_name}>对电影<{movie_name}>的评论写入，分数为<{rating_score}>!")
                new_movie_dt = {
                    "id": start_id,
                    "user_name": user_name,
                    "movie_name": movie_name,
                    "movie_rating": rating_score,
                    "short_commentary": short_commentary
                }
                new_movie_list.append(new_movie_dt)
                start_id += 1
                count_num += 1
            else:
                print(f"用户<{user_name}>对电影<{movie_name}>的评论已经存在！")
        new_movie_df = pd.DataFrame(new_movie_list)
        if new_movie_df.empty:
            print("暂无新影评可获取！")
        else:
            print(f"成功写入{count_num}条新数据！")
        return new_movie_df

    def get_movie_subject_id(self):
        movie_msg_df = self.pf.read_table_all("movie_msg")
        movie_data_comment_df = self.pf.read_table_all("movie_data_comment")
        merged_df = pd.merge(movie_msg_df, movie_data_comment_df, on='movie_name', how='left')
        result_df = merged_df.groupby('movie_name').size().reset_index(name='count')
        # 在 result_df 中包含 'subject_id' 列
        result_df = result_df.merge(merged_df[['movie_name', 'subject_id']].drop_duplicates(), on='movie_name',
                                    how='left')
        filtered_result_df = result_df[result_df['count'] < 100]
        movie_subject_id_list = filtered_result_df['subject_id'].values.tolist()
        return movie_subject_id_list

    def calculate_movie(self):
        # 筛除该库中评论数已超过100条的电影，并获取到需要获取评论的电影的subject_id
        movie_subject_id_list = self.get_movie_subject_id()
        # 对每部电影分别处理
        for subject_id in movie_subject_id_list:
            # movie_data_list用于存储所读取的电影评论信息
            self.movie_data_list = []
            movie_df = self.get_comment(subject_id)
            if movie_df is None:
                # 如果movie_df为空，则说明获取被拦截，跳出，下次再获取
                print("获取为空！！！")
                print("-----------------------------")
                continue
            new_movie_df = self.filter(movie_df)
            self.pf.write_sqlite_db(new_movie_df, 'movie_data_comment')
            print(f"电影{self.movie_name}的影评获取完毕!")
            print("---------------------------------")

    @timer
    def calculate(self):
        self.calculate_movie()



def main(**kwargs):
    obj = CommentsMovieGet(**kwargs)
    obj.calculate()
    # 同步表信息
    obs = CalculateUserMsg()
    obs.calculate()


def main_test():
    main()


if __name__ == '__main__':
    main_test()

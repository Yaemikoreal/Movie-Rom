import requests
import parsel
from sqlalchemy import create_engine
import pandas as pd
from algo.my_decorator import timer

'''
1、明确需求:
    爬取豆瓣Top250排行电影信息
        电影名字
        导演、主演
        年份、国家、类型
        评分、评价人数
        电影简介
'''


class DataGetTop250:
    def __init__(self):
        self.User_Agent = ('Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/81.0.4044.138 Safari/537.36')
        self.is_write = 1

    def get_top250(self):
        # movie_data_list用于存储所读取的所有电影信息
        movie_data_list = []
        # 模拟浏览器发送请求
        for page in range(0, 251, 25):
            url = f'https://movie.douban.com/top250?start={page}&filter='
            headers = {
                'User-Agent': self.User_Agent
            }
            response = requests.get(url=url, headers=headers)
            # 把 response.text 文本数据转换成 selector 对象
            selector = parsel.Selector(response.text)
            # 获取所有li标签
            lis = selector.css('.grid_view li')
            # 遍历出每个li标签内容
            for li in lis:
                # 获取电影标题 hd 类属性 下面的 a 标签下面的 第一个span标签里面的文本数据 get()输出形式是 字符串获取一个  getall() 输出形式是列表获取所有
                title = li.css('.hd a span:nth-child(1)::text').get()  # get()输出形式是 字符串
                movie_list = li.css('.bd p:nth-child(1)::text').getall()  # getall() 输出形式是列表
                star = movie_list[0].strip().replace('\xa0\xa0\xa0', '').replace('/...', '')
                movie_info = movie_list[1].strip().split('\xa0/\xa0')  # ['1994', '美国', '犯罪 剧情']
                movie_time = movie_info[0]  # 电影上映时间
                movie_country = movie_info[1]  # 哪个国家的电影
                movie_type = movie_info[2]  # 什么类型的电影
                rating_num = li.css('.rating_num::text').get()  # 电影评分
                people = li.css('.star span:nth-child(4)::text').get()  # 评价人数
                summary = li.css('.inq::text').get()  # 一句话概述
                dit = {
                    '电影名字': title,
                    '参演人员': star,
                    '上映时间': movie_time,
                    '拍摄国家': movie_country,
                    '电影类型': movie_type,
                    '电影评分': rating_num,
                    '评价人数': people,
                    '电影概述': summary,
                }
                movie_data_list.append(dit)
        return movie_data_list

    def write_sqlite_db(self, movie_data_list):
        movie_df = pd.DataFrame(movie_data_list)
        # 创建到 SQLite 数据库的引擎对象
        engine = create_engine('sqlite:///../db.sqlite3')
        # engine = create_engine('sqlite:///../MovieData.sqlite')
        # 将 DataFrame 写入 SQLite 数据库
        try:
            movie_df.to_sql('movie_data_top250', con=engine, if_exists='replace', index=False)
            print('写入成功！')
        except Exception as e:
            print(e)

    @timer
    def calculate(self):
        movie_data_list = self.get_top250()
        self.write_sqlite_db(movie_data_list)


def mian_test():
    obj = DataGetTop250()
    obj.calculate()


if __name__ == '__main__':
    mian_test()

import os
import numpy as np
import pandas as pd
from algo.MyDecorator import timer
from data_entry.PublicFunctions import PublicFunctions
from sklearn import model_selection as cv
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.metrics import mean_squared_error
from math import sqrt

"""
本脚本用于协同过滤算法推荐（test）
"""


class CollaborativeFiltering:
    def __init__(self, *args, **kwargs):
        self.collaborative_filtering = {}
        # 公共函数
        self.pf = PublicFunctions()
        # 数据库路径
        self.db_path = self.pf.path_get()
        # 所有数据综合df
        self.data_df = None
        # 电影总数
        self.n_items = None
        # 用户总数
        self.n_users = None
        # 推荐数据综合df
        self.user_movie_df = None
        # 传入的需要推荐的用户name
        self.user_name = kwargs.get('user_name')
        # 需要推荐的用户id
        self.user_id = self.pf.read_user_id(user_name=self.user_name)

    def read_movie_msg_df(self):
        movie_msg_df = self.pf.read_table_all("movie_msg")
        movie_msg_df['movie_id'] = movie_msg_df.reset_index().index + 1
        return movie_msg_df

    def splicing_processing(self, movie_data_comment_df, user_msg_df, movie_msg_df):
        # 拼接处理df
        merged_df = pd.merge(movie_data_comment_df, movie_msg_df, on='movie_name', how='right')
        merged_df = pd.merge(merged_df, user_msg_df, on='user_name', how='left')
        # 拼接df用于后续算法使用
        self.data_df = merged_df
        user_movie_df = merged_df[
            ['user_id', 'user_name', 'movie_id', 'movie_name', 'movie_rating', 'short_commentary']].copy()
        # 排除 'movie_rating' 列中的 float NaN 值
        user_movie_df = user_movie_df[user_movie_df['movie_rating'].notna()]
        return user_movie_df

    def read_data_df(self):
        """
        用于从库中得出所需数据，此处为全量读取
        :return:
        """
        movie_data_comment_df = self.pf.read_table_all("movie_data_comment")
        user_msg_df = self.pf.read_table_all("user_msg")
        movie_msg_df = self.read_movie_msg_df()

        # 处理拼接出需要用的数据df
        user_movie_df = self.splicing_processing(movie_data_comment_df, user_msg_df, movie_msg_df)
        self.user_movie_df = user_movie_df

        # 用户总数和电影总数
        self.n_users = user_msg_df.user_id.unique().shape[0]  # unique()为去重.shape[0]行个数
        self.n_items = movie_msg_df.movie_id.unique().shape[0]
        print('参与评价的用户数 = ' + str(self.n_users) + ' | 被评价的电影总数 = ' + str(self.n_items))
        return user_movie_df

    def calculate_data_matrix(self, data):
        # np.zeros是用于创建指定形状的全零数组的函数
        data_matrix = np.zeros((self.n_users, self.n_items))
        # .itertuples()用于迭代遍历数据框中的行，并返回每一行的命名元组
        for line in data.itertuples():
            user_id = int(line.user_id)
            movie_id = line.movie_id
            movie_rating = int(line.movie_rating)
            # 将用户id,电影Id和rating评分填写入矩阵对应框值里
            data_matrix[user_id - 1, movie_id - 1] = movie_rating
        return data_matrix

    def calculate_cosine_similarity(self, data_matrix):
        # # 计算了用户矩阵中每对用户之间的余弦相似度得分，最终生成一个用户相似度矩阵
        # user_similarity = pairwise_distances(data_matrix, metric='cosine')

        # 计算了转置后的用户-物品矩阵中每对物品之间的余弦相似度得分，最终生成一个物品相似度矩阵
        # .T 表示对 train_data_matrix 进行转置操作。
        item_similarity = pairwise_distances(data_matrix.T, metric='cosine')
        return item_similarity

    def predict(self, ratings, similarity, u_type):
        # 基于用户或物品的协同过滤算法，通过计算用户之间的相似度或物品之间的相似度，来预测用户对未评分物品的评分。
        # 根据不同的需求可以选择基于用户或基于物品的方法进行预测。
        if u_type == 'user':
            # 对于基于用户的预测，首先计算每个用户的平均评分，然后将原始评分减去平均评分，接着通过用户相似度加权得到预测评分。
            mean_user_rating = ratings.mean(axis=1)
            # 计算每个用户对电影评分与其对应平均评分的差值。mean_user_rating[:, np.newaxis]将平均评分数组转换为列向量，然后与原始评分矩阵相减，得到一个新的差值矩阵
            ratings_diff = (ratings - mean_user_rating[:, np.newaxis])
            # similarity.dot(ratings_diff)：计算电影之间的相似度与用户评分与平均评分的差值的乘积。
            # 这里利用了之前计算得到的相似度矩阵similarity，与用户评分与平均评分的差值矩阵相乘，得到一个新的矩阵，其中每个元素表示电影之间的相似度与用户评分差值的加权和。
            # np.array([np.abs(similarity).sum(axis=1)]).T：与之前相同，计算每部电影与其他电影相似度的绝对值之和，并将其转换为列向量。
            pred = mean_user_rating[:, np.newaxis] + similarity.dot(ratings_diff) / np.array(
                [np.abs(similarity).sum(axis=1)]).T
            return pred
        elif u_type == 'item':
            # 对于基于物品的预测，直接使用评分矩阵与物品相似度矩阵相乘，再除以物品相似度矩阵的绝对值之和，得到预测评分。
            # ratings.dot(similarity),矩阵相乘；np.array([np.abs(similarity).sum(axis=1)])，对similarity矩阵按行进行绝对值求和，并转成数组；
            pred = ratings.dot(similarity) / np.array([np.abs(similarity).sum(axis=1)])
            return pred

    def scoring_prediction(self, data_matrix, item_similarity):
        # 一行表示该用户对所有物品的评分预测结果，即用户对每个物品的预测评分。
        item_prediction = self.predict(data_matrix, item_similarity, u_type='item')
        # user_prediction = self.predict(data_matrix, user_similarity, u_type='user')
        return item_prediction

    def rmse(self, prediction, ground_truth):
        # ground_truth.nonzero()找出ground_truth中非零元素的位置,从prediction中提取对应位置的预测值，以便与真实值进行比较。
        # .flatten()：将提取出来的预测值和真实值展平为一维数组
        prediction = prediction[ground_truth.nonzero()].flatten()
        ground_truth = ground_truth[ground_truth.nonzero()].flatten()
        # 计算预测值和真实值之间的均方误差（MSE），即将预测值与真实值之差的平方求平均,然后对均方误差取平方根，得到均方根误差（RMSE），即误差的平方根。
        RMSE = sqrt(mean_squared_error(prediction, ground_truth))
        return RMSE

    def train_test_recommend(self, df, train_or_test='train', item_or_user='item'):
        # 计算item或者user推荐的最大50个值
        recommend_top50_train_arr = df[f'{train_or_test}_{item_or_user}'].nlargest(50).index.values
        # 分别取出训练集和测试集评价最高的五十个值
        recommend_top50_train_list = list(recommend_top50_train_arr)
        # 创建一个新的 DataFrame，只包含在 movie_id_list 中出现的 movie_id 对应的行
        filtered_train_df = self.data_df[self.data_df['movie_id'].isin(recommend_top50_train_list)]
        # 按照 movie_id_list 的顺序对筛选结果进行排序，保持原有推荐排序
        filtered_train_df['order'] = filtered_train_df['movie_id'].apply(lambda x: recommend_top50_train_list.index(x))
        filtered_train_df = filtered_train_df.sort_values('order')
        # 创建新的 DataFrame 包含电影ID和电影名
        recommend_top50_df = filtered_train_df[
            ['movie_id', 'movie_name', 'movie_labels', 'movie_img', 'average_score']].reset_index(drop=True)
        # recommend_top50_df 中根据 movie_id 和 movie_name 列进行去重操作，保留第一次出现的重复行，并在原 DataFrame 上进行修改。
        recommend_top50_df.drop_duplicates(subset=['movie_id', 'movie_name'], keep='first', inplace=True)
        return recommend_top50_df

    @timer
    def calculate_recommend(self, df):
        recommend_top50_train_df = self.train_test_recommend(df, 'train', 'item')
        recommend_top50_test_df = self.train_test_recommend(df, 'test', 'item')
        # # 使用 merge 函数在 movie_name 列上取交集
        # intersection_df = pd.merge(recommend_top50_train_df, recommend_top50_test_df, on='movie_name', how='inner')

        return recommend_top50_train_df, recommend_top50_test_df

    def save_data_to_csv(self, *predictions):
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录的上两层目录，也就是当前目录的父目录
        save_path = os.path.abspath(os.path.join(script_dir, '..', 'moviereal', 'csv'))

        # 确保保存路径存在
        os.makedirs(save_path, exist_ok=True)

        # 定义要保存的文件名列表
        file_names = ['train_item_prediction.csv', 'test_item_prediction.csv']

        # 遍历预测结果并保存为CSV文件
        for prediction, file_name in zip(predictions, file_names):
            # 将 NumPy 数组转换为 Pandas DataFrame 对象
            prediction_df = pd.DataFrame(prediction)
            file_path = os.path.join(save_path, file_name)
            prediction_df.to_csv(file_path, index=False)

        print("csv数据储存成功!")

    def read_first_row_and_column(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            # 读取第一行，并根据逗号分隔成列表
            first_row = file.readline().strip().split(',')
            # 读取第一列
            # 列表推导式，用于从文件中读取每一行，然后获取每行以逗号分隔的第一个元素，并将这些元素组成一个新的列表。
            first_column = [line.strip().split(',')[0] for line in file]

        return first_row, first_column

    def get_csv_shape(self, first_row, first_column):
        # 计算总行数
        num_rows = len(first_column)
        # 计算总列数
        num_cols = len(first_row)

        return num_rows, num_cols

    def check_csv_data(self):
        """
        检查csv中数据量是否和评论人数和电影数一致（即行数和列数）
        如果行数等于读取的用户数并且列数等于电影数，则可以认同数据没有大更新,则读取csv数据即可
        """
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录的上两层目录，也就是当前目录的父目录
        save_path = os.path.abspath(os.path.join(script_dir, '..', 'moviereal', 'csv'))
        read_path = os.path.join(save_path, 'train_item_prediction.csv')

        # 只读取第一行和第一列，这样避免了读取全量，读取获取速度更快
        first_row, first_column = self.read_first_row_and_column(read_path)

        # 获取总行数和列数
        num_rows, num_cols = self.get_csv_shape(first_row, first_column)

        # 如果行数等于读取的用户数并且列数等于电影数，则可以认同数据没有大更新,则读取csv数据即可
        if num_rows == self.n_users and num_cols == self.n_items:
            return False
        else:
            return True

    @timer
    def algorithm_processing(self, user_movie_df):
        """
        协同过滤算法处理阶段
        :param user_movie_df:
        :return:
        """

        # 使用train_test_split函数来将数据集划分为训练集和测试集，其中测试集占1/5
        train_data, test_data = cv.train_test_split(user_movie_df, test_size=0.2)
        # 创建了训练集和测试集的用户-物品矩阵，其中矩阵的行表示用户，列表示电影，矩阵中的值表示用户对电影的评分。
        train_data_matrix = self.calculate_data_matrix(train_data)
        test_data_matrix = self.calculate_data_matrix(test_data)
        # 使用 sklearn 的pairwise_distances函数来计算余弦相似性。注意，因为评价都为正值输出取值应为0到1.
        train_item_similarity = self.calculate_cosine_similarity(train_data_matrix)
        test_item_similarity = self.calculate_cosine_similarity(test_data_matrix)
        # 计算预测评分(运行时间最长，占用最大）
        train_item_prediction = self.scoring_prediction(train_data_matrix, train_item_similarity)
        test_item_prediction = self.scoring_prediction(test_data_matrix, test_item_similarity)
        # 存储数据到本地
        self.save_data_to_csv(train_item_prediction, test_item_prediction)
        # 估算一下，RMSE是一种常用的用于评估预测模型准确度的指标，
        # RMSE 的值越小，说明模型的预测结果与真实结果之间的差异越小，模型的拟合程度越好。因此，RMSE 越接近于零，表示模型的性能越好。
        print('(train)Item-based CF RMSE: ' + str(self.rmse(train_item_prediction, train_data_matrix)))
        print('(test)Item-based CF RMSE: ' + str(self.rmse(test_item_prediction, test_data_matrix)))

        # 此处id-1是因为构建矩阵长度从0开始，此处为获取当前检测用户的推荐计算结果值即可。
        user_id = self.user_id - 1
        data = {
            'train_item': train_item_prediction[user_id],
            'test_item': test_item_prediction[user_id],
        }
        data_df = pd.DataFrame(data)
        return data_df

    @timer
    def read_csv(self):
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录的上两层目录，也就是当前目录的父目录
        save_path = os.path.abspath(os.path.join(script_dir, '..', 'moviereal', 'csv'))

        read_path1 = os.path.join(save_path, 'train_item_prediction.csv')
        read_path2 = os.path.join(save_path, 'train_user_prediction.csv')
        read_path3 = os.path.join(save_path, 'test_item_prediction.csv')
        read_path4 = os.path.join(save_path, 'test_user_prediction.csv')

        # 此处id-1是因为构建矩阵长度从0开始
        user_id = self.user_id - 1

        # 读取CSV文件并加载数据为NumPy数组,只读了对应id的行，加快了读取速度
        train_item_prediction = np.genfromtxt(read_path1, delimiter=',', skip_header=user_id, max_rows=1)
        train_user_prediction = np.genfromtxt(read_path2, delimiter=',', skip_header=user_id, max_rows=1)
        test_item_prediction = np.genfromtxt(read_path3, delimiter=',', skip_header=user_id, max_rows=1)
        test_user_prediction = np.genfromtxt(read_path4, delimiter=',', skip_header=user_id, max_rows=1)

        data = {
            'train_item': train_item_prediction,
            'train_user': train_user_prediction,
            'test_item': test_item_prediction,
            'test_user': test_user_prediction
        }
        data_df = pd.DataFrame(data)

        return data_df

    def data_organization(self, recommend_top50_df):
        """
        数据整理，在推荐名单中去除该用户看过的电影
        :return:
        """
        one_user_df = self.data_df[self.data_df['user_name'] == self.user_name]
        user_movie_list = one_user_df['movie_name'].tolist()
        # 排除该用户已经看过的电影
        recommend_df = recommend_top50_df[~recommend_top50_df['movie_name'].isin(user_movie_list)]
        # 排除 movie_img 列中为空的行
        recommend_df = recommend_df.dropna(subset=['movie_img'])
        # 如果推荐数大于等于12，则返回十二个推荐结果；如果小于十二个，则有多少推荐多少
        if len(recommend_df) >= 12:
            # 推荐头12部电影
            recommend_df = recommend_df.head(12)
        else:
            # 获取所有电影
            recommend_df = recommend_df.head(len(recommend_df))
            # 随机抽取12部电影
            # recommend_df = recommend_df.sample(n=len(recommend_df), replace=False)
        return recommend_df

    @timer
    def calculate(self):
        user_movie_df = self.read_data_df()
        # 协同过滤算法推荐
        # 如果检查返回为True，则需要进行预测计算；为False时，简单认定可以沿用之前的csv预测数据
        # if not self.check_csv_data():
        print('需要计算！')
        data_df = self.algorithm_processing(user_movie_df)
        # else:
        #     print('正在读取！')
        #     data_df = self.read_csv()
        # 推荐计算(推荐前五十的电影)
        recommend_top50_train_df, recommend_top50_test_df = self.calculate_recommend(data_df)
        # 数据整理
        recommend_df = self.data_organization(recommend_top50_train_df)
        print(recommend_df)
        return recommend_df


@timer
def main(**kwargs):
    obj = CollaborativeFiltering(**kwargs)
    recommend_top10_df = obj.calculate()
    return recommend_top10_df


def main_test():
    user_name = '影志'
    main(user_name=user_name)


if __name__ == '__main__':
    main_test()

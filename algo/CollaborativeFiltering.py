import numpy as np
import pandas as pd

from algo.MyDecorator import timer
from data_entry.PublicFunctions import PublicFunctions
from sklearn import model_selection as cv
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.metrics import mean_squared_error
from math import sqrt

"""
本脚本用于协同过滤算法（test）
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
        # 传入的需要推荐的用户id
        self.user_id = kwargs.get('user_id')

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
        # 计算了用户矩阵中每对用户之间的余弦相似度得分，最终生成一个用户相似度矩阵
        user_similarity = pairwise_distances(data_matrix, metric='cosine')
        # 计算了转置后的用户-物品矩阵中每对物品之间的余弦相似度得分，最终生成一个物品相似度矩阵
        # .T 表示对 train_data_matrix 进行转置操作。
        item_similarity = pairwise_distances(data_matrix.T, metric='cosine')
        return user_similarity, item_similarity

    def predict(self, ratings, similarity, u_type):
        # 基于用户或物品的协同过滤算法，通过计算用户之间的相似度或物品之间的相似度，来预测用户对未评分物品的评分。
        # 根据不同的需求可以选择基于用户或基于物品的方法进行预测。
        if u_type == 'user':
            # 对于基于用户的预测，首先计算每个用户的平均评分，然后将原始评分减去平均评分，接着通过用户相似度加权得到预测评分。
            mean_user_rating = ratings.mean(axis=1)
            ratings_diff = (ratings - mean_user_rating[:, np.newaxis])
            pred = mean_user_rating[:, np.newaxis] + similarity.dot(ratings_diff) / np.array(
                [np.abs(similarity).sum(axis=1)]).T
            return pred
        elif u_type == 'item':
            # 对于基于物品的预测，直接使用评分矩阵与物品相似度矩阵相乘，再除以物品相似度矩阵的绝对值之和，得到预测评分。
            pred = ratings.dot(similarity) / np.array([np.abs(similarity).sum(axis=1)])
            return pred

    def scoring_prediction(self, data_matrix, item_similarity, user_similarity):
        # 一行表示该用户对所有物品的评分预测结果，即用户对每个物品的预测评分。
        item_prediction = self.predict(data_matrix, item_similarity, u_type='item')
        user_prediction = self.predict(data_matrix, user_similarity, u_type='user')
        return item_prediction, user_prediction

    def rmse(self, prediction, ground_truth):
        # ground_truth.nonzero()找出ground_truth中非零元素的位置,从prediction中提取对应位置的预测值，以便与真实值进行比较。
        # .flatten()：将提取出来的预测值和真实值展平为一维数组
        prediction = prediction[ground_truth.nonzero()].flatten()
        ground_truth = ground_truth[ground_truth.nonzero()].flatten()
        # 计算预测值和真实值之间的均方误差（MSE），即将预测值与真实值之差的平方求平均,然后对均方误差取平方根，得到均方根误差（RMSE），即误差的平方根。
        RMSE = sqrt(mean_squared_error(prediction, ground_truth))
        return RMSE

    def calculate_recommend(self, train_item_prediction, train_user_prediction, test_item_prediction,
                            test_user_prediction):
        # 将 NumPy 数组转换为 Pandas DataFrame，并根据用户 ID 获取对应行数据
        # 此处id-1是因为构建矩阵长度从0开始
        user_id = self.user_id - 1
        data = {
            'train_item': train_item_prediction[user_id],
            'train_user': train_user_prediction[user_id],
            'test_item': test_item_prediction[user_id],
            'test_user': test_user_prediction[user_id]
        }
        df = pd.DataFrame(data)
        # 计算每行除了新加一列外的其他列的平均值
        df['mean'] = df.mean(axis=1)
        # 取出评价的十个最大值
        top10_indices_arr = df['mean'].nlargest(50).index.values
        recommend_top50_list = list(top10_indices_arr)

        # 创建一个新的 DataFrame，只包含在 movie_id_list 中出现的 movie_id 对应的行
        filtered_df = self.data_df[self.data_df['movie_id'].isin(recommend_top50_list)]

        # 按照 movie_id_list 的顺序对筛选结果进行排序，保持原有推荐排序
        filtered_df['order'] = filtered_df['movie_id'].apply(lambda x: recommend_top50_list.index(x))
        filtered_df = filtered_df.sort_values('order')

        # 创建新的 DataFrame 包含电影ID和电影名
        recommend_top50_df = filtered_df[['movie_id', 'movie_name', 'movie_labels', 'movie_img','average_score']].reset_index(drop=True)
        # recommend_top50_df 中根据 movie_id 和 movie_name 列进行去重操作，保留第一次出现的重复行，并在原 DataFrame 上进行修改。
        recommend_top50_df.drop_duplicates(subset=['movie_id', 'movie_name'], keep='first', inplace=True)
        # todo 通过recommend_top10_df进行推荐分析
        return recommend_top50_df

    @timer
    def algorithm_processing(self, user_movie_df):
        """
        协同过滤算法处理阶段
        :param user_movie_df:
        :return:
        """
        # 使用train_test_split函数来将数据集划分为训练集和测试集，其中测试集占1/4
        train_data, test_data = cv.train_test_split(user_movie_df, test_size=0.25)
        # 创建了训练集和测试集的用户-物品矩阵，其中矩阵的行表示用户，列表示电影，矩阵中的值表示用户对电影的评分。
        train_data_matrix = self.calculate_data_matrix(train_data)
        test_data_matrix = self.calculate_data_matrix(test_data)
        # 使用 sklearn 的pairwise_distances函数来计算余弦相似性。注意，因为评价都为正值输出取值应为0到1.
        train_user_similarity, train_item_similarity = self.calculate_cosine_similarity(train_data_matrix)
        test_user_similarity, test_item_similarity = self.calculate_cosine_similarity(test_data_matrix)
        # 计算预测评分
        train_item_prediction, train_user_prediction = self.scoring_prediction(train_data_matrix, train_item_similarity,
                                                                               train_user_similarity)
        test_item_prediction, test_user_prediction = self.scoring_prediction(test_data_matrix, test_item_similarity,
                                                                             test_user_similarity)
        # 估算一下，RMSE是一种常用的用于评估预测模型准确度的指标，
        # RMSE 的值越小，说明模型的预测结果与真实结果之间的差异越小，模型的拟合程度越好。因此，RMSE 越接近于零，表示模型的性能越好。
        print('User-based CF RMSE: ' + str(self.rmse(train_user_prediction, train_data_matrix)))
        print('Item-based CF RMSE: ' + str(self.rmse(train_item_prediction, train_data_matrix)))
        print('User-based CF RMSE: ' + str(self.rmse(test_user_prediction, test_data_matrix)))
        print('Item-based CF RMSE: ' + str(self.rmse(test_item_prediction, test_data_matrix)))

        # 推荐计算(推荐前五十的电影)
        recommend_top50_df = self.calculate_recommend(train_item_prediction, train_user_prediction,
                                                      test_item_prediction,
                                                      test_user_prediction)

        return recommend_top50_df

    def calculate(self):
        user_movie_df = self.read_data_df()
        # 协同过滤算法推荐
        recommend_top50_df = self.algorithm_processing(user_movie_df)
        return recommend_top50_df


def main(**kwargs):
    obj = CollaborativeFiltering(**kwargs)
    recommend_top10_df = obj.calculate()
    return recommend_top10_df


def main_test():
    user_id = 21261
    main(user_id=user_id)


if __name__ == '__main__':
    main_test()

"""
title:python 实现协同过滤算法基于用户与基于内容
"""
import numpy as np
import pandas as pd
from sklearn import model_selection as cv

# u.data文件中包含了完整数据集。
u_data_path = "D:\\python_test\\MovieRecommended\\"
# 分别为：用户id,电影id，rating评分，以及评论的时间戳
header = ['user_id', 'item_id', 'rating', 'timestamp']
df = pd.read_csv(u_data_path + 'ml-100k/u.data', sep='\t', names=header)
print(df.head(5))
print(f"data_df长度:{len(df)}")
# 观察数据前两行。接下来，让我们统计其中的用户和电影总数。
n_users = df.user_id.unique().shape[0]  # unique()为去重.shape[0]行个数
n_items = df.item_id.unique().shape[0]
print('参与评价的用户数 = ' + str(n_users) + ' | 被评价的电影总数 = ' + str(n_items))

# 使用train_test_split函数来将数据集划分为训练集和测试集，其中测试集占1/4
train_data, test_data = cv.train_test_split(df, test_size=0.25)

# Create two user-item matrices, one for training and another for testing
# 差别在于train_data与test_data
# np.zeros是用于创建指定形状的全零数组的函数
# 创建了训练集和测试集的用户-物品矩阵，其中矩阵的行表示用户，列表示电影，矩阵中的值表示用户对电影的评分。
train_data_matrix = np.zeros((n_users, n_items))
print(train_data_matrix.shape)
# .itertuples()是 Pandas DataFrame 对象的一个方法，用于迭代遍历数据框中的行，并返回每一行的命名元组。该方法返回的是一个迭代器，您可以使用 for 循环来遍历数据框中的行，并获取每一行的数据。
for line in train_data.itertuples():
    # 将用户id,电影Id和rating评分填写入矩阵对应框值里
    train_data_matrix[line[1] - 1, line[2] - 1] = line[3]

test_data_matrix = np.zeros((n_users, n_items))
for line in test_data.itertuples():
    test_data_matrix[line[1] - 1, line[2] - 1] = line[3]
# 你可以使用 sklearn 的pairwise_distances函数来计算余弦相似性。注意，因为评价都为正值输出取值应为0到1.
from sklearn.metrics.pairwise import pairwise_distances

# 计算了用户矩阵中每对用户之间的余弦相似度得分，最终生成一个用户相似度矩阵
user_similarity = pairwise_distances(train_data_matrix, metric='cosine')
# 计算了转置后的用户-物品矩阵中每对物品之间的余弦相似度得分，最终生成一个物品相似度矩阵
# .T 表示对 train_data_matrix 进行转置操作。对于矩阵而言，转置是将矩阵的行和列进行交换，即原先的行变成了列，原先的列变成了行。
item_similarity = pairwise_distances(train_data_matrix.T, metric='cosine')


def predict(ratings, similarity, type='user'):
    if type == 'user':
        mean_user_rating = ratings.mean(axis=1)
        # You use np.newaxis so that mean_user_rating has same format as ratings
        ratings_diff = (ratings - mean_user_rating[:, np.newaxis])
        pred = mean_user_rating[:, np.newaxis] + similarity.dot(ratings_diff) / np.array(
            [np.abs(similarity).sum(axis=1)]).T
    elif type == 'item':
        pred = ratings.dot(similarity) / np.array([np.abs(similarity).sum(axis=1)])
    return pred

# 测结果 item_prediction 是一个矩阵，其中每行代表一个用户对所有物品的评分预测值。
item_prediction = predict(train_data_matrix, item_similarity, type='item')
# 预测结果 user_prediction 也是一个矩阵，其中每行代表一个用户对所有物品的评分预测值。
user_prediction = predict(train_data_matrix, user_similarity, type='user')

# 有许多的评价指标，但是用于评估预测精度最流行的指标之一是Root Mean Squared Error (RMSE)。
from sklearn.metrics import mean_squared_error
from math import sqrt

def rmse(prediction, ground_truth):
    prediction = prediction[ground_truth.nonzero()].flatten()  # nonzero(a)返回数组a中值不为零的元素的下标,相当于对稀疏矩阵进行提取
    ground_truth = ground_truth[ground_truth.nonzero()].flatten()
    return sqrt(mean_squared_error(prediction, ground_truth))


print('User-based CF RMSE: ' + str(rmse(user_prediction, test_data_matrix)))
print('Item-based CF RMSE: ' + str(rmse(item_prediction, test_data_matrix)))

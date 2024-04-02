import sqlite3
import pandas as pd

from data_entry.PublicFunctions import PublicFunctions


"""
获取用户基本信息用于展示
"""

class ReadUserLogMsg():
    def __init__(self):
        # 公共函数
        self.pf = PublicFunctions()
        # 数据库路径
        self.db_path = self.pf.path_get()

    def read_auth_user(self, username):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中读取到该用户信息
        auth_user_df = pd.read_sql_query(f"SELECT * FROM auth_user WHERE username = '{username}'", conn)
        conn.close()
        return auth_user_df

    def integrate_user_information(self, auth_user_df):
        # 整合用户信息
        user_information_dt = {}
        if auth_user_df.empty:
            return user_information_dt
        user_information_dt['id'] = str(auth_user_df['id'][0])
        user_information_dt['username'] = auth_user_df['username'][0]
        user_information_dt['email'] = auth_user_df['email'][0]
        # 只保留日期部分
        last_time = auth_user_df['last_login'][0]
        if last_time:
            last_time = auth_user_df['last_login'][0][:10]
        else:
            last_time = "没有登录记录！"
        user_information_dt['lastlogin'] = last_time
        if auth_user_df['last_name'][0] is not '' and auth_user_df['first_name'][0] is not '':
            user_information_dt['nickname'] = f"{auth_user_df['last_name'][0]}{auth_user_df['first_name'][0]}"
        else:
            user_information_dt['nickname'] = "暂无"
        return user_information_dt

    def calculate(self, username, static):
        # 当static等于1时，获取用户信息
        if static == 1:
            auth_user_df = self.read_auth_user(username)
            # 整合用户信息
            user_information_dt = self.integrate_user_information(auth_user_df)
            return user_information_dt
        # 当static等于2时，写入当前用户的登录信息
        elif static == 2:
            pass


def main():
    username = 'Yaemiko'
    obj = ReadUserLogMsg()
    obj.calculate(username)


def main_test():
    main()


if __name__ == '__main__':
    main_test()

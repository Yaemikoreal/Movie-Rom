import sqlite3

import pandas as pd

from data_entry.PublicFunctions import PublicFunctions


class UserRegister():
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

    def user_information_verification(self, user_dt):
        user_name = user_dt.get('username')
        user_df = self.read_auth_user(user_name)
        # 检查该用户名是否已经存在
        if not user_df.empty:
            return "该用户名已经存在!"
        # 密码检测
        user_password = user_dt.get('password')
        if len(user_password) < 8:
            return "你的密码必须包含至少 8 个字符。"
        if user_password.isdigit():
            return "你的密码不能全都是数字。"
        return False

    def calculate(self, user_dt):
        # 对用户信息进行验证
        static = self.user_information_verification(user_dt)
        return static


def main():
    user_dt = {
        "username": "test1",
        "password": "<PASSWORD>",
        "email": "<EMAIL>",
        "name": "+9112345678"
    }
    obj = UserRegister()
    obj.calculate(user_dt)


def main_test():
    main()


if __name__ == '__main__':
    main_test()

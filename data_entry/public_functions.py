import os
import sqlite3

import pandas as pd


class PublicFunctions(object):
    def __init__(self):
        self.db_path = self.path_get()

    def path_get(self):
        # 获取当前脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录的上一层目录
        script_dir = os.path.dirname(script_dir)
        # 构建数据库文件的路径
        db_path = os.path.join(script_dir, "MovieData.sqlite")
        return db_path

    def read_table_all(self, read_table):
        conn = sqlite3.connect(self.db_path)
        # 从数据库中读取表格数据到 DataFrame
        data_df = pd.read_sql_query(f"SELECT * FROM {read_table}", conn)
        conn.close()
        return data_df

    def write_sqlite_db(self, movie_df, write_table):
        if not movie_df.empty:
            conn = sqlite3.connect(self.db_path)
            # 将 DataFrame 写入到已存在的数据库表中
            movie_df.to_sql(write_table, conn, if_exists='append', index=False)
            print(f"{write_table}表内容写入成功！")
            # 关闭数据库连接
            conn.close()
        else:
            print("暂无信息需要写入！")

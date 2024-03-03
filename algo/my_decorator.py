from datetime import datetime


def timer(func):
    def wrapper(*args, **kwargs):
        # 在调用函数前的操作
        start_time = datetime.now()
        result = func(*args, **kwargs)
        # 在调用函数后的操作
        end_time = datetime.now()
        used_time = end_time - start_time
        print(f"该方法运行时间为:{used_time}")
        return result

    return wrapper

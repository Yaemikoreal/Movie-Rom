from datetime import datetime
import inspect


def timer(func):
    def wrapper(*args, **kwargs):
        # 获取调用函数的名称和路径
        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0])
        caller_function_name = caller_frame.function
        caller_function_path = caller_module.__file__

        # 在调用函数前的操作
        start_time = datetime.now()
        result = func(*args, **kwargs)
        # 在调用函数后的操作
        end_time = datetime.now()
        used_time = end_time - start_time
        print(f"函数 <{caller_function_name}>在路径 <{caller_function_path}> 下的运行时间为: <{used_time}>")
        return result

    return wrapper

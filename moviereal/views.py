import json
from django.shortcuts import render, HttpResponse, redirect
from algo.ReadMovieImgRandom import ReadMovieImgRandom
from functional_zone.ReadUserLogMsg import ReadUserLogMsg
from functional_zone.UserRegister import UserRegister
from .models import Moviereal
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse


# Create your views here.

def moviereal(request):
    # 重定向到用户登录页面
    return redirect('/moviereal/userlogin')


def userlogin(request):
    """
    用户登录
    :param request:
    :return:
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        # 处理表单提交逻辑
        username = data.get('username')
        password = data.get('password')

        # 进行用户认证逻辑
        authenticated_user = authenticate(request, username=username, password=password)

        if authenticated_user is not None:
            # 验证成功，返回成功信息给前端
            response_data = {'success': True, 'message': '登录成功!'}
            return JsonResponse(response_data)
        else:
            # 认证失败，可以返回一个错误页面或重定向到登录页面
            response_data = {'success': False, 'message': '用户名或密码不正确！'}
            return JsonResponse(response_data)
    else:
        # GET 请求时返回登录表单页面
        return render(request, 'user_login.html')


def userregister(request):
    """
    用户注册
    :param request:
    :return:
    """

    if request.method == 'POST':
        data = json.loads(request.body)
        # 处理表单提交逻辑

        # 密码规则:
        # 你的密码不能与你的其他个人信息太相似。
        # 你的密码必须包含至少 8 个字符。
        # 你的密码不能全都是数字。

        obj = UserRegister()
        static = obj.calculate(data)
        if static:
            response_data = {'success': False, 'message': static}
            return JsonResponse(response_data)
        # 创建用户对象
        try:
            # 使用 User.objects.create_user 方法创建用户时，Django 会自动处理密码的加密，并将用户对象（包括加密后的密码）保存到 auth_user 表中。
            user = User.objects.create_user(username=data["username"], email=data["email"], password=data["password"],
                                            first_name=data["name"][0:1], last_name=data["name"][1:])
            user.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        # 注册成功，返回成功信息
        response_data = {'success': True, 'message': '用户注册成功！'}
        return JsonResponse(response_data)
    else:
        # 如果不是POST请求，返回注册表单页面
        return render(request, 'userregister.html')


def index(request):
    """首页"""
    if request.method == 'GET':
        #  从表中读出随机三十个的电影信息
        obj = ReadMovieImgRandom()
        data_df = obj.calculate()
        json_data = data_df.to_json(orient='records')
        context = json.loads(json_data)
        return render(request, 'index.html', {'movies': context})


def userlogmsg(request):
    # 获取传递过来的用户名参数
    username = request.GET.get('username', None)
    if username:
        # 如果用户名存在，进行处理
        obj = ReadUserLogMsg()
        user_dt = obj.calculate(username=username, static=1)
        # 将字典转换为 JSON 字符串
        json_string = json.dumps(user_dt)
        # 认证成功，更新用户登录时间信息
        obj.calculate(username=username, static=2)
        return HttpResponse(json_string)


def detail(request, goods_id):
    """详情页"""
    # 通过request 获取请求参数 /goods/detail?id=3&username=xxx&pwd=yyy
    # goods_id = request.GET.get('id')
    # 查询具体某个商品的信息
    goods = Moviereal.objects.get(id=goods_id)
    goods.create_time = goods.create_time.date()
    # print(goods)

    # 传给模板的参数
    context = {'goods': goods}
    return render(request, 'detail.html', context)

import requests
from django.shortcuts import render, HttpResponse
from .models import Moviereal


# Create your views here.

def moviereal(request):
    return HttpResponse("欢迎访问moviereal!")


def userlogin(request):
    return render(request, "user_login.html")


def index(request):
    """首页"""
    # 通过模型获取数据库中的商品列表数据
    # Moviereal类--》表 objects对象 ---》表的记录
    goods_list = Moviereal.objects.all()
    print(goods_list)
    # return HttpResponse("商品首页")
    # 向模板页面传递的参数， 以字典的形式封装在context中
    context = {
        'infos': goods_list
    }
    # return HttpResponse("商品首页") 渲染
    # request: http 请求参数 ，index.html：模板页面 context：传给模板页面的参数
    return render(request, 'index.html', context)
    # return HttpResponse("商品首页")


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
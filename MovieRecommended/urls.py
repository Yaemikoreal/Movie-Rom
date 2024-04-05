"""
URL configuration for MovieRecommended project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

import moviereal.views

urlpatterns = [
    # admin管理界面
    path('admin/', admin.site.urls, name='admin'),

    # moviereal函数
    path('', moviereal.views.moviereal, name='moviereal'),

    # userlogin函数
    path('moviereal/userlogin', moviereal.views.userlogin, name='userlogin'),

    # 推荐页面
    path('moviereal/recommendation',moviereal.views.recommendation, name='recommendation'),

    # 推荐展示页面,接受 user_name 参数
    path('moviereal/recommendation_show/<str:user_name>/', moviereal.views.recommendation_show, name='recommendation_show'),

    # 注册处理
    path('moviereal/userregister', moviereal.views.userregister, name='userregister'),

    # 测试页面，用于展示
    path('moviereal/index', moviereal.views.index, name='index'),

    # 获取用户信息，从django默认用户表中
    path('moviereal/userlogmsg', moviereal.views.userlogmsg, name='userlogmsg'),

    # path('detail/', moviereal.views.detail, name='detail'),
    path('detail/<int:goods_id>/', moviereal.views.detail, name='detail'),
]

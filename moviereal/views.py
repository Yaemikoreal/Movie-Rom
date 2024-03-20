from django.shortcuts import render,HttpResponse

# Create your views here.

def moviereal(request):
    return HttpResponse("欢迎访问moviereal!")

def userlogin(request):
    return render(request,"user_login.html")

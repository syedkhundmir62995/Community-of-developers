from django.contrib import messages
from django.contrib import auth
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib import auth

def login(request):
    if request.method == 'POST':
        uname = request.POST['uname']
        passd = request.POST['passd']

        user = auth.authenticate(request, username = uname, password = passd)
        if user is None:
            messages.info(request,"INVALID CREDENTIALS")
            return redirect('loginpage')
        else:
            auth.login(request,user)
            messages.info(request,"LOGIN SUCCESSFUL")
            return redirect('dashboardpage')
    else:
        return render(request,'loginapp/login.html')



def logout(request):
    auth.logout(request)
    return redirect('homepage')
    
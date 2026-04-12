from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Song

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        User.objects.create_user(username=username, password=password)
        return redirect('login')

    return render(request, 'register.html')



def dashboard(request):
    songs = Song.objects.all()
    return render(request, 'dashboard.html', {'songs': songs})
    return render(request, 'dashboard.html')


def user_logout(request):
    logout(request)
    return redirect('login')


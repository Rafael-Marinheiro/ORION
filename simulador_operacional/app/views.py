from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

class HomeView(TemplateView):
    template_name = 'home.html'
    # login_url = '/accounts/login/'

@login_required
def home(request):
    return render(request, 'home.html')
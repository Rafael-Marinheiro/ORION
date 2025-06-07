from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import (
    TransportRoute,
    PriceList,
    Sale,
    FinancialResult,
    Ranking,
    EventHistory,
)


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("home")


class HomeView(TemplateView):
    template_name = "home.html"


@login_required
def home(request):
    return render(request, "home.html")


class DistributionView(ListView):
    template_name = "distribution.html"
    model = TransportRoute
    context_object_name = "rotas"


class FinancialView(ListView):
    template_name = "financial.html"
    model = Ranking
    context_object_name = "rankings"


class EventsView(ListView):
    template_name = "events.html"
    model = EventHistory
    context_object_name = "eventos"



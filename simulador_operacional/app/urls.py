from django.urls import path
from .views import (
    HomeView,
    CustomLoginView,
    DistributionView,
    FinancialView,
    EventsView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('distribuicao/', DistributionView.as_view(), name='distribution'),
    path('financeiro/', FinancialView.as_view(), name='financial'),
    path('eventos/', EventsView.as_view(), name='events'),
]

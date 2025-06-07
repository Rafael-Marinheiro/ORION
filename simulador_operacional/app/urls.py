from django.urls import path
from .views import HomeView, CustomLoginView, config_view, group_panel, production_config

urlpatterns = [
    path("config/", config_view, name="config"),
    path("painel/", group_panel, name="group_panel"),
    path("producao/", production_config, name="production_config"),
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
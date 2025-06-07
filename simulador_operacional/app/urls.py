from django.urls import path
from .views import (
    HomeView,
    CustomLoginView,
    relatorios_financeiros,
    ranking_grupos,
    sortear_evento,
    resumo_encerramento,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('financeiro/', relatorios_financeiros, name='relatorios_financeiros'),
    path('ranking/', ranking_grupos, name='ranking_grupos'),
    path('eventos/', sortear_evento, name='sortear_evento'),
    path('encerramento/', resumo_encerramento, name='resumo_encerramento'),
]

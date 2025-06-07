from django.urls import path, include
from django.contrib.auth.views import LogoutView
from .views import (
    HomeView,
    CustomLoginView,
    RegisterView,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
    GameConfigUpdateView,
    RodadaCreateView,
    PainelGrupoView,
    RankingView,
    GrupoViewSet,
    GrupoListView,
    GrupoCreateView,
    GrupoUpdateView,
    RankingAPIView,
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('grupos', GrupoViewSet)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('config/', GameConfigUpdateView.as_view(), name='game_config'),
    path('abrir_rodada/', RodadaCreateView.as_view(), name='abrir_rodada'),
    path('painel/', PainelGrupoView.as_view(), name='painel_grupo'),
    path('ranking/', RankingView.as_view(), name='ranking'),
    path('grupos/', GrupoListView.as_view(), name='lista_grupos'),
    path('grupos/novo/', GrupoCreateView.as_view(), name='criar_grupo'),
    path('grupos/<int:pk>/editar/', GrupoUpdateView.as_view(), name='editar_grupo'),
    path('api/', include(router.urls)),
    path('api/ranking/', RankingAPIView.as_view(), name='api_ranking'),
]

from django.urls import path, include
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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
    DecisaoViewSet,
    DistribuicaoViewSet,
    ResultadoFinanceiroViewSet,
    EventoViewSet,
    EventoRodadaViewSet,
    RodadaViewSet,
    CidadeViewSet,
    GameConfigViewSet,
    GrupoListView,
    GrupoCreateView,
    GrupoUpdateView,
    RankingAPIView,
    RelatoriosView,
    AjudaView,
    export_resultados_pdf,
    export_resultados_excel,
)

router = DefaultRouter()
router.register("grupos", GrupoViewSet)
router.register("decisoes", DecisaoViewSet)
router.register("distribuicoes", DistribuicaoViewSet)
router.register("resultados", ResultadoFinanceiroViewSet)
router.register("eventos", EventoViewSet)
router.register("eventos-rodada", EventoRodadaViewSet)
router.register("rodadas", RodadaViewSet)
router.register("cidades", CidadeViewSet)
router.register("config", GameConfigViewSet)

schema_view = get_schema_view(
    openapi.Info(title="Simulador API", default_version="v1"),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("config/", GameConfigUpdateView.as_view(), name="game_config"),
    path("abrir_rodada/", RodadaCreateView.as_view(), name="abrir_rodada"),
    path("painel/", PainelGrupoView.as_view(), name="painel_grupo"),
    path("ranking/", RankingView.as_view(), name="ranking"),
    path("grupos/", GrupoListView.as_view(), name="lista_grupos"),
    path("grupos/novo/", GrupoCreateView.as_view(), name="criar_grupo"),
    path("grupos/<int:pk>/editar/", GrupoUpdateView.as_view(), name="editar_grupo"),
    path("relatorios/", RelatoriosView.as_view(), name="relatorios"),
    path("ajuda/", AjudaView.as_view(), name="ajuda"),
    path("export/pdf/", export_resultados_pdf, name="export_resultados_pdf"),
    path("export/excel/", export_resultados_excel, name="export_resultados_excel"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/ranking/", RankingAPIView.as_view(), name="api_ranking"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/", include(router.urls)),
]

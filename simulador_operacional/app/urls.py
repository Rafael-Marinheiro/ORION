from django.contrib.auth.views import LogoutView
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AplicacaoFinanceiraGrupoViewSet,
    AjudaView,
    AuditoriaSubmissaoRodadaViewSet,
    CidadeViewSet,
    CapacidadeProdutoGrupoViewSet,
    CEOGrupoRodadaViewSet,
    ConsolidadoRodadaGrupoViewSet,
    DemandaCidadeProdutoViewSet,
    CompraMateriaPrimaViewSet,
    ComposicaoProdutoViewSet,
    CustomLoginView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    DecisaoViewSet,
    DistribuicaoViewSet,
    EventoRodadaViewSet,
    EventoViewSet,
    GameConfigUpdateView,
    GameConfigWizardView,
    GameConfigViewSet,
    GrupoCreateView,
    GrupoListView,
    GrupoUpdateView,
    GrupoViewSet,
    HomeView,
    IndicadorRodadaGrupoViewSet,
    InvestimentoViewSet,
    JobsView,
    JogoViewSet,
    MarketShareCidadeProdutoViewSet,
    MateriaPrimaViewSet,
    EstoqueMateriaPrimaViewSet,
    EstoqueProdutoViewSet,
    PainelGrupoView,
    ProducaoViewSet,
    ProdutoViewSet,
    RankingAPIView,
    RankingMulticriterioAPIView,
    RankingView,
    RegisterView,
    RelatoriosView,
    ResultadoFinanceiroViewSet,
    RodadaCreateView,
    RodadaViewSet,
    export_resultados_excel,
    export_resultados_pdf,
    ExecucaoJobViewSet,
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
router.register("jogos", JogoViewSet)
router.register("investimentos", InvestimentoViewSet)
router.register("materias-primas", MateriaPrimaViewSet)
router.register("produtos", ProdutoViewSet)
router.register("composicoes-produto", ComposicaoProdutoViewSet)
router.register("producoes", ProducaoViewSet)
router.register("capacidades-produto", CapacidadeProdutoGrupoViewSet)
router.register("consolidados-rodada", ConsolidadoRodadaGrupoViewSet)
router.register("ceos-rodada", CEOGrupoRodadaViewSet)
router.register("auditoria-submissoes", AuditoriaSubmissaoRodadaViewSet)
router.register("demanda-cidade-produto", DemandaCidadeProdutoViewSet)
router.register("aplicacoes-financeiras", AplicacaoFinanceiraGrupoViewSet)
router.register("execucoes-jobs", ExecucaoJobViewSet)
router.register("estoques-mp", EstoqueMateriaPrimaViewSet)
router.register("estoques-produto", EstoqueProdutoViewSet)
router.register("compras-mp", CompraMateriaPrimaViewSet)
router.register("market-share", MarketShareCidadeProdutoViewSet)
router.register("indicadores-rodada", IndicadorRodadaGrupoViewSet)

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
    path("config/wizard/", GameConfigWizardView.as_view(), name="game_config_wizard"),
    path("abrir_rodada/", RodadaCreateView.as_view(), name="abrir_rodada"),
    path("painel/", PainelGrupoView.as_view(), name="painel_grupo"),
    path("ranking/", RankingView.as_view(), name="ranking"),
    path("grupos/", GrupoListView.as_view(), name="lista_grupos"),
    path("grupos/novo/", GrupoCreateView.as_view(), name="criar_grupo"),
    path("grupos/<int:pk>/editar/", GrupoUpdateView.as_view(), name="editar_grupo"),
    path("relatorios/", RelatoriosView.as_view(), name="relatorios"),
    path("jobs/", JobsView.as_view(), name="jobs"),
    path("ajuda/", AjudaView.as_view(), name="ajuda"),
    path("export/pdf/", export_resultados_pdf, name="export_resultados_pdf"),
    path("export/excel/", export_resultados_excel, name="export_resultados_excel"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/ranking/", RankingAPIView.as_view(), name="api_ranking"),
    path("api/ranking-multicriterio/", RankingMulticriterioAPIView.as_view(), name="api_ranking_multicriterio"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/", include(router.urls)),
]

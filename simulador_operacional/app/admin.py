from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import (
    AplicacaoFinanceiraGrupo,
    AuditoriaSubmissaoRodada,
    CapacidadeProdutoGrupo,
    CEOGrupoRodada,
    Cidade,
    ConsolidadoRodadaGrupo,
    DemandaCidadeProduto,
    CompraMateriaPrima,
    ComposicaoProduto,
    Distribuicao,
    IndicadorRodadaGrupo,
    EstoqueProduto,
    EstoqueMateriaPrima,
    Evento,
    EventoRodada,
    ExecucaoJob,
    Grupo,
    Investimento,
    Jogo,
    MarketShareCidadeProduto,
    MateriaPrima,
    Producao,
    Produto,
    ResultadoFinanceiro,
    Rodada,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ("email_usuario", "nome_usuario", "tipo_usuario", "status_usuario")
    list_filter = ("tipo_usuario", "status_usuario")
    fieldsets = (
        (None, {"fields": ("email_usuario", "nome_usuario", "password")}),
        ("Permissoes", {"fields": ("tipo_usuario", "is_superuser", "groups", "user_permissions")}),
        ("Status", {"fields": ("status_usuario",)}),
        ("Datas", {"fields": ("last_login", "data_criacao")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email_usuario",
                    "nome_usuario",
                    "password1",
                    "password2",
                    "tipo_usuario",
                    "status_usuario",
                ),
            },
        ),
    )
    search_fields = ("email_usuario", "nome_usuario")
    ordering = ("email_usuario",)


@admin.register(Rodada)
class RodadaAdmin(admin.ModelAdmin):
    list_display = ("numero", "jogo", "inicio", "fim", "fechada")


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ("nome", "jogo")


@admin.register(ResultadoFinanceiro)
class ResultadoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("grupo", "rodada", "receita", "custos", "lucro", "saldo_caixa")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "probabilidade")


@admin.register(EventoRodada)
class EventoRodadaAdmin(admin.ModelAdmin):
    list_display = ("rodada", "evento", "data")


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "distancia_km", "demanda")


@admin.register(Distribuicao)
class DistribuicaoAdmin(admin.ModelAdmin):
    list_display = (
        "grupo",
        "produto",
        "cidade",
        "rodada",
        "quantidade",
        "quantidade_vendida",
        "quantidade_sobra",
        "preco_unitario",
        "receita_realizada",
        "processada",
    )


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "categoria", "valor", "rodada")


@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "preco_unitario", "ativa")


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "perecivel", "tempo_producao_min", "ativo")


@admin.register(ComposicaoProduto)
class ComposicaoProdutoAdmin(admin.ModelAdmin):
    list_display = ("produto", "materia_prima", "quantidade_por_unidade")


@admin.register(Producao)
class ProducaoAdmin(admin.ModelAdmin):
    list_display = (
        "grupo",
        "produto",
        "rodada",
        "quantidade_planejada",
        "quantidade_produzida",
        "custo_total",
    )


@admin.register(EstoqueMateriaPrima)
class EstoqueMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ("grupo", "materia_prima", "quantidade_kg")


@admin.register(CompraMateriaPrima)
class CompraMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = (
        "grupo",
        "materia_prima",
        "cidade_fornecedora",
        "rodada_pedido",
        "rodada_recebimento",
        "quantidade_kg",
        "desconto_logistico",
        "valor_total",
        "recebida",
    )


@admin.register(EstoqueProduto)
class EstoqueProdutoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "produto", "rodada_entrada", "quantidade")


@admin.register(MarketShareCidadeProduto)
class MarketShareCidadeProdutoAdmin(admin.ModelAdmin):
    list_display = ("rodada", "grupo", "cidade", "produto", "quantidade_vendida", "market_share_percent")


@admin.register(IndicadorRodadaGrupo)
class IndicadorRodadaGrupoAdmin(admin.ModelAdmin):
    list_display = (
        "rodada",
        "grupo",
        "lucro_rodada",
        "market_share_percent",
        "atendimento_demanda_percent",
        "eficiencia_estoque_percent",
        "score_multicriterio",
    )


@admin.register(CapacidadeProdutoGrupo)
class CapacidadeProdutoGrupoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "produto", "maquinas", "operadores", "minutos_por_maquina")


@admin.register(ConsolidadoRodadaGrupo)
class ConsolidadoRodadaGrupoAdmin(admin.ModelAdmin):
    list_display = (
        "rodada",
        "grupo",
        "receita_vendas",
        "custos_totais",
        "lucro_rodada",
        "score_multicriterio",
    )


@admin.register(CEOGrupoRodada)
class CEOGrupoRodadaAdmin(admin.ModelAdmin):
    list_display = ("rodada", "grupo", "usuario", "data_registro")


@admin.register(AuditoriaSubmissaoRodada)
class AuditoriaSubmissaoRodadaAdmin(admin.ModelAdmin):
    list_display = ("rodada", "grupo", "usuario", "ip_origem", "data_registro")


@admin.register(DemandaCidadeProduto)
class DemandaCidadeProdutoAdmin(admin.ModelAdmin):
    list_display = ("cidade", "produto", "demanda_maxima")


@admin.register(AplicacaoFinanceiraGrupo)
class AplicacaoFinanceiraGrupoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "saldo_aplicado", "taxa_juros_rodada", "data_atualizacao")


@admin.register(ExecucaoJob)
class ExecucaoJobAdmin(admin.ModelAdmin):
    list_display = ("comando", "status", "correlation_id", "rodada", "iniciado_em", "finalizado_em")

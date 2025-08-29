from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Rodada,
    ResultadoFinanceiro,
    Grupo,
    Evento,
    EventoRodada,
    Cidade,
    Distribuicao,
    Jogo,
    Investimento,
)
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        "email_usuario",
        "nome_usuario",
        "tipo_usuario",
        "status_usuario",
    )
    list_filter = ("tipo_usuario", "status_usuario")
    fieldsets = (
        (None, {"fields": ("email_usuario", "nome_usuario", "password")}),
        ("Permissões", {"fields": ("tipo_usuario", "is_superuser", "groups", "user_permissions")}),
        ("Status", {"fields": ("status_usuario",)}),
        ("Datas", {"fields": ("last_login", "data_criacao")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email_usuario", "nome_usuario", "password1", "password2", "tipo_usuario", "status_usuario"),
        }),
    )
    search_fields = ("email_usuario", "nome_usuario")
    ordering = ("email_usuario",)


@admin.register(Rodada)
class RodadaAdmin(admin.ModelAdmin):
    list_display = ("numero", "inicio", "fim", "fechada")


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ("nome",)


@admin.register(ResultadoFinanceiro)
class ResultadoFinanceiroAdmin(admin.ModelAdmin):
    list_display = (
        "grupo",
        "rodada",
        "receita",
        "custos",
        "lucro",
        "saldo_caixa",
    )


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
    list_display = ("grupo", "cidade", "quantidade", "preco_unitario")


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "cidade", "categoria", "valor", "rodada")

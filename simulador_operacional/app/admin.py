from django.contrib import
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import (
    User,
    Rodada,
    ResultadoFinanceiro,
    Grupo,
    EventoAleatorio,
    RegistroEvento,
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
    ordering = ("email_usuario",)


@admin.register(Rodada)
class RodadaAdmin(admin.ModelAdmin):
    list_display = ("numero", "data_inicio", "data_fim", "encerrada")


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
        "despesas",
        "lucro_liquido",
        "fluxo_caixa_liquido",
    )


@admin.register(EventoAleatorio)
class EventoAleatorioAdmin(admin.ModelAdmin):
    list_display = ("nome", "probabilidade")


@admin.register(RegistroEvento)
class RegistroEventoAdmin(admin.ModelAdmin):
    list_display = ("evento", "rodada", "data_aplicacao")
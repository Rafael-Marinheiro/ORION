from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import (
    User,
    TransportRoute,
    PriceList,
    Sale,
    FinancialResult,
    Ranking,
    RandomEvent,
    EventHistory,
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


@admin.register(TransportRoute)
class TransportRouteAdmin(admin.ModelAdmin):
    list_display = ("origem", "destino", "distancia_km", "custo_total", "prazo_estimado")


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ("produto", "praca", "preco", "promocao")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("data", "produto", "quantidade", "valor_unitario", "praca", "total")


@admin.register(FinancialResult)
class FinancialResultAdmin(admin.ModelAdmin):
    list_display = ("rodada", "receita", "despesas", "lucro")


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ("grupo", "resultado", "pontuacao")


@admin.register(RandomEvent)
class RandomEventAdmin(admin.ModelAdmin):
    list_display = ("descricao", "probabilidade")


@admin.register(EventHistory)
class EventHistoryAdmin(admin.ModelAdmin):
    list_display = ("evento", "rodada", "data_ocorrencia")
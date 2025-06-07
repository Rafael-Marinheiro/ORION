from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    GameConfig,
    Group,
    Decision,
    ProductionSetting,
    InventoryItem,
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
@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "capital_inicial", "estoque_inicial")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("nome",)


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = (
        "grupo",
        "rodada",
        "descricao",
        "producao",
        "venda",
        "data_criacao",
    )


@admin.register(ProductionSetting)
class ProductionSettingAdmin(admin.ModelAdmin):
    list_display = ("grupo", "maquinas", "capacidade_maquina")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("grupo", "produto", "quantidade")

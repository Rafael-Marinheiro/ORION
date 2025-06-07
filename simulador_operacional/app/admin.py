from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Produto,
    MovimentoEstoque,
    Maquina,
    Producao,
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


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "estoque_atual",
        "estoque_minimo",
        "estoque_maximo",
        "alerta_estoque",
    )


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "quantidade", "tipo", "data")


@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "capacidade_por_hora")


@admin.register(Producao)
class ProducaoAdmin(admin.ModelAdmin):
    list_display = ("produto", "maquina", "quantidade", "data")


from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import (
    User,
    GameConfig,
    Decisao,
    Distribuicao,
    Cidade,
    Rodada,
    Grupo,
)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email_usuario", "nome_usuario", "tipo_usuario")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email_usuario", "nome_usuario", "tipo_usuario", "status_usuario")


class GameConfigForm(forms.ModelForm):
    class Meta:
        model = GameConfig
        fields = [
            "capital_inicial",
            "estoque_inicial",
            "maquinas_iniciais",
            "capacidade_maquina",
            "produtos_habilitados",
            "modulo_producao",
            "modulo_distribuicao",
            "modulo_financeiro",
            "regra_eventos",
        ]


class DecisaoForm(forms.ModelForm):
    class Meta:
        model = Decisao
        fields = [
            "rodada",
            "descricao",
            "quantidade",
        ]


class DistribuicaoForm(forms.ModelForm):
    cidade = forms.ModelChoiceField(queryset=Cidade.objects.all())

    class Meta:
        model = Distribuicao
        fields = ["cidade", "rodada", "quantidade", "preco_unitario"]


class RodadaForm(forms.ModelForm):
    class Meta:
        model = Rodada
        fields = ["numero", "fim"]


class GrupoForm(forms.ModelForm):
    membros = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Grupo
        fields = [
            "nome",
            "membros",
            "capital",
            "estoque",
            "maquinas",
            "capacidade_maquina",
        ]

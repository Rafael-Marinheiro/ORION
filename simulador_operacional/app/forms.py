from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, GameConfig, Decision, ProductionSetting


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
            "produtos_habilitados",
            "modulo_producao",
            "modulo_distribuicao",
            "modulo_financeiro",
            "modulo_eventos",
            "regras_eventos",
        ]


class DecisionForm(forms.ModelForm):
    class Meta:
        model = Decision
        fields = ["rodada", "descricao", "producao", "venda"]


class ProductionSettingForm(forms.ModelForm):
    class Meta:
        model = ProductionSetting
        fields = ["maquinas", "capacidade_maquina"]

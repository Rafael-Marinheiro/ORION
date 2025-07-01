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
    Jogo,
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
            "maquinas_iniciais_a",
            "maquinas_iniciais_b",
            "maquinas_iniciais_c",
            "trabalhadores_iniciais",
            "capacidade_maquina",
            "numero_rodadas",
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
    jogo = forms.ModelChoiceField(queryset=Jogo.objects.all(), required=False)
    class Meta:
        model = Rodada
        fields = ["jogo", "numero", "fim"]

    def clean_numero(self):
        numero = self.cleaned_data["numero"]
        config = GameConfig.objects.first()
        max_rodadas = config.numero_rodadas if config else 12
        if numero < 1 or numero > max_rodadas:
            raise forms.ValidationError(
                f"Número da rodada deve ser entre 1 e {max_rodadas}"
            )
        return numero


class GrupoForm(forms.ModelForm):
    membros = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    jogo = forms.ModelChoiceField(queryset=Jogo.objects.all(), required=False)

    class Meta:
        model = Grupo
        fields = [
            "nome",
            "membros",
            "jogo",
            "capital",
            "estoque",
            "maquinas",
            "maquinas_a",
            "maquinas_b",
            "maquinas_c",
            "trabalhadores",
            "capacidade_maquina",
        ]

    def clean_membros(self):
        membros = self.cleaned_data.get("membros")
        total = membros.count() if membros is not None else 0
        if total < 3 or total > 6:
            raise forms.ValidationError(
                "O grupo deve possuir entre 3 e 6 participantes."
            )
        return membros


class ResultadoFilterForm(forms.Form):
    rodada = forms.IntegerField(required=False, label="Rodada")
    grupo = forms.ModelChoiceField(queryset=Grupo.objects.all(), required=False)

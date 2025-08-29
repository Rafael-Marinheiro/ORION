from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import formset_factory
from decimal import Decimal
from .models import (
    User,
    GameConfig,
    Decisao,
    Distribuicao,
    Cidade,
    Rodada,
    Grupo,
    Jogo,
    Fornecedor,
    PedidoMateriaPrima,
    LinhaProducao,
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
    PRODUTO_CHOICES = [
        ("A", "Produto A"),
        ("B", "Produto B"),
        ("C", "Produto C"),
    ]

    produtos_habilitados = forms.MultipleChoiceField(
        choices=PRODUTO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Produtos habilitados",
    )

    regra_eventos = forms.JSONField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Parâmetros de eventos",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.produtos_habilitados:
            self.initial["produtos_habilitados"] = (
                self.instance.produtos_habilitados.split(",")
            )

    def clean_produtos_habilitados(self):
        produtos = self.cleaned_data.get("produtos_habilitados", [])
        return ",".join(produtos)

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
            "materia_prima",
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


class MembroForm(forms.Form):
    nome = forms.CharField(max_length=150)
    email = forms.EmailField()
    senha = forms.CharField(widget=forms.PasswordInput)
    lider = forms.BooleanField(required=False, label="Líder do grupo")


MembroFormSet = formset_factory(
    MembroForm, min_num=3, max_num=6, validate_min=True, validate_max=True, extra=0
)


class GrupoCadastroForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ["nome", "jogo"]


class ResultadoFilterForm(forms.Form):
    rodada = forms.IntegerField(required=False, label="Rodada")
    grupo = forms.ModelChoiceField(queryset=Grupo.objects.all(), required=False)


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ["nome", "cidade", "prazo_entrega", "custo_logistico_km"]


class PedidoMateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = PedidoMateriaPrima
        fields = ["fornecedor", "quantidade", "custo_unitario"]


class InvestimentoCapacidadeForm(forms.Form):
    linha = forms.ModelChoiceField(queryset=LinhaProducao.objects.all())
    aumento_capacidade = forms.IntegerField(min_value=1)
    valor = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

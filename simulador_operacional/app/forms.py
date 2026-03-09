from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import formset_factory
from decimal import Decimal

from .models import (
    Cidade,
    CompraMateriaPrima,
    Decisao,
    Distribuicao,
    GameConfig,
    Grupo,
    Investimento,
    Jogo,
    MateriaPrima,
    Producao,
    Produto,
    Rodada,
    User,
    default_ranking_pesos,
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
    peso_lucro = forms.DecimalField(
        label="Peso - Lucro",
        min_value=0,
        max_value=1,
        decimal_places=4,
        max_digits=6,
    )
    peso_market_share = forms.DecimalField(
        label="Peso - Market Share",
        min_value=0,
        max_value=1,
        decimal_places=4,
        max_digits=6,
    )
    peso_atendimento = forms.DecimalField(
        label="Peso - Atendimento",
        min_value=0,
        max_value=1,
        decimal_places=4,
        max_digits=6,
    )
    peso_eficiencia_estoque = forms.DecimalField(
        label="Peso - Eficiencia de Estoque",
        min_value=0,
        max_value=1,
        decimal_places=4,
        max_digits=6,
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pesos = self.instance.ranking_pesos if self.instance and self.instance.ranking_pesos else default_ranking_pesos()
        self.fields["peso_lucro"].initial = pesos.get("lucro", 0.4)
        self.fields["peso_market_share"].initial = pesos.get("market_share", 0.3)
        self.fields["peso_atendimento"].initial = pesos.get("atendimento", 0.2)
        self.fields["peso_eficiencia_estoque"].initial = pesos.get("eficiencia_estoque", 0.1)

    def clean(self):
        cleaned_data = super().clean()
        soma = (
            Decimal(cleaned_data.get("peso_lucro") or 0)
            + Decimal(cleaned_data.get("peso_market_share") or 0)
            + Decimal(cleaned_data.get("peso_atendimento") or 0)
            + Decimal(cleaned_data.get("peso_eficiencia_estoque") or 0)
        )
        if abs(soma - Decimal("1")) > Decimal("0.0001"):
            raise forms.ValidationError("A soma dos pesos deve ser igual a 1.0.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.ranking_pesos = {
            "lucro": float(self.cleaned_data["peso_lucro"]),
            "market_share": float(self.cleaned_data["peso_market_share"]),
            "atendimento": float(self.cleaned_data["peso_atendimento"]),
            "eficiencia_estoque": float(self.cleaned_data["peso_eficiencia_estoque"]),
        }
        if commit:
            instance.save()
        return instance



class DecisaoForm(forms.ModelForm):
    class Meta:
        model = Decisao
        fields = ["descricao", "quantidade"]


class DistribuicaoForm(forms.ModelForm):
    produto = forms.ModelChoiceField(queryset=Produto.objects.filter(ativo=True))
    cidade = forms.ModelChoiceField(queryset=Cidade.objects.all())

    class Meta:
        model = Distribuicao
        fields = ["produto", "cidade", "quantidade", "preco_unitario"]


class ProducaoForm(forms.ModelForm):
    produto = forms.ModelChoiceField(queryset=Produto.objects.filter(ativo=True))

    class Meta:
        model = Producao
        fields = ["produto", "quantidade_planejada"]


class CompraMateriaPrimaForm(forms.ModelForm):
    materia_prima = forms.ModelChoiceField(queryset=MateriaPrima.objects.filter(ativa=True))
    cidade_fornecedora = forms.ModelChoiceField(queryset=Cidade.objects.all())

    class Meta:
        model = CompraMateriaPrima
        fields = ["materia_prima", "cidade_fornecedora", "quantidade_kg"]


class InvestimentoForm(forms.ModelForm):
    cidade = forms.ModelChoiceField(queryset=Cidade.objects.all(), required=False)
    produto = forms.ModelChoiceField(queryset=Produto.objects.filter(ativo=True), required=False)

    class Meta:
        model = Investimento
        fields = ["categoria", "cidade", "produto", "quantidade", "valor", "operacao_financeira"]

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get("categoria")
        cidade = cleaned_data.get("cidade")
        produto = cleaned_data.get("produto")
        operacao = cleaned_data.get("operacao_financeira")

        if categoria == "marketing" and not cidade:
            self.add_error("cidade", "Selecione a cidade para investimento de marketing.")
        if categoria in {"maquinas", "rh"} and not produto:
            self.add_error("produto", "Selecione o produto/linha para investimento operacional.")
        if categoria != "financeiro":
            cleaned_data["operacao_financeira"] = "aplicar"
        elif operacao not in {"aplicar", "resgatar"}:
            self.add_error("operacao_financeira", "Operacao financeira invalida.")
        return cleaned_data


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


class ConfigWizardStep1Form(forms.Form):
    capital_inicial = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12)
    estoque_inicial = forms.IntegerField(min_value=0)
    maquinas_iniciais = forms.IntegerField(min_value=0)
    capacidade_maquina = forms.IntegerField(min_value=1)


class ConfigWizardStep2Form(forms.Form):
    produtos_habilitados = forms.CharField(required=False)
    modulo_producao = forms.BooleanField(required=False, initial=True)
    modulo_distribuicao = forms.BooleanField(required=False, initial=True)
    modulo_financeiro = forms.BooleanField(required=False, initial=True)
    regra_eventos = forms.JSONField(required=False)


class FeedbackForm(forms.Form):
    suggestion = forms.CharField(
        label="Sugestao",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=1000,
    )
    email = forms.EmailField(required=False, label="Email (opcional)")

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import BaseFormSet, formset_factory
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
    peso_eo = forms.DecimalField(
        label="Peso - Eficiência Operacional (EO)",
        min_value=0, max_value=1, decimal_places=4, max_digits=6,
    )
    peso_df = forms.DecimalField(
        label="Peso - Desempenho Financeiro (DF)",
        min_value=0, max_value=1, decimal_places=4, max_digits=6,
    )
    peso_ee = forms.DecimalField(
        label="Peso - Eficiência de Estoques (EE)",
        min_value=0, max_value=1, decimal_places=4, max_digits=6,
    )
    peso_sd = forms.DecimalField(
        label="Peso - Satisfação da Demanda (SD)",
        min_value=0, max_value=1, decimal_places=4, max_digits=6,
    )
    peso_ds = forms.DecimalField(
        label="Peso - Sustentabilidade (DS)",
        min_value=0, max_value=1, decimal_places=4, max_digits=6,
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
        for sigla, padrao in default_ranking_pesos().items():
            self.fields[f"peso_{sigla.lower()}"].initial = pesos.get(sigla, padrao)

    def clean(self):
        cleaned_data = super().clean()
        campos = [f"peso_{sigla.lower()}" for sigla in default_ranking_pesos()]
        if all(campo in cleaned_data for campo in campos):
            soma = sum(cleaned_data[campo] for campo in campos)
            if abs(soma - Decimal("1")) > Decimal("0.0001"):
                raise forms.ValidationError("A soma dos pesos deve ser igual a 1.0.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.ranking_pesos = {
            sigla: float(self.cleaned_data[f"peso_{sigla.lower()}"])
            for sigla in default_ranking_pesos()
        }
        if commit:
            instance.save()
        return instance


class RotuloSemDoisPontos:
    """O Django acrescenta ":" a todo rotulo; em portugues so faz ruido."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class DecisaoForm(RotuloSemDoisPontos, forms.ModelForm):
    class Meta:
        model = Decisao
        fields = ["descricao", "quantidade"]


class DistribuicaoForm(RotuloSemDoisPontos, forms.ModelForm):
    # Rotulo vai na declaracao: `Meta.labels` so alcanca campo gerado do modelo.
    produto = forms.ModelChoiceField(queryset=Produto.objects.filter(ativo=True), label="Produto")
    cidade = forms.ModelChoiceField(
        # So praca em jogo. Praca aposentada pelo 9.1 fica com demanda zero
        # e o `seed_dados_base` mantem isso; oferece-la seria um destino que
        # cobra frete e nao vende nada.
        queryset=Cidade.objects.filter(demanda__gt=0),
        label="Praça de destino",
        help_text="A distância define o frete e o foco regional.",
    )

    class Meta:
        model = Distribuicao
        fields = ["produto", "cidade", "quantidade", "preco_unitario"]
        labels = {
            "produto": "Produto",
            "cidade": "Praça de destino",
            "quantidade": "Quantidade a enviar",
            "preco_unitario": "Preço de venda (R$)",
        }
        help_texts = {
            "preco_unitario": "Preço abaixo da média da praça aumenta a fatia da demanda.",
        }


class ProducaoForm(RotuloSemDoisPontos, forms.ModelForm):
    produto = forms.ModelChoiceField(queryset=Produto.objects.filter(ativo=True), label="Produto")

    class Meta:
        model = Producao
        fields = ["produto", "quantidade_planejada"]
        labels = {"produto": "Produto", "quantidade_planejada": "Quantidade a produzir"}
        help_texts = {
            "quantidade_planejada": "Limitada pela capacidade da linha e pela matéria-prima em estoque.",
        }


class CompraMateriaPrimaForm(RotuloSemDoisPontos, forms.ModelForm):
    materia_prima = forms.ModelChoiceField(
        queryset=MateriaPrima.objects.filter(ativa=True), label="Matéria-prima"
    )
    cidade_fornecedora = forms.ModelChoiceField(
        # Mesma regra do destino: praca fora da base do 9.1 nao e fornecedora
        # valida no 7.1, e listar uma so produz submissao recusada.
        queryset=Cidade.objects.filter(demanda__gt=0),
        label="Comprar de",
        help_text="A distância até a sede define o frete.",
    )

    class Meta:
        model = CompraMateriaPrima
        fields = ["materia_prima", "cidade_fornecedora", "quantidade_kg"]
        labels = {
            "materia_prima": "Matéria-prima",
            "cidade_fornecedora": "Comprar de",
            "quantidade_kg": "Quantidade (kg)",
        }
        help_texts = {
            "cidade_fornecedora": "A distância até a sede define o frete.",
        }


class InvestimentoForm(RotuloSemDoisPontos, forms.ModelForm):
    cidade = forms.ModelChoiceField(queryset=Cidade.objects.all(), required=False)
    produto = forms.ModelChoiceField(queryset=Produto.objects.filter(ativo=True), required=False)
    quantidade = forms.IntegerField(min_value=0, required=False)
    operacao_financeira = forms.ChoiceField(
        choices=Investimento.OPERACAO_FINANCEIRA_CHOICES,
        required=False,
    )

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
        else:
            cleaned_data["quantidade"] = 0
        return cleaned_data


class RodadaForm(forms.ModelForm):
    jogo = forms.ModelChoiceField(queryset=Jogo.objects.all(), required=False)

    class Meta:
        model = Rodada
        fields = ["jogo", "numero", "fim"]

    def clean(self):
        dados = super().clean()
        numero = dados.get("numero")
        jogo = dados.get("jogo")
        config = jogo.config if jogo else GameConfig.objects.filter(pk=1).first()
        max_rodadas = config.numero_rodadas if config else 12
        if numero is not None and not 1 <= numero <= max_rodadas:
            self.add_error(
                "numero", f"Número da rodada deve ser entre 1 e {max_rodadas}"
            )
        return dados


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

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email_usuario__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já possui cadastro.")
        return email

    def clean_senha(self):
        senha = self.cleaned_data["senha"]
        validate_password(senha)
        return senha


class BaseMembroFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        emails = [form.cleaned_data["email"].casefold() for form in self.forms]
        if len(emails) != len(set(emails)):
            raise forms.ValidationError("Cada integrante deve ter um e-mail diferente.")
        if sum(bool(form.cleaned_data.get("lider")) for form in self.forms) != 1:
            raise forms.ValidationError("Selecione exatamente um líder para o grupo.")


MembroFormSet = formset_factory(
    MembroForm, formset=BaseMembroFormSet,
    min_num=3, max_num=6, validate_min=True, validate_max=True, extra=0,
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

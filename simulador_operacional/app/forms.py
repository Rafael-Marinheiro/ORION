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
    Evento,
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
    jogo = forms.ModelChoiceField(
        queryset=Jogo.objects.all(), required=False, label="Turma",
        empty_label="Grupos sem turma",
    )

    class Meta:
        model = Rodada
        fields = ["jogo", "numero", "fim"]
        labels = {"numero": "Rodada", "fim": "Prazo-limite"}
        help_texts = {
            # 11.1: "o professor define obrigatoriamente o prazo-limite de
            # encerramento (data e hora exatas)". O fechamento acontece
            # sozinho nesse instante.
            "fim": "Data e hora em que a rodada fecha sozinha (§11.1).",
        }
        widgets = {
            # Era um campo de texto: a professora digitava o formato do
            # Django de cabeca. `datetime-local` abre o calendario do
            # proprio sistema.
            "fim": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    # --- Evento da rodada -------------------------------------------------
    # O 8.2 sorteia um evento por rodada. A partir de 25/09/2026 o professor
    # tambem pode determinar o evento -- escolhendo um do catalogo do 8.4 ou
    # descrevendo um novo em termos do que ele faz com uma metrica.
    TIPOS_MANUAIS = [
        ("demanda", "Demanda das praças"),
        ("custo_producao", "Custo de produção"),
        ("custo_transporte", "Custo de transporte"),
    ]
    SENTIDOS = [("beneficio", "Ajuda as equipes"), ("prejuizo", "Prejudica as equipes")]
    MEDIDAS = [("percentual", "Percentual (%)"), ("absoluto", "Valor absoluto")]

    adicionar_evento = forms.BooleanField(
        required=False, label="Determinar o evento desta rodada",
        help_text="Sem marcar, o evento sai do sorteio do §8.2.",
    )
    origem_evento = forms.ChoiceField(
        required=False, initial="catalogo", widget=forms.RadioSelect,
        choices=[("catalogo", "Usar um evento já cadastrado"), ("novo", "Criar um evento")],
        label="De onde vem o evento",
    )
    evento_existente = forms.ModelChoiceField(
        required=False, queryset=Evento.objects.none(), label="Evento cadastrado",
    )
    evento_nome = forms.CharField(required=False, max_length=100, label="Nome do evento")
    evento_frase = forms.CharField(
        required=False, max_length=200, label="Manchete para a turma",
        help_text="É o que o aluno lê na abertura da rodada (§8.4).",
    )
    evento_tipo = forms.ChoiceField(
        required=False, choices=TIPOS_MANUAIS, label="O que o evento afeta",
    )
    evento_sentido = forms.ChoiceField(
        required=False, choices=SENTIDOS, initial="prejuizo", label="Efeito",
    )
    evento_medida = forms.ChoiceField(
        required=False, choices=MEDIDAS, initial="percentual", label="Medida",
    )
    evento_valor = forms.DecimalField(
        required=False, min_value=0, max_digits=12, decimal_places=2, label="Intensidade",
    )
    evento_cidades = forms.ModelMultipleChoiceField(
        required=False, queryset=Cidade.objects.none(),
        widget=forms.CheckboxSelectMultiple, label="Praças atingidas",
        help_text="Nenhuma marcada: o efeito vale para todas.",
    )
    evento_com_sorteio = forms.BooleanField(
        required=False, label="Deixar também um evento sorteado acontecer",
        help_text="A RN-10 admite até dois eventos simultâneos na mesma rodada.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fim"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
        self.fields["evento_existente"].queryset = Evento.objects.filter(
            manual=False
        ).order_by("nome")
        self.fields["evento_cidades"].queryset = Cidade.objects.filter(
            demanda__gt=0
        ).order_by("nome")

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

        if not dados.get("adicionar_evento"):
            return dados

        origem = dados.get("origem_evento") or "catalogo"
        if origem == "catalogo":
            if not dados.get("evento_existente"):
                self.add_error("evento_existente", "Escolha o evento da rodada.")
            return dados

        if not dados.get("evento_nome"):
            self.add_error("evento_nome", "Dê um nome ao evento.")
        if not dados.get("evento_tipo"):
            self.add_error("evento_tipo", "Escolha o que o evento afeta.")
        valor = dados.get("evento_valor")
        if valor is None:
            self.add_error("evento_valor", "Informe a intensidade do efeito.")
        elif dados.get("evento_medida") == "percentual" and valor > 100:
            # Reduzir mais de 100% de um custo inverteria o sinal dele.
            self.add_error("evento_valor", "O percentual vai de 0 a 100.")
        return dados

    def efeito_do_evento(self):
        """Traduz "ajuda/prejudica" no sinal que o motor aplica.

        Demanda: ajudar e aumentar. Custo: ajudar e reduzir. O professor
        escolhe o efeito em palavras; o sinal e problema do sistema.
        """
        valor = self.cleaned_data.get("evento_valor") or 0
        ajuda = self.cleaned_data.get("evento_sentido") == "beneficio"
        if self.cleaned_data.get("evento_tipo") == "demanda":
            return valor if ajuda else -valor
        return -valor if ajuda else valor


class GrupoForm(forms.ModelForm):
    membros = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    jogo = forms.ModelChoiceField(queryset=Jogo.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Oferecia `User.objects.all()`: o professor via os alunos de todas as
        # turmas e a si mesmo numa lista unica. Marcar ali o lider de outra
        # equipe trocava o CEO deste grupo, porque o CEO sai de
        # `membros.filter(tipo_usuario="lider_grupo")`.
        alunos = User.objects.exclude(tipo_usuario="gamemaster").exclude(
            is_superuser=True
        )
        disponiveis = alunos.filter(grupos__isnull=True)
        if self.instance.pk:
            disponiveis = disponiveis | self.instance.membros.all()
        self.fields["membros"].queryset = disponiveis.distinct().order_by(
            "nome_usuario"
        )

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
    @property
    def preenchidos(self):
        """Os tres campos extras em branco nao sao integrantes."""
        return [form for form in self.forms if form.cleaned_data.get("email")]

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        formularios = self.preenchidos
        emails = [form.cleaned_data["email"].casefold() for form in formularios]
        if len(emails) != len(set(emails)):
            raise forms.ValidationError("Cada integrante deve ter um e-mail diferente.")
        if sum(bool(form.cleaned_data.get("lider")) for form in formularios) != 1:
            raise forms.ValidationError("Selecione exatamente um líder para o grupo.")


# 5: "cada grupo deve possuir no minimo 3 e no maximo 6 participantes". A tela
# abria com `extra=0`, ou seja, tres campos fixos e nenhum botao de adicionar:
# uma equipe de quatro a seis alunos nao tinha como ser cadastrada. Os tres
# ultimos campos sao opcionais e podem ficar em branco.
MembroFormSet = formset_factory(
    MembroForm, formset=BaseMembroFormSet,
    min_num=3, max_num=6, validate_min=True, validate_max=True, extra=3,
)


class GrupoCadastroForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ["nome", "jogo"]


class ResultadoFilterForm(forms.Form):
    """Filtro dos relatorios. So oferece rodada que existe.

    Era um `IntegerField` livre: dava para pedir a rodada -5 ou a 99 e
    receber a tela vazia, sem nada dizendo que aquela rodada nao existe. A
    lista sai das rodadas fechadas do jogo do proprio usuario, entao o campo
    tambem informa o que ha para ver.
    """

    rodada = forms.TypedChoiceField(
        required=False, label="Rodada", coerce=int, empty_value=None,
        choices=[("", "Todas as rodadas")],
    )
    grupo = forms.ModelChoiceField(queryset=Grupo.objects.all(), required=False)

    def __init__(self, *args, rodadas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rodada"].choices = [("", "Todas as rodadas")] + [
            (numero, f"Rodada {numero}") for numero in sorted(rodadas)
        ]


class ConfigWizardStep1Form(forms.Form):
    # Cada jogo tem a sua configuracao. Sem escolher a turma, o assistente
    # gravava sempre na `GameConfig` de id 1 -- que podia nao ser a de
    # nenhuma turma em andamento.
    jogo = forms.ChoiceField(required=False, label="Turma", choices=[])
    capital_inicial = forms.DecimalField(
        min_value=0, decimal_places=2, max_digits=12, label="Capital inicial",
    )
    estoque_inicial = forms.IntegerField(min_value=0, label="Estoque inicial")
    maquinas_iniciais = forms.IntegerField(min_value=0, label="Máquinas de largada")
    # 5: o numero de rodadas decide quando a classificacao final libera. O
    # assistente nao perguntava, e a turma nascia com o padrao.
    numero_rodadas = forms.IntegerField(
        min_value=3, max_value=12, label="Número de rodadas",
        help_text="Entre 3 e 12 (§5).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["jogo"].choices = [("", "Grupos sem turma")] + [
            (str(jogo.id), jogo.nome) for jogo in Jogo.objects.order_by("nome")
        ]


class ConfigWizardStep2Form(forms.Form):
    produtos_habilitados = forms.CharField(required=False, label="Produtos habilitados")
    modulo_producao = forms.BooleanField(required=False, initial=True, label="Módulo de produção")
    modulo_distribuicao = forms.BooleanField(required=False, initial=True, label="Módulo de distribuição")
    modulo_financeiro = forms.BooleanField(required=False, initial=True, label="Módulo financeiro")


class FeedbackForm(forms.Form):
    suggestion = forms.CharField(
        label="Sugestao",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=1000,
    )
    email = forms.EmailField(required=False, label="Email (opcional)")

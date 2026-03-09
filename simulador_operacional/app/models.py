from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def default_ranking_pesos():
    return {
        "lucro": 0.4,
        "market_share": 0.3,
        "atendimento": 0.2,
        "eficiencia_estoque": 0.1,
    }


class UserManager(BaseUserManager):
    def create_user(self, email_usuario, nome_usuario, password=None, **extra_fields):
        if not email_usuario:
            raise ValueError("O e-mail e obrigatorio")
        if not password:
            raise ValueError("Usuario deve ter uma senha")
        email_usuario = self.normalize_email(email_usuario)
        extra_fields.setdefault("tipo_usuario", "membro_grupo")
        user = self.model(
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_usuario, nome_usuario, password=None, **extra_fields):
        extra_fields.setdefault("tipo_usuario", "gamemaster")
        extra_fields.setdefault("status_usuario", True)
        extra_fields.setdefault("is_superuser", True)

        if not password:
            raise ValueError("Superusuario deve ter uma senha")

        return self.create_user(
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            password=password,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO_CHOICES = [
        ("gamemaster", "Administrador"),
        ("lider_grupo", "CEO do Grupo"),
        ("membro_grupo", "Membro do Grupo"),
    ]

    id_usuario = models.AutoField(primary_key=True)
    nome_usuario = models.CharField(max_length=150)
    email_usuario = models.EmailField(max_length=100, unique=True)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default="membro_grupo",
    )
    status_usuario = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email_usuario"
    REQUIRED_FIELDS = ["nome_usuario"]

    class Meta:
        db_table = "USUARIOS"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.nome_usuario

    @property
    def is_staff(self):
        return self.tipo_usuario == "gamemaster" or self.is_superuser

    @property
    def is_active(self):
        return self.status_usuario


class GameConfig(models.Model):
    capital_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1000000,
    )
    estoque_inicial = models.PositiveIntegerField(default=0)
    produtos_habilitados = models.TextField(blank=True)

    modulo_producao = models.BooleanField(default=True)
    modulo_distribuicao = models.BooleanField(default=True)
    modulo_financeiro = models.BooleanField(default=True)

    regra_eventos = models.JSONField(default=dict, blank=True)
    ranking_pesos = models.JSONField(default=default_ranking_pesos, blank=True)

    maquinas_iniciais = models.PositiveIntegerField(default=40)
    maquinas_iniciais_a = models.PositiveIntegerField(default=15)
    maquinas_iniciais_b = models.PositiveIntegerField(default=15)
    maquinas_iniciais_c = models.PositiveIntegerField(default=10)
    trabalhadores_iniciais = models.PositiveIntegerField(default=80)
    capacidade_maquina = models.PositiveIntegerField(default=100)
    numero_rodadas = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(3), MaxValueValidator(12)],
    )

    class Meta:
        db_table = "CONFIG"
        verbose_name = "Configuracao do Jogo"
        verbose_name_plural = "Configuracoes do Jogo"

    def __str__(self):
        return "Configuracao"


class Jogo(models.Model):
    nome = models.CharField(max_length=100)
    config = models.ForeignKey(GameConfig, on_delete=models.CASCADE, related_name="jogos")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "JOGOS"
        verbose_name = "Jogo"
        verbose_name_plural = "Jogos"

    def __str__(self):
        return self.nome


class Grupo(models.Model):
    nome = models.CharField(max_length=100)
    membros = models.ManyToManyField(User, related_name="grupos")
    lider = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="grupos_liderados",
        null=True,
        blank=True,
    )
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE, related_name="grupos", null=True, blank=True)
    capital = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estoque = models.PositiveIntegerField(default=0)
    materia_prima = models.PositiveIntegerField(default=0)
    maquinas = models.PositiveIntegerField(default=1)
    maquinas_a = models.PositiveIntegerField(default=15)
    maquinas_b = models.PositiveIntegerField(default=15)
    maquinas_c = models.PositiveIntegerField(default=10)
    trabalhadores = models.PositiveIntegerField(default=80)
    capacidade_maquina = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = "GRUPOS"
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"

    def __str__(self):
        return self.nome


class LinhaProducao(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="linhas_producao")
    capacidade = models.PositiveIntegerField(default=0)
    maquinas = models.PositiveIntegerField(default=0)
    mao_de_obra = models.PositiveIntegerField(default=0)
    producao = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "LINHAS_PRODUCAO"
        verbose_name = "Linha de Produção"
        verbose_name_plural = "Linhas de Produção"

    def __str__(self):
        return f"Linha {self.id} - {self.grupo.nome}"


class Decisao(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="decisoes")
    rodada = models.PositiveIntegerField()
    descricao = models.TextField()
    quantidade = models.IntegerField(default=0)
    resultado = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "DECISOES"
        ordering = ["-data_criacao"]
        verbose_name = "Decisao"
        verbose_name_plural = "Decisoes"
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "rodada"],
                name="uniq_decisao_grupo_rodada",
            ),
        ]

    def __str__(self):
        return f"Decisao {self.rodada} - {self.grupo.nome}"


class Mercado(models.Model):
    nome = models.CharField(max_length=100)

    class Meta:
        db_table = "MERCADOS"
        verbose_name = "Mercado"
        verbose_name_plural = "Mercados"

    def __str__(self):
        return self.nome


class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    distancia_km = models.PositiveIntegerField()
    demanda = models.PositiveIntegerField(default=0)
    limite_demanda = models.PositiveIntegerField(default=0)
    mercado = models.ForeignKey(
        Mercado,
        on_delete=models.CASCADE,
        related_name="cidades",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "CIDADES"
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"

    def __str__(self):
        return self.nome


class MateriaPrima(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    ativa = models.BooleanField(default=True)

    class Meta:
        db_table = "MATERIAS_PRIMAS"
        verbose_name = "Materia-Prima"
        verbose_name_plural = "Materias-Primas"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class EstoqueMateriaPrima(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="estoques_materia_prima")
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE, related_name="estoques")
    quantidade_kg = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "ESTOQUES_MATERIA_PRIMA"
        verbose_name = "Estoque de Materia-Prima"
        verbose_name_plural = "Estoques de Materias-Primas"
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "materia_prima"],
                name="uniq_estoque_materia_prima_grupo",
            ),
        ]

    def __str__(self):
        return f"{self.grupo.nome} - {self.materia_prima.codigo}: {self.quantidade_kg} kg"


class CompraMateriaPrima(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="compras_materia_prima")
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE, related_name="compras")
    cidade_fornecedora = models.ForeignKey(Cidade, on_delete=models.PROTECT, related_name="compras_materia_prima")
    rodada_pedido = models.PositiveIntegerField()
    rodada_recebimento = models.PositiveIntegerField()
    quantidade_kg = models.DecimalField(max_digits=14, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    custo_logistico = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    desconto_logistico = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    recebida = models.BooleanField(default=False)
    data_compra = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "COMPRAS_MATERIA_PRIMA"
        verbose_name = "Compra de Materia-Prima"
        verbose_name_plural = "Compras de Materia-Prima"
        ordering = ["-data_compra"]

    def __str__(self):
        return (
            f"{self.grupo.nome} - {self.materia_prima.codigo} - "
            f"R{self.valor_total} (R{self.rodada_pedido} -> R{self.rodada_recebimento})"
        )


class Produto(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    perecivel = models.BooleanField(default=False)
    validade_rodadas = models.PositiveIntegerField(default=0)
    tempo_producao_min = models.PositiveIntegerField(default=1)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "PRODUTOS"
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    @property
    def custo_unitario_estimado(self):
        total = Decimal("0")
        for item in self.composicoes.select_related("materia_prima").all():
            total += item.quantidade_por_unidade * item.materia_prima.preco_unitario
        return total


class ComposicaoProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="composicoes")
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE, related_name="composicoes")
    quantidade_por_unidade = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "PRODUTO_COMPOSICAO"
        verbose_name = "Composicao de Produto"
        verbose_name_plural = "Composicoes de Produto"
        constraints = [
            models.UniqueConstraint(
                fields=["produto", "materia_prima"],
                name="uniq_composicao_produto_materia_prima",
            ),
        ]

    def __str__(self):
        return f"{self.produto.codigo} - {self.materia_prima.codigo}"


class Producao(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="producoes")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="producoes")
    rodada = models.PositiveIntegerField()
    quantidade_planejada = models.PositiveIntegerField()
    quantidade_produzida = models.PositiveIntegerField(default=0)
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PRODUCOES"
        verbose_name = "Producao"
        verbose_name_plural = "Producoes"
        ordering = ["-data_criacao"]
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "produto", "rodada"],
                name="uniq_producao_grupo_produto_rodada",
            ),
        ]

    def __str__(self):
        return f"{self.grupo.nome} - {self.produto.codigo} - Rodada {self.rodada}"


class CapacidadeProdutoGrupo(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="capacidades_produto")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="capacidades_grupo")
    maquinas = models.PositiveIntegerField(default=0)
    operadores = models.PositiveIntegerField(default=0)
    minutos_por_maquina = models.PositiveIntegerField(default=400)

    class Meta:
        db_table = "CAPACIDADE_PRODUTO_GRUPO"
        verbose_name = "Capacidade por Produto do Grupo"
        verbose_name_plural = "Capacidades por Produto do Grupo"
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "produto"],
                name="uniq_capacidade_grupo_produto",
            ),
        ]

    def __str__(self):
        return f"{self.grupo.nome} - {self.produto.codigo}: {self.maquinas} maquinas"

    @property
    def capacidade_unidades_rodada(self):
        if self.produto.tempo_producao_min <= 0:
            return 0
        maquinas_ativas = min(self.maquinas, self.operadores // 2)
        minutos_total = maquinas_ativas * self.minutos_por_maquina
        return int(minutos_total // self.produto.tempo_producao_min)


class EstoqueProduto(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="estoques_produto")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="estoques")
    rodada_entrada = models.PositiveIntegerField()
    quantidade = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ESTOQUES_PRODUTO"
        verbose_name = "Estoque de Produto"
        verbose_name_plural = "Estoques de Produtos"
        ordering = ["rodada_entrada", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "produto", "rodada_entrada"],
                name="uniq_estoque_produto_por_rodada",
            ),
        ]

    def __str__(self):
        return (
            f"{self.grupo.nome} - {self.produto.codigo} - "
            f"R{self.rodada_entrada}: {self.quantidade}"
        )


class Distribuicao(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="envios")
    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribuicoes",
    )
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE)
    rodada = models.PositiveIntegerField(default=1)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    custo_transporte = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_vendida = models.PositiveIntegerField(default=0)
    quantidade_sobra = models.PositiveIntegerField(default=0)
    receita_realizada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processada = models.BooleanField(default=False)
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "DISTRIBUICOES"
        ordering = ["-data_envio"]
        verbose_name = "Distribuicao"
        verbose_name_plural = "Distribuicoes"

    def __str__(self):
        return f"{self.cidade.nome} - {self.quantidade}"


class MarketShareCidadeProduto(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="market_shares")
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, related_name="market_shares")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="market_shares")
    rodada = models.PositiveIntegerField()
    quantidade_vendida = models.PositiveIntegerField(default=0)
    market_share_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    class Meta:
        db_table = "MARKET_SHARE_CIDADE_PRODUTO"
        verbose_name = "Market Share Cidade Produto"
        verbose_name_plural = "Market Shares Cidade Produto"
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "cidade", "produto", "rodada"],
                name="uniq_market_share_cidade_produto_rodada",
            ),
        ]

    def __str__(self):
        return (
            f"R{self.rodada} - {self.grupo.nome} - {self.cidade.nome} - "
            f"{self.produto.codigo}: {self.market_share_percent}%"
        )


class IndicadorRodadaGrupo(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="indicadores_rodada")
    rodada = models.PositiveIntegerField()
    lucro_rodada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_share_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    atendimento_demanda_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    eficiencia_estoque_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    score_multicriterio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "INDICADORES_RODADA_GRUPO"
        verbose_name = "Indicador da Rodada por Grupo"
        verbose_name_plural = "Indicadores da Rodada por Grupo"
        ordering = ["rodada", "-score_multicriterio"]
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "rodada"],
                name="uniq_indicador_grupo_rodada",
            ),
        ]

    def __str__(self):
        return f"R{self.rodada} - {self.grupo.nome}: {self.score_multicriterio}"


class ConsolidadoRodadaGrupo(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="consolidados_rodada")
    rodada = models.PositiveIntegerField()
    receita_vendas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custos_operacionais = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalidade_sem_submissao = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    perda_pereciveis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custo_armazenagem_mp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custo_armazenagem_produtos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custos_totais = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lucro_rodada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_caixa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ofertado = models.PositiveIntegerField(default=0)
    total_vendido = models.PositiveIntegerField(default=0)
    market_share_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    atendimento_demanda_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    eficiencia_estoque_percent = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    score_multicriterio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "CONSOLIDADO_RODADA_GRUPO"
        verbose_name = "Consolidado da Rodada por Grupo"
        verbose_name_plural = "Consolidados da Rodada por Grupo"
        ordering = ["-rodada", "grupo__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "rodada"],
                name="uniq_consolidado_grupo_rodada",
            ),
        ]

    def __str__(self):
        return f"R{self.rodada} - {self.grupo.nome}: lucro {self.lucro_rodada}"


class ResultadoFinanceiro(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="resultados")
    rodada = models.PositiveIntegerField()
    receita = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lucro = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_caixa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalidades = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "FINANCEIRO"
        verbose_name = "Resultado Financeiro"
        verbose_name_plural = "Resultados Financeiros"
        ordering = ["rodada"]

    def __str__(self):
        return f"{self.grupo.nome} - Rodada {self.rodada}"

    @property
    def custo_envio_total(self):
        total = self.grupo.envios.filter(rodada=self.rodada).aggregate(
            total=Sum("custo_transporte")
        )["total"]
        return total or Decimal("0")


class Investimento(models.Model):
    OPERACAO_FINANCEIRA_CHOICES = [
        ("aplicar", "Aplicar"),
        ("resgatar", "Resgatar"),
    ]

    CATEGORIA_CHOICES = [
        ("marketing", "Marketing"),
        ("maquinas", "Aquisicao de Maquinas"),
        ("rh", "Recursos Humanos"),
        ("financeiro", "Aplicacoes Financeiras"),
    ]

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="investimentos")
    rodada = models.PositiveIntegerField(default=1)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="investimentos",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="investimentos",
    )
    quantidade = models.PositiveIntegerField(default=1)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    roi = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tempo_maturacao = models.PositiveIntegerField(default=1)
    retorno_aplicado = models.BooleanField(default=False)
    operacao_financeira = models.CharField(
        max_length=20,
        choices=OPERACAO_FINANCEIRA_CHOICES,
        default="aplicar",
    )
    rodada_ativacao = models.PositiveIntegerField(default=1)
    processado = models.BooleanField(default=False)
    data = models.DateTimeField(auto_now_add=True)

    CARACTERISTICAS = {
        "marketing": {"roi": Decimal("0.05"), "tempo": 1},
        "maquinas": {"roi": Decimal("0.10"), "tempo": 2},
        "rh": {"roi": Decimal("0.03"), "tempo": 1},
        "financeiro": {"roi": Decimal("0.02"), "tempo": 1},
    }

    class Meta:
        db_table = "INVESTIMENTOS"
        verbose_name = "Investimento"
        verbose_name_plural = "Investimentos"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.grupo.nome} - {self.get_categoria_display()} {self.valor}"

    def save(self, *args, **kwargs):
        if (self.roi == Decimal("0") or self.tempo_maturacao == 0) and self.categoria in self.CARACTERISTICAS:
            config = self.CARACTERISTICAS[self.categoria]
            self.roi = config["roi"]
            self.tempo_maturacao = config["tempo"]
        super().save(*args, **kwargs)

    @property
    def retorno_projetado(self):
        return (self.valor * self.roi).quantize(Decimal("0.01"))

    @property
    def retorno_efetivo(self):
        return self.retorno_projetado if self.retorno_aplicado else Decimal("0")


class Evento(models.Model):
    TIPO_CHOICES = [
        ("custo_producao", "Custo de Producao"),
        ("custo_transporte", "Custo de Transporte"),
        ("demanda", "Demanda"),
        ("perda_estoque", "Perda de Estoque"),
        ("greve", "Greve"),
    ]
    MODO_CHOICES = [
        ("percentual", "Percentual"),
        ("estado", "Estado"),
    ]
    EFEITO_ESTADO_CHOICES = [
        ("atraso_mp", "Atraso de Materia-Prima"),
        ("retencao_entrega", "Retencao de Entregas"),
        ("bloqueio_producao", "Bloqueio de Producao"),
        ("quebra_estoque", "Quebra de Estoque"),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    modo_aplicacao = models.CharField(max_length=20, choices=MODO_CHOICES, default="percentual")
    efeito_estado = models.CharField(max_length=30, choices=EFEITO_ESTADO_CHOICES, blank=True)
    duracao_rodadas = models.PositiveIntegerField(default=1)
    impacto_percentual = models.IntegerField()
    probabilidade = models.FloatField(default=0)
    descricao = models.TextField(blank=True)

    class Meta:
        db_table = "EVENTOS"
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def __str__(self):
        return self.nome


class EventoRodada(models.Model):
    rodada = models.PositiveIntegerField()
    jogo = models.ForeignKey(
        Jogo,
        on_delete=models.CASCADE,
        related_name="eventos_rodada",
        null=True,
        blank=True,
    )
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="rodadas")
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "EVENTOS_RODADA"
        verbose_name = "Evento da Rodada"
        verbose_name_plural = "Eventos da Rodada"
        ordering = ["rodada"]
        constraints = [
            models.UniqueConstraint(
                fields=["jogo", "rodada"],
                name="uniq_evento_rodada_por_jogo",
            ),
        ]

    def __str__(self):
        if self.jogo_id:
            return f"{self.jogo.nome} - Rodada {self.rodada} - {self.evento.nome}"
        return f"Rodada {self.rodada} - {self.evento.nome}"


class Rodada(models.Model):
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE, related_name="rodadas", null=True, blank=True)
    numero = models.PositiveIntegerField()
    inicio = models.DateTimeField(auto_now_add=True)
    fim = models.DateTimeField()
    fechada = models.BooleanField(default=False)

    class Meta:
        db_table = "RODADAS"
        verbose_name = "Rodada"
        verbose_name_plural = "Rodadas"
        ordering = ["numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["jogo", "numero"],
                name="uniq_rodada_numero_por_jogo",
            ),
        ]

    def __str__(self):
        return f"Rodada {self.numero}"


class CEOGrupoRodada(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="ceos_rodada")
    rodada = models.PositiveIntegerField()
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ceo_rodadas")
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "CEO_GRUPO_RODADA"
        verbose_name = "CEO do Grupo por Rodada"
        verbose_name_plural = "CEOs do Grupo por Rodada"
        ordering = ["-rodada", "grupo__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "rodada"],
                name="uniq_ceo_grupo_rodada",
            ),
        ]

    def __str__(self):
        return f"{self.grupo.nome} - R{self.rodada} - {self.usuario.nome_usuario}"


class AuditoriaSubmissaoRodada(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="auditorias_submissao")
    rodada = models.PositiveIntegerField()
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="auditorias_submissao")
    decisao = models.ForeignKey(
        Decisao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
    )
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "AUDITORIA_SUBMISSAO_RODADA"
        verbose_name = "Auditoria de Submissao da Rodada"
        verbose_name_plural = "Auditorias de Submissao da Rodada"
        ordering = ["-data_registro"]

    def __str__(self):
        return (
            f"{self.grupo.nome} - R{self.rodada} - "
            f"{self.usuario.nome_usuario} - {self.data_registro}"
        )


class DemandaCidadeProduto(models.Model):
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, related_name="demandas_produto")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="demandas_cidade")
    demanda_maxima = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "DEMANDA_CIDADE_PRODUTO"
        verbose_name = "Demanda por Cidade e Produto"
        verbose_name_plural = "Demandas por Cidade e Produto"
        constraints = [
            models.UniqueConstraint(
                fields=["cidade", "produto"],
                name="uniq_demanda_cidade_produto",
            ),
        ]

    def __str__(self):
        return f"{self.cidade.nome} - {self.produto.codigo}: {self.demanda_maxima}"


class AplicacaoFinanceiraGrupo(models.Model):
    grupo = models.OneToOneField(Grupo, on_delete=models.CASCADE, related_name="aplicacao_financeira")
    saldo_aplicado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    taxa_juros_rodada = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.015"))
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "APLICACAO_FINANCEIRA_GRUPO"
        verbose_name = "Aplicacao Financeira do Grupo"
        verbose_name_plural = "Aplicacoes Financeiras dos Grupos"

    def __str__(self):
        return f"{self.grupo.nome} - saldo aplicado {self.saldo_aplicado}"


class ExecucaoJob(models.Model):
    STATUS_CHOICES = [
        ("sucesso", "Sucesso"),
        ("falha", "Falha"),
    ]

    comando = models.CharField(max_length=120)
    correlation_id = models.CharField(max_length=40, db_index=True)
    rodada = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sucesso")
    detalhes = models.TextField(blank=True)
    iniciado_em = models.DateTimeField(auto_now_add=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "EXECUCAO_JOBS"
        verbose_name = "Execucao de Job"
        verbose_name_plural = "Execucoes de Jobs"
        ordering = ["-iniciado_em"]

    def __str__(self):
        return f"{self.comando} - {self.status} - {self.correlation_id}"

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Sum
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class UserManager(BaseUserManager):
    def create_user(self, email_usuario, nome_usuario, password=None, **extra_fields):
        if not email_usuario:
            raise ValueError('O e-mail é obrigatório')
        if not password:
            raise ValueError('Usuário deve ter uma senha')
        email_usuario = self.normalize_email(email_usuario)
        user = self.model(
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_usuario, nome_usuario, password=None, **extra_fields):
        extra_fields.setdefault('tipo_usuario', 'gamemaster')
        extra_fields.setdefault('status_usuario', True)
        extra_fields.setdefault('is_superuser', True)

        if not password:
            raise ValueError('Superusuário deve ter uma senha')

        return self.create_user(
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            password=password,
            **extra_fields
        )

class User(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO_CHOICES = [
        ('gamemaster', 'Administrador'),
        ('lider_grupo', 'CEO do Grupo'),
        ('membro_grupo', 'Membro do Grupo'),
    ]

    id_usuario = models.AutoField(primary_key=True)
    nome_usuario = models.CharField(max_length=150)
    email_usuario = models.EmailField(max_length=100, unique=True)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    status_usuario = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email_usuario'
    REQUIRED_FIELDS = ['nome_usuario']

    class Meta:
        db_table = 'USUARIOS'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.nome_usuario

    @property
    def is_staff(self):
        return self.tipo_usuario == 'gamemaster' or self.is_superuser

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
        db_table = 'CONFIG'
        verbose_name = 'Configuração do Jogo'
        verbose_name_plural = 'Configurações do Jogo'

    def __str__(self):
        return 'Configuração'


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
        db_table = 'GRUPOS'
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

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
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='decisoes')
    rodada = models.PositiveIntegerField()
    descricao = models.TextField()
    quantidade = models.IntegerField(default=0)
    resultado = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DECISOES'
        ordering = ['-data_criacao']
        verbose_name = 'Decisão'
        verbose_name_plural = 'Decisões'

    def __str__(self):
        return f"Decisão {self.rodada} - {self.grupo.nome}"


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
        db_table = 'CIDADES'
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'

    def __str__(self):
        return self.nome


class Distribuicao(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='envios')
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE)
    rodada = models.PositiveIntegerField(default=1)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    custo_transporte = models.DecimalField(max_digits=10, decimal_places=2)
    vendas_realizadas = models.PositiveIntegerField(default=0)
    qualidade = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    fator_marketing = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DISTRIBUICOES'
        ordering = ['-data_envio']
        verbose_name = 'Distribuição'
        verbose_name_plural = 'Distribuições'

    def __str__(self):
        return f"{self.cidade.nome} - {self.quantidade}"


class VendaCidade(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="vendas_cidade")
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, related_name="vendas_cidade")
    rodada = models.PositiveIntegerField()
    quantidade_vendida = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "VENDAS_CIDADE"
        unique_together = ("grupo", "cidade", "rodada")
        verbose_name = "Venda por Cidade"
        verbose_name_plural = "Vendas por Cidade"

    def __str__(self):
        return f"{self.grupo.nome} - {self.cidade.nome} ({self.rodada})"


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
    CATEGORIA_CHOICES = [
        ("marketing", "Marketing"),
        ("maquinas", "Aquisição de Máquinas"),
        ("rh", "Recursos Humanos"),
        ("financeiro", "Aplicações Financeiras"),
    ]

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="investimentos")
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, null=True, blank=True, related_name="investimentos")
    rodada = models.PositiveIntegerField(default=1)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    roi = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    tempo_maturacao = models.PositiveIntegerField(default=1)
    retorno_aplicado = models.BooleanField(default=False)
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
        ("custo_producao", "Custo de Produção"),
        ("custo_transporte", "Custo de Transporte"),
        ("demanda", "Demanda"),
        ("perda_estoque", "Perda de Estoque"),
        ("greve", "Greve"),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
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
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="rodadas")
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "EVENTOS_RODADA"
        verbose_name = "Evento da Rodada"
        verbose_name_plural = "Eventos da Rodada"
        ordering = ["rodada"]
        unique_together = ["rodada", "evento"]

    def __str__(self):
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

    def __str__(self):
        return f"Rodada {self.numero}"


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    quantidade = models.PositiveIntegerField(default=0)
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    custo_producao = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    validade = models.DateField(null=True, blank=True)
    materias_primas = models.ManyToManyField(
        "MateriaPrima", related_name="produtos", blank=True
    )
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="produtos")
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="produtos"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PRODUTOS"
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.nome

    def esta_vencido(self):
        return self.validade and self.validade < timezone.now().date()

    def custo_armazenagem(self):
        return self.quantidade * self.custo_producao * Decimal("0.02")


class EstoqueDetalhado(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="estoques")
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="estoques")
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_estoque",
    )
    quantidade = models.PositiveIntegerField()
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    custo_total = models.DecimalField(max_digits=12, decimal_places=2)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ESTOQUE_DETALHADO"
        verbose_name = "Estoque Detalhado"
        verbose_name_plural = "Estoques Detalhados"

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade}"


class MateriaPrima(models.Model):
    nome = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField(default=0)
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="materias_primas")
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materias_primas",
    )
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "MATERIAS_PRIMAS"
        verbose_name = "Matéria Prima"
        verbose_name_plural = "Matérias Primas"

    def __str__(self):
        return self.nome


class Fornecedor(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.ForeignKey(
        Cidade, on_delete=models.CASCADE, related_name="fornecedores"
    )
    prazo_entrega = models.PositiveIntegerField()
    custo_logistico_km = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("1.50")
    )

    class Meta:
        db_table = "FORNECEDORES"
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome


class PedidoMateriaPrima(models.Model):
    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.CASCADE, related_name="pedidos"
    )
    grupo = models.ForeignKey(
        Grupo, on_delete=models.CASCADE, related_name="pedidos_materia_prima"
    )
    quantidade = models.PositiveIntegerField()
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    prazo_entrega = models.PositiveIntegerField()
    custo_logistico = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_pedido = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PEDIDOS_MATERIA_PRIMA"
        verbose_name = "Pedido de Matéria-Prima"
        verbose_name_plural = "Pedidos de Matéria-Prima"

    def __str__(self):
        return f"{self.fornecedor.nome} - {self.quantidade}"

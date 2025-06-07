from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Sum
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email_usuario, nome_usuario, senha_usuario, **extra_fields):
        if not email_usuario:
            raise ValueError('O e-mail é obrigatório')
        if not senha_usuario:
            raise ValueError('Usuário deve ter uma senha')
        email_usuario = self.normalize_email(email_usuario)
        user = self.model(
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            **extra_fields
        )
        user.set_password(senha_usuario)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_usuario, nome_usuario, senha_usuario, **extra_fields):
        extra_fields.setdefault('tipo_usuario', 'aluno_admin')
        extra_fields.setdefault('status_usuario', True)
        
        if not senha_usuario:
            raise ValueError('Superusuário deve ter uma senha')
            
        return self.create_user(
@@ -35,25 +37,118 @@ class User(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO_CHOICES = [
        ('aluno_admin', 'Administrador'),
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
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
        return self.tipo_usuario == 'aluno_admin' or self.is_superuser

    @property
    def is_active(self):
        return self.status_usuario


class GameConfig(models.Model):
    capital_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estoque_inicial = models.PositiveIntegerField(default=0)
    produtos_habilitados = models.TextField(blank=True)

    modulo_producao = models.BooleanField(default=True)
    modulo_distribuicao = models.BooleanField(default=True)
    modulo_financeiro = models.BooleanField(default=True)

    regra_eventos = models.JSONField(default=dict, blank=True)

    maquinas_iniciais = models.PositiveIntegerField(default=1)
    capacidade_maquina = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = 'CONFIG'
        verbose_name = 'Configuração do Jogo'
        verbose_name_plural = 'Configurações do Jogo'

    def __str__(self):
        return 'Configuração'


class Grupo(models.Model):
    nome = models.CharField(max_length=100)
    membros = models.ManyToManyField(User, related_name="grupos")
    capital = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estoque = models.PositiveIntegerField(default=0)
    maquinas = models.PositiveIntegerField(default=1)
    capacidade_maquina = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = 'GRUPOS'
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return self.nome


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


class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    distancia_km = models.PositiveIntegerField()
    demanda = models.PositiveIntegerField(default=0)

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
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DISTRIBUICOES'
        ordering = ['-data_envio']
        verbose_name = 'Distribuição'
        verbose_name_plural = 'Distribuições'

    def __str__(self):
        return f"{self.cidade.nome} - {self.quantidade}"


class ResultadoFinanceiro(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="resultados")
    rodada = models.PositiveIntegerField()
    receita = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lucro = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_caixa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "FINANCEIRO"
        verbose_name = "Resultado Financeiro"
        verbose_name_plural = "Resultados Financeiros"
        ordering = ["rodada"]

    def __str__(self):
        return f"{self.grupo.nome} - Rodada {self.rodada}"


class Evento(models.Model):
    TIPO_CHOICES = [
        ("custo_producao", "Custo de Produção"),
        ("custo_transporte", "Custo de Transporte"),
        ("demanda", "Demanda"),
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
    rodada = models.PositiveIntegerField(unique=True)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="rodadas")
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "EVENTOS_RODADA"
        verbose_name = "Evento da Rodada"
        verbose_name_plural = "Eventos da Rodada"
        ordering = ["rodada"]

    def __str__(self):
        return f"Rodada {self.rodada} - {self.evento.nome}"


class Rodada(models.Model):
    numero = models.PositiveIntegerField(unique=True)
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

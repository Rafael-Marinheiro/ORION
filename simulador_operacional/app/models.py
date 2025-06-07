from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            senha_usuario=senha_usuario,
            **extra_fields
        )

class User(AbstractBaseUser, PermissionsMixin):
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


class TransportRoute(models.Model):
    """Rota de transporte com custo e prazo estimado."""

    origem = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    distancia_km = models.PositiveIntegerField()
    custo_por_km = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Rota de Transporte"
        verbose_name_plural = "Rotas de Transporte"

    @property
    def custo_total(self):
        return self.distancia_km * self.custo_por_km

    @property
    def prazo_estimado(self):
        return int(self.distancia_km / 50) + 1


class PriceList(models.Model):
    """Tabela de preços por praça."""

    produto = models.CharField(max_length=100)
    praca = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    promocao = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Preço"
        verbose_name_plural = "Preços"

    def preco_vigente(self):
        return self.promocao if self.promocao is not None else self.preco


class Sale(models.Model):
    """Registro de vendas realizadas."""

    data = models.DateField()
    produto = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField()
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    praca = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"

    @property
    def total(self):
        return self.quantidade * self.valor_unitario


class FinancialResult(models.Model):
    """Resultados financeiros por rodada."""

    rodada = models.PositiveIntegerField()
    receita = models.DecimalField(max_digits=12, decimal_places=2)
    despesas = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Resultado Financeiro"
        verbose_name_plural = "Resultados Financeiros"

    @property
    def lucro(self):
        return self.receita - self.despesas


class Ranking(models.Model):
    """Ranking dos grupos baseado no lucro."""

    grupo = models.CharField(max_length=100)
    resultado = models.ForeignKey(FinancialResult, on_delete=models.CASCADE)
    pontuacao = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ranking"
        verbose_name_plural = "Rankings"


class RandomEvent(models.Model):
    """Evento aleatório com probabilidade de ocorrência."""

    descricao = models.CharField(max_length=255)
    probabilidade = models.DecimalField(max_digits=5, decimal_places=2)
    impacto = models.TextField()

    class Meta:
        verbose_name = "Evento Aleatório"
        verbose_name_plural = "Eventos Aleatórios"

    def __str__(self):
        return self.descricao


class EventHistory(models.Model):
    """Registro de eventos aplicados em uma rodada."""

    evento = models.ForeignKey(RandomEvent, on_delete=models.CASCADE)
    rodada = models.PositiveIntegerField()
    data_ocorrencia = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Evento"
        verbose_name_plural = "Históricos de Eventos"

    def __str__(self):
        return f"Rodada {self.rodada} - {self.evento.descricao}"

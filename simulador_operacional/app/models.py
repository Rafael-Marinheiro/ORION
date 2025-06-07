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


class Grupo(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'GRUPOS'
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return self.nome


class Rodada(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fim = models.DateTimeField()
    encerrada = models.BooleanField(default=False)

    class Meta:
        db_table = 'RODADAS'
        verbose_name = 'Rodada'
        verbose_name_plural = 'Rodadas'

    def encerrar(self):
        self.encerrada = True
        self.save(update_fields=["encerrada"])

    def __str__(self):
        return f"Rodada {self.numero}"


class ResultadoFinanceiro(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='resultados',
        null=True,
        blank=True,
    )
    rodada = models.OneToOneField(Rodada, on_delete=models.CASCADE, related_name='resultado_financeiro')
    receita = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    custos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    despesas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fluxo_caixa_entrada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fluxo_caixa_saida = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lucro_liquido = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    fluxo_caixa_liquido = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    class Meta:
        db_table = 'RESULTADOS_FINANCEIROS'
        verbose_name = 'Resultado Financeiro'
        verbose_name_plural = 'Resultados Financeiros'

    def calcular_resultados(self):
        self.lucro_liquido = self.receita - self.custos - self.despesas
        self.fluxo_caixa_liquido = self.fluxo_caixa_entrada - self.fluxo_caixa_saida

    def save(self, *args, **kwargs):
        self.calcular_resultados()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Resultado {self.rodada}"


class EventoAleatorio(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    probabilidade = models.FloatField(help_text="Probabilidade de 0 a 1")

    class Meta:
        db_table = 'EVENTOS_ALEATORIOS'
        verbose_name = 'Evento Aleatório'
        verbose_name_plural = 'Eventos Aleatórios'

    def __str__(self):
        return self.nome


class RegistroEvento(models.Model):
    evento = models.ForeignKey(EventoAleatorio, on_delete=models.CASCADE)
    rodada = models.ForeignKey(Rodada, on_delete=models.CASCADE)
    data_aplicacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'REGISTRO_EVENTOS'
        verbose_name = 'Registro de Evento'
        verbose_name_plural = 'Registros de Eventos'

    def __str__(self):
        return f"{self.evento} - {self.rodada}"
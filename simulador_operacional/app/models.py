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


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    estoque_minimo = models.PositiveIntegerField(default=0)
    estoque_maximo = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'PRODUTOS'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return self.nome

    @property
    def estoque_atual(self):
        entradas = self.movimentos.filter(tipo='entrada').aggregate(total=models.Sum('quantidade'))['total'] or 0
        saidas = self.movimentos.filter(tipo='saida').aggregate(total=models.Sum('quantidade'))['total'] or 0
        return entradas - saidas

    def alerta_estoque(self):
        atual = self.estoque_atual
        if atual < self.estoque_minimo:
            return 'Risco de ruptura'
        if self.estoque_maximo and atual > self.estoque_maximo:
            return 'Risco de desperdício'
        return 'OK'


class MovimentoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]
    produto = models.ForeignKey(Produto, related_name='movimentos', on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'MOVIMENTOS_ESTOQUE'
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'

    def __str__(self):
        return f"{self.produto.nome} - {self.tipo} ({self.quantidade})"


class Maquina(models.Model):
    nome = models.CharField(max_length=100)
    capacidade_por_hora = models.PositiveIntegerField(help_text='Unidades produzidas por hora')

    class Meta:
        db_table = 'MAQUINAS'
        verbose_name = 'Máquina'
        verbose_name_plural = 'Máquinas'

    def __str__(self):
        return self.nome


class Producao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PRODUCOES'
        verbose_name = 'Produção'
        verbose_name_plural = 'Produções'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        MovimentoEstoque.objects.create(produto=self.produto, quantidade=self.quantidade, tipo='entrada')

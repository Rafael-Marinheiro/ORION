from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver

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


class GameConfig(models.Model):
    capital_inicial = models.PositiveIntegerField(default=0)
    estoque_inicial = models.PositiveIntegerField(default=0)
    produtos_habilitados = models.CharField(max_length=255, blank=True)
    modulo_producao = models.BooleanField(default=True)
    modulo_distribuicao = models.BooleanField(default=True)
    modulo_financeiro = models.BooleanField(default=True)
    modulo_eventos = models.BooleanField(default=True)
    regras_eventos = models.TextField(blank=True)

    class Meta:
        db_table = "CONFIGURACAO_JOGO"
        verbose_name = "Configuração do Jogo"
        verbose_name_plural = "Configurações do Jogo"

    def __str__(self):
        return f"Config {self.id}"


class Group(models.Model):
    nome = models.CharField(max_length=100)
    membros = models.ManyToManyField(User, related_name="grupos")

    class Meta:
        db_table = "GRUPOS"
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"

    def __str__(self):
        return self.nome


class ProductionSetting(models.Model):
    grupo = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="producao_config")
    maquinas = models.PositiveIntegerField(default=1)
    capacidade_maquina = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = "CONFIG_PRODUCAO"
        verbose_name = "Configuração de Produção"
        verbose_name_plural = "Configurações de Produção"

    def __str__(self):
        return f"Produção {self.grupo.nome}"


class InventoryItem(models.Model):
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="estoque")
    produto = models.CharField(max_length=100)
    quantidade = models.IntegerField(default=0)

    class Meta:
        db_table = "ESTOQUE"
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"

    def __str__(self):
        return f"{self.produto} - {self.quantidade}"


class Decision(models.Model):
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="decisoes")
    rodada = models.PositiveIntegerField(default=1)
    descricao = models.TextField()
    producao = models.PositiveIntegerField(default=0)
    venda = models.PositiveIntegerField(default=0)
    resultado = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "DECISOES"
        verbose_name = "Decisão"
        verbose_name_plural = "Decisões"
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"Decisão {self.rodada} - {self.grupo.nome}"


@receiver(post_save, sender=Group)
def criar_config_padrao(sender, instance, created, **kwargs):
    if created:
        ProductionSetting.objects.create(grupo=instance)
        InventoryItem.objects.create(grupo=instance, produto="Padrao", quantidade=0)


@receiver(post_save, sender=Decision)
def atualizar_estoque(sender, instance, created, **kwargs):
    if created:
        item, _ = InventoryItem.objects.get_or_create(
            grupo=instance.grupo, produto="Padrao"
        )
        item.quantidade += instance.producao - instance.venda
        item.save()

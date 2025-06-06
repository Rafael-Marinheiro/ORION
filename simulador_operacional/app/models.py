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

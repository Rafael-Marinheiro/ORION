import os
import django
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'simulador_operacional')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simulador_operacional.settings')
django.setup()

from app.models import User

def create_gamemaster_user():
    email = 'rafasilvamarinheiro@gmail.com'
    nome = 'Rafael Marinheiro'
    senha = 'Naroc123.'
    tipo_usuario = 'gamemaster'  # novo tipo conforme atualização

    if not User.objects.filter(email_usuario=email).exists():
        user = User(
            email_usuario=email,
            nome_usuario=nome,
            tipo_usuario=tipo_usuario,
        )
        user.set_password(senha)
        user.save()
        print(f'Usuário GameMaster {nome} criado com sucesso.')
    else:
        print(f'Usuário com email {email} já existe.')

if __name__ == '__main__':
    create_gamemaster_user()

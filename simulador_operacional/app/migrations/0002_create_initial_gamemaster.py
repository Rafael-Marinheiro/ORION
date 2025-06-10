from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_gamemaster(apps, schema_editor):
    User = apps.get_model('app', 'User')
    if not User.objects.filter(email_usuario='rafasilvamarinheiro@gmail.com').exists():
        User.objects.create(
            email_usuario='rafasilvamarinheiro@gmail.com',
            nome_usuario='Rafael Marinheiro',
            tipo_usuario='gamemaster',
            is_superuser=True,
            status_usuario=True,
            password=make_password('Naroc123.')
        )


def delete_gamemaster(apps, schema_editor):
    User = apps.get_model('app', 'User')
    User.objects.filter(email_usuario='rafasilvamarinheiro@gmail.com').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_gamemaster, delete_gamemaster),
    ]

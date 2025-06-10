from django.db import migrations


def create_gamemaster(apps, schema_editor):
    User = apps.get_model('app', 'User')
    if not User.objects.filter(email_usuario='rafasilvamarinheiro@gmail.com').exists():
        User.objects.create_superuser(
            email_usuario='rafasilvamarinheiro@gmail.com',
            nome_usuario='Rafael Marinheiro',
            password='Naroc123.'
        )


def delete_gamemaster(apps, schema_editor):
    User = apps.get_model('app', 'User')
    User.objects.filter(email_usuario='rafasilvamarinheiro@gmail.com').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_update_user_roles'),
    ]

    operations = [
        migrations.RunPython(create_gamemaster, delete_gamemaster),
    ]

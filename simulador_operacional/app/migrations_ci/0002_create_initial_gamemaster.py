from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_gamemaster(apps, schema_editor):
    user_model = apps.get_model("app", "User")
    if not user_model.objects.filter(email_usuario="rafasilvamarinheiro@gmail.com").exists():
        user_model.objects.create(
            email_usuario="rafasilvamarinheiro@gmail.com",
            nome_usuario="Rafael Marinheiro",
            tipo_usuario="gamemaster",
            is_superuser=True,
            status_usuario=True,
            password=make_password("Naroc123."),
        )


def delete_gamemaster(apps, schema_editor):
    user_model = apps.get_model("app", "User")
    user_model.objects.filter(email_usuario="rafasilvamarinheiro@gmail.com").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_gamemaster, delete_gamemaster),
    ]

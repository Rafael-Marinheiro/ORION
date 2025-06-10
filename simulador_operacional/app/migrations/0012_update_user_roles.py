from django.db import migrations

ROLE_MAP = {
    'aluno_admin': 'lider_grupo',
    'professor': 'gamemaster',
    'aluno': 'membro_grupo',
}

def forwards(apps, schema_editor):
    User = apps.get_model('app', 'User')
    for old, new in ROLE_MAP.items():
        User.objects.filter(tipo_usuario=old).update(tipo_usuario=new)

def backwards(apps, schema_editor):
    User = apps.get_model('app', 'User')
    for old, new in ROLE_MAP.items():
        User.objects.filter(tipo_usuario=new).update(tipo_usuario=old)

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_sprint23_features'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

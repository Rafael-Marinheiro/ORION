"""Mantém o nó da trilha consolidada sem provisionar acesso administrativo.

A versão anterior criava uma conta com senha fixa. Instalações novas devem
usar createsuperuser; nas existentes, o responsável deve redefinir a senha
da conta provisionada antes de expor o ambiente. Não apagamos usuários no rollback.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("app", "0001_initial")]
    operations = []

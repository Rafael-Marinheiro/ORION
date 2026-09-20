"""Verifica migrações reais e seed sem tocar no banco local da turma.

Executar dentro do Docker: python ../tools/verificar_base_limpa.py
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "simulador_operacional"))
os.environ["DJANGO_SETTINGS_MODULE"] = "simulador_operacional.settings_ci"

import django
from django.conf import settings
from django.core.management import call_command
from django.db import connections


def main():
    with tempfile.TemporaryDirectory(prefix="orion-base-limpa-") as tmp:
        settings.DATABASES["default"]["NAME"] = str(Path(tmp) / "base.sqlite3")
        django.setup()
        from app.models import Cidade, DemandaCidadeProduto, Evento, User

        try:
            call_command("migrate", interactive=False, verbosity=0)
            assert User.objects.count() == 0, "Migração não deve provisionar administrador."
            call_command("seed_dados_base", verbosity=0)
            cidades = list(Cidade.objects.order_by("pk").values())
            call_command("seed_dados_base", verbosity=0)
            assert list(Cidade.objects.order_by("pk").values()) == cidades
            assert Cidade.objects.count() == 12
            assert DemandaCidadeProduto.objects.count() == 36
            assert Evento.objects.count() == 6
            assert User.objects.count() == 0
            call_command("check")
            print("OK: migrações reais; 12 praças, 36 demandas, 6 eventos; nenhuma conta automática.")
        finally:
            connections.close_all()


if __name__ == "__main__":
    main()

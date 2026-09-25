"""Comentario de template nao pode vazar para a tela.

`{# ... #}` do Django e de UMA linha so. Escrito em varias, ele nao e
comentario: o texto inteiro vai para o HTML e aparece para o aluno. O
projeto ja caiu nisso duas vezes -- a segunda em 24/09/2026, no aviso de
rodada sem operacao. Para comentario de varias linhas existe
`{% comment %}`.
"""

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

TEMPLATES = Path(settings.BASE_DIR) / "app" / "templates"


class ComentarioDeTemplateTest(SimpleTestCase):
    def test_nenhum_comentario_de_chave_cerquilha_atravessa_linhas(self):
        vazando = []
        for arquivo in TEMPLATES.rglob("*.html"):
            for numero, linha in enumerate(
                arquivo.read_text(encoding="utf-8").splitlines(), start=1
            ):
                abre = linha.count("{#")
                fecha = linha.count("#}")
                if abre != fecha:
                    vazando.append(f"{arquivo.relative_to(TEMPLATES)}:{numero}")

        self.assertEqual(
            vazando,
            [],
            "comentário {# #} aberto e não fechado na mesma linha vaza para a "
            "página renderizada; use {% comment %} para várias linhas: "
            + ", ".join(vazando),
        )

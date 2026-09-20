"""Base IBGE Censo 2022/malha 2023 e rotas: docs/BASE_REGIONAL.md."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from app.models import Cidade, DemandaCidadeProduto


class BaseRegionalTest(TestCase):
    def test_seed_idempotente_com_rotas_e_demanda_derivada(self):
        call_command("seed_dados_base", stdout=StringIO())
        ids = dict(Cidade.objects.values_list("nome", "pk"))
        call_command("seed_dados_base", stdout=StringIO())
        self.assertEqual(dict(Cidade.objects.values_list("nome", "pk")), ids)
        self.assertEqual(Cidade.objects.count(), 12)
        self.assertEqual(DemandaCidadeProduto.objects.count(), 36)
        # Valores esperados calculados a partir da tabela de fontes, não do seed.
        esperados = {
            "Currais Novos": (0, 100), "Acari": (29, 50),
            "Caico": (88, 150), "Santa Cruz": (64, 100),
            "Patos": (143, 200), "Assu": (139, 100),
            "Natal": (181, 1550), "Campina Grande": (167, 850),
            "Mossoro": (198, 550), "Joao Pessoa": (263, 1750),
            "Recife": (342, 3100), "Fortaleza": (437, 5050),
        }
        for cidade in Cidade.objects.all():
            with self.subTest(cidade=cidade.nome):
                km, demanda = esperados[cidade.nome]
                self.assertEqual((cidade.distancia_km, cidade.demanda), (km, demanda))
                self.assertEqual(dict(DemandaCidadeProduto.objects.filter(
                    cidade=cidade
                ).values_list("produto__codigo", "demanda_maxima")), {
                    "A": demanda // 2, "B": demanda * 3 // 10,
                    "C": demanda // 5,
                })

    def test_seed_corrige_praca_sem_apagar_catalogo_personalizado(self):
        patos = Cidade.objects.create(nome="Patos", distancia_km=135, demanda=250)
        extra = Cidade.objects.create(nome="Praça personalizada", distancia_km=10, demanda=20)
        call_command("seed_dados_base", stdout=StringIO())
        patos.refresh_from_db()
        self.assertEqual((patos.distancia_km, patos.demanda), (143, 200))
        self.assertTrue(Cidade.objects.filter(pk=extra.pk).exists())

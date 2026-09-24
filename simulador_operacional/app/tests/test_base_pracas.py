"""Base de pracas do 9.1.

A fabrica fica em Natal-RN (9, abertura) e as dez pracas sao a tabela do
9.1, com a distancia ate Natal e o teto de absorcao por rodada. A coluna do
documento e "Demanda Maxima (unid./PRODUTO)": o mesmo teto vale para cada
produto, nao e um total rateado entre A, B e C.

Ate 2026-09-24 o seed usava doze cidades do Serido/RN com demanda derivada
da populacao -- desvio do dono do projeto, revertido para o documento.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from app.models import Cidade, DemandaCidadeProduto, GameConfig, default_ranking_pesos


class BasePracasDoDocumentoTest(TestCase):
    def test_seed_inicia_cinco_pesos_sem_sobrescrever_configuracao_existente(self):
        call_command("seed_dados_base", stdout=StringIO())
        config = GameConfig.objects.get(pk=1)
        self.assertEqual(config.ranking_pesos, default_ranking_pesos())
        config.ranking_pesos = {"EO": 1, "DF": 0, "EE": 0, "SD": 0, "DS": 0}
        config.save()
        call_command("seed_dados_base", stdout=StringIO())
        config.refresh_from_db()
        self.assertEqual(config.ranking_pesos["EO"], 1)

    # Tabela 9.1, transcrita do documento -- nao do seed.
    PRACAS_DO_91 = {
        "São Paulo": (2896, 27000),
        "Rio de Janeiro": (2588, 15000),
        "Recife": (290, 4000),
        "João Pessoa": (181, 2000),
        "Aracaju": (782, 1000),
        "Fortaleza": (527, 6000),
        "Goiânia": (1949, 3000),
        "Belém": (1952, 3000),
        "Maceió": (542, 2000),
        "Porto Alegre": (4034, 3000),
    }

    def test_seed_idempotente_com_as_dez_pracas_do_documento(self):
        call_command("seed_dados_base", stdout=StringIO())
        ids = dict(Cidade.objects.values_list("nome", "pk"))
        call_command("seed_dados_base", stdout=StringIO())
        self.assertEqual(dict(Cidade.objects.values_list("nome", "pk")), ids)
        self.assertEqual(Cidade.objects.count(), 10)
        self.assertEqual(DemandaCidadeProduto.objects.count(), 30)
        for cidade in Cidade.objects.all():
            with self.subTest(cidade=cidade.nome):
                km, demanda = self.PRACAS_DO_91[cidade.nome]
                self.assertEqual((cidade.distancia_km, cidade.demanda), (km, demanda))
                # 9.1: o teto e POR PRODUTO, igual para os tres.
                self.assertEqual(
                    dict(
                        DemandaCidadeProduto.objects.filter(cidade=cidade).values_list(
                            "produto__codigo", "demanda_maxima"
                        )
                    ),
                    {"A": demanda, "B": demanda, "C": demanda},
                )

    def test_natal_nao_e_praca_de_venda(self):
        """O 9 poe a fabrica em Natal; ela nao consta entre as pracas do 9.1."""
        call_command("seed_dados_base", stdout=StringIO())

        self.assertFalse(Cidade.objects.filter(nome="Natal").exists())

    def test_seed_corrige_praca_sem_apagar_catalogo_personalizado(self):
        recife = Cidade.objects.create(nome="Recife", distancia_km=342, demanda=3100)
        extra = Cidade.objects.create(nome="Praça personalizada", distancia_km=10, demanda=20)
        call_command("seed_dados_base", stdout=StringIO())
        recife.refresh_from_db()
        self.assertEqual((recife.distancia_km, recife.demanda), (290, 4000))
        self.assertTrue(Cidade.objects.filter(pk=extra.pk).exists())

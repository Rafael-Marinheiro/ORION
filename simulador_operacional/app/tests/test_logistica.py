from decimal import Decimal

from django.test import TestCase

from app.models import ComposicaoProduto, MateriaPrima, Produto
from app.parametros import CAPACIDADE_CAMINHAO_KG
from app.services.logistica import (
    calcular_frete,
    calcular_frete_materia_prima,
    peso_do_envio,
    viagens_necessarias,
)


class ViagensTest(TestCase):
    def test_caminhao_nao_se_divide(self):
        self.assertEqual(viagens_necessarias(0), 0)
        self.assertEqual(viagens_necessarias(1), 1)
        self.assertEqual(viagens_necessarias(CAPACIDADE_CAMINHAO_KG), 1)
        self.assertEqual(viagens_necessarias(CAPACIDADE_CAMINHAO_KG + 1), 2)
        self.assertEqual(viagens_necessarias(CAPACIDADE_CAMINHAO_KG * 3), 3)

    def test_peso_negativo_ou_nulo_nao_gera_viagem(self):
        self.assertEqual(viagens_necessarias(None), 0)
        self.assertEqual(viagens_necessarias(-5), 0)


class FreteTest(TestCase):
    def test_frete_de_materia_prima_usa_quilo_quilometro_documentado(self):
        frete = calcular_frete_materia_prima(1000, 500, produtos_remetidos=300)

        self.assertEqual(frete["custo_bruto"], Decimal("750000.00"))
        self.assertEqual(frete["desconto_retorno"], Decimal("150000.00"))
        self.assertEqual(frete["custo"], Decimal("600000.00"))

    def test_desconto_de_materia_prima_nao_excede_quantidade_comprada(self):
        frete = calcular_frete_materia_prima(100, 50, produtos_remetidos=80)

        self.assertEqual(frete["desconto_retorno"], Decimal("2500.00"))
    def test_consolidar_nao_muda_o_frete_mas_muda_o_custo_por_quilo(self):
        """A licao central: o caminhao cheio e o vazio custam o mesmo."""
        pouco = calcular_frete(190, 1000)
        cheio = calcular_frete(190, CAPACIDADE_CAMINHAO_KG)

        self.assertEqual(pouco["custo"], cheio["custo"])
        self.assertEqual(pouco["viagens"], cheio["viagens"])
        # mas a ocupacao denuncia o desperdicio
        self.assertLess(pouco["ocupacao_percentual"], Decimal("10"))
        self.assertEqual(cheio["ocupacao_percentual"], Decimal("100.00"))

    def test_um_quilo_a_mais_dobra_o_frete(self):
        no_limite = calcular_frete(190, CAPACIDADE_CAMINHAO_KG)
        estourado = calcular_frete(190, CAPACIDADE_CAMINHAO_KG + 1)

        self.assertEqual(estourado["custo"], no_limite["custo"] * 2)

    def test_frete_cresce_com_a_distancia(self):
        perto = calcular_frete(75, 5000)
        longe = calcular_frete(470, 5000)

        self.assertGreater(longe["custo"], perto["custo"])

    def test_custo_de_produto_tem_deslocamento_e_carga_por_viagem(self):
        frete = calcular_frete(190, CAPACIDADE_CAMINHAO_KG + 1)

        self.assertEqual(frete["viagens"], 2)
        self.assertEqual(frete["custo_bruto"], Decimal("2900.00"))  # 2 x (190 x 5 + 500)

    def test_caminhao_cheio_de_a_tem_frete_compatível_com_a_escala_do_orion(self):
        frete = calcular_frete(172, 12000)  # 40 unidades de A, de 300 kg cada

        self.assertEqual(frete["custo"], Decimal("1360.00"))
        self.assertEqual(frete["custo"] / Decimal("40"), Decimal("34.00"))

    def test_desconto_de_retorno_abate_por_viagem(self):
        sem = calcular_frete(190, 5000)
        com = calcular_frete(190, 5000, viagens_com_retorno=1)

        self.assertEqual(com["desconto_retorno"], Decimal("95.00"))  # 190 x 0,50
        self.assertEqual(com["custo"], sem["custo"] - Decimal("95.00"))

    def test_retorno_nao_passa_das_viagens_existentes(self):
        frete = calcular_frete(190, 5000, viagens_com_retorno=9)

        self.assertEqual(frete["viagens"], 1)
        self.assertEqual(frete["desconto_retorno"], Decimal("95.00"))

    def test_desconto_nunca_deixa_o_frete_negativo(self):
        frete = calcular_frete(10, 5000, viagens_com_retorno=1)

        self.assertGreaterEqual(frete["custo"], Decimal("0"))

    def test_envio_vazio_nao_custa(self):
        self.assertEqual(calcular_frete(190, 0)["custo"], Decimal("0"))
        self.assertEqual(calcular_frete(0, 5000)["custo"], Decimal("0"))


class PesoDoProdutoTest(TestCase):
    def test_peso_e_a_soma_da_composicao_como_no_documento(self):
        """6.1 traz a coluna Total (kg): A = 300."""
        mp1 = MateriaPrima.objects.create(codigo="MP1", nome="MP1", preco_unitario=3)
        mp2 = MateriaPrima.objects.create(codigo="MP2", nome="MP2", preco_unitario=Decimal("5.5"))
        mp3 = MateriaPrima.objects.create(codigo="MP3", nome="MP3", preco_unitario=8)
        mp4 = MateriaPrima.objects.create(codigo="MP4", nome="MP4", preco_unitario=15)
        a = Produto.objects.create(codigo="A", nome="Produto A", tempo_producao_min=2)
        for mp, qtd in ((mp1, 120), (mp2, 40), (mp3, 60), (mp4, 80)):
            ComposicaoProduto.objects.create(
                produto=a, materia_prima=mp, quantidade_por_unidade=qtd
            )

        self.assertEqual(a.peso_unitario_kg, Decimal("300"))
        # e o custo do 6.1 continua batendo
        self.assertEqual(a.custo_unitario_estimado, Decimal("2260.00"))
        self.assertEqual(peso_do_envio(a, 40), Decimal("12000"))

    def test_produto_sem_composicao_pesa_zero(self):
        vazio = Produto.objects.create(codigo="Z", nome="Sem composicao", tempo_producao_min=1)

        self.assertEqual(peso_do_envio(vazio, 10), Decimal("0"))
        self.assertEqual(peso_do_envio(None, 10), Decimal("0"))

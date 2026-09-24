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


class FreteDeMateriaPrimaTest(TestCase):
    """7.2 e 7.2.1 com os valores do documento, por VIAGEM de caminhao.

    Ao pe da letra -- R$ 1,50 x km x kg -- o exemplo do proprio 7.2.1 cobra
    R$ 750.000 para trazer 500 kg que valem R$ 4.000, e o produto A pagava
    R$ 204.360 de frete de insumo por unidade contra o caixa de R$ 1.000.000
    do 5. A unidade passou a ser a viagem em 24/09/2026; os valores do
    documento ficaram intactos.
    """

    def test_o_exemplo_do_721_cabe_no_caixa_do_grupo(self):
        """500 kg de Belem a 1.000 km: uma viagem, R$ 1.500 -- nao 750.000."""
        frete = calcular_frete_materia_prima(1000, 500)

        self.assertEqual(frete["viagens"], 1)
        self.assertEqual(frete["custo_bruto"], Decimal("1500.00"))

    def test_consolidar_pedido_nao_muda_o_frete(self):
        """A licao: meio caminhao e um caminhao cheio custam o mesmo."""
        pouco = calcular_frete_materia_prima(190, 500)
        cheio = calcular_frete_materia_prima(190, CAPACIDADE_CAMINHAO_KG)

        self.assertEqual(pouco["custo"], cheio["custo"])
        self.assertEqual(pouco["custo"], Decimal("285.00"))  # 190 x 1,50
        self.assertLess(pouco["ocupacao_percentual"], Decimal("5"))
        self.assertEqual(cheio["ocupacao_percentual"], Decimal("100.00"))

    def test_um_quilo_alem_do_caminhao_dobra_a_conta(self):
        frete = calcular_frete_materia_prima(190, CAPACIDADE_CAMINHAO_KG + 1)

        self.assertEqual(frete["viagens"], 2)
        self.assertEqual(frete["custo_bruto"], Decimal("570.00"))

    def test_desconto_de_retorno_vale_pelas_viagens_de_produto(self):
        """7.2.1: o caminhao que levou produto volta carregado com a MP."""
        frete = calcular_frete_materia_prima(1000, 500, peso_remetido_kg=12000)

        self.assertEqual(frete["desconto_retorno"], Decimal("500.00"))  # 1 x 1000 x 0,50
        self.assertEqual(frete["custo"], Decimal("1000.00"))

    def test_desconto_nao_passa_das_viagens_de_materia_prima(self):
        """Remeter dez caminhoes de produto nao barateia uma viagem de MP
        alem do frete dela."""
        frete = calcular_frete_materia_prima(1000, 500, peso_remetido_kg=120000)

        self.assertEqual(frete["desconto_retorno"], Decimal("500.00"))

    def test_sem_remessa_nao_ha_desconto(self):
        self.assertEqual(
            calcular_frete_materia_prima(1000, 500)["desconto_retorno"], Decimal("0")
        )

    def test_compra_vazia_nao_custa(self):
        self.assertEqual(calcular_frete_materia_prima(1000, 0)["custo"], Decimal("0"))
        self.assertEqual(calcular_frete_materia_prima(0, 500)["custo"], Decimal("0"))

    def test_a_mesma_carga_custa_o_mesmo_nas_duas_pontas(self):
        """O que motivou a correcao: 12 t na mesma estrada custavam 2.677x
        mais como MP do que como produto acabado."""
        como_mp = calcular_frete_materia_prima(290, 12000)["custo"]
        como_produto = calcular_frete(290, 12000)["custo"]

        self.assertLess(como_mp, como_produto * 2)


class FreteTest(TestCase):
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

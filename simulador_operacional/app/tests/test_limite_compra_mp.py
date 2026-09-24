"""Limite de compra de materia-prima -- RN-05.

"Compra de MP | minimo 0 kg | maximo 150% do consumo estimado da producao",
e "quantidades acima do limite serao automaticamente ajustadas pelo sistema,
com alerta ao CEO do grupo".

A regra estava na especificacao e em lugar nenhum do codigo: dava para
comprar qualquer volume, limitado so pelo caixa.

"Consumo estimado da producao" aparece UMA vez nos quinze documentos e nao e
definido. A leitura adotada vem da linha de cima da mesma tabela, que mede a
producao por "capacidade da planta x numero de turnos", e do RN-06, que diz
que a rodada e um turno unico: o consumo estimado e o que as linhas consomem
rodando cheias por uma rodada.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    CapacidadeProdutoGrupo,
    Cidade,
    ComposicaoProduto,
    CompraMateriaPrima,
    Grupo,
    MateriaPrima,
    Produto,
    Rodada,
    User,
)
from app.services.suprimentos import consumo_de_capacidade, limite_de_compra


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class LimiteDeCompraTest(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo-limite@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("5000000"))
        self.grupo.membros.add(self.ceo)
        self.mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("3")
        )
        # 1 min por unidade e 2 kg por unidade.
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=self.mp, quantidade_por_unidade=Decimal("2")
        )
        # 1 maquina x 400 min = 400 unidades por rodada -> 800 kg de consumo.
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo,
            produto=self.produto,
            maquinas=1,
            operadores=2,
            minutos_por_maquina=400,
        )
        # 7.1: MP1 vem de Fortaleza. Distancia ate Natal pelo 9.1.
        self.cidade = Cidade.objects.create(
            nome="Fortaleza", distancia_km=527, demanda=6000
        )
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        self.client.login(username="ceo-limite@example.com", password="pass")

    def _comprar(self, kg):
        return self.client.post(
            reverse("painel_grupo"),
            {
                "enviar_compra_mp": "1",
                "materia_prima": self.mp.id,
                "cidade_fornecedora": self.cidade.id,
                "quantidade_kg": str(kg),
            },
            follow=True,
        )

    def _comprado(self):
        return sum(
            compra.quantidade_kg
            for compra in CompraMateriaPrima.objects.filter(grupo=self.grupo)
        )

    def test_consumo_estimado_e_a_capacidade_cheia_da_linha(self):
        """400 unidades por rodada x 2 kg por unidade."""
        self.assertEqual(consumo_de_capacidade(self.grupo, self.mp), Decimal("800"))

    def test_teto_e_cento_e_cinquenta_por_cento_do_consumo(self):
        self.assertEqual(limite_de_compra(self.grupo, self.mp, 1)["teto"], Decimal("1200.00"))

    def test_compra_dentro_do_teto_passa_inteira(self):
        self._comprar(1000)

        self.assertEqual(self._comprado(), Decimal("1000"))

    def test_compra_acima_do_teto_e_aparada_e_avisada(self):
        """RN-05: ajusta automaticamente, com alerta -- nao recusa."""
        resposta = self._comprar(5000)

        self.assertEqual(self._comprado(), Decimal("1200.00"))
        self.assertIn("Compra ajustada", resposta.content.decode())

    def test_o_teto_e_por_rodada_nao_por_pedido(self):
        """Tres pedidos de metade nao furam o limite."""
        self._comprar(700)
        self._comprar(700)

        self.assertEqual(self._comprado(), Decimal("1200.00"))

    def test_pedido_com_limite_ja_esgotado_e_recusado(self):
        self._comprar(1200)

        resposta = self._comprar(100)

        self.assertEqual(self._comprado(), Decimal("1200.00"))
        self.assertIn("ja atingido nesta rodada", resposta.content.decode())

    def test_linha_com_mais_maquinas_compra_mais(self):
        """O teto acompanha a fabrica: quem investiu em maquina pode abastecer."""
        linha = CapacidadeProdutoGrupo.objects.get(grupo=self.grupo, produto=self.produto)
        linha.maquinas = 3
        linha.operadores = 6
        linha.save(update_fields=["maquinas", "operadores"])

        self.assertEqual(limite_de_compra(self.grupo, self.mp, 1)["teto"], Decimal("3600.00"))

    def test_maquina_sem_operador_nao_conta_no_teto(self):
        """14.2.3: maquina sem os dois operadores fica inativa, entao nao consome."""
        linha = CapacidadeProdutoGrupo.objects.get(grupo=self.grupo, produto=self.produto)
        linha.maquinas = 3
        linha.operadores = 2
        linha.save(update_fields=["maquinas", "operadores"])

        self.assertEqual(limite_de_compra(self.grupo, self.mp, 1)["teto"], Decimal("1200.00"))

# -*- coding: utf-8 -*-
"""Pool estendido de eventos, e duracao maior que uma rodada.

O 8.4 e a tabela fechada do documento e continua sendo o padrao: turma sem
configuracao explicita sorteia exatamente os seis eventos de la. O pool
estendido e opcional por turma.

O 8.2 ressalva "reversao automatica dos impactos na rodada seguinte (salvo
eventos recorrentes)". O campo `duracao_rodadas` existia e so era lido para
eventos de estado -- um evento percentual de tres rodadas durava uma.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import Cidade, Evento, GameConfig, Jogo, Rodada
from app.services.eventos import (
    eventos_da_rodada,
    fator_percentual,
    sortear_evento,
)


def _rodada(jogo, numero, **extra):
    return Rodada.objects.get_or_create(
        jogo=jogo, numero=numero,
        defaults={"fim": timezone.now() + timedelta(hours=2), **extra},
    )[0]


def _evento(nome, **extra):
    campos = {
        "tipo": "demanda",
        "modo_aplicacao": "percentual",
        "impacto_percentual": 10,
        "probabilidade": 50,
    }
    campos.update(extra)
    return Evento.objects.create(nome=nome, **campos)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PoolEstendidoTest(TestCase):
    def setUp(self):
        self.config = GameConfig.objects.create(numero_rodadas=4)
        self.jogo = Jogo.objects.create(nome="Turma A", config=self.config)
        _rodada(self.jogo, 1)
        self.do_documento = _evento("Boom de consumo")
        self.estendido = _evento("Retracao de consumo", extensao=True,
                                 impacto_percentual=-15)

    def test_sem_a_opcao_so_sorteia_a_tabela_do_documento(self):
        sorteados = set()
        for numero in range(1, 40):
            _rodada(self.jogo, numero)
            evento = sortear_evento(numero, self.jogo.id)
            if evento:
                sorteados.add(evento.nome)

        self.assertEqual(sorteados, {"Boom de consumo"})

    def test_com_a_opcao_o_estendido_entra_no_sorteio(self):
        self.config.eventos_estendidos = True
        self.config.save(update_fields=["eventos_estendidos"])

        sorteados = set()
        for numero in range(1, 60):
            _rodada(self.jogo, numero)
            evento = sortear_evento(numero, self.jogo.id)
            if evento:
                sorteados.add(evento.nome)

        self.assertIn("Retracao de consumo", sorteados)
        self.assertIn("Boom de consumo", sorteados)

    def test_a_opcao_de_uma_turma_nao_vaza_para_a_outra(self):
        self.config.eventos_estendidos = True
        self.config.save(update_fields=["eventos_estendidos"])
        outra = Jogo.objects.create(
            nome="Turma B", config=GameConfig.objects.create(numero_rodadas=4)
        )

        sorteados = set()
        for numero in range(1, 40):
            _rodada(outra, numero)
            evento = sortear_evento(numero, outra.id)
            if evento:
                sorteados.add(evento.nome)

        self.assertEqual(sorteados, {"Boom de consumo"})


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EventoRecorrenteTest(TestCase):
    """8.2: "salvo eventos recorrentes"."""

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=6)
        )
        self.tarifa = _evento(
            "Tarifacao externa", tipo="custo_producao", extensao=True,
            impacto_percentual=15, duracao_rodadas=3,
        )
        _rodada(self.jogo, 1, sorteio_evento=False)
        from app.models import EventoRodada
        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=self.tarifa, manual=True
        )

    def test_o_evento_de_tres_rodadas_vale_nas_tres(self):
        for numero in (1, 2, 3):
            nomes = [e.nome for e in eventos_da_rodada(numero, self.jogo.id)]
            self.assertIn("Tarifacao externa", nomes, f"rodada {numero}")

    def test_e_some_na_quarta(self):
        nomes = [e.nome for e in eventos_da_rodada(4, self.jogo.id)]

        self.assertNotIn("Tarifacao externa", nomes)

    def test_o_custo_continua_majorado_na_segunda_rodada(self):
        fator = fator_percentual(
            eventos_da_rodada(2, self.jogo.id), "custo_producao"
        )

        self.assertEqual(fator, Decimal("1.15"))

    def test_evento_de_uma_rodada_nao_atravessa(self):
        """Os seis do 8.4 tem duracao 1 e nao podem mudar de comportamento."""
        from app.models import EventoRodada
        boom = _evento("Boom de consumo", duracao_rodadas=1)
        EventoRodada.objects.create(
            rodada=2, jogo=self.jogo, evento=boom, manual=True
        )

        nomes = [e.nome for e in eventos_da_rodada(3, self.jogo.id)]

        self.assertNotIn("Boom de consumo", nomes)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SeedDoPoolTest(TestCase):
    def test_o_seed_cria_os_dois_catalogos_e_as_probabilidades_fecham(self):
        from django.core.management import call_command

        call_command("seed_dados_base")

        documento = Evento.objects.filter(manual=False, extensao=False)
        estendidos = Evento.objects.filter(manual=False, extensao=True)
        self.assertEqual(documento.count(), 6)
        self.assertEqual(estendidos.count(), 13)
        # Os seis do 8.4 mantem as probabilidades do documento, que somam
        # 100% -- mesmo com o sorteio uniforme, o dado continua fiel.
        self.assertEqual(sum(e.probabilidade for e in documento), 100)
        # Os estendidos tem a mesma chance entre si, como o sorteio trata.
        self.assertEqual(
            {e.probabilidade for e in estendidos}, {8}
        )

    def test_o_surto_e_o_unico_evento_marcado_como_unico_por_jogo(self):
        from django.core.management import call_command

        call_command("seed_dados_base")

        unicos = list(
            Evento.objects.filter(unico_por_jogo=True).values_list(
                "nome", flat=True
            )
        )
        self.assertEqual(unicos, ["Surto de gripe"])

    def test_ha_eventos_logisticos_favoraveis_ao_grupo(self):
        """O 8.4 so tinha greve e enchente: nenhum alivio logistico."""
        from django.core.management import call_command

        call_command("seed_dados_base")

        favoraveis = Evento.objects.filter(
            tipo="custo_transporte", impacto_percentual__lt=0
        )
        self.assertGreaterEqual(favoraveis.count(), 3)

    def test_o_seed_preserva_o_evento_manual_do_professor(self):
        from django.core.management import call_command

        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        proprio = _evento("Feira regional", manual=True, jogo=jogo)
        Cidade.objects.create(nome="Recife", distancia_km=290, demanda=4000)

        call_command("seed_dados_base")

        self.assertTrue(Evento.objects.filter(id=proprio.id).exists())


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class BloqueioDeProducaoTest(TestCase):
    """O fechamento tambem para a fabrica, nao so a tela.

    `bloqueio_producao` era verificado apenas no registro da ordem pelo
    painel. A ordem registrada antes do evento entrar era produzida no
    fechamento assim mesmo: a tela dizia que a producao estava bloqueada e
    o resultado mostrava producao.
    """

    def setUp(self):
        from app.models import (
            CapacidadeProdutoGrupo,
            EstoqueMateriaPrima,
            MateriaPrima,
            Producao,
            Produto,
            ComposicaoProduto,
        )

        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        from app.models import Grupo
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=10
        )
        mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("1")
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=mp,
            quantidade_por_unidade=Decimal("1"),
        )
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=mp, quantidade_kg=Decimal("10000")
        )
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo, produto=self.produto, maquinas=15,
            operadores=30, minutos_por_maquina=400,
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=100,
        )
        _rodada(self.jogo, 1)

    def _executar(self, eventos):
        from app.services.producao import executar_producao

        return executar_producao(grupo=self.grupo, rodada=1, eventos=eventos)

    def test_sem_evento_a_ordem_e_produzida(self):
        from app.models import Producao

        self._executar([])

        ordem = Producao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(ordem.quantidade_produzida, 100)

    def test_o_apagao_zera_a_producao_da_rodada(self):
        from app.models import Producao

        apagao = _evento(
            "Apagao na regiao", tipo="greve", modo_aplicacao="estado",
            efeito_estado="bloqueio_producao", impacto_percentual=0,
            extensao=True,
        )

        _, ajustes = self._executar([apagao])

        ordem = Producao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(ordem.quantidade_produzida, 0)
        self.assertEqual(ajustes[0]["limitador"], "produção bloqueada por evento")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SorteioUniformeComCooldownTest(TestCase):
    """Decisao de 14/10/2026: mesma chance para todos, e cooldown de verdade.

    Antes o sorteio usava os pesos do 8.4 e so PENALIZAVA o evento recente,
    para nao achatar pesos distintos. Com os pesos iguais por decisao, a
    objecao caiu e o cooldown duro passou a ser a ferramenta certa.
    """

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=12)
        )
        self.eventos = [
            _evento(f"Evento {letra}", probabilidade=prob)
            for letra, prob in zip("ABCD", (70, 10, 10, 10))
        ]

    def _sortear_ate(self, ultima):
        saidos = []
        for numero in range(1, ultima + 1):
            _rodada(self.jogo, numero)
            evento = sortear_evento(numero, self.jogo.id)
            if evento:
                saidos.append(evento.nome)
        return saidos

    def test_a_probabilidade_gravada_nao_pesa_mais_no_sorteio(self):
        """O evento de peso 70 nao pode dominar: a chance e igual."""
        from app.models import EventoRodada

        contagem = {e.nome: 0 for e in self.eventos}
        for _ in range(40):
            EventoRodada.objects.all().delete()
            evento = sortear_evento(1, self.jogo.id)
            contagem[evento.nome] += 1

        # com peso, "Evento A" levaria ~70%; uniforme, ~25%
        self.assertLess(contagem["Evento A"], 28)

    def test_o_evento_que_saiu_fica_de_fora_pelas_rodadas_do_cooldown(self):
        from unittest.mock import patch

        from app.parametros import COOLDOWN_EVENTO_RODADAS

        # o evento duplo e sorteado a parte e consumiria o pool; aqui o que
        # se mede e o cooldown.
        with patch("app.services.eventos.CHANCE_EVENTO_DUPLO", 0):
            saidos = self._sortear_ate(COOLDOWN_EVENTO_RODADAS + 1)

        self.assertEqual(len(set(saidos)), len(saidos))

    def test_pool_menor_que_o_cooldown_nao_deixa_a_rodada_sem_evento(self):
        """8.2: "sempre haja um evento ativo"."""
        from unittest.mock import patch

        Evento.objects.exclude(nome="Evento A").delete()

        with patch("app.services.eventos.CHANCE_EVENTO_DUPLO", 0):
            saidos = self._sortear_ate(4)

        self.assertEqual(saidos, ["Evento A"] * 4)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EventoUnicoPorJogoTest(TestCase):
    """O surto acontece no maximo uma vez por turma.

    Na segunda vez a equipe ja conhece preco e efeito exatos: deixa de ser
    decisao sob incerteza e vira conta.
    """

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=12)
        )
        self.unico = _evento("Surto de gripe", unico_por_jogo=True)
        self.comum = _evento("Boom de consumo")

    def test_depois_de_sair_uma_vez_nao_volta(self):
        from app.models import EventoRodada

        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=self.unico, manual=False
        )

        saidos = set()
        for numero in range(2, 20):
            _rodada(self.jogo, numero)
            evento = sortear_evento(numero, self.jogo.id)
            if evento:
                saidos.add(evento.nome)

        self.assertNotIn("Surto de gripe", saidos)
        self.assertIn("Boom de consumo", saidos)

    def test_a_restricao_e_por_turma_e_nao_global(self):
        from app.models import EventoRodada

        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=self.unico, manual=False
        )
        outra = Jogo.objects.create(
            nome="Turma B", config=GameConfig.objects.create(numero_rodadas=12)
        )
        Evento.objects.filter(nome="Boom de consumo").delete()

        _rodada(outra, 1)
        evento = sortear_evento(1, outra.id)

        self.assertEqual(evento.nome, "Surto de gripe")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EventoDuploTest(TestCase):
    """RN-10: "ate 2 eventos aleatorios simultaneos", em 30% das rodadas."""

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=12)
        )
        for letra in "ABCDEFGH":
            _evento(f"Evento {letra}")

    def _quantidade_na_rodada(self, numero):
        from app.models import EventoRodada

        return EventoRodada.objects.filter(
            jogo=self.jogo, rodada=numero
        ).count()

    def test_as_vezes_a_rodada_sai_com_dois_eventos(self):
        from app.models import EventoRodada

        duplas = 0
        for tentativa in range(60):
            EventoRodada.objects.all().delete()
            _rodada(self.jogo, 1)
            sortear_evento(1, self.jogo.id)
            if self._quantidade_na_rodada(1) == 2:
                duplas += 1

        self.assertGreater(duplas, 0, "nunca saiu dupla em 60 tentativas")
        self.assertLess(duplas, 45, "saiu dupla quase sempre")

    def test_nunca_passa_de_dois(self):
        from app.models import EventoRodada

        for tentativa in range(40):
            EventoRodada.objects.all().delete()
            _rodada(self.jogo, 1)
            sortear_evento(1, self.jogo.id)
            self.assertLessEqual(self._quantidade_na_rodada(1), 2)

    def test_com_evento_manual_o_sorteio_so_acrescenta_um(self):
        """RN-10 limita a rodada a dois; o do professor ja conta."""
        from app.models import EventoRodada

        manual = _evento("Feira regional", manual=True, jogo=self.jogo)
        for tentativa in range(30):
            EventoRodada.objects.all().delete()
            _rodada(self.jogo, 1)
            EventoRodada.objects.create(
                rodada=1, jogo=self.jogo, evento=manual, manual=True
            )
            sortear_evento(1, self.jogo.id)
            self.assertLessEqual(self._quantidade_na_rodada(1), 2)

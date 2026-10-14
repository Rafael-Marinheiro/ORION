"""Os eventos do 8.4: manchete, probabilidade e sorteio ponderado."""

from collections import Counter
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Evento, EventoRodada, Grupo, Rodada, User
from app.views import sortear_evento


class SeedDosEventosTest(TestCase):
    """O catalogo do documento, que o pool estendido nao pode contaminar.

    Desde 07/10/2026 o banco tambem guarda eventos fora do 8.4
    (`extensao=True`), sorteados so pela turma que os ligar. Estas asercoes
    continuam valendo para o catalogo do documento, e sao justamente o que
    impede o pool de alterar as probabilidades de la.
    """

    def setUp(self):
        call_command("seed_dados_base")

    def test_sao_exatamente_os_seis_do_documento(self):
        nomes = set(
            Evento.objects.filter(extensao=False).values_list("nome", flat=True)
        )

        self.assertEqual(
            nomes,
            {
                "Greve de caminhoneiros",
                "Crise de abastecimento",
                "Boom de consumo",
                "Enchentes nas regiões",
                "Estabilidade econômica",
                "Superoferta agrícola",
            },
        )

    def test_probabilidades_somam_cem_por_cento(self):
        """8.4: "A soma total das probabilidades e de 100%"."""
        total = sum(
            Decimal(str(p))
            for p in Evento.objects.filter(extensao=False).values_list(
                "probabilidade", flat=True
            )
        )

        self.assertEqual(total, Decimal("100"))

    def test_cada_evento_tem_manchete(self):
        sem_manchete = Evento.objects.filter(frase_indicativa="").values_list("nome", flat=True)

        self.assertEqual(list(sem_manchete), [])

    def test_manchete_e_diferente_da_descricao(self):
        """Sao colunas distintas no 8.4: uma e noticia, a outra e mecanismo."""
        for evento in Evento.objects.all():
            self.assertNotEqual(evento.frase_indicativa, evento.descricao, evento.nome)

    def test_probabilidades_do_documento(self):
        esperado = {
            "Greve de caminhoneiros": Decimal("15"),
            "Crise de abastecimento": Decimal("20"),
            "Boom de consumo": Decimal("20"),
            "Enchentes nas regiões": Decimal("15"),
            "Estabilidade econômica": Decimal("15"),
            "Superoferta agrícola": Decimal("15"),
        }
        obtido = {
            e.nome: Decimal(str(e.probabilidade))
            for e in Evento.objects.filter(extensao=False)
        }

        self.assertEqual(obtido, esperado)


class SorteioIgualitarioTest(TestCase):
    """Decisao de 14/10/2026: todo evento elegivel tem a mesma chance.

    Ate entao o sorteio usava os pesos do 8.4. A tabela continua gravada no
    banco -- o dado segue fiel ao documento --, mas nao pesa mais no
    resultado. Pendente de ratificacao do autor da especificacao.
    """

    def test_a_probabilidade_gravada_nao_decide_mais_o_sorteio(self):
        from unittest.mock import patch

        Evento.objects.all().delete()
        raro = Evento.objects.create(
            nome="Raro", tipo="demanda", impacto_percentual=1, probabilidade=1
        )
        comum = Evento.objects.create(
            nome="Comum", tipo="demanda", impacto_percentual=1, probabilidade=99
        )

        contagem = Counter()
        with patch("app.services.eventos.COOLDOWN_EVENTO_RODADAS", 0),                 patch("app.services.eventos.CHANCE_EVENTO_DUPLO", 0):
            for rodada in range(1, 201):
                EventoRodada.objects.all().delete()
                contagem[sortear_evento(rodada).nome] += 1

        # com peso, "Comum" levaria 99%; com chance igual, perto de 50%
        self.assertGreater(contagem[raro.nome], 60)
        self.assertGreater(contagem[comum.nome], 60)

    def test_sem_probabilidade_configurada_nao_trava(self):
        Evento.objects.create(
            nome="Sem peso", tipo="demanda", impacto_percentual=1, probabilidade=0
        )

        self.assertIsNotNone(sortear_evento(1))


class BoletimNaTelaTest(TestCase):
    def test_manchete_aparece_para_o_aluno(self):
        user = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100"))
        grupo.membros.add(user)
        rodada = Rodada.objects.create(
            numero=1, fim=timezone.now() + timezone.timedelta(hours=1)
        )
        evento = Evento.objects.create(
            nome="Greve de caminhoneiros",
            frase_indicativa="O país enfrenta uma greve geral no setor de transporte rodoviário.",
            tipo="custo_transporte",
            impacto_percentual=30,
            probabilidade=15,
        )
        EventoRodada.objects.create(rodada=rodada.numero, jogo=None, evento=evento)
        self.client.force_login(user)

        html = self.client.get(reverse("ajuda")).content.decode()

        self.assertIn("O país enfrenta uma greve geral", html)
        self.assertIn("o-boletim", html)


class VariedadeDeEventosTest(TestCase):
    """O evento que saiu fica BLOQUEADO por algumas rodadas.

    Ate 14/10/2026 ele apenas perdia peso, nunca era proibido: cooldown
    duro achata pesos distintos -- com 60/30/10, bloquear duas rodadas os
    transforma em 33/33/33. A decisao de igualar as chances tirou o chao
    dessa objecao, e o bloqueio passou a ser o comportamento pedido.
    """

    def setUp(self):
        Evento.objects.all().delete()
        self.primeiro = Evento.objects.create(
            nome="Primeiro", tipo="demanda", impacto_percentual=5, probabilidade=80
        )
        self.segundo = Evento.objects.create(
            nome="Segundo", tipo="demanda", impacto_percentual=5, probabilidade=20
        )

    def test_o_evento_da_rodada_anterior_nao_se_repete(self):
        from unittest.mock import patch

        EventoRodada.objects.create(rodada=1, evento=self.primeiro)

        with patch("app.services.eventos.CHANCE_EVENTO_DUPLO", 0):
            for _ in range(40):
                EventoRodada.objects.filter(rodada__gt=1).delete()
                self.assertEqual(sortear_evento(2).id, self.segundo.id)

    def test_passado_o_cooldown_ele_volta_a_ser_possivel(self):
        from unittest.mock import patch

        from app.parametros import COOLDOWN_EVENTO_RODADAS

        EventoRodada.objects.create(rodada=1, evento=self.primeiro)
        fora_do_alcance = 1 + COOLDOWN_EVENTO_RODADAS + 1

        voltou = 0
        with patch("app.services.eventos.CHANCE_EVENTO_DUPLO", 0):
            for _ in range(40):
                EventoRodada.objects.filter(rodada__gt=1).delete()
                if sortear_evento(fora_do_alcance).id == self.primeiro.id:
                    voltou += 1

        self.assertGreater(voltou, 0)

    def test_lacuna_de_rodada_nao_encurta_a_distancia(self):
        """Rodada sem evento nao pode fazer um evento antigo parecer recente."""
        from unittest.mock import patch

        from app.services.eventos import _em_cooldown
        from app.parametros import COOLDOWN_EVENTO_RODADAS

        EventoRodada.objects.create(rodada=2, evento=self.primeiro)

        # a distancia sai da rodada corrente, nao da ultima com evento
        dentro = 2 + COOLDOWN_EVENTO_RODADAS
        fora = dentro + 1
        self.assertIn(self.primeiro.id, _em_cooldown(dentro, None))
        self.assertNotIn(self.primeiro.id, _em_cooldown(fora, None))

    def test_com_um_unico_evento_ele_sai_mesmo_em_cooldown(self):
        """8.2: "sempre haja um evento ativo"."""
        self.segundo.delete()
        EventoRodada.objects.create(rodada=1, evento=self.primeiro)

        self.assertEqual(sortear_evento(2).id, self.primeiro.id)

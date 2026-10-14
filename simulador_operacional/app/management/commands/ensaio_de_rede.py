# -*- coding: utf-8 -*-
"""11.1 -- ensaio de carga antes da aula.

O 11.1 exige que o fechamento ocorra "no momento exato do prazo-limite", e
o painel atualiza o contador a cada segundo. Nada disso foi medido na rede
da instituicao com uma turma inteira ligada ao mesmo tempo, e o risco nao e
teorico: se o servidor nao aguentar a rajada do ultimo minuto, a equipe que
submeter em cima do prazo perde a rodada por lentidao, nao por decisao.

Este comando NAO substitui o ensaio com alunos reais -- so ele mede a rede
da instituicao. O que ele faz e tirar a medicao do improviso: roda a mesma
rajada que uma turma produz, mede o que o servidor devolve, e diz se o
fechamento cabe na janela do cron.

Uso:
    python manage.py ensaio_de_rede --equipes 12 --repeticoes 5
"""

import statistics
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.test import Client
from django.utils import timezone

from app.models import CEOGrupoRodada, Grupo, Jogo, Rodada, User


class Command(BaseCommand):
    help = "Mede a resposta do painel e do fechamento sob a carga de uma turma."

    def add_arguments(self, parser):
        parser.add_argument(
            "--turma", default=None,
            help="Nome da turma a medir. Sem isto, usa a de rodada mais recente.",
        )
        parser.add_argument("--equipes", type=int, default=0,
                            help="Limita quantas equipes entram na medicao.")
        parser.add_argument("--repeticoes", type=int, default=3,
                            help="Quantas vezes cada equipe abre o painel.")
        parser.add_argument(
            "--limite-ms", type=float, default=1000.0,
            help="Tempo acima do qual a tela e considerada lenta (ms).",
        )

    def handle(self, *args, **opcoes):
        jogo = self.escolher_turma(opcoes["turma"])
        if jogo is None:
            self.stderr.write("Nenhuma turma encontrada para medir.")
            return

        grupos = list(Grupo.objects.filter(jogo=jogo).select_related("lider"))
        if opcoes["equipes"]:
            grupos = grupos[: opcoes["equipes"]]
        if not grupos:
            self.stderr.write(f'A turma "{jogo.nome}" nao tem equipes.')
            return

        rodada = (
            Rodada.objects.filter(jogo=jogo).order_by("-numero").first()
        )
        self.stdout.write(
            f'Turma "{jogo.nome}": {len(grupos)} equipes, '
            f'rodada {rodada.numero if rodada else "-"}'
        )

        tempos = self.medir_painel(grupos, rodada, opcoes["repeticoes"])
        if not tempos:
            self.stderr.write(
                "Nenhuma equipe tem CEO definido na rodada; nada a medir."
            )
            return

        self.relatar_painel(tempos, opcoes["limite_ms"])
        self.relatar_fechamento(jogo, len(grupos))

    def escolher_turma(self, nome):
        if nome:
            return Jogo.objects.filter(nome=nome).first()
        ultima = Rodada.objects.exclude(jogo=None).order_by("-id").first()
        return ultima.jogo if ultima else Jogo.objects.order_by("-id").first()

    def medir_painel(self, grupos, rodada, repeticoes):
        """Cada CEO abre o painel, como no minuto final da rodada."""
        tempos = []
        for grupo in grupos:
            ceo = self.ceo_do_grupo(grupo, rodada)
            if ceo is None:
                continue
            cliente = Client()
            cliente.force_login(ceo)
            for _ in range(repeticoes):
                reset_queries()
                inicio = time.perf_counter()
                resposta = cliente.get("/painel/")
                decorrido = (time.perf_counter() - inicio) * 1000
                tempos.append({
                    "grupo": grupo.nome,
                    "ms": decorrido,
                    "status": resposta.status_code,
                    "consultas": len(connection.queries),
                })
        return tempos

    def ceo_do_grupo(self, grupo, rodada):
        if rodada:
            vinculo = CEOGrupoRodada.objects.filter(
                grupo=grupo, rodada=rodada.numero
            ).select_related("usuario").first()
            if vinculo:
                return vinculo.usuario
        if grupo.lider:
            return grupo.lider
        return grupo.membros.filter(tipo_usuario="lider_grupo").first()

    def relatar_painel(self, tempos, limite_ms):
        valores = sorted(t["ms"] for t in tempos)
        consultas = [t["consultas"] for t in tempos]
        erros = [t for t in tempos if t["status"] >= 400]
        lentos = [t for t in tempos if t["ms"] > limite_ms]

        def percentil(fracao):
            if not valores:
                return 0.0
            indice = min(int(len(valores) * fracao), len(valores) - 1)
            return valores[indice]

        self.stdout.write("")
        self.stdout.write("Painel do grupo")
        self.stdout.write(f"  amostras .......... {len(valores)}")
        self.stdout.write(f"  mediana ........... {statistics.median(valores):.0f} ms")
        self.stdout.write(f"  p95 ............... {percentil(0.95):.0f} ms")
        self.stdout.write(f"  pior .............. {max(valores):.0f} ms")
        self.stdout.write(
            f"  consultas SQL ..... {statistics.median(consultas):.0f} "
            f"(pior {max(consultas)})"
        )
        if erros:
            self.stdout.write(
                self.style.ERROR(f"  RESPOSTAS COM ERRO: {len(erros)}")
            )
        if lentos:
            self.stdout.write(
                self.style.WARNING(
                    f"  acima de {limite_ms:.0f} ms: {len(lentos)} de {len(valores)}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"  nenhuma carga acima de {limite_ms:.0f} ms")
            )

    def relatar_fechamento(self, jogo, total_grupos):
        """O fechamento precisa caber na janela do cron (1 minuto)."""
        from app.management.commands.fechar_rodadas import Command as Fechar

        rodada = Rodada.objects.filter(jogo=jogo, fechada=False).first()
        self.stdout.write("")
        self.stdout.write("Fechamento da rodada")
        if rodada is None:
            self.stdout.write(
                "  nenhuma rodada aberta: medicao do fechamento pulada."
            )
            self.stdout.write(
                "  abra uma rodada de ensaio e rode de novo para medir."
            )
            return

        original = rodada.fim
        rodada.fim = timezone.now() - timedelta(seconds=1)
        rodada.save(update_fields=["fim"])
        inicio = time.perf_counter()
        try:
            Fechar().handle()
        finally:
            decorrido = time.perf_counter() - inicio
            if not Rodada.objects.get(id=rodada.id).fechada:
                Rodada.objects.filter(id=rodada.id).update(fim=original)

        self.stdout.write(
            f"  {total_grupos} equipes processadas em {decorrido:.1f} s"
        )
        if decorrido > 55:
            self.stdout.write(
                self.style.ERROR(
                    "  NAO CABE na janela de 1 minuto do cron: a execucao "
                    "seguinte comecaria antes desta terminar."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  cabe na janela de 1 minuto do cron")
            )

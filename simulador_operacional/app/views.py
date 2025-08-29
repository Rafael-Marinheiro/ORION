from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from .serializers import (
    GrupoSerializer,
    ResultadoFinanceiroSerializer,
    DecisaoSerializer,
    DistribuicaoSerializer,
    EventoSerializer,
    EventoRodadaSerializer,
    RodadaSerializer,
    CidadeSerializer,
    GameConfigSerializer,
    JogoSerializer,
    InvestimentoSerializer,
    FornecedorSerializer,
    PedidoMateriaPrimaSerializer,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from .forms import (
    CustomUserCreationForm,
    DecisaoForm,
    DistribuicaoForm,
    RodadaForm,
    GrupoForm,
    ResultadoFilterForm,
    MembroFormSet,
    GrupoCadastroForm,
    FornecedorForm,
    PedidoMateriaPrimaForm,
    InvestimentoCapacidadeForm,
)
from .models import (
    GameConfig,
    Grupo,
    Decisao,
    Distribuicao,
    Cidade,
    ResultadoFinanceiro,
    Evento,
    EventoRodada,
    Rodada,
    Jogo,
    Investimento,
    User,
    Fornecedor,
    PedidoMateriaPrima,
    LinhaProducao,
)
from .services.economia_service import (
    calcular_custo_total,
    calcular_demanda,
    calcular_preco_final,
)
from .services.penalidade_service import aplicar_penalidade
from .services.materias_primas import calcular_custo_logistico
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.pdfgen import canvas
import random
import logging
from math import log
from django.utils import timezone
from django.db.models import Sum
from collections import defaultdict

logger = logging.getLogger('agendamentos')


def sortear_eventos(rodada):
    registros = EventoRodada.objects.filter(rodada=rodada)
    if registros.exists():
        return [r.evento for r in registros]

    eventos = list(Evento.objects.all())
    if not eventos:
        return []

    escolhidos = []
    total = sum(e.probabilidade for e in eventos)
    for _ in range(2):
        r = random.uniform(0, total)
        acum = 0
        escolha = eventos[-1]
        for e in eventos:
            acum += e.probabilidade
            if r <= acum:
                escolha = e
                break
        if escolha not in escolhidos:
            escolhidos.append(escolha)

    for evento in escolhidos:
        EventoRodada.objects.create(rodada=rodada, evento=evento)
    if escolhidos:
        logger.info('Eventos sorteados para rodada %s: %s', rodada, ', '.join(e.nome for e in escolhidos))
    else:
        logger.info('Nenhum evento sorteado para rodada %s', rodada)
    return escolhidos


def calcular_ranking():
    grupos = Grupo.objects.annotate(
        total_lucro=Sum('resultados__lucro'),
        total_penalidades=Sum('resultados__penalidades'),
    )

    totais_por_rodada = {
        d['rodada']: d['total']
        for d in Distribuicao.objects.values('rodada').annotate(
            total=Sum('vendas_realizadas')
        )
    }

    vendas_por_grupo = Distribuicao.objects.values('grupo_id', 'rodada').annotate(
        total=Sum('vendas_realizadas')
    )

    shares = defaultdict(list)
    for dado in vendas_por_grupo:
        total_rodada = totais_por_rodada.get(dado['rodada']) or 0
        share = dado['total'] / total_rodada if total_rodada else 0
        shares[dado['grupo_id']].append(share)

    ranking = []
    for g in grupos:
        market_share_medio = (
            sum(shares[g.id]) / len(shares[g.id]) if shares[g.id] else 0
        )
        ultimo_rf = g.resultados.order_by('-rodada').first()
        saldo_caixa = ultimo_rf.saldo_caixa if ultimo_rf else g.capital
        g.market_share_medio = market_share_medio
        g.saldo_caixa_final = saldo_caixa
        g.total_penalidades = g.total_penalidades or 0
        ranking.append(g)

    return sorted(
        ranking,
        key=lambda g: (
            -(float(g.total_lucro or 0)),
            -float(g.market_share_medio),
            -(float(g.saldo_caixa_final or 0)),
            float(g.total_penalidades or 0),
        ),
    )

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if getattr(user, "tipo_usuario", None) == "gamemaster" or user.is_superuser:
            return reverse_lazy("game_config")
        return reverse_lazy("painel_grupo")

class HomeView(TemplateView):
    template_name = 'home.html'
    # login_url = '/accounts/login/'

class AjudaView(TemplateView):
    """Página com tutoriais rápidos e perguntas frequentes."""
    template_name = 'ajuda.html'

@login_required
def home(request):
    return render(request, 'home.html')


class RegisterView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'registration/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def test_func(self):
        return getattr(self.request.user, 'tipo_usuario', '') == 'gamemaster'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


from django.views.generic import UpdateView, FormView
from .models import GameConfig
from .forms import GameConfigForm


class GameConfigUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = GameConfig
    form_class = GameConfigForm
    template_name = 'game_config_form.html'
    success_url = reverse_lazy('home')


    permission_required = 'app.change_gameconfig'

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_object(self, queryset=None):
        obj, _ = GameConfig.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        form.instance.produtos_habilitados = form.cleaned_data["produtos_habilitados"]
        form.instance.regra_eventos = form.cleaned_data.get("regra_eventos", {})
        return super().form_valid(form)


class RodadaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Rodada
    form_class = RodadaForm
    template_name = 'rodada_form.html'
    success_url = reverse_lazy('home')

    permission_required = 'app.add_rodada'

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class RankingView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'ranking.html'
    model = Grupo
    context_object_name = 'grupos'
    permission_required = 'app.view_resultadofinanceiro'

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_queryset(self):
        return calcular_ranking()


class PainelGrupoView(LoginRequiredMixin, TemplateView):
    template_name = 'painel_grupo.html'

    def calcular_capacidade_producao(self, grupo):
        maquinas_operacionais = min(grupo.maquinas, grupo.trabalhadores // 2)
        return maquinas_operacionais * grupo.capacidade_maquina

    def get(self, request, *args, **kwargs):
        grupo = request.user.grupos.first()
        if not grupo:
            messages.error(
                request,
                "Você ainda não foi alocado a um grupo. Procure o GameMaster.",
            )
            return redirect("home")
        membros = grupo.membros.count()
        if membros < 3 or membros > 6:
            messages.error(
                request, "O grupo deve possuir entre 3 e 6 participantes."
            )
            return redirect("home")
        form = DecisaoForm()
        envio_form = DistribuicaoForm()
        fornecedor_form = FornecedorForm()
        pedido_form = PedidoMateriaPrimaForm()
        decisoes = grupo.decisoes.all()
        envios = grupo.envios.select_related("cidade").all()
        resultados = grupo.resultados.all()
        produtos = grupo.produtos.prefetch_related("materias_primas").all()
        fornecedores = Fornecedor.objects.all()
        pedidos = grupo.pedidos_materia_prima.select_related("fornecedor").all()
        ultima_vista = request.session.get("ultima_rodada_vista", 0)
        nova = resultados.order_by("-rodada").first()
        notificacao = None
        if nova and nova.rodada > ultima_vista:
            notificacao = f"Resultados da rodada {nova.rodada} disponíveis."
            request.session["ultima_rodada_vista"] = nova.rodada
        ultima = grupo.decisoes.first()
        rodada_atual = ultima.rodada + 1 if ultima else 1
        eventos = [er.evento for er in EventoRodada.objects.filter(rodada=rodada_atual)]
        perda_key = f'perda_aplicada_{rodada_atual}'
        for evento in eventos:
            if evento.tipo == 'perda_estoque' and not request.session.get(perda_key):
                perda = int(grupo.estoque * evento.impacto_percentual / 100)
                if perda:
                    grupo.estoque -= perda
                    grupo.save()
                    messages.warning(request, f'Perda de estoque de {perda} unidades.')
                request.session[perda_key] = True
        capacidade_total = self.calcular_capacidade_producao(grupo)
        alerta = None
        if grupo.estoque < capacidade_total * 0.2:
            alerta = 'Risco de ruptura de estoque'
        elif grupo.estoque > capacidade_total:
            alerta = 'Risco de desperdício de estoque'
        produtos = grupo.produtos.prefetch_related("materias_primas").all()
        return render(request, self.template_name, {
            'grupo': grupo,
            'decisoes': decisoes,
            'form': form,
            'envio_form': envio_form,
            'fornecedor_form': fornecedor_form,
            'pedido_form': pedido_form,
            'envios': envios,
            'fornecedores': fornecedores,
            'pedidos': pedidos,
            'resultados': resultados,
            'alerta': alerta,
            'eventos': eventos,
            'notificacao': notificacao,
            'produtos': produtos,
        })

    def post(self, request, *args, **kwargs):
        grupo = request.user.grupos.first()
        if not grupo:
            messages.error(
                request,
                "Você ainda não foi alocado a um grupo. Procure o GameMaster.",
            )
            return redirect("home")
        membros = grupo.membros.count()
        if membros < 3 or membros > 6:
            messages.error(
                request, "O grupo deve possuir entre 3 e 6 participantes."
            )
            return redirect("home")
        if 'enviar_decisao' in request.POST:
            if request.user.tipo_usuario != 'lider_grupo' and not request.user.is_staff:
                messages.error(request, 'Apenas o Aluno CEO pode enviar decisões')
                return redirect('painel_grupo')
            form = DecisaoForm(request.POST)
            if form.is_valid():
                decisao = form.save(commit=False)
                decisao.grupo = grupo
                capacidade_total = self.calcular_capacidade_producao(grupo)
                if decisao.quantidade > capacidade_total:
                    decisao.quantidade = capacidade_total
                    messages.warning(
                        request,
                        'Quantidade de produção ajustada ao limite operacional.',
                    )
                if Decisao.objects.filter(grupo=grupo, rodada=decisao.rodada).exists():
                    messages.error(request, 'Decisão já enviada para esta rodada')
                    return redirect('painel_grupo')
                if Rodada.objects.filter(numero=decisao.rodada, fim__lt=timezone.now()).exists() or Rodada.objects.filter(numero=decisao.rodada, fechada=True).exists():
                    messages.error(request, 'Prazo encerrado para esta rodada')
                    return redirect('painel_grupo')

                eventos = [er.evento for er in EventoRodada.objects.filter(rodada=decisao.rodada)]
                perda_key = f'perda_aplicada_{decisao.rodada}'
                perda_aplicada = False
                for evento in eventos:
                    if evento.tipo == 'perda_estoque' and not request.session.get(perda_key):
                        perda = int(grupo.estoque * evento.impacto_percentual / 100)
                        if perda:
                            grupo.estoque -= perda
                            grupo.save()
                            messages.warning(request, f'Perda de estoque de {perda} unidades.')
                        perda_aplicada = True
                    if evento.tipo == 'greve':
                        messages.error(request, 'Greve em andamento. Produção paralisada.')
                        return redirect('painel_grupo')
                if perda_aplicada:
                    request.session[perda_key] = True
                custo_prod = Decimal(decisao.quantidade) * Decimal('5')
                for evento in eventos:
                    if evento.tipo == 'custo_producao':
                        custo_prod *= Decimal(1 + evento.impacto_percentual / 100)
                decisao.save()
                if grupo.capital < custo_prod:
                    penalidade = custo_prod * Decimal('0.02')
                    aplicar_penalidade(grupo, decisao.rodada, penalidade)
                    messages.error(request, 'Capital insuficiente para produção. Penalidade aplicada.')
                else:
                    if grupo.materia_prima < decisao.quantidade:
                        messages.error(request, 'Matéria-prima insuficiente para produção.')
                        return redirect('painel_grupo')
                    grupo.capital -= custo_prod
                    grupo.materia_prima -= decisao.quantidade
                    grupo.estoque += decisao.quantidade
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo, rodada=decisao.rodada
                    )
                    rf.custos += custo_prod
                    rf.saldo_caixa = grupo.capital
                    rf.lucro = rf.receita - rf.custos
                    rf.save()
                    messages.success(request, 'Decisão registrada')
                    return redirect('painel_grupo')
        elif 'enviar_envio' in request.POST:
            if request.user.tipo_usuario != 'lider_grupo' and not request.user.is_staff:
                messages.error(request, 'Apenas o Aluno CEO pode enviar distribuições')
                return redirect('painel_grupo')
            envio_form = DistribuicaoForm(request.POST)
            if envio_form.is_valid():
                envio = envio_form.save(commit=False)
                envio.grupo = grupo
                if Distribuicao.objects.filter(grupo=grupo, rodada=envio.rodada).exists():
                    messages.error(request, 'Envio já realizado nesta rodada')
                    return redirect('painel_grupo')
                if Rodada.objects.filter(numero=envio.rodada, fim__lt=timezone.now()).exists() or Rodada.objects.filter(numero=envio.rodada, fechada=True).exists():
                    messages.error(request, 'Prazo encerrado para esta rodada')
                    return redirect('painel_grupo')

                eventos = [er.evento for er in EventoRodada.objects.filter(rodada=envio.rodada)]
                perda_key = f'perda_aplicada_{envio.rodada}'
                perda_aplicada = False
                for evento in eventos:
                    if evento.tipo == 'perda_estoque' and not request.session.get(perda_key):
                        perda = int(grupo.estoque * evento.impacto_percentual / 100)
                        if perda:
                            grupo.estoque -= perda
                            grupo.save()
                            messages.warning(request, f'Perda de estoque de {perda} unidades.')
                        perda_aplicada = True
                if perda_aplicada:
                    request.session[perda_key] = True
                if envio.quantidade > grupo.estoque:
                    penalidade = envio.quantidade * envio.preco_unitario * Decimal('0.05')
                    aplicar_penalidade(grupo, envio.rodada, penalidade)
                    messages.error(request, 'Estoque insuficiente. Penalidade aplicada.')
                else:
                    custo = calcular_custo_total(envio.quantidade, envio.cidade.distancia_km, eventos)
                    envio.custo_transporte = custo

                    # calcular fator de marketing baseado nos investimentos da cidade
                    total_marketing = (
                        Investimento.objects.filter(
                            grupo=grupo,
                            categoria='marketing',
                            cidade=envio.cidade,
                        ).aggregate(total=Sum('valor'))['total']
                        or 0
                    )
                    fator_marketing = Decimal('1')
                    if total_marketing > 0:
                        total_marketing = min(total_marketing, Decimal('10000'))
                        fator_marketing = Decimal(
                            1 + (log(float(total_marketing)) / log(10000)) * 0.2
                        )
                        fator_marketing = min(fator_marketing, Decimal('1.2'))

                    demanda_ajustada = calcular_demanda(
                        envio.cidade.demanda, fator_marketing, eventos
                    )
                    vendas_realizadas = min(envio.quantidade, demanda_ajustada)
                    envio.vendas_realizadas = vendas_realizadas
                    envio.fator_marketing = fator_marketing
                    preco_final = calcular_preco_final(
                        envio.preco_unitario,
                        Decimal('0'),
                        fator_marketing,
                        eventos,
                    )
                    envio.qualidade = Decimal('1')
                    envio.save()

                    grupo.estoque -= envio.quantidade
                    if vendas_realizadas < envio.quantidade:
                        messages.warning(
                            request,
                            'Parte da remessa não foi vendida por falta de demanda.',
                        )
                    receita = vendas_realizadas * preco_final
                    grupo.capital += receita - custo
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo, rodada=envio.rodada
                    )
                    rf.receita += receita
                    rf.custos += custo
                    rf.lucro = rf.receita - rf.custos
                    rf.saldo_caixa = grupo.capital
                    rf.save()
                    messages.success(request, 'Distribuição registrada')
                    return redirect('painel_grupo')
        elif 'registrar_fornecedor' in request.POST:
            fornecedor_form = FornecedorForm(request.POST)
            if fornecedor_form.is_valid():
                fornecedor_form.save()
                messages.success(request, 'Fornecedor registrado')
                return redirect('painel_grupo')
        elif 'registrar_pedido' in request.POST:
            pedido_form = PedidoMateriaPrimaForm(request.POST)
            if pedido_form.is_valid():
                pedido = pedido_form.save(commit=False)
                pedido.grupo = grupo
                pedido.prazo_entrega = pedido.fornecedor.prazo_entrega
                ultima = grupo.decisoes.first()
                rodada_atual = ultima.rodada + 1 if ultima else 1
                remessa = grupo.envios.filter(
                    cidade=pedido.fornecedor.cidade, rodada=rodada_atual
                ).exists()
                valor_pedido = pedido.quantidade * pedido.custo_unitario
                pedido.custo_logistico = calcular_custo_logistico(
                    pedido.fornecedor.cidade.distancia_km,
                    valor_pedido,
                    remessa_simultanea=remessa,
                )
                total = valor_pedido + pedido.custo_logistico
                if grupo.capital < total:
                    messages.error(
                        request, 'Capital insuficiente para compra de matéria-prima'
                    )
                    return redirect('painel_grupo')
                pedido.save()
                grupo.capital -= total
                grupo.materia_prima += pedido.quantidade
                grupo.save()
                messages.success(request, 'Pedido registrado')
                return redirect('painel_grupo')
        form = DecisaoForm()
        envio_form = DistribuicaoForm()
        fornecedor_form = FornecedorForm()
        pedido_form = PedidoMateriaPrimaForm()
        decisoes = grupo.decisoes.all()
        envios = grupo.envios.select_related("cidade").all()
        resultados = grupo.resultados.all()
        produtos = grupo.produtos.prefetch_related("materias_primas").all()
        fornecedores = Fornecedor.objects.all()
        pedidos = grupo.pedidos_materia_prima.select_related("fornecedor").all()
        ultima_vista = request.session.get("ultima_rodada_vista", 0)
        nova = resultados.order_by("-rodada").first()
        notificacao = None
        if nova and nova.rodada > ultima_vista:
            notificacao = f"Resultados da rodada {nova.rodada} disponíveis."
            request.session["ultima_rodada_vista"] = nova.rodada
        ultima = grupo.decisoes.first()
        rodada_atual = ultima.rodada + 1 if ultima else 1
        eventos = [er.evento for er in EventoRodada.objects.filter(rodada=rodada_atual)]
        capacidade_total = self.calcular_capacidade_producao(grupo)
        alerta = None
        if grupo.estoque < capacidade_total * 0.2:
            alerta = 'Risco de ruptura de estoque'
        elif grupo.estoque > capacidade_total:
            alerta = 'Risco de desperdício de estoque'
        return render(request, self.template_name, {
            'grupo': grupo,
            'decisoes': decisoes,
            'form': form,
            'envio_form': envio_form,
            'fornecedor_form': fornecedor_form,
            'pedido_form': pedido_form,
            'envios': envios,
            'fornecedores': fornecedores,
            'pedidos': pedidos,
            'resultados': resultados,
            'alerta': alerta,
            'eventos': eventos,
            'notificacao': notificacao,
            'produtos': produtos,
        })


class GrupoViewSet(viewsets.ModelViewSet):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer


class DecisaoViewSet(viewsets.ModelViewSet):
    queryset = Decisao.objects.all()
    serializer_class = DecisaoSerializer


class DistribuicaoViewSet(viewsets.ModelViewSet):
    queryset = Distribuicao.objects.all()
    serializer_class = DistribuicaoSerializer


class ResultadoFinanceiroViewSet(viewsets.ModelViewSet):
    queryset = ResultadoFinanceiro.objects.all()
    serializer_class = ResultadoFinanceiroSerializer


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer


class EventoRodadaViewSet(viewsets.ModelViewSet):
    queryset = EventoRodada.objects.all()
    serializer_class = EventoRodadaSerializer


class RodadaViewSet(viewsets.ModelViewSet):
    queryset = Rodada.objects.all()
    serializer_class = RodadaSerializer


class CidadeViewSet(viewsets.ModelViewSet):
    queryset = Cidade.objects.all()
    serializer_class = CidadeSerializer


class GameConfigViewSet(viewsets.ModelViewSet):
    queryset = GameConfig.objects.all()
    serializer_class = GameConfigSerializer


class JogoViewSet(viewsets.ModelViewSet):
    queryset = Jogo.objects.all()
    serializer_class = JogoSerializer


class InvestimentoViewSet(viewsets.ModelViewSet):
    queryset = Investimento.objects.all()
    serializer_class = InvestimentoSerializer

    def create(self, request, *args, **kwargs):
        grupo_id = request.data.get('grupo')
        if grupo_id:
            resultados = (
                ResultadoFinanceiro.objects.filter(grupo_id=grupo_id)
                .order_by('-rodada')[:2]
            )
            if len(resultados) == 2 and all(r.saldo_caixa < 0 for r in resultados):
                return Response(
                    {
                        'detail': 'Investimentos bloqueados por fluxo de caixa negativo.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return super().create(request, *args, **kwargs)


class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer


class PedidoMateriaPrimaViewSet(viewsets.ModelViewSet):
    queryset = PedidoMateriaPrima.objects.all()
    serializer_class = PedidoMateriaPrimaSerializer


class RankingAPIView(generics.GenericAPIView):
    serializer_class = GrupoSerializer

    def get(self, request, *args, **kwargs):
        grupos = calcular_ranking()
        serializer = self.get_serializer(grupos, many=True)
        return Response(serializer.data)


class GrupoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = "grupo_list.html"
    context_object_name = "grupos"
    permission_required = "app.view_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class GrupoCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "grupo_form.html"
    success_url = reverse_lazy("lista_grupos")

    def test_func(self):
        user = self.request.user
        return getattr(user, "tipo_usuario", "") == "gamemaster" or user.is_superuser

    def get(self, request, *args, **kwargs):
        grupo_form = GrupoCadastroForm()
        membro_formset = MembroFormSet()
        return render(
            request,
            self.template_name,
            {"form": grupo_form, "membro_formset": membro_formset},
        )

    def post(self, request, *args, **kwargs):
        grupo_form = GrupoCadastroForm(request.POST)
        membro_formset = MembroFormSet(request.POST)
        if grupo_form.is_valid() and membro_formset.is_valid():
            grupo = grupo_form.save(commit=False)
            config, _ = GameConfig.objects.get_or_create(id=1)
            grupo.capital = config.capital_inicial
            grupo.estoque = config.estoque_inicial
            grupo.maquinas_a = config.maquinas_iniciais_a
            grupo.maquinas_b = config.maquinas_iniciais_b
            grupo.maquinas_c = config.maquinas_iniciais_c
            grupo.maquinas = (
                config.maquinas_iniciais_a
                + config.maquinas_iniciais_b
                + config.maquinas_iniciais_c
            )
            grupo.trabalhadores = config.trabalhadores_iniciais
            grupo.capacidade_maquina = config.capacidade_maquina
            grupo.save()
            lider = None
            for form in membro_formset:
                user = User.objects.create_user(
                    email_usuario=form.cleaned_data["email"],
                    nome_usuario=form.cleaned_data["nome"],
                    password=form.cleaned_data["senha"],
                    tipo_usuario=(
                        "lider_grupo" if form.cleaned_data.get("lider") else "membro_grupo"
                    ),
                )
                grupo.membros.add(user)
                if form.cleaned_data.get("lider"):
                    lider = user
            if not lider:
                grupo.delete()
                membro_formset._non_form_errors = membro_formset.error_class(
                    ["Selecione um líder para o grupo."]
                )
                return render(
                    request,
                    self.template_name,
                    {"form": grupo_form, "membro_formset": membro_formset},
                )
            grupo.lider = lider
            grupo.save()
            messages.success(request, "Grupo criado com sucesso.")
            return redirect(self.success_url)
        return render(
            request,
            self.template_name,
            {"form": grupo_form, "membro_formset": membro_formset},
        )


class GrupoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    form_class = GrupoForm
    template_name = "grupo_form.html"
    success_url = reverse_lazy("lista_grupos")
    permission_required = "app.change_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class InvestimentoCapacidadeView(LoginRequiredMixin, FormView):
    template_name = "investimento_capacidade.html"
    form_class = InvestimentoCapacidadeForm
    success_url = reverse_lazy("investir_capacidade")

    def form_valid(self, form):
        linha = form.cleaned_data["linha"]
        aumento = form.cleaned_data["aumento_capacidade"]
        valor = form.cleaned_data["valor"]
        linha.capacidade += aumento
        linha.save()
        Investimento.objects.create(
            grupo=linha.grupo, categoria="maquinas", valor=valor
        )
        messages.success(self.request, "Capacidade ampliada com sucesso.")
        return super().form_valid(form)


class RelatoriosView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "financeiro/relatorios.html"
    permission_required = "app.view_resultadofinanceiro"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get(self, request, *args, **kwargs):
        form = ResultadoFilterForm(request.GET or None)
        resultados = ResultadoFinanceiro.objects.select_related("grupo")
        if form.is_valid():
            if form.cleaned_data.get("rodada"):
                resultados = resultados.filter(rodada=form.cleaned_data["rodada"])
            if form.cleaned_data.get("grupo"):
                resultados = resultados.filter(grupo=form.cleaned_data["grupo"])
        return render(
            request,
            self.template_name,
            {"resultados": resultados, "form": form},
        )


@login_required
def export_resultados_pdf(request):
    rodada = request.GET.get("rodada")
    grupo_id = request.GET.get("grupo")
    qs = ResultadoFinanceiro.objects.select_related("grupo")
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=resultados.pdf"
    p = canvas.Canvas(response)
    y = 800
    p.drawString(100, y, "Resultados Financeiros")
    y -= 20
    for r in qs:
        p.drawString(
            100,
            y,
            f"Grupo {r.grupo.nome} - Rodada {r.rodada} - Lucro {r.lucro}",
        )
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.showPage()
    p.save()
    return response


@login_required
def export_resultados_excel(request):
    rodada = request.GET.get("rodada")
    grupo_id = request.GET.get("grupo")
    qs = ResultadoFinanceiro.objects.select_related("grupo")
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    wb = Workbook()
    ws = wb.active
    ws.append(["Grupo", "Rodada", "Receita", "Custos", "Lucro", "Caixa"])
    for r in qs:
        ws.append(
            [
                r.grupo.nome,
                r.rodada,
                float(r.receita),
                float(r.custos),
                float(r.lucro),
                float(r.saldo_caixa),
            ]
        )
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=resultados.xlsx"
    wb.save(response)
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def investir_capacidade_api(request):
    linha_id = request.data.get("linha")
    aumento = int(request.data.get("aumento", 0))
    valor = Decimal(request.data.get("valor", 0))
    linha = get_object_or_404(LinhaProducao, id=linha_id)
    linha.capacidade += aumento
    linha.save()
    Investimento.objects.create(grupo=linha.grupo, categoria="maquinas", valor=valor)
    return Response({"nova_capacidade": linha.capacidade})

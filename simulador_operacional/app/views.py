from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.db.models import Sum

from .models import (
    ResultadoFinanceiro,
    Grupo,
    EventoAleatorio,
    RegistroEvento,
    Rodada,
)
import random

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

class HomeView(TemplateView):
    template_name = 'home.html'
    # login_url = '/accounts/login/'

@login_required
def home(request):
    return render(request, 'home.html')


@login_required
def relatorios_financeiros(request):
    resultados = ResultadoFinanceiro.objects.select_related('rodada').order_by('rodada__numero')
    context = {'resultados': resultados}
    return render(request, 'financeiro/relatorios.html', context)


@login_required
def ranking_grupos(request):
    ranking = (
        Grupo.objects.annotate(total_lucro=Sum('resultados__lucro_liquido'))
        .order_by('-total_lucro')
    )
    context = {'ranking': ranking}
    return render(request, 'financeiro/ranking.html', context)


@login_required
def sortear_evento(request):
    eventos = list(EventoAleatorio.objects.all())
    evento_sorteado = None
    if eventos:
        total_prob = sum(e.probabilidade for e in eventos)
        alvo = random.uniform(0, total_prob)
        acumulado = 0
        for e in eventos:
            acumulado += e.probabilidade
            if alvo <= acumulado:
                evento_sorteado = e
                break
        rodada = Rodada.objects.order_by('-numero').first()
        if evento_sorteado and rodada:
            RegistroEvento.objects.create(evento=evento_sorteado, rodada=rodada)
    context = {'evento': evento_sorteado}
    return render(request, 'financeiro/eventos.html', context)


@login_required
def resumo_encerramento(request):
    rodada = Rodada.objects.filter(encerrada=True).order_by('-numero').first()
    resultado = None
    if rodada:
        resultado = getattr(rodada, 'resultado_financeiro', None)
    context = {"rodada": rodada, "resultado": resultado}
    return render(request, 'financeiro/encerramento.html', context)

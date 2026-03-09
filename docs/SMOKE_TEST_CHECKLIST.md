# Smoke Test Checklist

## Objetivo
Validar rapidamente os fluxos críticos após mudanças ou antes de release.

## Pré-requisitos
- Banco migrado: `python manage.py migrate`
- Dados base: `python manage.py seed_dados_base`
- Usuário gamemaster existente.
- Pelo menos um grupo com membros.

## Roteiro Gamemaster
1. Login com perfil gamemaster.
2. Acessar `/config/wizard/`:
- preencher etapas 1 e 2;
- confirmar na etapa 3;
- validar mensagem de sucesso.
3. Abrir rodada em `/abrir_rodada/`.
4. Definir/validar CEO da rodada (via admin/API `ceos-rodada`).
5. Executar fechamento:
- `python manage.py fechar_rodadas`
6. Validar:
- `/relatorios/` com consolidado preenchido;
- `/ranking/` com score multicritério;
- `/jobs/` com execução registrada e `correlation_id`.

## Roteiro Grupo (CEO da rodada)
1. Login como usuário do grupo.
2. Acessar `/painel/`.
3. Registrar compra de MP.
4. Registrar produção.
5. Registrar distribuição.
6. Registrar investimento:
- marketing (cidade);
- máquinas/RH (produto);
- financeiro (aplicar/resgatar).
7. Enviar submissão oficial.
8. Validar bloqueio de edição após submissão.

## Validações de Resultado
1. Em rodada seguinte, validar ativação D+1 de máquinas/RH.
2. Confirmar saldo aplicado com rendimento financeiro.
3. Confirmar demanda por cidade+produto respeitando teto.
4. Confirmar evento de estado (quando ocorrer) impactando o fluxo.
5. Exportar PDF/Excel em `/relatorios/`.

## Critério de Aprovação
- Nenhum erro 500 em fluxos acima.
- Dados persistidos em relatórios/ranking/jobs.
- Regras de negócio chave observadas (CEO da rodada, D+1, demanda por produto, isolamento por jogo).

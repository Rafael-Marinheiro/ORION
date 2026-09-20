# Auditoria RN-01 e RN-02 — 20/09/2026

Leitura direta de `word/document.xml` dos originais DOCX 3 (RF.01–03),
5 (RN-01/RN-02), 7 (§7.2), 9 (§9.1–9.2), 11 e 12 (§12.2/12.4), em
`_documentação/DOC/`, confrontada com `docs/GUIA_IMPLEMENTACAO.md`.
Nenhuma fórmula pendente do Product Owner foi alterada.

| Requisito | Código / evidência | Teste / diagnóstico |
|---|---|---|
| Login único associado a e-mail institucional | `models.User.email_usuario` único e `USERNAME_FIELD`; `MembroForm.clean_email` e `BaseMembroFormSet.clean` rejeitam duplicatas | `test_cadastro_grupo`: duplicata na equipe, e-mail existente (inclusive caixa diferente) e rollback. Domínios institucionais permitidos não constam nos originais: professor confere a lista de e-mails. Não foi inventada uma lista de domínios. |
| Senha ≥ 8 com letras e números | Validadores Django + `LetterAndDigitPasswordValidator`; `CustomUserCreationForm`, `MembroForm`, fluxo de redefinição | `test_regras_iniciais.test_senha_minima_com_letras_e_numeros`, `test_validators`, `test_cadastro_grupo` |
| Só administrador cadastra usuários | `RegisterView.test_func`, `GrupoCreateView.test_func` | `test_regras_iniciais.test_alunos_nao_administram_pelas_telas_ou_api`; contas desconhecidas/inativas não autenticam |
| Perfis distintos, submissão exclusiva do CEO | `CEOGrupoRodada`, `PainelGrupoView.usuario_pode_submeter`, `ProfessorWritePermission` | `test_primeira_turma`: membro não submete, CEO submete uma vez, autor e horário auditados; `test_regras_iniciais`: aluno não altera configuração/rodada/jogo/CEO pela API |
| 3–12 rodadas configuradas | Validadores de `GameConfig.numero_rodadas` aplicados por ModelForm e serializer | `test_regras_iniciais.test_limites_de_rodadas_api`; `RodadaForm.clean` usa o jogo selecionado, não a primeira configuração do banco |
| Prazo definido previamente pelo professor | `RodadaForm.fim`, `RodadaCreateView.form_valid` | Rejeita prazo passado; cenário completo abre três rodadas via HTTP e executa fechamento após vencimento |
| 3–6 integrantes por grupo | `MembroFormSet` e `GrupoForm.clean_membros` | `test_cadastro_grupo.test_limites_de_integrantes`; exatamente um líder; tentativa inválida não deixa contas órfãs |
| R$ 1.000.000 iniciais | Default em `GameConfig`, copiado por `GrupoCreateView` | `test_models.GameConfigModelTest`, `test_primeira_turma`; configuração específica do jogo validada em `test_cadastro_grupo` |
| 40 máquinas: A15/B15/C10 | Defaults em `GameConfig` e inicialização de `CapacidadeProdutoGrupo` | `test_primeira_turma` verifica os 40 equipamentos operacionais e criação dos grupos |
| 80 operadores, dois por máquina | Defaults em `GameConfig` e inicialização operacional | `test_primeira_turma` verifica 80; `test_models.CapacidadeProdutoGrupoModelTest` cobre capacidade com operador faltando |
| Pesos configuráveis, soma 1 (DOCX 12) | `GameConfigForm`, seed e `fechar_rodadas` usam EO/DF/EE/SD/DS | `test_forms`, `test_base_regional`, `test_primeira_turma`: peso 100% EO é efetivamente aplicado no resultado |

## Desvios corrigidos

- Cadastro sem líder criava contas órfãs; múltiplos líderes eram aceitos;
  e-mail repetido produzia erro de banco após criação parcial. Validação
  antecipada e transação agora preservam a integridade, inclusive em conflito.
- Cadastro e limite de rodada liam a configuração global mesmo com outro jogo
  selecionado. Passaram a usar a configuração vinculada.
- Alunos autenticados podiam escrever nos endpoints administrativos. Escrita
  exige professor; o painel continua sendo o caminho de decisões do CEO.
- A tela salvava quatro pesos antigos ignorados pelo fechamento. Agora exibe
  e persiste os cinco eixos. O seed novo usa os mesmos valores; configurações
  existentes não são sobrescritas silenciosamente. O fechamento lê os pesos
  de cada jogo.

- A migração consolidada criava administrador com senha fixa. O nó histórico
  foi preservado sem provisionar conta nem apagar usuários no rollback.
  `tools/verificar_base_limpa.py` verifica migrações reais em banco temporário,
  inclusive ausência de contas automáticas; a senha provisionada neste worktree
  foi invalidada. Instalações anteriores devem redefinir a senha pelo responsável.

## Pendências que não exigem inventar regras neste incremento

- B8/B10: o guia diz aguardar ratificação, mas `parametros.py` já contém SD
  60/40 e limite regional de 200 km. Preservados como encontrados. Solicitar
  ratificação do Dr. Pio antes de usar ranking como nota oficial; o ensaio
  técnico não resolve esta divergência documental.
- Cadastro institucional: não há domínio especificado. O professor valida
  os e-mails ao cadastrar. Bloqueio automático por domínio depende da lista
  da instituição.
- Personalização de máquinas/estoques pelo wizard não foi certificada por
  este ensaio: ele cobre os padrões RN-02 (40/80, estoque zero). A
  inicialização operacional ainda usa a divisão padrão por produto.
- A API de escrita do professor é administrativa, não certificada como
  substituta dos formulários. Usar as telas do roteiro para criar grupos e
  rodadas; os campos crus da API não executam todo o fluxo operacional.
- Não houve teste de carga, de rede da instituição nem ensaio humano no
  navegador. O resultado automatizado comprova o fluxo HTTP/ORM e permissões
  exercitadas, não esses itens operacionais.

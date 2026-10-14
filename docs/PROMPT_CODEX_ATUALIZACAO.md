# Prompt para o CODEX — atualizar a máquina do Dr. Pio

Copie **tudo** que está entre as linhas de marcação e cole no CODEX, na
máquina do Dr. Pio.

---8<--- INÍCIO DO PROMPT ---8<---

Você vai atualizar uma instalação local do ORION (simulador de gestão
empresarial em Django) para a versão de testes e deixá-la rodando. A máquina
já tem uma cópia antiga do repositório.

**Repositório:** https://github.com/Rafael-Marinheiro/ORION
**Branch alvo:** `claude/recursing-pascal-f25acd`
**Pré-requisito:** Docker Desktop instalado e em execução.

## Regras

- Não altere código. Esta é uma atualização de ambiente, não de software.
- Se algum passo falhar, **pare e relate o erro completo**. Não tente
  contornar criando dados à mão nem editando arquivos do projeto.
- O banco é um SQLite local de desenvolvimento. Pode ser recriado à vontade.

## Passo 1 — Atualizar o repositório

Na pasta do projeto:

```bash
git fetch origin
git checkout claude/recursing-pascal-f25acd
git pull origin claude/recursing-pascal-f25acd
```

Se houver alterações locais impedindo o checkout, **não as descarte**:
mostre `git status` e `git diff`, e pergunte antes de qualquer coisa.

Confirme que chegou na versão certa — o commit mais recente deve mencionar
a Ajuda e o §7.1:

```bash
git log --oneline -3
```

## Passo 2 — Variáveis de ambiente

Se não existir um `.env` na raiz:

```bash
cp .env.example .env
```

Mantenha `DJANGO_DEBUG=True`. É uma instalação local de avaliação.

## Passo 3 — Subir a aplicação

```bash
docker compose up --build -d
```

A subida roda as migrações e popula o catálogo (produtos, matérias-primas,
praças e eventos) automaticamente. Aguarde e confirme:

```bash
docker compose logs --tail 20 web
```

Deve aparecer `Dados base populados com sucesso.`

## Passo 4 — Criar o game master

```bash
docker compose exec web python manage.py shell -c "from app.models import User; User.objects.filter(email_usuario='professor@orion.local').delete(); User.objects.create_superuser(email_usuario='professor@orion.local', nome_usuario='Dr. Pio Marinheiro', password='orion-demo-2026')"
```

## Passo 5 — Criar a turma de demonstração

```bash
docker compose exec web python manage.py seed_turma_demo --nome "Turma Demo" --senha "orion-demo-2026" --rodadas 4 --abrir-rodada --limpar
```

Isso cria três equipes de três alunos, com CEO definido em cada uma, e deixa
a rodada 1 aberta com prazo de duas horas.

**Se duas horas for pouco para a avaliação**, estenda o prazo:

```bash
docker compose exec web python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from app.models import Rodada; Rodada.objects.filter(fechada=False).update(fim=timezone.now() + timedelta(days=7))"
```

## Passo 6 — Verificar

Abra `http://localhost:8000/` e confirme, nesta ordem:

1. A página inicial carrega **com estilo** (fundo escuro, logo do ORION). Se
   aparecer sem formatação, pare e relate — é problema de arquivos estáticos.
2. `http://localhost:8000/ajuda/` mostra as tabelas de produtos,
   matérias-primas, praças e a seção de classificação.
3. Entrar como professor abre o menu com "Gerenciar jogo".
4. Entrar como CEO de equipe abre o "Painel do grupo" com a rodada 1 em
   andamento e o prazo no topo.

Por fim, rode a suíte de testes e informe o resultado:

```bash
docker compose run --rm web python manage.py test app --settings=simulador_operacional.settings_test
```

Deve terminar com `OK`. Leva de 8 a 12 minutos.

## Relatório final

Informe:

- o commit em que ficou (`git log --oneline -1`);
- o resultado da suíte (número de testes e OK/FALHOU);
- se algum dos quatro itens de verificação falhou, e qual foi o erro.

---8<--- FIM DO PROMPT ---8<---

---

## Credenciais que serão criadas

Todas com a **mesma senha: `orion-demo-2026`**

### Game master

| Papel | E-mail |
|---|---|
| Professor / moderador | `professor@orion.local` |

### Equipes — o CEO é quem submete a rodada

| Equipe | CEO | Integrantes |
|---|---|---|
| Equipe Vega | `ana1@demo.orion` | `bruno1@demo.orion`, `carla1@demo.orion` |
| Equipe Lira | `diego2@demo.orion` | `elisa2@demo.orion`, `fabio2@demo.orion` |
| Equipe Rigel | `gabriela3@demo.orion` | `hugo3@demo.orion`, `iara3@demo.orion` |

Para ver a diferença entre os perfis do §10.1, entre com um CEO
(`ana1@demo.orion`) e depois com um integrante comum
(`bruno1@demo.orion`): o segundo vê o painel em modo leitura e não consegue
submeter.

> **Senhas de demonstração.** Valem para esta instalação local de avaliação.
> Numa instalação de sala de aula, as contas são criadas pela tela de
> cadastro de grupos, com senha escolhida pelo professor.

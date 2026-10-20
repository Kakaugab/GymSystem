# GymSystem — Back-end (Python / Flask)

API do app de academia GymSystem. O back-end recebe os pedidos do front-end, aplica as regras
(login, XP, níveis, sequência, recordes, ranking) e devolve os dados em JSON.

**Por enquanto os dados ficam em memória** (arquivo `dados_exemplo.py`). Quando o banco
estiver pronto, só o arquivo `repositorio.py` muda. Ao reiniciar o servidor, os dados voltam ao início.

---

## Como rodar

Precisa de Python 3.10 ou mais novo.

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Abra **http://localhost:5000** no navegador: o próprio servidor já abre o app (front-end).

| Usuário | E-mail | Senha |
|---|---|---|
| Aluno | lucas.oliveira@email.com | senha1234567 |
| Academia (admin) | admin@gymsystem.com | admin123 |

Rodar os testes automáticos (10 testes):

```bash
cd backend
python -m unittest -v
```

---

## Estrutura

```
gymsystem/
├── backend/
│   ├── app.py              ← inicia o servidor, junta as rotas, serve o front
│   ├── rotas/
│   │   ├── auth.py         ← login, logout, controle de acesso (token)
│   │   ├── aluno.py        ← rotas do app do aluno
│   │   └── admin.py        ← rotas do painel da academia
│   ├── gamificacao.py      ← REGRAS: XP, nível, sequência, recordes, conquistas
│   ├── repositorio.py      ← ACESSO AOS DADOS (o time do banco mexe só aqui)
│   ├── dados_exemplo.py    ← dados fictícios, usados até o banco ficar pronto
│   ├── test_api.py         ← testes automáticos
│   └── requirements.txt
└── frontend/               ← index.html, style.css, app.js (já ligado na API)
```

Fluxo: **front** → `rotas/` → `gamificacao.py` → `repositorio.py` → **banco**

---

## Para cada parte do grupo

### Front-end
O `app.js` já foi adaptado: todos os dados vêm da API (não há mais dados fixos no JS).
- Se o front rodar pelo servidor Python (porta 5000), funciona direto.
- Se rodar pelo Live Server (VS Code, porta 5500), ele chama `http://localhost:5000` sozinho.
  O servidor precisa estar ligado.
- Outro endereço (ex.: testar no celular pela rede): no `index.html`, descomente
  `window.API_URL = "http://SEU_IP:5000"`.

### Banco de dados
Abram o `repositorio.py`. Cada função tem, no comentário, **o formato exato que precisa devolver**.
Troquem o corpo da função por um SELECT/INSERT/UPDATE e mantenham nome, parâmetros e retorno.
Nada mais no back-end precisa mudar.

Tabelas que o back-end espera (sugestão, podem adaptar os nomes):

| Tabela | Campos principais |
|---|---|
| usuarios | id, nome, email, senha_hash, papel (aluno/admin) |
| perfis | usuario_id, nivel, xp, sequencia, melhor_sequencia, ultimo_treino, treinos_feitos, categoria_ranking |
| configuracoes | usuario_id, chave, valor |
| treinos | codigo, nome, grupo, minutos, xp |
| exercicios | id, treino_codigo, ordem, nome, grupo, series, reps, carga |
| historico_treinos | id, usuario_id, data, treino_codigo, minutos, exercicios, xp |
| recordes | usuario_id, exercicio, carga |
| titulos / medalhas | usuario_id, icone, nome, descricao, liberado / meta |
| duelos, convites | oponente, xp de cada um, objetivo, data fim / de, desafio, dias |
| desafios, participacoes | id, nome, meta, recompensa_xp, termina_em / desafio_id, usuario_id |
| membros (matrículas) | id, nome, cpf, plano, valor_mensal, vencimento, ativo, cadastro |
| planos | id, nome, preco |
| pagamentos | aluno, plano, valor, confirmado, data |

> A senha **nunca** vai em texto puro para o banco: gravem o `senha_hash`
> (gerado com `werkzeug.security.generate_password_hash`).

---

## Rotas da API (contrato)

Todas começam com `/api`. Respostas e corpos em JSON.
Depois do login, enviar o cabeçalho `Authorization: Bearer <token>`.
Em caso de erro a resposta é `{"erro": "mensagem"}` com o status HTTP correspondente
(400 dado inválido, 401 sem login, 403 sem permissão, 404 não encontrado).

### Autenticação
| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST | `/login` | `{email, senha}` | `{token, usuario:{id, nome, papel}}` |
| POST | `/logout` | — | `{ok: true}` |
| GET | `/eu` | — | usuário logado |
| GET | `/saude` | — | `{status: "ok"}` (servidor no ar) |

### Aluno (papel `aluno`)
| Método | Rota | Corpo / parâmetros | O que faz |
|---|---|---|---|
| GET | `/treinos` | — | Treinos A, B, C com exercícios |
| GET | `/aluno/resumo` | — | Nível, XP, sequência, semana, próximo treino, posição no ranking, config |
| GET | `/aluno/historico` | — | Treinos recentes, recordes e gráfico de carga |
| POST | `/treinos/concluir` | `{treino:"A", segundos:2700, cargas:[40,30,14,20,25]}` | Salva o treino, calcula XP/nível/sequência/recordes |
| PUT | `/aluno/config` | `{chave:"sons_app", valor:false}` | Liga/desliga uma configuração |
| GET | `/aluno/conquistas` | — | Títulos e medalhas com progresso |
| GET | `/ranking` | `?categoria=Evoluídos` (ou Moderados, Iniciantes) | Lista ordenada por XP |
| GET | `/duelos` | — | Duelo ativo e convites |
| POST | `/duelos/convites/<id>` | `{aceitar:true}` | Aceita ou recusa um convite |
| GET | `/desafios` | — | Desafio ativo (com progresso) e desafios da academia |
| POST | `/desafios/<id>/participar` | — | Entra/sai do desafio |

### Academia (papel `admin`)
| Método | Rota | Corpo / parâmetros | O que faz |
|---|---|---|---|
| GET | `/admin/painel` | — | Totais de membros, receita, inadimplência, vencimentos |
| GET | `/admin/membros` | `?busca=nome_ou_cpf&status=ativos\|inativos` | Lista de alunos |
| GET | `/admin/membros/<id>` | — | Ficha completa do aluno |
| PATCH | `/admin/membros/<id>` | `{ativo:false}` | Ativa/desativa aluno |
| GET | `/admin/planos` | — | Planos, resumo de contratos, próximos vencimentos |
| GET | `/admin/financeiro` | `?pendentes=1` | Receita, gráfico e recebimentos |

---

## Regras de gamificação (em `gamificacao.py`)

- XP do treino: A = 120, B = 130, C = 140.
- **+50 XP** no primeiro treino do dia (mantém a sequência).
- **+100 XP** por recorde pessoal batido (carga maior que a anterior no mesmo exercício).
- A cada **3.000 XP** sobe um nível.
- Títulos por nível: 1–5 Iniciante, 6–10 Moderado, 11–15 Intermediário, 16–20 Avançado, 21+ Evoluído.
- Sequência: treinou ontem e treinou hoje → +1 dia; ficou um dia sem treinar → volta para 1.
- Próximo treino segue o rodízio A → B → C.

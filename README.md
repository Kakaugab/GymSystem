# GymSystem — App de academia com gamificação

App de academia com XP, níveis, sequência, recordes, ranking, duelos e desafios, mais um painel
administrativo para a academia.

- **Front-end:** HTML, CSS e JavaScript puro (pasta `frontend/`)
- **Back-end:** Python + Flask (pasta `backend/`)
- **Banco de dados:** MySQL 8 (também roda no MariaDB do XAMPP)

Os dados ficam **no banco**: concluir um treino, mudar uma configuração ou desativar um aluno
continua valendo depois de reiniciar o servidor. O login também fica no banco, então reiniciar
não desloga ninguém.

---

## Sumário

1. [Instalação no Windows, do zero](#1-instalação-no-windows-do-zero)
2. [Uso do dia a dia](#2-uso-do-dia-a-dia)
3. [Testes automáticos](#3-testes-automáticos)
4. [Estrutura do projeto](#4-estrutura-do-projeto)
5. [O banco de dados](#5-o-banco-de-dados)
6. [Para cada parte do grupo](#6-para-cada-parte-do-grupo)
7. [Rotas da API (contrato)](#7-rotas-da-api-contrato)
8. [Regras de gamificação](#8-regras-de-gamificação)
9. [Roteiro da apresentação](#9-roteiro-da-apresentação)
10. [Limitações conhecidas](#10-limitações-conhecidas)

---

## 1. Instalação no Windows, do zero

São quatro partes: **MySQL**, **bancos + usuário**, **Python** e **projeto**. Faça uma vez só.

### 1.1 Instalar o MySQL 8 (versão ZIP)

> Usa XAMPP? Pule para o [1.1-B](#11-b-alternativa-xampp-mariadb).

1. **Pré-requisito:** o MySQL precisa do *Visual C++ Redistributable*. Num PowerShell:
   ```powershell
   winget install -e --id Microsoft.VCRedist.2015+.x64
   ```
2. **Baixar:** em <https://dev.mysql.com/downloads/mysql/>, escolha a versão **8.0**,
   sistema **Microsoft Windows** e baixe o **"Windows (x86, 64-bit), ZIP Archive"**.
   Não precisa criar conta: clique em *"No thanks, just start my download"*.
3. **Extrair** o conteúdo do ZIP para `C:\mysql`. Deve existir o arquivo `C:\mysql\bin\mysqld.exe`.
4. **Criar o arquivo de configuração** `C:\mysql\my.ini` (no Bloco de Notas) com:
   ```ini
   [mysqld]
   basedir=C:/mysql
   datadir=C:/mysql/data
   port=3306
   character-set-server=utf8mb4
   collation-server=utf8mb4_unicode_ci

   [client]
   default-character-set=utf8mb4
   ```
   Use barras normais (`/`) nos caminhos. A pasta `C:\mysql\data` **não pode existir ainda**:
   o próximo passo cria essa pasta.
5. **Inicializar e instalar o serviço.** Abra o PowerShell **como administrador**:
   ```powershell
   C:\mysql\bin\mysqld --defaults-file=C:\mysql\my.ini --initialize --console
   ```
   No fim da saída aparece `A temporary password is generated for root@localhost: XXXXXXXX`.
   **Anote essa senha temporária.** Depois:
   ```powershell
   C:\mysql\bin\mysqld --install MySQL80 --defaults-file=C:\mysql\my.ini
   net start MySQL80
   ```
   O serviço `MySQL80` passa a iniciar sozinho com o Windows.
6. **Colocar o MySQL no PATH**, ainda no PowerShell de administrador:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\mysql\bin", "Machine")
   ```
   **Feche e abra um terminal novo** e confira com `mysql --version`.

### 1.1-B Alternativa: XAMPP (MariaDB)

1. Instale o XAMPP e, no *XAMPP Control Panel*, clique em **Start** na linha **MySQL**.
2. Clique em **Shell** e entre com `mysql -u root` (no XAMPP o root vem sem senha).
3. Siga para o 1.2. O `schema.sql` foi escrito para funcionar também no MariaDB (10.2 ou mais novo).

### 1.2 Criar os bancos e o usuário `gym`

Entre no MySQL como administrador:
```powershell
mysql -u root -p
```
Digite a senha temporária do passo 5 (no XAMPP, apenas Enter). Depois cole os comandos abaixo,
trocando `uma_senha_forte` (senha do `root`) e `troque_pela_sua_senha` (senha do usuário `gym`)
por senhas suas. No XAMPP, pule a primeira linha.
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'uma_senha_forte';

CREATE DATABASE gymsystem      CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE gymsystem_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'gym'@'localhost' IDENTIFIED BY 'troque_pela_sua_senha';
GRANT ALL PRIVILEGES ON gymsystem.*      TO 'gym'@'localhost';
GRANT ALL PRIVILEGES ON gymsystem_test.* TO 'gym'@'localhost';
EXIT;
```
- `gymsystem` é o banco do app e da apresentação.
- `gymsystem_test` é usado pelos testes automáticos, que **apagam e recriam** esse banco a cada execução.
- O usuário `gym` só tem acesso a esses dois bancos. O app não usa o `root`.
- **Importante:** a senha que você colocou no `CREATE USER` (no lugar de `troque_pela_sua_senha`)
  tem que ser **exatamente a mesma** do `DB_PASSWORD` no seu `.env` (passo 1.4). Se forem
  diferentes, o seed e o servidor dão erro de acesso negado (`Access denied for user 'gym'`).

### 1.3 Instalar o Python 3.12

```powershell
winget install -e --id Python.Python.3.12
```
Ou baixe em <https://www.python.org/downloads/> e marque **"Add python.exe to PATH"** na instalação.
**Abra um terminal novo** e confira com `python --version`.

### 1.4 Preparar o projeto

No terminal, dentro da pasta `gymsystem\backend`:

1. Criar o ambiente virtual (uma pasta `.venv` com as bibliotecas só deste projeto):
   ```powershell
   python -m venv .venv
   ```
2. Ativar o ambiente. Repita isso **toda vez** que abrir um terminal novo:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   O começo da linha passa a mostrar `(.venv)`. Se o PowerShell reclamar que *"a execução de
   scripts foi desabilitada"*, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
   ou use o **cmd** com `.venv\Scripts\activate.bat`.
3. Instalar as bibliotecas:
   ```powershell
   pip install -r requirements.txt
   ```
4. Criar o seu `.env` a partir do modelo:
   ```powershell
   copy .env.example .env
   ```
   Abra o `.env` e coloque em `DB_PASSWORD` a **mesma senha** que você usou no `CREATE USER` do
   usuário `gym` (passo 1.2). O `.env` tem senha, por isso
   **não vai para o Git** (está no `.gitignore`). Cada pessoa do grupo tem o seu.
5. Criar as tabelas e os dados iniciais:
   ```powershell
   python db\seed.py
   ```
   O seed pergunta antes de apagar. Use `-y` para pular a pergunta.
6. Subir o servidor:
   ```powershell
   python app.py
   ```
   Abra **<http://localhost:5000>**: o próprio servidor abre o app (front-end).
   Daqui em diante, basta dar dois cliques no **`iniciar.bat`** (veja a seção 2).

### Logins de teste

| Quem | E-mail | Senha |
|---|---|---|
| Aluno principal | lucas.oliveira@email.com | senha1234567 |
| Academia (admin) | admin@gymsystem.com | admin123 |
| Demais alunos de demonstração | `nome.sobrenome@email.com` (ex.: maria.silva@email.com) | aluno123 |

As senhas acima são **só para demonstração**. No banco fica apenas o *hash* delas.

---

## 2. Uso do dia a dia

**Jeito rápido:** dê dois cliques no **`iniciar.bat`**, na raiz do projeto. Ele:
- entra em `backend/` e usa o Python do `.venv`, sem precisar ativar nada;
- sobe o servidor;
- abre o navegador em <http://localhost:5000> depois de alguns segundos.

Para parar, use **Ctrl+C** na janela preta (ou feche a janela). Se faltar o `.venv` ou o `.env`,
o script avisa e indica a parte do README a seguir. Se o servidor parar com erro (ex.: MySQL
desligado), a janela fica aberta mostrando a mensagem.

**Pelo terminal** (mesmo resultado, sem abrir o navegador):

```powershell
cd gymsystem\backend
.\.venv\Scripts\Activate.ps1
python app.py
```

- **Voltar os dados ao estado inicial:** `python db\seed.py -y`. Isso apaga tudo e recria.
- O serviço do MySQL já inicia com o Windows. No XAMPP, clique em **Start** no MySQL antes.

---

## 3. Testes automáticos

```powershell
cd gymsystem\backend
.\.venv\Scripts\Activate.ps1
python -m unittest -v
```

- São **17 testes**: os 10 originais da API e mais 7 do banco (transação, ranking, persistência
  e sessões: token válido após reiniciar, logout, sessão vencida).
- Rodam **sempre no banco `gymsystem_test`** (variável `DB_NAME_TESTE` do `.env`), que é **apagado
  e recriado** pelo seed no início de cada execução. O banco `gymsystem` nunca é tocado.
- Trava de segurança: se o nome do banco de teste não terminar em `_test`, os testes se recusam a rodar.

---

## 4. Estrutura do projeto

```
gymsystem/
├── .gitattributes          ← garante quebra de linha do Windows (CRLF) nos .bat
├── .gitignore
├── iniciar.bat             ← dois cliques: sobe o servidor e abre o navegador
├── README.md
├── backend/
│   ├── app.py              ← inicia o servidor, junta as rotas, liga o banco, serve o front
│   ├── .env.example        ← modelo de configuração (copiar para .env)
│   ├── rotas/
│   │   ├── auth.py         ← login, logout, controle de acesso (token)
│   │   ├── aluno.py        ← rotas do app do aluno
│   │   └── admin.py        ← rotas do painel da academia
│   ├── gamificacao.py      ← REGRAS: XP, nível, sequência, recordes, conquistas
│   ├── repositorio.py      ← ACESSO AOS DADOS: todas as consultas SQL ficam aqui
│   ├── db/
│   │   ├── schema.sql      ← CREATE TABLE de todas as tabelas
│   │   ├── seed.py         ← recria as tabelas e insere os dados de demonstração
│   │   ├── conexao.py      ← conexão por requisição + COMMIT/ROLLBACK
│   │   └── diagrama.md     ← diagrama entidade-relacionamento (Mermaid)
│   ├── test_api.py         ← testes automáticos
│   └── requirements.txt
└── frontend/               ← index.html, style.css, app.js (já ligado na API)
```

Fluxo: **front** → `rotas/` → `gamificacao.py` → `repositorio.py` → `db/conexao.py` → **MySQL**

---

## 5. O banco de dados

### Tabelas

O diagrama completo, com PKs, FKs e cardinalidades, está em
**[backend/db/diagrama.md](backend/db/diagrama.md)**. Lá também estão os pontos para a apresentação.

| Área | Tabelas |
|---|---|
| Pessoas e acesso | `usuarios` (alunos e admins, com CPF), `sessoes` (logins ativos) |
| Gamificação | `perfis` (1:1 com usuário), `categorias_ranking`, `opcoes_configuracao`, `configuracoes_usuario` |
| Treinos | `treinos`, `exercicios`, `treino_exercicios` (N:N), `historico_treinos`, `recordes` |
| Conquistas | `titulos`, `usuario_titulos` (N:N), `medalhas` |
| Social | `duelos` (2 FKs para `usuarios`: convite e duelo na mesma tabela), `desafios`, `participacoes`, `desafios_academia` |
| Administração | `planos`, `matriculas`, `pagamentos` |

### Decisões principais (resumo para a apresentação)

- **Usuário = membro.** Um "membro" do painel é um `usuarios` com papel `aluno` mais a sua
  matrícula **atual** (a mais recente). Login, ranking e painel mostram a mesma pessoa.
- **Calcular em vez de guardar.** Total de membros, receita, inadimplência, alunos por plano,
  vencimentos, recorde atual e gráfico de evolução são calculados com `COUNT`, `SUM` e `MAX` na hora.
  Nada de número fixo.
- **Desnormalização consciente.** `perfis` guarda contadores (`treinos_feitos`, `sequencia`) porque
  o `gamificacao.py` calcula e grava esses valores.
- **utf8mb4 + utf8mb4_unicode_ci** para aceitar emoji e funcionar no MySQL e no MariaDB.
- **DECIMAL para dinheiro.** O repositório converte para número antes de mandar no JSON.

### Segurança

- **Senhas:** só o hash (`werkzeug.security.generate_password_hash`, algoritmo scrypt). A senha em
  texto puro nunca chega ao banco.
- **Sessões de login:** a tabela `sessoes` guarda só o **hash SHA-256** do token, nunca o token.
  Uma cópia vazada da tabela não serve para entrar no sistema. O SHA-256 (rápido e sem salt) é
  suficiente aqui porque o token é aleatório e longo (256 bits), ao contrário de uma senha. O
  logout apaga a linha, e as sessões vencidas (12 horas) são apagadas a cada novo login.
- **SQL Injection:** todas as consultas são **parametrizadas** (`%s`). Nenhum valor é colado no SQL
  com f-string.
- **Credenciais** ficam no `.env`, fora do Git. O app usa o usuário `gym`, que só enxerga os dois bancos.

### Transações (COMMIT / ROLLBACK)

O `db/conexao.py` abre **uma conexão por requisição**. Tudo o que a requisição grava fica numa
transação só:
- resposta de sucesso → **COMMIT** (grava tudo);
- exceção **ou** resposta de erro (status ≥ 400) → **ROLLBACK** (desfaz tudo).

Exemplo: "concluir treino" grava recordes, perfil, histórico e duelo. Se o último passo falhar, os
anteriores são desfeitos. Isso é a **atomicidade**, o "A" do ACID, e o teste `test_concluir_treino_atomico`
comprova. Além disso, `buscar_perfil` usa `SELECT ... FOR UPDATE` para que dois treinos concluídos
ao mesmo tempo não sobrescrevam o XP um do outro.

---

## 6. Para cada parte do grupo

### Front-end
O `app.js` busca todos os dados na API. Não há dados fixos no JS.
- Se o front rodar pelo servidor Python (porta 5000), funciona direto.
- Se rodar pelo Live Server (VS Code, porta 5500), ele chama `http://localhost:5000` sozinho.
  O servidor precisa estar ligado.
- Outro endereço (ex.: testar no celular pela rede): no `index.html`, descomente
  `window.API_URL = "http://SEU_IP:5000"`.

### Banco de dados
- **Toda consulta SQL fica no `repositorio.py`.** Cada função tem, no docstring, o formato exato que
  devolve. As rotas e o `gamificacao.py` não sabem que existe SQL.
- **Para criar uma consulta nova:** escreva a função no `repositorio.py` usando `_todos`, `_um` ou
  `_executar`, passe os valores como parâmetros (`%s`) e **não chame `commit()`**. O `conexao.py` faz
  o commit no fim da requisição.
- **Mudou o `schema.sql`?** Atualize o `seed.py` e o `diagrama.md` e rode `python db\seed.py -y`.

---

## 7. Rotas da API (contrato)

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
| GET | `/ranking` | `?categoria=Evoluídos` (ou Moderados, Iniciantes) | Lista ordenada por XP total (só matrículas ativas) |
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

## 8. Regras de gamificação

Ficam em `gamificacao.py`:

- XP do treino: A = 120, B = 130, C = 140.
- **+50 XP** no primeiro treino do dia (mantém a sequência).
- **+100 XP** por recorde pessoal batido (carga maior que a anterior no mesmo exercício).
- A cada **3.000 XP** sobe um nível.
- Títulos por nível: 1–5 Iniciante, 6–10 Moderado, 11–15 Intermediário, 16–20 Avançado, 21+ Evoluído.
- Sequência: treinou ontem e treinou hoje → +1 dia; ficou um dia sem treinar → volta para 1.
- Próximo treino segue o rodízio A → B → C.
- Ranking: ordenado pelo **XP total** = nível × 3.000 + XP dentro do nível.
- Progresso no desafio da semana = treinos concluídos nos **últimos 7 dias** (até a meta de 5).

---

## 9. Roteiro da apresentação

### Antes de apresentar

1. **Rode o seed no dia da apresentação** (ou no máximo 3 dias antes):
   ```powershell
   python db\seed.py -y
   ```
   Os dados são relativos ao dia em que o seed roda (D). O desafio dura até D+7, mas o ponto de
   partida do Lucas envelhece:

   | Apresentação em | Barra do desafio ao abrir | Sequência ao concluir um treino | Duelo ativo |
   |---|---|---|---|
   | D (mesmo dia) — **ideal** | 3/5 | 3 → **4 dias** | sim |
   | D+1 a D+3 | 3/5 | recomeça em 1 dia | sim |
   | D+4 / D+5 | 2/5 / 1/5 | recomeça em 1 dia | sim |
   | D+6 / D+7 | 0/5 | recomeça em 1 dia | não |
   | D+8 em diante | desafio encerrado | recomeça em 1 dia | não |

2. Dê dois cliques no **`iniciar.bat`**: ele sobe o servidor e abre <http://localhost:5000>.
3. Logins: Lucas (`lucas.oliveira@email.com` / `senha1234567`, já vem preenchido na tela) e admin
   (botão **"Acesso da academia"**).

### Sequência para mostrar (estado logo após o seed)

1. **Tela inicial do Lucas:** Nível 12 — Intermediário, **2.450 / 3.000 XP**, 🔥 3 dias, #4 no ranking.
2. **Perfil → Desafios:** "Desafio Semanal de Cardio" com **3/5 treinos**. Clique em **Participar**
   (12 → 13 participantes).
3. **Concluir treino:** na tela inicial, **Começar Treino** (Treino A).
   - No Supino Reto, aperte **+** três vezes (40 → **47,5 kg**) para bater o recorde de 45 kg.
   - Vá clicando em **Concluir série** e em **Pular intervalo** até o fim.
   - Tela "Treino Concluído!": **+270 XP** (treino 120 + sequência 50 + recorde 100) e o aviso
     **"Novo Recorde Pessoal!"**.
4. **XP e barra subindo:**
   - Tela inicial: **2.720 / 3.000 XP**, 🔥 4 dias.
   - Desafios: **4/5**.
   - Treinos → Histórico: o treino de "Hoje" e o recorde de **47,5 kg** no Supino.
   - *Opcional:* conclua o Treino B (+130 XP, sem bônus de sequência, porque já treinou hoje) para
     ver a barra chegar a **5/5**.
   - *Opcional:* em Duelos, o XP do Lucas contra a Maria Silva também subiu (1.850 → 2.120).
5. **Ranking (Evoluídos):** Lucas em **#4**, com **38.720 XP** no total (era 38.450 antes do treino).
6. **Painel admin:** Perfil → **Sair da conta** → **Acesso da academia**.
   - Painel: **22 / 23** alunos ativos, receita do mês e inadimplência calculadas dos pagamentos.
   - Membros → **Camila Rocha** → **Desativar Aluno**. O painel passa a mostrar **21 / 23**, e o
     Financeiro mostra +1 cancelamento.
7. **Fechando o ciclo:** saia, entre de novo como Lucas e abra o Ranking. A Camila **sumiu** (matrícula
   inativa) e o Lucas subiu para **#3**.
8. *Opcional (persistência):* com o Lucas logado no navegador, pare o servidor (Ctrl+C) e suba
   de novo. **Sem recarregar a página**, clique em outra aba: o app continua logado (a sessão está
   no banco) e o XP, o histórico e o ranking sem a Camila continuam lá. Não aperte F5: o front
   guarda o token só na memória da página, então recarregar volta para a tela de login, mesmo
   com a sessão ainda válida no banco.

**Depois da apresentação:** `python db\seed.py -y` volta tudo ao estado inicial.

---

## 10. Limitações conhecidas

1. **Duelos vencidos não mudam para `encerrado`.** Eles só deixam de aparecer depois de `termina_em`.
   Mudar o status exigiria uma rotina agendada.
2. **Aluno sem matrícula não aparece no painel.** Para o sistema, "membro" = aluno + matrícula.
3. **Não existe rota para cadastrar aluno** (nem matrícula ou pagamento). Esses dados entram pelo seed.
   Os botões "Criar conta" e "Esqueci minha senha" do app ainda não fazem nada.
4. **Títulos não são liberados automaticamente.** Só existem os que o seed liberou. Medalhas, ao
   contrário, têm o progresso calculado na hora.
5. **O progresso do desafio conta os últimos 7 dias**, e não o período do desafio (regra do
   `gamificacao.py`). A recompensa de XP ao fim do desafio ainda não é entregue.
6. **O gráfico de evolução mostra o recorde, que só sobe**, e não a carga de cada treino: a API não
   grava a carga de cada exercício por treino, só os recordes.
7. **A meta de frequência mensal é fixa (10 dias)** e a frequência do painel ("3x/sem") é a média dos
   últimos 28 dias.
8. **Os dados do seed são relativos ao dia em que ele roda** (veja o roteiro acima).
9. **Uma conexão por requisição, sem pool.** É suficiente para o trabalho; com muitos usuários
    simultâneos valeria usar um pool de conexões.

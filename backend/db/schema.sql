-- =====================================================================
-- GymSystem - esquema do banco de dados
-- Compatível com MySQL 8 e MariaDB 10.4+ (XAMPP).
--
-- Como usar:
--   * Jeito fácil: python db/seed.py   (cria o banco, roda este arquivo e insere os dados)
--   * Manual (Workbench / phpMyAdmin): crie o banco, selecione-o e rode este arquivo:
--       CREATE DATABASE gymsystem CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
--       USE gymsystem
--
-- ATENÇÃO: rodar este arquivo APAGA as tabelas e todos os dados (DROP TABLE).
--
-- Convenções:
--   * utf8mb4: guarda qualquer caractere, inclusive emoji. O "utf8" antigo do MySQL não guarda.
--   * utf8mb4_unicode_ci: ignora maiúsculas/minúsculas e acentos nas comparações
--     (existe no MySQL e no MariaDB).
--   * InnoDB: motor que suporta chaves estrangeiras (FK) e transações.
--   * Dinheiro em DECIMAL (exato), nunca FLOAT (tem erro de arredondamento).
--   * Datas em DATE. O repositorio.py converte para texto ISO ("2026-09-25").
--   * BOOLEAN no MySQL/MariaDB é TINYINT(1): 0 = falso, 1 = verdadeiro.
--   * ON DELETE CASCADE: apagar o usuário apaga junto os dados "dele" (perfil, histórico...).
--     ON DELETE RESTRICT: impede apagar (ex.: aluno com matrícula/pagamento - registro financeiro
--     não pode sumir).
-- Regra deste arquivo: nenhum ponto e vírgula dentro de comentários (o seed.py separa
-- os comandos por ele).
-- =====================================================================

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS pagamentos;
DROP TABLE IF EXISTS matriculas;
DROP TABLE IF EXISTS planos;
DROP TABLE IF EXISTS desafios_academia;
DROP TABLE IF EXISTS participacoes;
DROP TABLE IF EXISTS desafios;
DROP TABLE IF EXISTS duelos;
DROP TABLE IF EXISTS medalhas;
DROP TABLE IF EXISTS usuario_titulos;
DROP TABLE IF EXISTS titulos;
DROP TABLE IF EXISTS recordes;
DROP TABLE IF EXISTS historico_treinos;
DROP TABLE IF EXISTS treino_exercicios;
DROP TABLE IF EXISTS exercicios;
DROP TABLE IF EXISTS treinos;
DROP TABLE IF EXISTS configuracoes_usuario;
DROP TABLE IF EXISTS opcoes_configuracao;
DROP TABLE IF EXISTS perfis;
DROP TABLE IF EXISTS categorias_ranking;
DROP TABLE IF EXISTS usuarios;
SET FOREIGN_KEY_CHECKS = 1;


-- =====================================================================
-- 1. PESSOAS E ACESSO
-- =====================================================================

-- Todo mundo que usa o sistema: alunos (app + painel + ranking) e administradores.
-- "Membro" do painel = usuário com papel 'aluno' + matrícula.
CREATE TABLE usuarios (
    id          INT          NOT NULL AUTO_INCREMENT,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL,
    senha_hash  VARCHAR(255) NOT NULL,              -- hash do werkzeug, NUNCA a senha
    papel       ENUM('aluno', 'admin') NOT NULL,
    cpf         CHAR(14)     NULL,                  -- "123.456.789-00", admin não tem
    criado_em   DATE         NOT NULL,              -- vira o campo "cadastro" do painel
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuarios_email (email),
    UNIQUE KEY uq_usuarios_cpf (cpf)                -- UNIQUE aceita vários NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- =====================================================================
-- 2. GAMIFICAÇÃO DO ALUNO
-- =====================================================================

-- Categorias do ranking. Tabela própria para a lista existir mesmo se nenhuma pessoa estiver nela.
CREATE TABLE categorias_ranking (
    nome   VARCHAR(30) NOT NULL,
    ordem  TINYINT     NOT NULL,                    -- ordem de exibição
    PRIMARY KEY (nome)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Perfil de jogo do aluno (relação 1:1 com usuarios: a PK também é FK).
-- Os contadores (treinos_feitos, sequencia...) são calculados pelo gamificacao.py e gravados
-- aqui. É uma desnormalização consciente: não temos o histórico completo de todos os treinos.
CREATE TABLE perfis (
    usuario_id         INT         NOT NULL,
    nivel              INT         NOT NULL DEFAULT 1,
    xp                 INT         NOT NULL DEFAULT 0,  -- XP dentro do nível atual (zera a cada 3000)
    sequencia          INT         NOT NULL DEFAULT 0,
    melhor_sequencia   INT         NOT NULL DEFAULT 0,
    treinos_feitos     INT         NOT NULL DEFAULT 0,
    ultimo_treino      DATE        NULL,
    frequencia_ativos  INT         NOT NULL DEFAULT 0,  -- dias ativos no mês de frequencia_mes
    frequencia_meta    INT         NOT NULL DEFAULT 10,
    frequencia_mes     CHAR(7)     NULL,                -- "2026-10". Mês virou = ativos volta a 0
    categoria_ranking  VARCHAR(30) NOT NULL,
    emoji              VARCHAR(16) NULL,                -- avatar no ranking
    PRIMARY KEY (usuario_id),
    KEY ix_perfis_ranking (categoria_ranking, nivel, xp),  -- acelera o ORDER BY do ranking
    CONSTRAINT fk_perfis_usuario   FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_perfis_categoria FOREIGN KEY (categoria_ranking) REFERENCES categorias_ranking (nome)
        ON UPDATE CASCADE,
    CONSTRAINT ck_perfis_valores CHECK (nivel >= 1 AND xp >= 0 AND sequencia >= 0
        AND melhor_sequencia >= 0 AND treinos_feitos >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Quais configurações existem e o valor padrão de cada uma.
CREATE TABLE opcoes_configuracao (
    chave   VARCHAR(40)  NOT NULL,
    rotulo  VARCHAR(100) NOT NULL,
    padrao  BOOLEAN      NOT NULL,
    ordem   TINYINT      NOT NULL,                  -- ordem de exibição na tela de perfil
    PRIMARY KEY (chave)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Só o que o aluno mudou. Sem linha aqui = vale o padrão (LEFT JOIN no repositorio.py).
CREATE TABLE configuracoes_usuario (
    usuario_id  INT         NOT NULL,
    chave       VARCHAR(40) NOT NULL,
    valor       BOOLEAN     NOT NULL,
    PRIMARY KEY (usuario_id, chave),                -- PK composta: 1 valor por aluno por chave
    CONSTRAINT fk_config_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_config_chave   FOREIGN KEY (chave) REFERENCES opcoes_configuracao (chave) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- =====================================================================
-- 3. TREINOS, HISTÓRICO E RECORDES
-- =====================================================================

CREATE TABLE treinos (
    codigo   CHAR(1)      NOT NULL,                 -- 'A', 'B', 'C'
    nome     VARCHAR(50)  NOT NULL,
    grupo    VARCHAR(100) NOT NULL,                 -- "Peito e Tríceps"
    minutos  INT          NOT NULL,
    xp       INT          NOT NULL,
    PRIMARY KEY (codigo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Catálogo de exercícios: cada exercício existe uma vez só, mesmo que apareça em vários treinos.
CREATE TABLE exercicios (
    id     INT          NOT NULL AUTO_INCREMENT,
    nome   VARCHAR(100) NOT NULL,
    grupo  VARCHAR(50)  NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_exercicios_nome (nome)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Relação N:N treino <-> exercício, com os dados da prescrição (séries, reps, carga sugerida).
CREATE TABLE treino_exercicios (
    treino_codigo  CHAR(1)      NOT NULL,
    ordem          TINYINT      NOT NULL,           -- posição do exercício dentro do treino (1, 2, 3...)
    exercicio_id   INT          NOT NULL,
    series         TINYINT      NOT NULL,
    reps           TINYINT      NOT NULL,
    carga          DECIMAL(6,2) NOT NULL,           -- kg sugeridos
    PRIMARY KEY (treino_codigo, ordem),
    KEY ix_te_exercicio (exercicio_id),
    CONSTRAINT fk_te_treino    FOREIGN KEY (treino_codigo) REFERENCES treinos (codigo) ON DELETE CASCADE,
    CONSTRAINT fk_te_exercicio FOREIGN KEY (exercicio_id) REFERENCES exercicios (id),
    CONSTRAINT ck_te_valores CHECK (series > 0 AND reps > 0 AND carga >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Cada treino concluído por um aluno.
CREATE TABLE historico_treinos (
    id             INT     NOT NULL AUTO_INCREMENT,
    usuario_id     INT     NOT NULL,
    treino_codigo  CHAR(1) NOT NULL,
    data           DATE    NOT NULL,
    minutos        INT     NOT NULL,
    exercicios     INT     NOT NULL,                -- quantos exercícios foram feitos
    xp             INT     NOT NULL,                -- XP ganho no treino (com bônus)
    PRIMARY KEY (id),
    KEY ix_historico_usuario_data (usuario_id, data),  -- "últimos treinos do aluno X"
    KEY ix_historico_treino (treino_codigo),
    CONSTRAINT fk_historico_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_historico_treino  FOREIGN KEY (treino_codigo) REFERENCES treinos (codigo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Histórico de recordes: uma linha cada vez que o aluno bate a própria marca.
--   recorde atual        = MAX(carga) por exercício
--   gráfico de evolução  = recorde vigente no fim de cada semana / mês / ano
CREATE TABLE recordes (
    id            INT          NOT NULL AUTO_INCREMENT,
    usuario_id    INT          NOT NULL,
    exercicio_id  INT          NOT NULL,
    carga         DECIMAL(6,2) NOT NULL,
    data          DATE         NOT NULL,
    PRIMARY KEY (id),
    KEY ix_recordes_usuario (usuario_id, exercicio_id, data),
    KEY ix_recordes_exercicio (exercicio_id),
    CONSTRAINT fk_recordes_usuario   FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_recordes_exercicio FOREIGN KEY (exercicio_id) REFERENCES exercicios (id),
    CONSTRAINT ck_recordes_carga CHECK (carga >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- =====================================================================
-- 4. CONQUISTAS
-- =====================================================================

-- Catálogo de títulos.
CREATE TABLE titulos (
    id         INT          NOT NULL AUTO_INCREMENT,
    icone      VARCHAR(16)  NOT NULL,
    nome       VARCHAR(50)  NOT NULL,
    descricao  VARCHAR(200) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_titulos_nome (nome)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Títulos que cada aluno já liberou (existe linha = liberado).
CREATE TABLE usuario_titulos (
    usuario_id   INT  NOT NULL,
    titulo_id    INT  NOT NULL,
    liberado_em  DATE NOT NULL,
    PRIMARY KEY (usuario_id, titulo_id),
    KEY ix_ut_titulo (titulo_id),
    CONSTRAINT fk_ut_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_ut_titulo  FOREIGN KEY (titulo_id) REFERENCES titulos (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Catálogo de medalhas (igual para todos). O progresso é calculado no gamificacao.py
-- a partir do "contador" (qual número do perfil alimenta a medalha).
CREATE TABLE medalhas (
    id         INT          NOT NULL AUTO_INCREMENT,
    icone      VARCHAR(16)  NOT NULL,
    nome       VARCHAR(50)  NOT NULL,
    descricao  VARCHAR(200) NOT NULL,
    meta       INT          NOT NULL,
    contador   ENUM('treinos_feitos', 'melhor_sequencia', 'recordes') NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_medalhas_nome (nome)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- =====================================================================
-- 5. SOCIAL: DUELOS E DESAFIOS
-- =====================================================================

-- Convite e duelo são a MESMA coisa em momentos diferentes:
--   pendente (convite) -> ativo (aceito) ou recusado -> encerrado
-- Duas FKs para a mesma tabela (usuarios): quem desafiou e quem foi desafiado.
CREATE TABLE duelos (
    id              INT          NOT NULL AUTO_INCREMENT,
    desafiante_id   INT          NOT NULL,
    desafiado_id    INT          NOT NULL,
    objetivo        VARCHAR(100) NOT NULL,          -- "Mais XP em 7 dias", "Foco em Pernas"
    dias            INT          NOT NULL,          -- duração combinada
    status          ENUM('pendente', 'ativo', 'recusado', 'encerrado') NOT NULL DEFAULT 'pendente',
    criado_em       DATE         NOT NULL,
    inicio          DATE         NULL,              -- preenchido quando o convite é aceito
    termina_em      DATE         NULL,
    xp_desafiante   INT          NOT NULL DEFAULT 0,
    xp_desafiado    INT          NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY ix_duelos_desafiante (desafiante_id, status),
    KEY ix_duelos_desafiado (desafiado_id, status),
    -- RESTRICT (padrão) e não CASCADE: o MySQL não deixa usar no CHECK uma coluna com CASCADE.
    CONSTRAINT fk_duelos_desafiante FOREIGN KEY (desafiante_id) REFERENCES usuarios (id),
    CONSTRAINT fk_duelos_desafiado  FOREIGN KEY (desafiado_id) REFERENCES usuarios (id),
    CONSTRAINT ck_duelos_oponentes CHECK (desafiante_id <> desafiado_id),  -- ninguém duela consigo
    CONSTRAINT ck_duelos_dias CHECK (dias > 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Competições com prazo. Ativa = hoje entre inicio e termina_em.
CREATE TABLE desafios (
    id             INT          NOT NULL AUTO_INCREMENT,
    nome           VARCHAR(100) NOT NULL,
    meta           VARCHAR(200) NOT NULL,
    recompensa_xp  INT          NOT NULL,
    treinos_meta   INT          NOT NULL,
    inicio         DATE         NOT NULL,
    termina_em     DATE         NOT NULL,
    PRIMARY KEY (id),
    KEY ix_desafios_periodo (inicio, termina_em),
    CONSTRAINT ck_desafios_periodo CHECK (termina_em >= inicio)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Quem está participando de cada desafio (N:N usuarios <-> desafios).
CREATE TABLE participacoes (
    desafio_id  INT  NOT NULL,
    usuario_id  INT  NOT NULL,
    entrou_em   DATE NOT NULL,
    PRIMARY KEY (desafio_id, usuario_id),
    KEY ix_participacoes_usuario (usuario_id),
    CONSTRAINT fk_part_desafio FOREIGN KEY (desafio_id) REFERENCES desafios (id) ON DELETE CASCADE,
    CONSTRAINT fk_part_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Metas fixas divulgadas pela academia.
CREATE TABLE desafios_academia (
    id         INT          NOT NULL AUTO_INCREMENT,
    icone      VARCHAR(16)  NOT NULL,
    nome       VARCHAR(100) NOT NULL,
    descricao  VARCHAR(200) NOT NULL,
    xp         INT          NOT NULL,
    status     ENUM('Pendente', 'Finalizado') NOT NULL DEFAULT 'Pendente',
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- =====================================================================
-- 6. ADMINISTRAÇÃO: PLANOS, MATRÍCULAS E PAGAMENTOS
-- =====================================================================

CREATE TABLE planos (
    id             INT           NOT NULL AUTO_INCREMENT,
    nome           VARCHAR(50)   NOT NULL,
    preco          DECIMAL(10,2) NOT NULL,          -- preço de tabela do pacote
    duracao_meses  INT           NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_planos_nome (nome),
    CONSTRAINT ck_planos_valores CHECK (preco >= 0 AND duracao_meses > 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Contrato do aluno com a academia. Um aluno pode ter várias ao longo do tempo
-- (renovou, cancelou, voltou). A atual é a mais recente.
CREATE TABLE matriculas (
    id            INT           NOT NULL AUTO_INCREMENT,
    usuario_id    INT           NOT NULL,
    plano_id      INT           NOT NULL,
    valor_mensal  DECIMAL(10,2) NOT NULL,           -- valor contratado (pode ter desconto)
    data_inicio   DATE          NOT NULL,
    vencimento    DATE          NOT NULL,           -- fim da vigência do contrato
    ativo         BOOLEAN       NOT NULL DEFAULT TRUE,
    cancelada_em  DATE          NULL,               -- preenchida ao desativar o aluno
    PRIMARY KEY (id),
    KEY ix_matriculas_usuario (usuario_id),
    KEY ix_matriculas_plano (plano_id),
    KEY ix_matriculas_vencimento (vencimento),
    -- RESTRICT: aluno com matrícula não pode ser apagado (é registro financeiro).
    CONSTRAINT fk_matriculas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    CONSTRAINT fk_matriculas_plano   FOREIGN KEY (plano_id) REFERENCES planos (id),
    CONSTRAINT ck_matriculas_valores CHECK (valor_mensal >= 0 AND vencimento >= data_inicio)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Uma mensalidade por matrícula por mês. confirmado = pago_em preenchido.
CREATE TABLE pagamentos (
    id            INT           NOT NULL AUTO_INCREMENT,
    matricula_id  INT           NOT NULL,
    referencia    DATE          NOT NULL,           -- 1º dia do mês cobrado (2026-10-01)
    valor         DECIMAL(10,2) NOT NULL,
    vencimento    DATE          NOT NULL,           -- data limite para pagar
    pago_em       DATE          NULL,               -- NULL = pendente
    PRIMARY KEY (id),
    UNIQUE KEY uq_pagamentos_mes (matricula_id, referencia),  -- não cobra o mesmo mês duas vezes
    KEY ix_pagamentos_referencia (referencia),
    CONSTRAINT fk_pagamentos_matricula FOREIGN KEY (matricula_id) REFERENCES matriculas (id),
    CONSTRAINT ck_pagamentos_valor CHECK (valor >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

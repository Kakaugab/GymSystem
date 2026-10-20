"""
REPOSITÓRIO — camada de acesso aos dados (MySQL / MariaDB).

Este é o ÚNICO arquivo do back-end que conhece o banco. As rotas (pasta rotas/) e as regras de
negócio (gamificacao.py) chamam as funções daqui sem saber que existe SQL por trás.
Cada função mantém o MESMO nome, os MESMOS parâmetros e o MESMO formato de retorno de quando
os dados ficavam em memória (descritos em cada docstring).

Regras seguidas em todo o arquivo:
  * Consultas SEMPRE parametrizadas: os valores vão separados do SQL (%s ou %(nome)s) e o driver
    os escapa. Nunca montamos SQL com f-string/concatenação de valores -> sem SQL Injection.
  * Conexão e transação: conexao.obter() devolve a conexão da requisição atual. Ninguém aqui
    chama commit(): quem decide COMMIT/ROLLBACK é o db/conexao.py, ao fim da requisição.
    Assim, tudo o que o "concluir treino" grava (recordes, perfil, histórico, duelo) entra ou
    sai junto.
  * Conversões para manter o contrato da API:
      DATE    -> texto ISO ("2026-09-25")
      DECIMAL -> int/float (o Flask transformaria Decimal em texto no JSON)
      TINYINT -> bool
  * "Hoje" vem do Python (date.today()), igual ao gamificacao.py, para os dois concordarem.
"""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from db import conexao

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


# =========================================================== AUXILIARES
def _todos(sql, params=None):
    """Executa um SELECT e devolve todas as linhas (lista de dicionários)."""
    with conexao.obter().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _um(sql, params=None):
    """Executa um SELECT e devolve a primeira linha (ou None)."""
    with conexao.obter().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _executar(sql, params=None):
    """Executa INSERT/UPDATE/DELETE e devolve quantas linhas foram afetadas."""
    with conexao.obter().cursor() as cur:
        return cur.execute(sql, params)


def _iso(d):
    return d.isoformat() if d else None


def _num(v):
    """Decimal('45.00') -> 45 ; Decimal('74.83') -> 74.83"""
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return v


def _somar_meses(d, meses):
    """Primeiro dia do mês, 'meses' para frente (ou para trás, se negativo)."""
    total = d.year * 12 + d.month - 1 + meses
    return date(total // 12, total % 12 + 1, 1)


# =========================================================== USUÁRIOS
def buscar_usuario_por_email(email):
    """-> {id, nome, email, senha_hash, papel('aluno'|'admin')} ou None"""
    # A collation utf8mb4_unicode_ci ignora maiúsculas: "Lucas@Email.com" também encontra.
    return _um("SELECT id, nome, email, senha_hash, papel FROM usuarios WHERE email = %s", (email,))


def buscar_usuario_por_id(usuario_id):
    """-> mesmo formato de buscar_usuario_por_email, ou None"""
    return _um("SELECT id, nome, email, senha_hash, papel FROM usuarios WHERE id = %s", (usuario_id,))


# =========================================================== TREINOS
def _treinos(codigo):
    """codigo=None -> todos os treinos. Duas consultas: os treinos e os exercícios de cada um."""
    filtro = {"codigo": codigo}
    treinos = _todos("SELECT codigo, nome, grupo, minutos, xp FROM treinos "
                     "WHERE (%(codigo)s IS NULL OR codigo = %(codigo)s) ORDER BY codigo", filtro)
    exercicios = _todos(
        "SELECT te.treino_codigo, e.nome, e.grupo, te.series, te.reps, te.carga "
        "FROM treino_exercicios te JOIN exercicios e ON e.id = te.exercicio_id "
        "WHERE (%(codigo)s IS NULL OR te.treino_codigo = %(codigo)s) "
        "ORDER BY te.treino_codigo, te.ordem", filtro)
    por_treino = defaultdict(list)
    for ex in exercicios:
        por_treino[ex["treino_codigo"]].append({"nome": ex["nome"], "grupo": ex["grupo"], "series": ex["series"],
                                                "reps": ex["reps"], "carga": _num(ex["carga"])})
    for t in treinos:
        t["exercicios"] = por_treino[t["codigo"]]
    return treinos


def listar_treinos():
    """-> [{codigo, nome, grupo, minutos, xp, exercicios:[{nome, grupo, series, reps, carga}]}]"""
    return _treinos(None)


def buscar_treino(codigo):
    """-> um treino (formato acima) ou None"""
    lista = _treinos(codigo)
    return lista[0] if lista else None


# =========================================================== PERFIL DO ALUNO
def buscar_perfil(usuario_id):
    """-> {nivel, xp, sequencia, melhor_sequencia, ultimo_treino(data|None), treinos_feitos,
           categoria_ranking, frequencia_mes:{ativos, meta}, config:{chave: bool}} ou None"""
    # FOR UPDATE trava a linha do perfil até o fim da requisição (COMMIT/ROLLBACK).
    # Sem isso, dois "concluir treino" ao mesmo tempo (ex.: duas abas) leriam o mesmo XP,
    # e o segundo a gravar apagaria o ganho do primeiro ("lost update").
    p = _um("SELECT nivel, xp, sequencia, melhor_sequencia, ultimo_treino, treinos_feitos, categoria_ranking, "
            "frequencia_ativos, frequencia_meta, frequencia_mes "
            "FROM perfis WHERE usuario_id = %s FOR UPDATE", (usuario_id,))
    if not p:
        return None
    # Os dias ativos são do mês gravado em frequencia_mes. Se o mês virou, o aluno começa do zero.
    ativos = p["frequencia_ativos"] if p["frequencia_mes"] == date.today().strftime("%Y-%m") else 0
    # Configurações: todas as opções existentes, com o valor do aluno ou, se ele nunca mudou, o padrão.
    config = _todos("SELECT o.chave, COALESCE(c.valor, o.padrao) AS valor FROM opcoes_configuracao o "
                    "LEFT JOIN configuracoes_usuario c ON c.chave = o.chave AND c.usuario_id = %s "
                    "ORDER BY o.chave", (usuario_id,))
    return {"nivel": p["nivel"], "xp": p["xp"], "sequencia": p["sequencia"],
            "melhor_sequencia": p["melhor_sequencia"], "ultimo_treino": _iso(p["ultimo_treino"]),
            "treinos_feitos": p["treinos_feitos"], "categoria_ranking": p["categoria_ranking"],
            "frequencia_mes": {"ativos": ativos, "meta": p["frequencia_meta"]},
            "config": {c["chave"]: bool(c["valor"]) for c in config}}


def salvar_perfil(usuario_id, perfil):
    """Grava o perfil inteiro (mesmo formato de buscar_perfil)."""
    _executar("UPDATE perfis SET nivel = %s, xp = %s, sequencia = %s, melhor_sequencia = %s, "
              "treinos_feitos = %s, ultimo_treino = %s, frequencia_ativos = %s, frequencia_meta = %s, "
              "frequencia_mes = %s, categoria_ranking = %s WHERE usuario_id = %s",
              (perfil["nivel"], perfil["xp"], perfil["sequencia"], perfil["melhor_sequencia"],
               perfil["treinos_feitos"], perfil["ultimo_treino"], perfil["frequencia_mes"]["ativos"],
               perfil["frequencia_mes"]["meta"], date.today().strftime("%Y-%m"),
               perfil["categoria_ranking"], usuario_id))
    # Configurações: só guardamos o que é DIFERENTE do padrão (igual ao padrão = apaga a linha).
    padroes = {o["chave"]: bool(o["padrao"]) for o in _todos("SELECT chave, padrao FROM opcoes_configuracao")}
    for chave, valor in perfil.get("config", {}).items():
        if chave not in padroes:
            continue
        if bool(valor) == padroes[chave]:
            _executar("DELETE FROM configuracoes_usuario WHERE usuario_id = %s AND chave = %s", (usuario_id, chave))
        else:
            # "Upsert": insere; se a linha já existe (PK repetida), só atualiza o valor.
            _executar("INSERT INTO configuracoes_usuario (usuario_id, chave, valor) VALUES (%s, %s, %s) "
                      "ON DUPLICATE KEY UPDATE valor = %s", (usuario_id, chave, bool(valor), bool(valor)))


# =========================================================== HISTÓRICO E RECORDES
def listar_historico(usuario_id, limite=10):
    """-> [{data, treino(codigo), minutos, exercicios, xp}] do mais recente para o mais antigo"""
    linhas = _todos("SELECT data, treino_codigo AS treino, minutos, exercicios, xp FROM historico_treinos "
                    "WHERE usuario_id = %s ORDER BY data DESC, id DESC LIMIT %s", (usuario_id, int(limite)))
    for h in linhas:
        h["data"] = _iso(h["data"])
    return linhas


def adicionar_historico(usuario_id, registro):
    """registro = {data, treino, minutos, exercicios, xp}"""
    _executar("INSERT INTO historico_treinos (usuario_id, treino_codigo, data, minutos, exercicios, xp) "
              "VALUES (%s, %s, %s, %s, %s, %s)",
              (usuario_id, registro["treino"], registro["data"], registro["minutos"],
               registro["exercicios"], registro["xp"]))


def listar_recordes(usuario_id):
    """-> {nome_do_exercicio: carga_kg}"""
    # A tabela guarda TODOS os recordes batidos; o recorde atual é o maior (MAX) de cada exercício.
    linhas = _todos("SELECT e.nome, MAX(r.carga) AS carga FROM recordes r "
                    "JOIN exercicios e ON e.id = r.exercicio_id WHERE r.usuario_id = %s "
                    "GROUP BY e.id, e.nome ORDER BY e.id", (usuario_id,))
    return {r["nome"]: _num(r["carga"]) for r in linhas}


def salvar_recorde(usuario_id, exercicio, carga):
    # INSERT ... SELECT: troca o nome do exercício pelo id dele na mesma instrução.
    inseridas = _executar("INSERT INTO recordes (usuario_id, exercicio_id, carga, data) "
                          "SELECT %s, id, %s, %s FROM exercicios WHERE nome = %s",
                          (usuario_id, carga, date.today(), exercicio))
    if inseridas == 0:
        raise ValueError(f"Exercício desconhecido: {exercicio}")  # vira ROLLBACK da requisição toda


def buscar_evolucao_carga(usuario_id):
    """-> {exercicio, variacao, 'Semana'|'Mês'|'Geral': {rotulos:[...], valores:[...]}} ou None"""
    # Calculado a partir da tabela recordes: o exercício com mais recordes batidos e,
    # para cada período, o recorde que valia no fim dele.
    ex = _um("SELECT r.exercicio_id, e.nome FROM recordes r JOIN exercicios e ON e.id = r.exercicio_id "
             "WHERE r.usuario_id = %s GROUP BY r.exercicio_id, e.nome "
             "ORDER BY COUNT(*) DESC, MAX(r.data) DESC LIMIT 1", (usuario_id,))
    if not ex:
        return None
    marcas = _todos("SELECT data, carga FROM recordes WHERE usuario_id = %s AND exercicio_id = %s ORDER BY data",
                    (usuario_id, ex["exercicio_id"]))

    def recorde_em(dia):
        """Maior carga registrada até aquele dia (0 se ainda não tinha recorde)."""
        return max([_num(m["carga"]) for m in marcas if m["data"] <= dia], default=0)

    hoje = date.today()
    mes_atual = hoje.replace(day=1)
    semanas = [hoje - timedelta(weeks=n) for n in (3, 2, 1, 0)]
    meses = [_somar_meses(mes_atual, n) for n in (-3, -2, -1, 0)]
    fim_meses = [_somar_meses(m, 1) - timedelta(days=1) for m in meses[:-1]] + [hoje]
    anos = [hoje.year - n for n in (3, 2, 1, 0)]
    fim_anos = [date(a, 12, 31) for a in anos[:-1]] + [hoje]

    inicio = recorde_em(mes_atual - timedelta(days=1))  # recorde no último dia do mês passado
    atual = recorde_em(hoje)
    if inicio and atual > inicio:
        variacao = f"+{round((atual - inicio) / inicio * 100)}% este mês"
    elif not inicio and atual:
        variacao = "Primeiro recorde este mês"
    else:
        variacao = "Sem variação este mês"

    return {"exercicio": ex["nome"], "variacao": variacao,
            "Semana": {"rotulos": [f"Semana {i}" for i in range(1, 5)], "valores": [recorde_em(d) for d in semanas]},
            "Mês": {"rotulos": [MESES[m.month - 1] for m in meses], "valores": [recorde_em(d) for d in fim_meses]},
            "Geral": {"rotulos": [str(a) for a in anos], "valores": [recorde_em(d) for d in fim_anos]}}


# =========================================================== CONQUISTAS
def listar_titulos(usuario_id):
    """-> [{icone, nome, descricao, liberado}]"""
    # LEFT JOIN: traz todos os títulos do catálogo; "liberado" = o aluno tem a linha em usuario_titulos.
    linhas = _todos("SELECT t.icone, t.nome, t.descricao, ut.titulo_id IS NOT NULL AS liberado FROM titulos t "
                    "LEFT JOIN usuario_titulos ut ON ut.titulo_id = t.id AND ut.usuario_id = %s "
                    "ORDER BY t.id", (usuario_id,))
    for t in linhas:
        t["liberado"] = bool(t["liberado"])
    return linhas


def listar_medalhas(usuario_id):
    """-> [{icone, nome, descricao, meta, contador}]  (o progresso é calculado no gamificacao.py)"""
    # As medalhas são um catálogo igual para todos (por isso usuario_id não entra na consulta).
    return _todos("SELECT icone, nome, descricao, meta, contador FROM medalhas ORDER BY id")


# =========================================================== RANKING
def listar_categorias_ranking():
    return [c["nome"] for c in _todos("SELECT nome FROM categorias_ranking ORDER BY ordem")]


def listar_ranking(categoria):
    """-> [{usuario_id|None, nome, xp, emoji}] ordenado por XP (maior primeiro), ou None se a categoria não existe"""
    if not _um("SELECT nome FROM categorias_ranking WHERE nome = %s", (categoria,)):
        return None
    # Ordem: nível maior primeiro e, no mesmo nível, mais XP (o XP zera a cada nível,
    # então ordenar só pelo XP colocaria um nível 18 com 100 XP atrás de um nível 2 com 900).
    return _todos("SELECT p.usuario_id, u.nome, p.xp, p.emoji FROM perfis p "
                  "JOIN usuarios u ON u.id = p.usuario_id WHERE p.categoria_ranking = %s "
                  "ORDER BY p.nivel DESC, p.xp DESC, u.nome", (categoria,))


# =========================================================== DUELOS
def buscar_duelo_ativo(usuario_id):
    """-> {id, oponente:{nome, nivel, xp}, xp_usuario, objetivo, termina_em} ou None"""
    # O usuário pode ser o desafiante OU o desafiado: os CASE escolhem "o meu lado" e "o lado do outro".
    d = _um("SELECT d.id, d.objetivo, d.termina_em, "
            "  CASE WHEN d.desafiante_id = %(u)s THEN d.xp_desafiante ELSE d.xp_desafiado END AS xp_usuario, "
            "  CASE WHEN d.desafiante_id = %(u)s THEN d.xp_desafiado ELSE d.xp_desafiante END AS xp_oponente, "
            "  o.nome AS oponente_nome, COALESCE(p.nivel, 1) AS oponente_nivel "
            "FROM duelos d "
            "JOIN usuarios o ON o.id = CASE WHEN d.desafiante_id = %(u)s THEN d.desafiado_id ELSE d.desafiante_id END "
            "LEFT JOIN perfis p ON p.usuario_id = o.id "
            "WHERE d.status = 'ativo' AND d.termina_em >= %(hoje)s "
            "  AND (d.desafiante_id = %(u)s OR d.desafiado_id = %(u)s) "
            "ORDER BY d.termina_em, d.id LIMIT 1", {"u": usuario_id, "hoje": date.today()})
    if not d:
        return None
    return {"id": d["id"],
            "oponente": {"nome": d["oponente_nome"], "nivel": d["oponente_nivel"], "xp": d["xp_oponente"]},
            "xp_usuario": d["xp_usuario"], "objetivo": d["objetivo"], "termina_em": _iso(d["termina_em"])}


def somar_xp_duelo(usuario_id, xp):
    # Soma no lado certo (desafiante ou desafiado) de todos os duelos ativos e ainda no prazo.
    _executar("UPDATE duelos SET "
              "  xp_desafiante = xp_desafiante + CASE WHEN desafiante_id = %(u)s THEN %(xp)s ELSE 0 END, "
              "  xp_desafiado  = xp_desafiado  + CASE WHEN desafiado_id  = %(u)s THEN %(xp)s ELSE 0 END "
              "WHERE status = 'ativo' AND inicio <= %(hoje)s AND termina_em >= %(hoje)s "
              "  AND (desafiante_id = %(u)s OR desafiado_id = %(u)s)",
              {"u": usuario_id, "xp": xp, "hoje": date.today()})


def listar_convites(usuario_id):
    """-> [{id, de, desafio, dias}]"""
    # Convite = duelo com status 'pendente' em que o usuário é o desafiado.
    return _todos("SELECT d.id, u.nome AS de, d.objetivo AS desafio, d.dias FROM duelos d "
                  "JOIN usuarios u ON u.id = d.desafiante_id "
                  "WHERE d.desafiado_id = %s AND d.status = 'pendente' "
                  "ORDER BY d.criado_em DESC, d.id DESC", (usuario_id,))


def responder_convite(usuario_id, convite_id, aceito):
    """Remove o convite pendente e registra a resposta. -> True se o convite existia."""
    # O convite sai da lista porque deixa de ser 'pendente'. Aceito -> vira duelo ativo a partir de hoje.
    # As condições no WHERE garantem que só o desafiado responde, e só uma vez.
    hoje = date.today()
    if aceito:
        alteradas = _executar("UPDATE duelos SET status = 'ativo', inicio = %s, "
                              "termina_em = DATE_ADD(%s, INTERVAL dias DAY) "
                              "WHERE id = %s AND desafiado_id = %s AND status = 'pendente'",
                              (hoje, hoje, convite_id, usuario_id))
    else:
        alteradas = _executar("UPDATE duelos SET status = 'recusado' "
                              "WHERE id = %s AND desafiado_id = %s AND status = 'pendente'",
                              (convite_id, usuario_id))
    return alteradas == 1


# =========================================================== DESAFIOS
def buscar_desafio_ativo():
    """-> {id, nome, meta, recompensa_xp, treinos_meta, termina_em} ou None"""
    hoje = date.today()
    d = _um("SELECT id, nome, meta, recompensa_xp, treinos_meta, termina_em FROM desafios "
            "WHERE inicio <= %s AND termina_em >= %s ORDER BY termina_em, id LIMIT 1", (hoje, hoje))
    if d:
        d["termina_em"] = _iso(d["termina_em"])
    return d


def contar_participantes(desafio_id):
    return _um("SELECT COUNT(*) AS n FROM participacoes WHERE desafio_id = %s", (desafio_id,))["n"]


def usuario_participa(usuario_id, desafio_id):
    return _um("SELECT 1 AS sim FROM participacoes WHERE desafio_id = %s AND usuario_id = %s",
               (desafio_id, usuario_id)) is not None


def definir_participacao(usuario_id, desafio_id, participa):
    if participa:
        # Se já participa (PK repetida), não faz nada: o UPDATE "entrou_em = entrou_em" não muda a linha.
        _executar("INSERT INTO participacoes (desafio_id, usuario_id, entrou_em) VALUES (%s, %s, %s) "
                  "ON DUPLICATE KEY UPDATE entrou_em = entrou_em", (desafio_id, usuario_id, date.today()))
    else:
        _executar("DELETE FROM participacoes WHERE desafio_id = %s AND usuario_id = %s", (desafio_id, usuario_id))


def listar_desafios_academia():
    """-> [{icone, nome, descricao, xp, status}]"""
    return _todos("SELECT icone, nome, descricao, xp, status FROM desafios_academia ORDER BY id")


# =========================================================== ADMINISTRAÇÃO
# Membro = usuário com papel 'aluno' + sua matrícula ATUAL (a mais recente).
# Este pedaço de SQL aparece em várias consultas: escolhe o id da matrícula atual do aluno u.
SQL_MATRICULA_ATUAL = ("SELECT m2.id FROM matriculas m2 WHERE m2.usuario_id = u.id "
                       "ORDER BY m2.data_inicio DESC, m2.id DESC LIMIT 1")

SQL_MEMBROS = (
    "SELECT u.id, u.nome, u.cpf, u.criado_em, "
    "  COALESCE(p.nivel, 1) AS nivel, COALESCE(p.sequencia, 0) AS sequencia, p.ultimo_treino, "
    "  m.ativo, m.valor_mensal, m.vencimento, pl.nome AS plano, "
    "  (SELECT COUNT(*) FROM historico_treinos h "
    "    WHERE h.usuario_id = u.id AND h.data > %(desde)s) AS treinos_28d "
    "FROM usuarios u "
    "JOIN matriculas m ON m.id = (" + SQL_MATRICULA_ATUAL + ") "
    "JOIN planos pl ON pl.id = m.plano_id "
    "LEFT JOIN perfis p ON p.usuario_id = u.id "
    "WHERE u.papel = 'aluno' AND (%(id)s IS NULL OR u.id = %(id)s) "
    "ORDER BY u.id")

# Os 3 treinos mais recentes de cada aluno. ROW_NUMBER() numera os treinos de cada aluno
# (PARTITION BY) do mais novo para o mais velho. Funciona no MySQL 8 e no MariaDB 10.2+.
SQL_TREINOS_RECENTES = (
    "SELECT usuario_id, data, minutos, xp, nome, grupo FROM ("
    "  SELECT h.usuario_id, h.data, h.minutos, h.xp, t.nome, t.grupo, "
    "    ROW_NUMBER() OVER (PARTITION BY h.usuario_id ORDER BY h.data DESC, h.id DESC) AS n "
    "  FROM historico_treinos h JOIN treinos t ON t.codigo = h.treino_codigo "
    "  WHERE (%(id)s IS NULL OR h.usuario_id = %(id)s)"
    ") x WHERE n <= 3 ORDER BY usuario_id, data DESC")


def _frequencia(treinos_28d):
    """Treinos nos últimos 28 dias -> média por semana: 12 -> '3x/sem'. Sem treinos -> ''."""
    if not treinos_28d:
        return ""
    return f"{max(1, round(treinos_28d / 4))}x/sem"


def _membros(membro_id=None):
    hoje = date.today()
    linhas = _todos(SQL_MEMBROS, {"id": membro_id, "desde": hoje - timedelta(days=28)})
    recentes = defaultdict(list)
    for t in _todos(SQL_TREINOS_RECENTES, {"id": membro_id}):
        recentes[t["usuario_id"]].append({"titulo": f"{t['nome']} — {t['grupo']}", "minutos": t["minutos"],
                                          "xp": t["xp"], "data": _iso(t["data"])})
    return [{"id": m["id"], "nome": m["nome"], "cpf": m["cpf"], "frequencia": _frequencia(m["treinos_28d"]),
             "nivel": m["nivel"], "ativo": bool(m["ativo"]), "sequencia": m["sequencia"],
             "ultimo_treino": _iso(m["ultimo_treino"]), "cadastro": _iso(m["criado_em"]),
             "plano": m["plano"], "valor_mensal": _num(m["valor_mensal"]), "vencimento": _iso(m["vencimento"]),
             "treinos_recentes": recentes[m["id"]]}
            for m in linhas]


def listar_membros():
    """-> [{id, nome, cpf, frequencia, nivel, ativo, sequencia, ultimo_treino, cadastro,
            plano, valor_mensal, vencimento, treinos_recentes:[{titulo, minutos, xp, data}]}]"""
    return _membros()


def buscar_membro(membro_id):
    lista = _membros(membro_id)
    return lista[0] if lista else None


def atualizar_status_membro(membro_id, ativo):
    """-> membro atualizado ou None"""
    # Ativar/desativar o aluno = ativar/desativar a matrícula atual dele.
    # (O MySQL não deixa um UPDATE consultar a própria tabela num subselect, por isso são 2 passos.)
    m = _um("SELECT m.id FROM matriculas m JOIN usuarios u ON u.id = m.usuario_id "
            "WHERE u.id = %s AND u.papel = 'aluno' "
            "ORDER BY m.data_inicio DESC, m.id DESC LIMIT 1 FOR UPDATE", (membro_id,))
    if not m:
        return None
    # Desativar grava a data do cancelamento (usada em "cancelamentos do mês"); reativar limpa.
    # COALESCE: se já estava cancelada, mantém a data original.
    _executar("UPDATE matriculas SET ativo = %s, "
              "cancelada_em = CASE WHEN %s THEN NULL ELSE COALESCE(cancelada_em, %s) END WHERE id = %s",
              (ativo, ativo, date.today(), m["id"]))
    return buscar_membro(membro_id)


def contar_membros():
    """-> (total_cadastrados, total_ativos)"""
    r = _um("SELECT COUNT(*) AS total, COALESCE(SUM(m.ativo), 0) AS ativos FROM usuarios u "
            "JOIN matriculas m ON m.id = (" + SQL_MATRICULA_ATUAL + ") WHERE u.papel = 'aluno'")
    return int(r["total"]), int(r["ativos"])


def listar_planos():
    """-> [{id, nome, preco, alunos_ativos}]"""
    linhas = _todos("SELECT pl.id, pl.nome, pl.preco, COUNT(m.id) AS alunos_ativos FROM planos pl "
                    "LEFT JOIN matriculas m ON m.plano_id = pl.id AND m.ativo = TRUE "
                    "GROUP BY pl.id, pl.nome, pl.preco ORDER BY pl.id")
    for p in linhas:
        p["preco"] = _num(p["preco"])
    return linhas


def resumo_contratos():
    """-> {vencendo_30d, vencidas, novos_mes}"""
    # SUM(condição) conta quantas linhas atendem a condição (verdadeiro = 1, falso = 0).
    hoje = date.today()
    r = _um("SELECT "
            "  COALESCE(SUM(ativo AND vencimento BETWEEN %(hoje)s AND %(em30)s), 0) AS vencendo_30d, "
            "  COALESCE(SUM(ativo AND vencimento < %(hoje)s), 0) AS vencidas, "
            "  COALESCE(SUM(data_inicio BETWEEN %(mes)s AND %(hoje)s), 0) AS novos_mes "
            "FROM matriculas",
            {"hoje": hoje, "em30": hoje + timedelta(days=30), "mes": hoje.replace(day=1)})
    return {k: int(v) for k, v in r.items()}


def listar_vencimentos():
    """-> [{aluno, plano, vence_em}]"""
    hoje = date.today()
    linhas = _todos("SELECT u.nome AS aluno, pl.nome AS plano, m.vencimento AS vence_em FROM matriculas m "
                    "JOIN usuarios u ON u.id = m.usuario_id JOIN planos pl ON pl.id = m.plano_id "
                    "WHERE m.ativo = TRUE AND m.vencimento BETWEEN %s AND %s "
                    "ORDER BY m.vencimento, u.nome LIMIT 10", (hoje, hoje + timedelta(days=30)))
    for v in linhas:
        v["vence_em"] = _iso(v["vence_em"])
    return linhas


def resumo_financeiro():
    """-> {receita_estimada, recebido, inadimplencia, cancelamentos_mes, evolucao:[{mes, valor}]}"""
    hoje = date.today()
    mes = hoje.replace(day=1)
    r = _um("SELECT "
            "  COALESCE(SUM(CASE WHEN referencia = %(mes)s THEN valor END), 0) AS receita_estimada, "
            "  COALESCE(SUM(CASE WHEN referencia = %(mes)s AND pago_em IS NOT NULL THEN valor END), 0) AS recebido, "
            "  COALESCE(SUM(CASE WHEN pago_em IS NULL AND vencimento < %(hoje)s THEN valor END), 0) AS inadimplencia "
            "FROM pagamentos", {"mes": mes, "hoje": hoje})
    cancelamentos = _um("SELECT COUNT(*) AS n FROM matriculas WHERE cancelada_em BETWEEN %s AND %s",
                        (mes, hoje))["n"]
    # Evolução: quanto foi efetivamente recebido em cada um dos últimos 6 meses.
    inicio = _somar_meses(mes, -5)
    pagos = {p["referencia"]: p["valor"] for p in _todos(
        "SELECT referencia, SUM(valor) AS valor FROM pagamentos "
        "WHERE pago_em IS NOT NULL AND referencia BETWEEN %s AND %s GROUP BY referencia", (inicio, mes))}
    evolucao = [{"mes": MESES[m.month - 1], "valor": _num(pagos.get(m, Decimal(0)))}
                for m in (_somar_meses(inicio, i) for i in range(6))]
    return {"receita_estimada": _num(r["receita_estimada"]), "recebido": _num(r["recebido"]),
            "inadimplencia": _num(r["inadimplencia"]), "cancelamentos_mes": cancelamentos, "evolucao": evolucao}


def listar_recebimentos():
    """-> [{aluno, plano, valor, confirmado}]"""
    # Mensalidades do mês atual: pendentes primeiro, depois as pagas mais recentes.
    linhas = _todos("SELECT u.nome AS aluno, pl.nome AS plano, pg.valor, pg.pago_em IS NOT NULL AS confirmado "
                    "FROM pagamentos pg JOIN matriculas m ON m.id = pg.matricula_id "
                    "JOIN usuarios u ON u.id = m.usuario_id JOIN planos pl ON pl.id = m.plano_id "
                    "WHERE pg.referencia = %s ORDER BY confirmado, pg.pago_em DESC, u.nome",
                    (date.today().replace(day=1),))
    for r in linhas:
        r["valor"] = _num(r["valor"])
        r["confirmado"] = bool(r["confirmado"])
    return linhas

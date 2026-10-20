"""
REPOSITÓRIO — camada de acesso aos dados.

>>> PARA O TIME DO BANCO DE DADOS <<<
Este é o ÚNICO arquivo do back-end que precisa mudar quando o banco ficar pronto.
Hoje cada função lê/grava nos dados de exemplo (memória). Para ligar no banco:
  1. troquem o CORPO de cada função por uma consulta (SELECT / INSERT / UPDATE);
  2. mantenham o MESMO nome, os MESMOS parâmetros e o MESMO formato de retorno
     (descrito em cada função).
As rotas (pasta rotas/) e as regras de negócio (gamificacao.py) não mudam.

Datas são sempre strings ISO: "2026-09-25".
"""
import copy

import dados_exemplo as D


def _c(x):
    """Devolve uma cópia, para ninguém alterar os dados sem passar por uma função de gravação."""
    return copy.deepcopy(x)


# =========================================================== USUÁRIOS
def buscar_usuario_por_email(email):
    """-> {id, nome, email, senha_hash, papel('aluno'|'admin')} ou None"""
    for u in D.USUARIOS:
        if u["email"].lower() == email.lower():
            return _c(u)
    return None


def buscar_usuario_por_id(usuario_id):
    """-> mesmo formato de buscar_usuario_por_email, ou None"""
    for u in D.USUARIOS:
        if u["id"] == usuario_id:
            return _c(u)
    return None


# =========================================================== TREINOS
def listar_treinos():
    """-> [{codigo, nome, grupo, minutos, xp, exercicios:[{nome, grupo, series, reps, carga}]}]"""
    return _c(D.TREINOS)


def buscar_treino(codigo):
    """-> um treino (formato acima) ou None"""
    for t in D.TREINOS:
        if t["codigo"] == codigo:
            return _c(t)
    return None


# =========================================================== PERFIL DO ALUNO
def buscar_perfil(usuario_id):
    """-> {nivel, xp, sequencia, melhor_sequencia, ultimo_treino(data|None), treinos_feitos,
           categoria_ranking, frequencia_mes:{ativos, meta}, config:{chave: bool}} ou None"""
    p = D.PERFIS.get(usuario_id)
    return _c(p) if p else None


def salvar_perfil(usuario_id, perfil):
    """Grava o perfil inteiro (mesmo formato de buscar_perfil)."""
    D.PERFIS[usuario_id] = _c(perfil)


# =========================================================== HISTÓRICO E RECORDES
def listar_historico(usuario_id, limite=10):
    """-> [{data, treino(codigo), minutos, exercicios, xp}] do mais recente para o mais antigo"""
    return _c(D.HISTORICO.get(usuario_id, [])[:limite])


def adicionar_historico(usuario_id, registro):
    """registro = {data, treino, minutos, exercicios, xp}"""
    D.HISTORICO.setdefault(usuario_id, []).insert(0, _c(registro))


def listar_recordes(usuario_id):
    """-> {nome_do_exercicio: carga_kg}"""
    return _c(D.RECORDES.get(usuario_id, {}))


def salvar_recorde(usuario_id, exercicio, carga):
    D.RECORDES.setdefault(usuario_id, {})[exercicio] = carga


def buscar_evolucao_carga(usuario_id):
    """-> {exercicio, variacao, 'Semana'|'Mês'|'Geral': {rotulos:[...], valores:[...]}} ou None"""
    e = D.EVOLUCAO_CARGA.get(usuario_id)
    return _c(e) if e else None


# =========================================================== CONQUISTAS
def listar_titulos(usuario_id):
    """-> [{icone, nome, descricao, liberado}]"""
    return _c(D.TITULOS.get(usuario_id, []))


def listar_medalhas(usuario_id):
    """-> [{icone, nome, descricao, meta, contador}]  (o progresso é calculado no gamificacao.py)"""
    return _c(D.MEDALHAS.get(usuario_id, []))


# =========================================================== RANKING
def listar_categorias_ranking():
    return list(D.RANKING.keys())


def listar_ranking(categoria):
    """-> [{usuario_id|None, nome, xp, emoji}] ordenado por XP (maior primeiro), ou None se a categoria não existe"""
    if categoria not in D.RANKING:
        return None
    lista = _c(D.RANKING[categoria])
    for item in lista:
        if item["usuario_id"] in D.PERFIS:
            item["xp"] = D.PERFIS[item["usuario_id"]]["xp"]
    return sorted(lista, key=lambda i: i["xp"], reverse=True)


# =========================================================== DUELOS
def buscar_duelo_ativo(usuario_id):
    """-> {id, oponente:{nome, nivel, xp}, xp_usuario, objetivo, termina_em} ou None"""
    d = D.DUELOS.get(usuario_id)
    return _c(d) if d else None


def somar_xp_duelo(usuario_id, xp):
    if usuario_id in D.DUELOS:
        D.DUELOS[usuario_id]["xp_usuario"] += xp


def listar_convites(usuario_id):
    """-> [{id, de, desafio, dias}]"""
    return _c(D.CONVITES.get(usuario_id, []))


def responder_convite(usuario_id, convite_id, aceito):
    """Remove o convite pendente e registra a resposta. -> True se o convite existia."""
    pendentes = D.CONVITES.get(usuario_id, [])
    for c in pendentes:
        if c["id"] == convite_id:
            pendentes.remove(c)
            D.CONVITES_RESPONDIDOS.append({"usuario_id": usuario_id, "convite_id": convite_id, "aceito": aceito})
            return True
    return False


# =========================================================== DESAFIOS
def buscar_desafio_ativo():
    """-> {id, nome, meta, recompensa_xp, treinos_meta, termina_em} ou None"""
    return _c(D.DESAFIO_ATIVO)


def contar_participantes(desafio_id):
    p = D.PARTICIPANTES_DESAFIO.get(desafio_id, {"outros": 0, "usuarios": set()})
    return p["outros"] + len(p["usuarios"])


def usuario_participa(usuario_id, desafio_id):
    return usuario_id in D.PARTICIPANTES_DESAFIO.get(desafio_id, {"usuarios": set()})["usuarios"]


def definir_participacao(usuario_id, desafio_id, participa):
    p = D.PARTICIPANTES_DESAFIO.setdefault(desafio_id, {"outros": 0, "usuarios": set()})
    (p["usuarios"].add if participa else p["usuarios"].discard)(usuario_id)


def listar_desafios_academia():
    """-> [{icone, nome, descricao, xp, status}]"""
    return _c(D.DESAFIOS_ACADEMIA)


# =========================================================== ADMINISTRAÇÃO
def listar_membros():
    """-> [{id, nome, cpf, frequencia, nivel, ativo, sequencia, ultimo_treino, cadastro,
            plano, valor_mensal, vencimento, treinos_recentes:[{titulo, minutos, xp, data}]}]"""
    return _c(D.MEMBROS)


def buscar_membro(membro_id):
    for m in D.MEMBROS:
        if m["id"] == membro_id:
            return _c(m)
    return None


def atualizar_status_membro(membro_id, ativo):
    """-> membro atualizado ou None"""
    for m in D.MEMBROS:
        if m["id"] == membro_id:
            m["ativo"] = ativo
            return _c(m)
    return None


def contar_membros():
    """-> (total_cadastrados, total_ativos)"""
    ativos = D.ATIVOS_FORA_DA_AMOSTRA + sum(1 for m in D.MEMBROS if m["ativo"])
    return D.TOTAL_MEMBROS, ativos


def listar_planos():
    """-> [{id, nome, preco, alunos_ativos}]"""
    return _c(D.PLANOS)


def resumo_contratos():
    """-> {vencendo_30d, vencidas, novos_mes}"""
    return _c(D.RESUMO_CONTRATOS)


def listar_vencimentos():
    """-> [{aluno, plano, vence_em}]"""
    return _c(D.VENCIMENTOS)


def resumo_financeiro():
    """-> {receita_estimada, recebido, inadimplencia, cancelamentos_mes, evolucao:[{mes, valor}]}"""
    return _c(D.FINANCEIRO)


def listar_recebimentos():
    """-> [{aluno, plano, valor, confirmado}]"""
    return _c(D.RECEBIMENTOS)

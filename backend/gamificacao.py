"""
Regras de negócio da gamificação: XP, níveis, sequência, recordes e conquistas.
Não acessa dados diretamente; tudo passa pelo repositorio.
"""
from datetime import date, timedelta

import repositorio as repo

XP_POR_NIVEL = 3000
BONUS_SEQUENCIA = 50   # por dia de sequência mantida
BONUS_RECORDE = 100    # por recorde pessoal batido
DIAS_SEMANA = ["S", "T", "Q", "Q", "S", "S", "D"]


def titulo(nivel):
    if nivel <= 5:
        return "Iniciante"
    if nivel <= 10:
        return "Moderado"
    if nivel <= 15:
        return "Intermediário"
    if nivel <= 20:
        return "Avançado"
    return "Evoluído"


def quando(data_iso, hoje=None):
    """'2026-09-24' -> 'Ontem' (texto amigável para o app)."""
    if not data_iso:
        return "Nunca"
    hoje = hoje or date.today()
    dias = (hoje - date.fromisoformat(data_iso)).days
    if dias <= 0:
        return "Hoje"
    if dias == 1:
        return "Ontem"
    if dias < 30:
        return f"Há {dias} dias"
    meses = dias // 30
    return "Há 1 mês" if meses == 1 else f"Há {meses} meses"


def _treinou_hoje(perfil, hoje):
    return perfil["ultimo_treino"] == hoje.isoformat()


def _semana(perfil, hoje):
    """Bolinhas da semana (segunda a domingo): True nos dias que fazem parte da sequência atual."""
    inicio = hoje - timedelta(days=hoje.weekday())
    ultimo = date.fromisoformat(perfil["ultimo_treino"]) if perfil["ultimo_treino"] else None
    dias = []
    for i in range(7):
        d = inicio + timedelta(days=i)
        ativo = bool(ultimo) and d <= ultimo and (ultimo - d).days < perfil["sequencia"]
        dias.append({"dia": DIAS_SEMANA[i], "treinou": ativo, "hoje": d == hoje})
    return dias


def proximo_treino(usuario_id):
    """Rodízio A -> B -> C a partir do último treino feito."""
    codigos = [t["codigo"] for t in repo.listar_treinos()]
    hist = repo.listar_historico(usuario_id, limite=1)
    if not hist or hist[0]["treino"] not in codigos:
        return codigos[0]
    return codigos[(codigos.index(hist[0]["treino"]) + 1) % len(codigos)]


def posicao_ranking(usuario_id, categoria):
    for i, item in enumerate(repo.listar_ranking(categoria) or []):
        if item["usuario_id"] == usuario_id:
            return i + 1
    return None


def treinos_na_semana(usuario_id, hoje=None):
    hoje = hoje or date.today()
    return sum(1 for h in repo.listar_historico(usuario_id, limite=50)
               if (hoje - date.fromisoformat(h["data"])).days < 7)


def resumo_aluno(usuario_id, hoje=None):
    """Tudo o que a tela inicial, perfil e sequência precisam."""
    hoje = hoje or date.today()
    p = repo.buscar_perfil(usuario_id)
    u = repo.buscar_usuario_por_id(usuario_id)
    desafio = repo.buscar_desafio_ativo()
    return {
        "nome": u["nome"],
        "nivel": p["nivel"],
        "titulo": titulo(p["nivel"]),
        "xp": p["xp"],
        "xp_proximo_nivel": XP_POR_NIVEL,
        "sequencia": p["sequencia"],
        "melhor_sequencia": p["melhor_sequencia"],
        "treinou_hoje": _treinou_hoje(p, hoje),
        "semana": _semana(p, hoje),
        "frequencia_mes": p["frequencia_mes"],
        "treinos_feitos": p["treinos_feitos"],
        "proximo_treino": proximo_treino(usuario_id),
        "categoria_ranking": p["categoria_ranking"],
        "posicao_ranking": posicao_ranking(usuario_id, p["categoria_ranking"]),
        "config": p["config"],
        "desafio": {
            "id": desafio["id"],
            "nome": desafio["nome"],
            "recompensa_xp": desafio["recompensa_xp"],
            "dias_restantes": max(0, (date.fromisoformat(desafio["termina_em"]) - hoje).days),
            "participando": repo.usuario_participa(usuario_id, desafio["id"]),
        } if desafio else None,
    }


def concluir_treino(usuario_id, codigo, segundos, cargas, hoje=None):
    """
    Registra um treino concluído e aplica as regras:
      - XP do treino
      - +50 XP se for o primeiro treino do dia (sequência)
      - +100 XP por recorde pessoal batido
      - sobe de nível a cada 3.000 XP
    `cargas` = carga usada em cada exercício, na mesma ordem do treino.
    Retorna o resultado para a tela "Treino Concluído!".
    """
    hoje = hoje or date.today()
    treino = repo.buscar_treino(codigo)
    p = repo.buscar_perfil(usuario_id)

    # --- sequência
    bonus_seq = 0
    if not _treinou_hoje(p, hoje):
        ontem = (hoje - timedelta(days=1)).isoformat()
        p["sequencia"] = p["sequencia"] + 1 if p["ultimo_treino"] == ontem else 1
        p["melhor_sequencia"] = max(p["melhor_sequencia"], p["sequencia"])
        p["frequencia_mes"]["ativos"] += 1
        p["ultimo_treino"] = hoje.isoformat()
        bonus_seq = BONUS_SEQUENCIA

    # --- recordes pessoais
    recordes_atuais = repo.listar_recordes(usuario_id)
    novos = []
    for ex, carga in zip(treino["exercicios"], cargas):
        anterior = recordes_atuais.get(ex["nome"])
        if anterior is None or carga > anterior:
            repo.salvar_recorde(usuario_id, ex["nome"], carga)
            if anterior is not None:  # só conta como "novo recorde" se superou uma marca anterior
                novos.append({"exercicio": ex["nome"], "carga": carga, "anterior": anterior})

    # --- XP e nível
    ganho = treino["xp"] + bonus_seq + BONUS_RECORDE * len(novos)
    p["xp"] += ganho
    subiu = False
    while p["xp"] >= XP_POR_NIVEL:
        p["xp"] -= XP_POR_NIVEL
        p["nivel"] += 1
        subiu = True
    p["treinos_feitos"] += 1

    minutos = max(1, round(segundos / 60))
    repo.salvar_perfil(usuario_id, p)
    repo.adicionar_historico(usuario_id, {"data": hoje.isoformat(), "treino": codigo, "minutos": minutos,
                                          "exercicios": len(treino["exercicios"]), "xp": ganho})
    repo.somar_xp_duelo(usuario_id, ganho)

    return {
        "xp": ganho,
        "detalhe_xp": {"treino": treino["xp"], "sequencia": bonus_seq, "recordes": BONUS_RECORDE * len(novos)},
        "minutos": minutos,
        "exercicios": len(treino["exercicios"]),
        "series": sum(e["series"] for e in treino["exercicios"]),
        "recordes": novos,
        "subiu_de_nivel": subiu,
        "nivel": p["nivel"],
    }


def conquistas(usuario_id):
    """Títulos + medalhas com progresso calculado a partir do perfil."""
    p = repo.buscar_perfil(usuario_id)
    valores = {"treinos_feitos": p["treinos_feitos"], "melhor_sequencia": p["melhor_sequencia"],
               "recordes": len(repo.listar_recordes(usuario_id))}
    medalhas = []
    for m in repo.listar_medalhas(usuario_id):
        contador = m.pop("contador", None)
        progresso = valores.get(contador, 0) if contador else 0
        m["progresso"] = min(progresso, m["meta"])
        m["concluida"] = progresso >= m["meta"]
        medalhas.append(m)
    return {"titulos": repo.listar_titulos(usuario_id), "medalhas": medalhas}

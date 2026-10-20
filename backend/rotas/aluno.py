"""Rotas usadas pelo app do ALUNO."""
from datetime import date

from flask import Blueprint, g, jsonify, request

import gamificacao as gm
import repositorio as repo
from rotas.auth import corpo, erro, exige_login

bp = Blueprint("aluno", __name__)
aluno = exige_login("aluno")


@bp.get("/treinos")
@aluno
def listar_treinos():
    return jsonify(repo.listar_treinos())


@bp.get("/aluno/resumo")
@aluno
def resumo():
    return jsonify(gm.resumo_aluno(g.usuario_id))


@bp.get("/aluno/historico")
@aluno
def historico():
    treinos = repo.listar_treinos()
    nomes = {t["codigo"]: t for t in treinos}
    itens = []
    for h in repo.listar_historico(g.usuario_id):
        t = nomes.get(h["treino"], {})
        itens.append({**h, "quando": gm.quando(h["data"]), "nome": t.get("nome"), "grupo": t.get("grupo")})
    recordes = [{"exercicio": k, "carga": v} for k, v in repo.listar_recordes(g.usuario_id).items()]
    return jsonify({"treinos": itens, "recordes": recordes,
                    "evolucao_carga": repo.buscar_evolucao_carga(g.usuario_id)})


@bp.post("/treinos/concluir")
@aluno
def concluir():
    dados = corpo()
    codigo = dados.get("treino")
    treino = repo.buscar_treino(codigo) if isinstance(codigo, str) else None
    if not treino:
        return erro("Treino não encontrado.", 404)

    segundos = dados.get("segundos", 0)
    if not isinstance(segundos, (int, float)) or segundos < 0 or segundos > 6 * 3600:
        return erro("Duração do treino inválida.", 400)

    padrao = [e["carga"] for e in treino["exercicios"]]
    cargas = dados.get("cargas", padrao)
    if (not isinstance(cargas, list) or len(cargas) != len(padrao)
            or not all(isinstance(c, (int, float)) and 0 <= c <= 1000 for c in cargas)):
        return erro("Envie uma carga (kg) válida para cada exercício.", 400)

    resultado = gm.concluir_treino(g.usuario_id, codigo, segundos, cargas)
    return jsonify({"resultado": resultado, "resumo": gm.resumo_aluno(g.usuario_id)}), 201


@bp.put("/aluno/config")
@aluno
def config():
    dados = corpo()
    chave, valor = dados.get("chave"), dados.get("valor")
    perfil = repo.buscar_perfil(g.usuario_id)
    if chave not in perfil["config"] or not isinstance(valor, bool):
        return erro("Configuração inválida.", 400)
    perfil["config"][chave] = valor
    repo.salvar_perfil(g.usuario_id, perfil)
    return jsonify({"config": perfil["config"]})


@bp.get("/aluno/conquistas")
@aluno
def conquistas():
    return jsonify(gm.conquistas(g.usuario_id))


# ------------------------------------------------------------------ social
@bp.get("/ranking")
@aluno
def ranking():
    categoria = request.args.get("categoria", "Evoluídos")
    lista = repo.listar_ranking(categoria)
    if lista is None:
        return erro(f"Categoria inválida. Use: {', '.join(repo.listar_categorias_ranking())}.", 400)
    perfil = repo.buscar_perfil(g.usuario_id)
    return jsonify([{"posicao": i + 1, "nome": x["nome"], "xp": x["xp"], "emoji": x["emoji"],
                     "eu": x["usuario_id"] == g.usuario_id,
                     "sequencia": perfil["sequencia"] if x["usuario_id"] == g.usuario_id else None}
                    for i, x in enumerate(lista)])


def _duelos_json():
    u = repo.buscar_usuario_por_id(g.usuario_id)
    perfil = repo.buscar_perfil(g.usuario_id)
    d = repo.buscar_duelo_ativo(g.usuario_id)
    ativo = None
    if d:
        ativo = {"id": d["id"], "objetivo": d["objetivo"],
                 "dias_restantes": max(0, (date.fromisoformat(d["termina_em"]) - date.today()).days),
                 "oponente": d["oponente"],
                 "voce": {"nome": u["nome"], "nivel": perfil["nivel"], "xp": d["xp_usuario"]}}
    return {"ativo": ativo, "convites": repo.listar_convites(g.usuario_id)}


@bp.get("/duelos")
@aluno
def duelos():
    return jsonify(_duelos_json())


@bp.post("/duelos/convites/<int:convite_id>")
@aluno
def responder_convite(convite_id):
    aceitar = corpo().get("aceitar")
    if not isinstance(aceitar, bool):
        return erro("Informe 'aceitar': true ou false.", 400)
    if not repo.responder_convite(g.usuario_id, convite_id, aceitar):
        return erro("Convite não encontrado.", 404)
    return jsonify(_duelos_json())


@bp.get("/desafios")
@aluno
def desafios():
    d = repo.buscar_desafio_ativo()
    ativo = None
    if d:
        feitos = min(gm.treinos_na_semana(g.usuario_id), d["treinos_meta"])
        ativo = {**d,
                 "dias_restantes": max(0, (date.fromisoformat(d["termina_em"]) - date.today()).days),
                 "participantes": repo.contar_participantes(d["id"]),
                 "participando": repo.usuario_participa(g.usuario_id, d["id"]),
                 "progresso": feitos}
    return jsonify({"ativo": ativo, "academia": repo.listar_desafios_academia()})


@bp.post("/desafios/<int:desafio_id>/participar")
@aluno
def participar(desafio_id):
    d = repo.buscar_desafio_ativo()
    if not d or d["id"] != desafio_id:
        return erro("Desafio não encontrado.", 404)
    novo = not repo.usuario_participa(g.usuario_id, desafio_id)
    repo.definir_participacao(g.usuario_id, desafio_id, novo)
    return jsonify({"participando": novo, "participantes": repo.contar_participantes(desafio_id)})

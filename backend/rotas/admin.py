"""Rotas do painel da ACADEMIA (administrador)."""
from datetime import date

from flask import Blueprint, jsonify, request

import gamificacao as gm
import repositorio as repo
from rotas.auth import corpo, erro, exige_login

bp = Blueprint("admin", __name__, url_prefix="/admin")
admin = exige_login("admin")


def _dias_ate(data_iso):
    return (date.fromisoformat(data_iso) - date.today()).days


def _membro_resumo(m):
    dias = _dias_ate(m["vencimento"])
    return {"id": m["id"], "nome": m["nome"], "cpf": m["cpf"], "frequencia": m["frequencia"],
            "nivel": m["nivel"], "ativo": m["ativo"], "ultimo_treino": gm.quando(m["ultimo_treino"]),
            "vencido_ha_dias": -dias if dias < 0 else 0}


def _membro_ficha(m):
    return {**_membro_resumo(m),
            "sequencia": m["sequencia"], "cadastro": m["cadastro"], "plano": m["plano"],
            "valor_mensal": m["valor_mensal"], "vencimento": m["vencimento"],
            "treinos_recentes": [{**t, "quando": gm.quando(t["data"])} for t in m["treinos_recentes"]]}


@bp.get("/painel")
@admin
def painel():
    total, ativos = repo.contar_membros()
    fin = repo.resumo_financeiro()
    return jsonify({"total_membros": total, "membros_ativos": ativos,
                    "receita_mes": fin["receita_estimada"], "inadimplencia": fin["inadimplencia"],
                    "vencendo_30d": repo.resumo_contratos()["vencendo_30d"]})


@bp.get("/membros")
@admin
def membros():
    """Filtros opcionais: ?busca=nome_ou_cpf&status=ativos|inativos"""
    busca = request.args.get("busca", "").strip().lower()
    status = request.args.get("status", "todos").lower()
    lista = repo.listar_membros()
    if busca:
        lista = [m for m in lista if busca in m["nome"].lower() or busca in m["cpf"]]
    if status == "ativos":
        lista = [m for m in lista if m["ativo"]]
    elif status == "inativos":
        lista = [m for m in lista if not m["ativo"]]
    total, _ = repo.contar_membros()
    return jsonify({"total": total, "membros": [_membro_resumo(m) for m in lista]})


@bp.get("/membros/<int:membro_id>")
@admin
def ficha(membro_id):
    m = repo.buscar_membro(membro_id)
    if not m:
        return erro("Aluno não encontrado.", 404)
    return jsonify(_membro_ficha(m))


@bp.patch("/membros/<int:membro_id>")
@admin
def atualizar(membro_id):
    ativo = corpo().get("ativo")
    if not isinstance(ativo, bool):
        return erro("Informe 'ativo': true ou false.", 400)
    m = repo.atualizar_status_membro(membro_id, ativo)
    if not m:
        return erro("Aluno não encontrado.", 404)
    return jsonify(_membro_ficha(m))


@bp.get("/planos")
@admin
def planos():
    venc = [{**v, "dias": _dias_ate(v["vence_em"])} for v in repo.listar_vencimentos()]
    return jsonify({"resumo": repo.resumo_contratos(), "planos": repo.listar_planos(), "vencimentos": venc})


@bp.get("/financeiro")
@admin
def financeiro():
    """Filtro opcional: ?pendentes=1 mostra só recebimentos não confirmados."""
    rec = repo.listar_recebimentos()
    if request.args.get("pendentes") == "1":
        rec = [r for r in rec if not r["confirmado"]]
    return jsonify({**repo.resumo_financeiro(), "recebimentos": rec})

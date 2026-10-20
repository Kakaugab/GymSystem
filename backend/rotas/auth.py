"""Login, logout e o controle de acesso (quem pode chamar cada rota).

As sessões ficam no banco (tabela sessoes, só o hash do token): reiniciar o servidor não desloga ninguém.
"""
import secrets
from functools import wraps

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash

import repositorio as repo

bp = Blueprint("auth", __name__)

DURACAO_SESSAO = 12 * 60 * 60  # 12 horas


def erro(mensagem, status):
    return jsonify({"erro": mensagem}), status


def corpo():
    """JSON enviado pelo front (ou {} se veio vazio/inválido)."""
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}


def exige_login(papel=None):
    """Decorador: exige 'Authorization: Bearer <token>' e, se informado, o papel certo."""
    def decorador(func):
        @wraps(func)
        def envolvida(*args, **kwargs):
            token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            sessao = repo.buscar_sessao(token) if token else None  # None = não existe ou venceu
            if not sessao:
                return erro("Sessão expirada. Faça login novamente.", 401)
            if papel and sessao["papel"] != papel:
                return erro("Você não tem permissão para acessar isso.", 403)
            g.usuario_id = sessao["usuario_id"]
            g.papel = sessao["papel"]
            g.token = token
            return func(*args, **kwargs)
        return envolvida
    return decorador


@bp.post("/login")
def login():
    dados = corpo()
    email = str(dados.get("email", "")).strip()
    senha = str(dados.get("senha", ""))
    if not email or not senha:
        return erro("Informe e-mail e senha.", 400)
    usuario = repo.buscar_usuario_por_email(email)
    if not usuario or not check_password_hash(usuario["senha_hash"], senha):
        return erro("E-mail ou senha incorretos.", 401)
    token = secrets.token_urlsafe(32)  # 32 bytes aleatórios = 256 bits
    repo.criar_sessao(token, usuario["id"], DURACAO_SESSAO)
    return jsonify({"token": token,
                    "usuario": {"id": usuario["id"], "nome": usuario["nome"], "papel": usuario["papel"]}})


@bp.post("/logout")
@exige_login()
def logout():
    repo.apagar_sessao(g.token)
    return jsonify({"ok": True})


@bp.get("/eu")
@exige_login()
def eu():
    u = repo.buscar_usuario_por_id(g.usuario_id)
    return jsonify({"id": u["id"], "nome": u["nome"], "papel": u["papel"]})

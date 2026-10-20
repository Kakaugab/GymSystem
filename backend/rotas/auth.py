"""Login, logout e o controle de acesso (quem pode chamar cada rota)."""
import secrets
import time
from functools import wraps

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash

import repositorio as repo

bp = Blueprint("auth", __name__)

DURACAO_SESSAO = 12 * 60 * 60  # 12 horas
SESSOES = {}  # token -> {usuario_id, papel, expira}


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
            sessao = SESSOES.get(token)
            if not sessao or sessao["expira"] < time.time():
                SESSOES.pop(token, None)
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
    token = secrets.token_urlsafe(32)
    SESSOES[token] = {"usuario_id": usuario["id"], "papel": usuario["papel"],
                      "expira": time.time() + DURACAO_SESSAO}
    return jsonify({"token": token,
                    "usuario": {"id": usuario["id"], "nome": usuario["nome"], "papel": usuario["papel"]}})


@bp.post("/logout")
@exige_login()
def logout():
    SESSOES.pop(g.token, None)
    return jsonify({"ok": True})


@bp.get("/eu")
@exige_login()
def eu():
    u = repo.buscar_usuario_por_id(g.usuario_id)
    return jsonify({"id": u["id"], "nome": u["nome"], "papel": u["papel"]})

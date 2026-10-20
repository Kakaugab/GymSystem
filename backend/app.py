"""
GymSystem — Back-end (API em Python / Flask)

Como rodar:
    pip install -r requirements.txt
    python app.py
API em http://localhost:5000/api  e o app (front) em http://localhost:5000
"""
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from db import conexao
from rotas import admin, aluno, auth

PASTA_FRONT = Path(__file__).resolve().parent.parent / "frontend"


def criar_app():
    app = Flask(__name__, static_folder=None)
    app.json.ensure_ascii = False  # acentos aparecem normalmente no JSON
    conexao.registrar(app)  # banco: 1 conexão por requisição, COMMIT no fim (ROLLBACK se der erro)

    for bp in (auth.bp, aluno.bp, admin.bp):
        app.register_blueprint(bp, url_prefix="/api" + (bp.url_prefix or ""))

    # CORS: libera o front rodando em outra porta (ex.: Live Server 5500)
    @app.after_request
    def cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = os.environ.get("CORS_ORIGEM", "*")
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return resp

    @app.route("/api/<path:_>", methods=["OPTIONS"])
    def preflight(_):
        return "", 204

    @app.get("/api/saude")
    def saude():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def nao_encontrado(_):
        return jsonify({"erro": "Rota não encontrada."}), 404

    @app.errorhandler(405)
    def metodo(_):
        return jsonify({"erro": "Método não permitido nesta rota."}), 405

    @app.errorhandler(500)
    def interno(_):
        return jsonify({"erro": "Erro interno no servidor."}), 500

    # Serve o front-end (index.html, style.css, app.js) na mesma porta
    @app.get("/")
    @app.get("/<path:arquivo>")
    def front(arquivo="index.html"):
        if (PASTA_FRONT / arquivo).is_file():
            return send_from_directory(PASTA_FRONT, arquivo)
        return jsonify({"erro": "Arquivo não encontrado."}), 404

    return app


app = criar_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORTA", 5000)), debug=True)

"""
CONEXÃO COM O BANCO — uma conexão (e uma transação) por requisição.

Como funciona, passo a passo, em cada requisição HTTP:
  1. A primeira função do repositorio.py que precisar do banco chama obter().
  2. obter() abre a conexão e guarda em flask.g (um "armário" que só existe durante
     esta requisição). As próximas chamadas na mesma requisição reutilizam a mesma conexão.
  3. A conexão NÃO usa autocommit: tudo o que for gravado fica numa transação aberta.
  4. Quando a resposta fica pronta, o Flask chama marcar_falha() (after_request): se o status
     é de erro (400 ou mais), anota g._falhou = True.
  5. Quando a requisição termina, o Flask chama fechar() (teardown_appcontext), que decide:
       - houve exceção                      -> ROLLBACK (desfaz tudo)
       - resposta de erro (status >= 400)   -> ROLLBACK (desfaz tudo)
       - resposta de sucesso (2xx/3xx)      -> COMMIT   (grava tudo de uma vez)
     e a conexão é fechada.

Por que isso importa: "concluir treino" chama várias funções do repositório (recordes, perfil,
histórico, duelo). Se a última falhar, o ROLLBACK desfaz as anteriores, e o aluno não fica com
XP somado sem o treino no histórico. Isso é a propriedade de ATOMICIDADE (o "A" do ACID).

Por que também desfazer nos erros 4xx? Uma rota pode gravar algo e DEPOIS descobrir que o pedido
era inválido (return erro("...", 400)). Sem exceção, isso seria gravado pela metade. Com a regra
"resposta de erro = ROLLBACK", o banco só muda quando a API responde sucesso, mesmo que uma rota
nova esqueça de validar antes de gravar.

Por que as duas funções? O after_request enxerga a resposta (o status), mas NÃO roda quando
acontece uma exceção não tratada. O teardown roda SEMPRE e recebe a exceção, mas não vê a
resposta. Juntas, cobrem todos os casos.

Por que não um pool de conexões? Abrir uma conexão local custa poucos milissegundos, e para
um trabalho de faculdade a simplicidade vale mais. Se um dia precisar, basta trocar conectar()
por um pool (ex.: biblioteca DBUtils) sem mexer no resto.

Configuração: variáveis do arquivo backend/.env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME).
"""
import os
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from flask import g, has_app_context

# Lê o backend/.env. Variáveis que já existem no ambiente têm prioridade:
# é assim que os testes trocam DB_NAME para o banco de teste.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def conectar(banco=None):
    """Abre uma conexão NOVA. As linhas voltam como dicionário: {"nome": "Lucas", ...}."""
    try:
        return pymysql.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ["DB_USER"],
            password=os.environ.get("DB_PASSWORD", ""),
            database=banco or os.environ["DB_NAME"],
            charset="utf8mb4",                       # aceita emoji e acentos
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,                        # quem decide o COMMIT é o fechar()
        )
    except KeyError as falta:
        raise RuntimeError(f"Variável {falta} não definida. Crie o backend/.env (veja o .env.example).") from None


def obter():
    """Conexão da requisição atual (abre na primeira chamada, reaproveita nas seguintes)."""
    if not has_app_context():
        raise RuntimeError("O banco só pode ser usado dentro de uma requisição do Flask "
                           "(ou dentro de 'with app.app_context():').")
    if "_conexao" not in g:
        g._conexao = conectar()
    return g._conexao


def marcar_falha(resposta):
    """after_request: anota em g se a resposta é de erro (status >= 400)."""
    if resposta.status_code >= 400:
        g._falhou = True
    return resposta  # o after_request precisa devolver a resposta (sem alterar nada)


def fechar(excecao=None):
    """Chamado pelo Flask ao fim de cada requisição: COMMIT ou ROLLBACK e fecha a conexão."""
    con = g.pop("_conexao", None)
    falhou = g.pop("_falhou", False)
    if con is None:
        return  # a requisição não usou o banco (ex.: arquivos do front)
    try:
        if excecao is None and not falhou:
            con.commit()
        else:
            con.rollback()
    finally:
        con.close()


def registrar(app):
    """Liga o banco ao Flask. Chamado UMA vez, no criar_app() do app.py."""
    # after_request: roda com a resposta pronta -> anota se foi erro.
    app.after_request(marcar_falha)
    # teardown_appcontext: roda SEMPRE ao fim da requisição, recebendo a exceção que
    # aconteceu (ou None) -> decide COMMIT ou ROLLBACK e fecha a conexão.
    app.teardown_appcontext(fechar)

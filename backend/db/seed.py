"""
SEED — recria as tabelas e coloca os dados iniciais (os mesmos do antigo dados_exemplo.py).

Rodar (dentro da pasta backend, com o .env preenchido):
    python db/seed.py            -> pergunta antes de apagar
    python db/seed.py -y         -> sem perguntar
    python db/seed.py --banco gymsystem_test -y

ATENÇÃO: APAGA todas as tabelas do banco escolhido e cria de novo.
O banco em si (CREATE DATABASE) precisa já existir: quem cria é o administrador do MySQL.

Por que em Python e não um seed.sql?
  * as datas são relativas a HOJE (ex.: "treinou ontem"), então o app sempre abre parecido,
    em qualquer dia que o seed for rodado;
  * as senhas precisam virar hash (generate_password_hash). SQL puro não sabe fazer isso.

Todas as consultas usam parâmetros (%s): o driver escapa os valores, nada de f-string em SQL.
"""
import argparse
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

PASTA_DB = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DB.parent))  # permite "python db/seed.py" achar o pacote db
from db.conexao import conectar  # noqa: E402  (mesma configuração do .env usada pelo servidor)

HOJE = date.today()


def dia(n):
    """dia(-1) = ontem, dia(5) = daqui a 5 dias."""
    return HOJE + timedelta(days=n)


def somar_meses(d, meses):
    """somar_meses(31/jan, 1) = 28/fev (ajusta o dia se o mês for mais curto)."""
    total = d.year * 12 + d.month - 1 + meses
    ano, mes = divmod(total, 12)
    mes += 1
    fim_do_mes = (date(ano + mes // 12, mes % 12 + 1, 1) - timedelta(days=1)).day
    return date(ano, mes, min(d.day, fim_do_mes))


def email_de(nome):
    """'Lívia Santana' -> 'livia.santana@email.com'"""
    sem_acento = nome.lower().translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))
    return ".".join(sem_acento.split()) + "@email.com"


# =====================================================================
# DADOS
# =====================================================================
SENHA_ALUNOS_DEMO = "aluno123"

TREINOS = [
    ("A", "Treino A", "Peito e Tríceps", 45, 120,
     [("Supino Reto", "Peito", 4, 12, 40), ("Supino Inclinado", "Peito", 3, 12, 30),
      ("Crucifixo", "Peito", 3, 15, 14), ("Tríceps Testa", "Tríceps", 3, 12, 20),
      ("Tríceps Corda", "Tríceps", 3, 15, 25)]),
    ("B", "Treino B", "Costas e Bíceps", 50, 130,
     [("Puxada Frontal", "Costas", 4, 12, 45), ("Remada Curvada", "Costas", 4, 10, 40),
      ("Remada Baixa", "Costas", 3, 12, 35), ("Rosca Direta", "Bíceps", 3, 12, 20),
      ("Rosca Martelo", "Bíceps", 3, 12, 12)]),
    ("C", "Treino C", "Pernas e Ombros", 55, 140,
     [("Agachamento", "Pernas", 4, 10, 80), ("Leg Press", "Pernas", 4, 12, 150),
      ("Cadeira Extensora", "Pernas", 3, 15, 45), ("Desenvolvimento", "Ombros", 3, 12, 24),
      ("Elevação Lateral", "Ombros", 3, 15, 8)]),
]

CATEGORIAS = [("Evoluídos", 1), ("Moderados", 2), ("Iniciantes", 3)]

OPCOES_CONFIG = [("notificacoes_treino", "Notificações de treino", True, 1),
                 ("sons_app", "Sons do app", True, 2),
                 ("lembretes_agua", "Lembretes de água", False, 3)]

PLANOS = [(1, "Mensal", 99.00, 1), (2, "Trimestral", 249.00, 3),
          (3, "Semestral", 449.00, 6), (4, "Anual", 799.00, 12)]

# Alunos. Os ids 1 a 4 são os mesmos do painel antigo (os testes usam o 4).
# O "Lucas Silva" do painel e o "Lucas Oliveira" do app viraram a mesma pessoa.
# As pessoas do ranking, do duelo, do convite e do financeiro viraram alunos reais.
#  id, nome, cpf, cadastro, categoria, nivel, xp, sequencia, melhor_seq, ultimo_treino(dias atrás),
#  treinos_feitos, emoji, treinos nos últimos 28 dias (gera o histórico e a "frequência"),
#  plano, valor_mensal, vencimento(dias a partir de hoje), ativo
_ = None
ALUNOS = [
    (1, "Lucas Oliveira", "123.456.789-00", date(2026, 1, 10), "Evoluídos", 12, 2450, 3, 18, 1, 57, _, 12, "Trimestral", 99.00, 78, True),
    (2, "Mariana Costa", "234.567.890-11", date(2025, 11, 20), "Evoluídos", 15, 2710, 8, 14, 1, 160, "💪", 16, "Anual", 79.00, 56, True),
    (3, "Gustavo Santos", "345.678.901-22", date(2025, 8, 3), "Evoluídos", 18, 2950, 21, 25, 2, 240, "🏋️", 20, "Semestral", 74.83, 131, True),
    (4, "Carlos Oliveira", "456.789.012-33", date(2026, 2, 28), "Iniciantes", 5, 120, 0, 6, 32, 20, _, 0, "Mensal", 99.00, -15, False),
    (5, "Camila Rocha", _, _, "Evoluídos", 13, 2580, 5, 15, 1, 180, "🏃‍♀️", 12, "Anual", 66.58, 200, True),
    (6, "Rafaela Fernandes", _, _, "Evoluídos", 12, 2120, 3, 10, 1, 150, _, 10, "Semestral", 74.83, 20, True),
    (7, "Mateus Barbosa", _, _, "Evoluídos", 11, 1980, 4, 9, 1, 130, _, 9, "Trimestral", 83.00, 45, True),
    (8, "Diego Teixeira", _, _, "Evoluídos", 10, 1710, 2, 8, 2, 110, _, 8, "Mensal", 99.00, -3, True),
    (9, "Bianca Lima", _, _, "Moderados", 10, 1890, 6, 11, 1, 100, "🧘", 10, "Anual", 66.58, 300, True),
    (10, "Renato Alves", _, _, "Moderados", 9, 1760, 3, 7, 1, 90, "🚴", 8, "Semestral", 74.83, 90, True),
    (11, "Paula Mendes", _, _, "Moderados", 9, 1640, 2, 6, 2, 85, "🏃", 8, "Trimestral", 83.00, 25, True),
    (12, "Caio Martins", _, _, "Moderados", 8, 1420, 1, 5, 3, 70, _, 6, "Mensal", 99.00, 12, True),
    (13, "Alice Ribeiro", _, _, "Moderados", 7, 1210, 2, 5, 1, 60, _, 6, "Anual", 66.58, 150, True),
    (14, "Tiago Pereira", _, _, "Iniciantes", 5, 980, 3, 4, 1, 25, "🌱", 6, "Trimestral", 83.00, 70, True),
    (15, "Nina Carvalho", _, _, "Iniciantes", 5, 870, 2, 4, 1, 22, "🌱", 5, "Mensal", 99.00, 18, True),
    (16, "Otávio Gomes", _, _, "Iniciantes", 5, 760, 1, 3, 2, 20, "🌱", 5, "Semestral", 74.83, 160, True),
    (17, "Lívia Santana", _, _, "Iniciantes", 4, 650, 1, 3, 4, 15, _, 4, "Trimestral", 83.00, -7, True),
    (18, "Hugo Pacheco", _, _, "Iniciantes", 4, 540, 1, 2, 3, 12, _, 4, "Mensal", 99.00, 28, True),
    (19, "Maria Silva", _, _, "Evoluídos", 11, 1450, 6, 12, 1, 125, _, 12, "Trimestral", 83.00, 60, True),
    (20, "Pedro Costa", _, _, "Moderados", 7, 900, 2, 6, 1, 55, _, 6, "Semestral", 74.83, 100, True),
    (21, "Pedro Camargo", _, _, "Iniciantes", 3, 400, 1, 2, 2, 8, _, 4, "Mensal", 119.00, 20, True),
    (22, "Bruno Medeiros", _, _, "Iniciantes", 2, 300, 1, 2, 1, 5, _, 3, "Mensal", 99.00, 2, True),
    (23, "Jessica Souza", _, _, "Iniciantes", 1, 150, 1, 1, 1, 3, _, 3, "Trimestral", 83.00, 5, True),
]

# Dias (atrás) em que o Lucas treinou: 12 treinos em 28 dias = "3x/sem" no painel.
# Nenhum treino entre 4 e 6 dias atrás: a janela "últimos 7 dias" do desafio só pega os dias 1, 2 e 3.
DIAS_TREINO_LUCAS = [1, 2, 3, 7, 9, 11, 13, 16, 19, 22, 25, 27]

# Mensalidades que ficaram sem pagar: (usuario_id, meses atrás). 0 = mês atual.
NAO_PAGOS = {(21, 0), (8, 0), (17, 0), (17, 1)}

# Recordes do Lucas: (exercício, carga, dias atrás). A progressão alimenta o gráfico de evolução.
RECORDES_LUCAS = [("Supino Reto", 20, 1100), ("Supino Reto", 30, 730), ("Supino Reto", 38, 365),
                  ("Supino Reto", 40, 150), ("Supino Reto", 41, 60), ("Supino Reto", 43, 20),
                  ("Supino Reto", 45, 5), ("Agachamento", 80, 40)]

TITULOS = [("🛡️", "Guerreiro", "Fazer 50 treinos no total"),
           ("🏃", "Maratonista", "Treinar 30 dias seguidos"),
           ("🔥", "Recordista", "Bater 10 recordes pessoais"),
           ("🥇", "Campeão", "1ª vitória em uma competição")]
TITULOS_LUCAS = [("Guerreiro", 60), ("Recordista", 20)]  # (título, liberado há N dias)

MEDALHAS = [("🌱", "Primeiro Treino", "Primeiro dia no aplicativo feito", 1, "treinos_feitos"),
            ("🔥", "Consistência 7", "Treinar por 7 dias seguidos", 7, "melhor_sequencia"),
            ("💪", "Guerreiro 50", "Completar 50 treinos", 50, "treinos_feitos"),
            ("🛡️", "Guerreiro 100", "Completar 100 treinos", 100, "treinos_feitos"),
            ("⚡", "Recordista", "Bater recordes de força", 1, "recordes"),
            ("🏆", "Top 10 Ranking", "Ficar no top 10 semanal", 1, None)]

DESAFIOS_ACADEMIA = [("🔥", "Treino Fiel", "Treinar 5x em uma semana", 200, "Pendente"),
                     ("💪", "Monstro do Legpress", "Atingir 150kg no Legpress", 300, "Finalizado")]


# =====================================================================
# EXECUÇÃO
# =====================================================================
def comandos_do_schema():
    """Lê o schema.sql, tira os comentários (-- ...) e separa os comandos pelo ';'."""
    texto = (PASTA_DB / "schema.sql").read_text(encoding="utf-8")
    texto = re.sub(r"--[^\n]*", "", texto)
    return [c.strip() for c in texto.split(";") if c.strip()]


def criar_tabelas(cur):
    for comando in comandos_do_schema():
        cur.execute(comando)


def inserir_dados(cur):
    # --- catálogos
    cur.executemany("INSERT INTO categorias_ranking (nome, ordem) VALUES (%s, %s)", CATEGORIAS)
    cur.executemany("INSERT INTO opcoes_configuracao (chave, rotulo, padrao, ordem) VALUES (%s, %s, %s, %s)",
                    OPCOES_CONFIG)
    cur.executemany("INSERT INTO planos (id, nome, preco, duracao_meses) VALUES (%s, %s, %s, %s)", PLANOS)

    exercicio_id = {}
    for codigo, nome, grupo, minutos, xp, exercicios in TREINOS:
        cur.execute("INSERT INTO treinos (codigo, nome, grupo, minutos, xp) VALUES (%s, %s, %s, %s, %s)",
                    (codigo, nome, grupo, minutos, xp))
        for ordem, (ex_nome, ex_grupo, series, reps, carga) in enumerate(exercicios, start=1):
            if ex_nome not in exercicio_id:
                cur.execute("INSERT INTO exercicios (nome, grupo) VALUES (%s, %s)", (ex_nome, ex_grupo))
                exercicio_id[ex_nome] = cur.lastrowid
            cur.execute("INSERT INTO treino_exercicios (treino_codigo, ordem, exercicio_id, series, reps, carga) "
                        "VALUES (%s, %s, %s, %s, %s, %s)", (codigo, ordem, exercicio_id[ex_nome], series, reps, carga))

    cur.executemany("INSERT INTO titulos (icone, nome, descricao) VALUES (%s, %s, %s)", TITULOS)
    cur.executemany("INSERT INTO medalhas (icone, nome, descricao, meta, contador) VALUES (%s, %s, %s, %s, %s)", MEDALHAS)
    cur.executemany("INSERT INTO desafios_academia (icone, nome, descricao, xp, status) VALUES (%s, %s, %s, %s, %s)",
                    DESAFIOS_ACADEMIA)

    # --- administrador
    cur.execute("INSERT INTO usuarios (id, nome, email, senha_hash, papel, cpf, criado_em) "
                "VALUES (%s, %s, %s, %s, 'admin', NULL, %s)",
                (100, "Administrador", "admin@gymsystem.com", generate_password_hash("admin123"), date(2025, 1, 1)))

    # --- alunos: usuário + perfil + matrícula + pagamentos + histórico
    codigos = [t[0] for t in TREINOS]
    info_treino = {t[0]: t for t in TREINOS}
    duracao = {nome: meses for _id, nome, _p, meses in PLANOS}
    plano_id = {nome: pid for pid, nome, _p, _m in PLANOS}
    mes_atual = HOJE.replace(day=1)

    for (uid, nome, cpf, cadastro, categoria, nivel, xp, seq, melhor, ult, feitos, emoji, n28,
         plano, valor, venc_dias, ativo) in ALUNOS:
        vencimento = dia(venc_dias)
        inicio = somar_meses(vencimento, -duracao[plano])
        cpf = cpf or f"{100 + uid:03d}.{200 + uid:03d}.{300 + uid:03d}-{uid:02d}"  # CPF fictício
        cadastro = cadastro or inicio
        senha = "senha1234567" if uid == 1 else SENHA_ALUNOS_DEMO

        cur.execute("INSERT INTO usuarios (id, nome, email, senha_hash, papel, cpf, criado_em) "
                    "VALUES (%s, %s, %s, %s, 'aluno', %s, %s)",
                    (uid, nome, email_de(nome), generate_password_hash(senha), cpf, cadastro))

        ultimo = dia(-ult)
        # O Lucas mantém os números da tela inicial antiga (9 de 10 dias no mês).
        ativos_mes = 9 if uid == 1 else min(n28, HOJE.day)
        cur.execute("INSERT INTO perfis (usuario_id, nivel, xp, sequencia, melhor_sequencia, treinos_feitos, "
                    "ultimo_treino, frequencia_ativos, frequencia_meta, frequencia_mes, categoria_ranking, emoji) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (uid, nivel, xp, seq, melhor, feitos, ultimo, ativos_mes, 10,
                     HOJE.strftime("%Y-%m"), categoria, emoji))

        # Matrícula
        cancelada = vencimento if not ativo else None
        cur.execute("INSERT INTO matriculas (usuario_id, plano_id, valor_mensal, data_inicio, vencimento, ativo, "
                    "cancelada_em) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (uid, plano_id[plano], valor, inicio, vencimento, ativo, cancelada))
        matricula_id = cur.lastrowid

        # Mensalidades: vencem todo dia 10 (ou no dia da matrícula, no primeiro mês), dos últimos 6 meses.
        for meses_atras in range(5, -1, -1):
            ref = somar_meses(mes_atual, -meses_atras)
            if ref < inicio.replace(day=1):
                continue
            venc_pag = inicio if ref == inicio.replace(day=1) and inicio.day > 10 else ref.replace(day=10)
            if venc_pag > vencimento or (cancelada and venc_pag > cancelada):
                continue
            pago = venc_pag < HOJE and (uid, meses_atras) not in NAO_PAGOS
            cur.execute("INSERT INTO pagamentos (matricula_id, referencia, valor, vencimento, pago_em) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (matricula_id, ref, valor, venc_pag, venc_pag - timedelta(days=1) if pago else None))

        # Histórico: n28 treinos espalhados nos últimos 28 dias, o mais recente = ultimo_treino.
        # Lucas: treinou nos últimos 3 dias (sequência de 3) e não treinou há 4 dias (quebra a sequência).
        # Assim ele tem 3 treinos nos últimos 7 dias: o desafio da semana começa em 3/5 e a barra
        # sobe a cada treino concluído na apresentação (3 -> 4 -> 5).
        if uid == 1:
            dias_atras = DIAS_TREINO_LUCAS
        elif n28:
            passo = (28 - ult) / max(n28 - 1, 1)
            dias_atras = sorted({ult + round(i * passo) for i in range(n28)})
        else:
            dias_atras = [ult]  # Carlos: só um treino, há 32 dias
        for i, d in enumerate(dias_atras):
            codigo = codigos[(2 - i) % 3]  # rodízio de trás pra frente: o mais recente é o C
            t = info_treino[codigo]
            cur.execute("INSERT INTO historico_treinos (usuario_id, treino_codigo, data, minutos, exercicios, xp) "
                        "VALUES (%s, %s, %s, %s, %s, %s)", (uid, codigo, dia(-d), t[3], len(t[5]), t[4]))

    # --- recordes e títulos do Lucas
    cur.executemany("INSERT INTO recordes (usuario_id, exercicio_id, carga, data) VALUES (1, %s, %s, %s)",
                    [(exercicio_id[ex], carga, dia(-d)) for ex, carga, d in RECORDES_LUCAS])
    cur.executemany("INSERT INTO usuario_titulos (usuario_id, titulo_id, liberado_em) "
                    "SELECT 1, id, %s FROM titulos WHERE nome = %s",
                    [(dia(-d), nome) for nome, d in TITULOS_LUCAS])

    # --- duelo ativo (Lucas x Maria Silva) e convite pendente (Pedro Costa -> Lucas)
    cur.execute("INSERT INTO duelos (id, desafiante_id, desafiado_id, objetivo, dias, status, criado_em, inicio, "
                "termina_em, xp_desafiante, xp_desafiado) VALUES (1, 1, 19, %s, 7, 'ativo', %s, %s, %s, 1850, 1450)",
                ("Mais XP em 7 dias", dia(-2), dia(-2), dia(5)))
    cur.execute("INSERT INTO duelos (id, desafiante_id, desafiado_id, objetivo, dias, status, criado_em) "
                "VALUES (7, 20, 1, %s, 5, 'pendente', %s)", ("Foco em Pernas", dia(-1)))

    # --- desafio da semana: 12 participantes (o Lucas ainda não entrou)
    cur.execute("INSERT INTO desafios (id, nome, meta, recompensa_xp, treinos_meta, inicio, termina_em) "
                "VALUES (1, %s, %s, 500, 5, %s, %s)",
                ("Desafio Semanal de Cardio", "Maior ganho de XP em 7 dias", dia(-5), dia(2)))
    cur.executemany("INSERT INTO participacoes (desafio_id, usuario_id, entrou_em) VALUES (1, %s, %s)",
                    [(uid, dia(-4)) for uid in (2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)])


CONTAGEM = """
SELECT 'usuarios' AS tabela, COUNT(*) AS linhas FROM usuarios UNION ALL
SELECT 'categorias_ranking', COUNT(*) FROM categorias_ranking UNION ALL
SELECT 'perfis', COUNT(*) FROM perfis UNION ALL
SELECT 'opcoes_configuracao', COUNT(*) FROM opcoes_configuracao UNION ALL
SELECT 'configuracoes_usuario', COUNT(*) FROM configuracoes_usuario UNION ALL
SELECT 'treinos', COUNT(*) FROM treinos UNION ALL
SELECT 'exercicios', COUNT(*) FROM exercicios UNION ALL
SELECT 'treino_exercicios', COUNT(*) FROM treino_exercicios UNION ALL
SELECT 'historico_treinos', COUNT(*) FROM historico_treinos UNION ALL
SELECT 'recordes', COUNT(*) FROM recordes UNION ALL
SELECT 'titulos', COUNT(*) FROM titulos UNION ALL
SELECT 'usuario_titulos', COUNT(*) FROM usuario_titulos UNION ALL
SELECT 'medalhas', COUNT(*) FROM medalhas UNION ALL
SELECT 'duelos', COUNT(*) FROM duelos UNION ALL
SELECT 'desafios', COUNT(*) FROM desafios UNION ALL
SELECT 'participacoes', COUNT(*) FROM participacoes UNION ALL
SELECT 'desafios_academia', COUNT(*) FROM desafios_academia UNION ALL
SELECT 'planos', COUNT(*) FROM planos UNION ALL
SELECT 'matriculas', COUNT(*) FROM matriculas UNION ALL
SELECT 'pagamentos', COUNT(*) FROM pagamentos
"""


def popular(banco=None):
    """Recria as tabelas e insere os dados. Devolve [(tabela, linhas)]. Usado também pelos testes."""
    banco = banco or os.environ["DB_NAME"]
    con = conectar(banco)
    try:
        with con.cursor() as cur:
            criar_tabelas(cur)   # CREATE/DROP fazem commit automático no MySQL
            inserir_dados(cur)   # os INSERTs são uma transação só...
        con.commit()             # ...confirmada aqui (se algo falhar antes, nada fica pela metade)
        with con.cursor() as cur:
            cur.execute(CONTAGEM)
            return [(r["tabela"], r["linhas"]) for r in cur.fetchall()]
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser(description="Recria as tabelas do GymSystem e insere os dados iniciais.")
    parser.add_argument("--banco", help="nome do banco (padrão: DB_NAME do .env)")
    parser.add_argument("-y", "--sim", action="store_true", help="não pedir confirmação")
    args = parser.parse_args()
    banco = args.banco or os.environ.get("DB_NAME")
    if not banco or "DB_USER" not in os.environ:
        sys.exit("Configure o arquivo backend/.env (veja o .env.example).")

    if not args.sim:
        resp = input(f"Isto APAGA todos os dados do banco '{banco}' e recria do zero. Continuar? [s/N] ")
        if resp.strip().lower() != "s":
            sys.exit("Cancelado.")

    linhas = popular(banco)
    print(f"Banco '{banco}' populado:")
    for tabela, n in linhas:
        print(f"  {tabela:<22} {n:>4}")
    print(f"\nLogins: lucas.oliveira@email.com / senha1234567  |  admin@gymsystem.com / admin123"
          f"\n        demais alunos: <nome.sobrenome>@email.com / {SENHA_ALUNOS_DEMO}")


if __name__ == "__main__":
    main()

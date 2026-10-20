"""
Dados fictícios usados ENQUANTO o banco de dados não está pronto.

Tudo aqui fica em memória: ao reiniciar o servidor, volta ao estado inicial.
Quando o time do banco terminar, este arquivo deixa de ser usado
(o repositorio.py passa a consultar o banco).
"""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

HOJE = date.today()


def dias_atras(n):
    return (HOJE - timedelta(days=n)).isoformat()


def dias_depois(n):
    return (HOJE + timedelta(days=n)).isoformat()


# ------------------------------------------------------------------ usuários
# A senha NUNCA é guardada em texto puro, só o hash.
USUARIOS = [
    {"id": 1, "nome": "Lucas Oliveira", "email": "lucas.oliveira@email.com",
     "senha_hash": generate_password_hash("senha1234567"), "papel": "aluno"},
    {"id": 100, "nome": "Administrador", "email": "admin@gymsystem.com",
     "senha_hash": generate_password_hash("admin123"), "papel": "admin"},
]


# ------------------------------------------------------------------ treinos
def _ex(nome, grupo, series, reps, carga):
    return {"nome": nome, "grupo": grupo, "series": series, "reps": reps, "carga": carga}


TREINOS = [
    {"codigo": "A", "nome": "Treino A", "grupo": "Peito e Tríceps", "minutos": 45, "xp": 120,
     "exercicios": [_ex("Supino Reto", "Peito", 4, 12, 40), _ex("Supino Inclinado", "Peito", 3, 12, 30),
                    _ex("Crucifixo", "Peito", 3, 15, 14), _ex("Tríceps Testa", "Tríceps", 3, 12, 20),
                    _ex("Tríceps Corda", "Tríceps", 3, 15, 25)]},
    {"codigo": "B", "nome": "Treino B", "grupo": "Costas e Bíceps", "minutos": 50, "xp": 130,
     "exercicios": [_ex("Puxada Frontal", "Costas", 4, 12, 45), _ex("Remada Curvada", "Costas", 4, 10, 40),
                    _ex("Remada Baixa", "Costas", 3, 12, 35), _ex("Rosca Direta", "Bíceps", 3, 12, 20),
                    _ex("Rosca Martelo", "Bíceps", 3, 12, 12)]},
    {"codigo": "C", "nome": "Treino C", "grupo": "Pernas e Ombros", "minutos": 55, "xp": 140,
     "exercicios": [_ex("Agachamento", "Pernas", 4, 10, 80), _ex("Leg Press", "Pernas", 4, 12, 150),
                    _ex("Cadeira Extensora", "Pernas", 3, 15, 45), _ex("Desenvolvimento", "Ombros", 3, 12, 24),
                    _ex("Elevação Lateral", "Ombros", 3, 15, 8)]},
]

# ------------------------------------------------------------------ perfil do aluno (gamificação)
PERFIS = {
    1: {"nivel": 12, "xp": 2450, "sequencia": 12, "melhor_sequencia": 18,
        "ultimo_treino": dias_atras(1), "treinos_feitos": 57, "categoria_ranking": "Evoluídos",
        "frequencia_mes": {"ativos": 9, "meta": 10},
        "config": {"notificacoes_treino": True, "sons_app": True, "lembretes_agua": False}},
}

HISTORICO = {
    1: [{"data": dias_atras(1), "treino": "C", "minutos": 55, "exercicios": 5, "xp": 140},
        {"data": dias_atras(2), "treino": "B", "minutos": 50, "exercicios": 5, "xp": 130}],
}

RECORDES = {1: {"Supino Reto": 45, "Agachamento": 80}}

EVOLUCAO_CARGA = {
    1: {"exercicio": "Supino Reto", "variacao": "+15% este mês",
        "Semana": {"rotulos": ["Semana 1", "Semana 2", "Semana 3", "Semana 4"], "valores": [34, 38, 41, 45]},
        "Mês": {"rotulos": ["Jun", "Jul", "Ago", "Set"], "valores": [30, 35, 40, 45]},
        "Geral": {"rotulos": ["2023", "2024", "2025", "2026"], "valores": [20, 30, 38, 45]}},
}

TITULOS = {
    1: [{"icone": "🛡️", "nome": "Guerreiro", "descricao": "Fazer 50 treinos no total", "liberado": True},
        {"icone": "🏃", "nome": "Maratonista", "descricao": "Treinar 30 dias seguidos", "liberado": False},
        {"icone": "🔥", "nome": "Recordista", "descricao": "Bater 10 recordes pessoais", "liberado": True},
        {"icone": "🥇", "nome": "Campeão", "descricao": "1ª vitória em uma competição", "liberado": False}],
}

# "contador" diz ao back-end qual número do perfil alimenta o progresso da medalha.
MEDALHAS = {
    1: [{"icone": "🌱", "nome": "Primeiro Treino", "descricao": "Primeiro dia no aplicativo feito", "meta": 1, "contador": "treinos_feitos"},
        {"icone": "🔥", "nome": "Consistência 7", "descricao": "Treinar por 7 dias seguidos", "meta": 7, "contador": "melhor_sequencia"},
        {"icone": "💪", "nome": "Guerreiro 50", "descricao": "Completar 50 treinos", "meta": 50, "contador": "treinos_feitos"},
        {"icone": "🛡️", "nome": "Guerreiro 100", "descricao": "Completar 100 treinos", "meta": 100, "contador": "treinos_feitos"},
        {"icone": "⚡", "nome": "Recordista", "descricao": "Bater recordes de força", "meta": 1, "contador": "recordes"},
        {"icone": "🏆", "nome": "Top 10 Ranking", "descricao": "Ficar no top 10 semanal", "meta": 1, "contador": None}],
}

# ------------------------------------------------------------------ social
# usuario_id preenchido = aluno do sistema (o XP vem do perfil dele).
RANKING = {
    "Evoluídos": [{"usuario_id": None, "nome": "Gustavo", "xp": 3240, "emoji": "🏋️"},
                  {"usuario_id": None, "nome": "Mariana", "xp": 2710, "emoji": "💪"},
                  {"usuario_id": None, "nome": "Camila", "xp": 2580, "emoji": "🏃‍♀️"},
                  {"usuario_id": 1, "nome": "Lucas Oliveira", "xp": 0, "emoji": None},
                  {"usuario_id": None, "nome": "Rafaela F.", "xp": 2120, "emoji": None},
                  {"usuario_id": None, "nome": "Mateus B.", "xp": 1980, "emoji": None},
                  {"usuario_id": None, "nome": "Diego T.", "xp": 1710, "emoji": None}],
    "Moderados": [{"usuario_id": None, "nome": "Bianca", "xp": 1890, "emoji": "🧘"},
                  {"usuario_id": None, "nome": "Renato", "xp": 1760, "emoji": "🚴"},
                  {"usuario_id": None, "nome": "Paula", "xp": 1640, "emoji": "🏃"},
                  {"usuario_id": None, "nome": "Caio M.", "xp": 1420, "emoji": None},
                  {"usuario_id": None, "nome": "Alice R.", "xp": 1210, "emoji": None}],
    "Iniciantes": [{"usuario_id": None, "nome": "Tiago", "xp": 980, "emoji": "🌱"},
                   {"usuario_id": None, "nome": "Nina", "xp": 870, "emoji": "🌱"},
                   {"usuario_id": None, "nome": "Otávio", "xp": 760, "emoji": "🌱"},
                   {"usuario_id": None, "nome": "Lívia S.", "xp": 650, "emoji": None},
                   {"usuario_id": None, "nome": "Hugo P.", "xp": 540, "emoji": None}],
}

DUELOS = {
    1: {"id": 1, "oponente": {"nome": "Maria Silva", "nivel": 15, "xp": 1450},
        "xp_usuario": 1850, "objetivo": "Mais XP em 7 dias", "termina_em": dias_depois(5)},
}

CONVITES = {1: [{"id": 7, "de": "Pedro Costa", "desafio": "Foco em Pernas", "dias": 5}]}
CONVITES_RESPONDIDOS = []

DESAFIO_ATIVO = {"id": 1, "nome": "Desafio Semanal de Cardio", "meta": "Maior ganho de XP em 7 dias",
                 "recompensa_xp": 500, "treinos_meta": 5, "termina_em": dias_depois(2)}
PARTICIPANTES_DESAFIO = {1: {"outros": 12, "usuarios": set()}}

DESAFIOS_ACADEMIA = [
    {"icone": "🔥", "nome": "Treino Fiel", "descricao": "Treinar 5x em uma semana", "xp": 200, "status": "Pendente"},
    {"icone": "💪", "nome": "Monstro do Legpress", "descricao": "Atingir 150kg no Legpress", "xp": 300, "status": "Finalizado"},
]

# ------------------------------------------------------------------ administração
TOTAL_MEMBROS = 234
ATIVOS_FORA_DA_AMOSTRA = 186  # a amostra abaixo tem só 4 alunos; o resto é contado aqui

MEMBROS = [
    {"id": 1, "nome": "Lucas Silva", "cpf": "123.456.789-00", "frequencia": "3x/sem", "nivel": 12, "ativo": True,
     "sequencia": 12, "ultimo_treino": dias_atras(0), "cadastro": "2026-01-10",
     "plano": "Trimestral Recorrente", "valor_mensal": 99.00, "vencimento": dias_depois(78),
     "treinos_recentes": [{"titulo": "Treino A — Peito e Tríceps", "minutos": 48, "xp": 120, "data": dias_atras(0)},
                          {"titulo": "Desafio Semanal de Cardio", "minutos": 30, "xp": 200, "data": dias_atras(1)}]},
    {"id": 2, "nome": "Mariana Costa", "cpf": "234.567.890-11", "frequencia": "4x/sem", "nivel": 15, "ativo": True,
     "sequencia": 8, "ultimo_treino": dias_atras(1), "cadastro": "2025-11-20",
     "plano": "Anual", "valor_mensal": 79.00, "vencimento": dias_depois(56),
     "treinos_recentes": [{"titulo": "Treino B — Costas e Bíceps", "minutos": 52, "xp": 130, "data": dias_atras(1)}]},
    {"id": 3, "nome": "Gustavo Santos", "cpf": "345.678.901-22", "frequencia": "5x/sem", "nivel": 18, "ativo": True,
     "sequencia": 21, "ultimo_treino": dias_atras(2), "cadastro": "2025-08-03",
     "plano": "Semestral", "valor_mensal": 74.83, "vencimento": dias_depois(131),
     "treinos_recentes": [{"titulo": "Treino C — Pernas e Ombros", "minutos": 60, "xp": 140, "data": dias_atras(2)}]},
    {"id": 4, "nome": "Carlos Oliveira", "cpf": "456.789.012-33", "frequencia": "", "nivel": 5, "ativo": False,
     "sequencia": 0, "ultimo_treino": dias_atras(32), "cadastro": "2026-02-28",
     "plano": "Mensal", "valor_mensal": 99.00, "vencimento": dias_atras(15),
     "treinos_recentes": []},
]

PLANOS = [{"id": 1, "nome": "Mensal", "preco": 99.0, "alunos_ativos": 45},
          {"id": 2, "nome": "Trimestral", "preco": 249.0, "alunos_ativos": 92},
          {"id": 3, "nome": "Semestral", "preco": 449.0, "alunos_ativos": 38},
          {"id": 4, "nome": "Anual", "preco": 799.0, "alunos_ativos": 14}]

RESUMO_CONTRATOS = {"vencendo_30d": 15, "vencidas": 23, "novos_mes": 8}

VENCIMENTOS = [{"aluno": "Bruno Medeiros", "plano": "Mensal", "vence_em": dias_depois(2)},
               {"aluno": "Jessica Souza", "plano": "Trimestral", "vence_em": dias_depois(5)}]

FINANCEIRO = {"receita_estimada": 28400, "recebido": 26200, "inadimplencia": 2200, "cancelamentos_mes": 3,
              "evolucao": [{"mes": "Abr", "valor": 18000}, {"mes": "Mai", "valor": 20000},
                           {"mes": "Jun", "valor": 24000}, {"mes": "Jul", "valor": 26000},
                           {"mes": "Ago", "valor": 28000}, {"mes": "Set", "valor": 28400}]}

RECEBIMENTOS = [{"aluno": "Lucas Silva", "plano": "Trimestral", "valor": 99.00, "confirmado": True},
                {"aluno": "Mariana Costa", "plano": "Anual", "valor": 79.00, "confirmado": True},
                {"aluno": "Pedro Camargo", "plano": "Mensal", "valor": 119.00, "confirmado": False}]

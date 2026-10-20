"""
Testes automáticos da API.  Rodar (dentro da pasta backend):
    python -m unittest -v

Os testes rodam SEMPRE no banco de TESTE (DB_NAME_TESTE do .env, padrão "gymsystem_test"),
nunca no banco principal. No início de cada execução o banco de teste é APAGADO e recriado
pelo seed, então os testes sempre começam dos mesmos dados.
"""
import os
import unittest
from pathlib import Path

from dotenv import dotenv_values

# --- Escolhe o banco de teste ANTES de importar o app (a conexão lê DB_NAME do ambiente).
_ENV = dotenv_values(Path(__file__).resolve().parent / ".env")
BANCO_TESTE = os.environ.get("DB_NAME_TESTE") or _ENV.get("DB_NAME_TESTE") or "gymsystem_test"
if not BANCO_TESTE.endswith("_test"):
    # Trava de segurança: o seed apaga tudo. O nome precisa deixar claro que é banco de teste.
    raise RuntimeError(f"Banco de teste '{BANCO_TESTE}' recusado: o nome precisa terminar em '_test'.")
os.environ["DB_NAME"] = BANCO_TESTE

import app as modulo_app  # noqa: E402
import repositorio as repo  # noqa: E402
from db import seed  # noqa: E402


def setUpModule():
    """Roda uma vez, antes de todos os testes: recria o banco de teste do zero."""
    seed.popular(BANCO_TESTE)


class TesteAPI(unittest.TestCase):
    def setUp(self):
        self.app = modulo_app.criar_app()
        self.c = self.app.test_client()

    def entrar(self, email="lucas.oliveira@email.com", senha="senha1234567"):
        r = self.c.post("/api/login", json={"email": email, "senha": senha})
        self.assertEqual(r.status_code, 200, r.json)
        return {"Authorization": "Bearer " + r.json["token"]}

    # ---------------- autenticação
    def test_login_errado(self):
        r = self.c.post("/api/login", json={"email": "lucas.oliveira@email.com", "senha": "errada"})
        self.assertEqual(r.status_code, 401)
        self.assertIn("erro", r.json)

    def test_sem_token(self):
        self.assertEqual(self.c.get("/api/aluno/resumo").status_code, 401)

    def test_aluno_nao_acessa_admin(self):
        self.assertEqual(self.c.get("/api/admin/painel", headers=self.entrar()).status_code, 403)

    def test_logout_invalida_token(self):
        h = self.entrar()
        self.c.post("/api/logout", headers=h)
        self.assertEqual(self.c.get("/api/eu", headers=h).status_code, 401)

    # ---------------- aluno
    def test_resumo_e_treinos(self):
        h = self.entrar()
        r = self.c.get("/api/aluno/resumo", headers=h).json
        self.assertEqual(r["nome"], "Lucas Oliveira")
        self.assertEqual(r["titulo"], "Intermediário")
        self.assertEqual(len(r["semana"]), 7)
        treinos = self.c.get("/api/treinos", headers=h).json
        self.assertEqual([t["codigo"] for t in treinos], ["A", "B", "C"])

    def test_concluir_treino(self):
        h = self.entrar()
        antes = self.c.get("/api/aluno/resumo", headers=h).json
        cargas = [50, 30, 14, 20, 25]  # 50 kg no supino supera o recorde de 45
        r = self.c.post("/api/treinos/concluir", headers=h,
                        json={"treino": "A", "segundos": 2700, "cargas": cargas})
        self.assertEqual(r.status_code, 201, r.json)
        res = r.json["resultado"]
        self.assertEqual(res["minutos"], 45)
        self.assertTrue(any(x["exercicio"] == "Supino Reto" for x in res["recordes"]))
        depois = r.json["resumo"]
        self.assertTrue(depois["treinou_hoje"])
        self.assertGreater(depois["nivel"] * 3000 + depois["xp"], antes["nivel"] * 3000 + antes["xp"])
        hist = self.c.get("/api/aluno/historico", headers=h).json
        self.assertEqual(hist["treinos"][0]["quando"], "Hoje")

    def test_concluir_invalido(self):
        h = self.entrar()
        self.assertEqual(self.c.post("/api/treinos/concluir", headers=h, json={"treino": "Z"}).status_code, 404)
        self.assertEqual(self.c.post("/api/treinos/concluir", headers=h,
                                     json={"treino": "A", "cargas": [1, 2]}).status_code, 400)

    def test_ranking(self):
        h = self.entrar()
        lista = self.c.get("/api/ranking?categoria=Evoluídos", headers=h).json
        self.assertEqual(sum(1 for x in lista if x["eu"]), 1)
        self.assertEqual(self.c.get("/api/ranking?categoria=xyz", headers=h).status_code, 400)

    def test_desafio_e_config(self):
        h = self.entrar()
        d = self.c.get("/api/desafios", headers=h).json["ativo"]
        r = self.c.post(f"/api/desafios/{d['id']}/participar", headers=h).json
        self.assertNotEqual(r["participando"], d["participando"])
        c = self.c.put("/api/aluno/config", headers=h, json={"chave": "sons_app", "valor": False})
        self.assertFalse(c.json["config"]["sons_app"])

    # ---------------- admin
    def test_admin(self):
        h = self.entrar("admin@gymsystem.com", "admin123")
        # Contado do banco: todos os alunos com matrícula criados pelo seed.
        self.assertEqual(self.c.get("/api/admin/painel", headers=h).json["total_membros"], len(seed.ALUNOS))
        m = self.c.get("/api/admin/membros?status=inativos", headers=h).json["membros"]
        self.assertTrue(all(not x["ativo"] for x in m))
        r = self.c.patch("/api/admin/membros/4", headers=h, json={"ativo": True})
        self.assertTrue(r.json["ativo"])
        self.c.patch("/api/admin/membros/4", headers=h, json={"ativo": False})
        self.assertEqual(self.c.get("/api/admin/membros/999", headers=h).status_code, 404)
        self.assertEqual(len(self.c.get("/api/admin/planos", headers=h).json["planos"]), 4)
        self.assertIn("recebimentos", self.c.get("/api/admin/financeiro", headers=h).json)

    # ---------------- banco de dados (novos)
    def test_concluir_treino_atomico(self):
        """Se um passo do 'concluir treino' falha, NADA do que foi gravado antes fica no banco."""
        h = self.entrar()
        antes = (self.c.get("/api/aluno/resumo", headers=h).json, self.c.get("/api/aluno/historico", headers=h).json,
                 self.c.get("/api/duelos", headers=h).json)
        original = repo.somar_xp_duelo

        def falha(*_):  # último passo do concluir_treino: recordes, perfil e histórico já foram gravados
            raise RuntimeError("falha simulada")

        repo.somar_xp_duelo = falha
        self.app.logger.disabled = True  # o erro é proposital: não sujar a saída dos testes
        try:
            r = self.c.post("/api/treinos/concluir", headers=h,
                            json={"treino": "C", "segundos": 3000, "cargas": [100, 150, 45, 24, 8]})
        finally:
            repo.somar_xp_duelo = original
        self.assertEqual(r.status_code, 500)
        depois = (self.c.get("/api/aluno/resumo", headers=h).json, self.c.get("/api/aluno/historico", headers=h).json,
                  self.c.get("/api/duelos", headers=h).json)
        self.assertEqual(antes, depois)

    def test_ranking_so_matricula_ativa(self):
        """Aluno com matrícula inativa (Carlos, id 4) não aparece no ranking; reativado, aparece."""
        h, adm = self.entrar(), self.entrar("admin@gymsystem.com", "admin123")

        def nomes():
            return [x["nome"] for x in self.c.get("/api/ranking?categoria=Iniciantes", headers=h).json]

        self.assertNotIn("Carlos Oliveira", nomes())
        self.c.patch("/api/admin/membros/4", headers=adm, json={"ativo": True})
        try:
            self.assertIn("Carlos Oliveira", nomes())
        finally:
            self.c.patch("/api/admin/membros/4", headers=adm, json={"ativo": False})

    def test_dados_persistem_em_novo_app(self):
        """Um treino concluído continua lá numa instância NOVA do app (os dados estão no banco, não na memória)."""
        h = self.entrar()
        self.assertEqual(self.c.post("/api/treinos/concluir", headers=h,
                                     json={"treino": "B", "segundos": 3000}).status_code, 201)
        novo = modulo_app.criar_app().test_client()
        r = novo.post("/api/login", json={"email": "lucas.oliveira@email.com", "senha": "senha1234567"})
        hist = novo.get("/api/aluno/historico", headers={"Authorization": "Bearer " + r.json["token"]}).json
        self.assertEqual((hist["treinos"][0]["treino"], hist["treinos"][0]["quando"]), ("B", "Hoje"))


if __name__ == "__main__":
    unittest.main()

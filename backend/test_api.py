"""
Testes automáticos da API.  Rodar (dentro da pasta backend):
    python -m unittest -v
"""
import unittest

import app as modulo_app


class TesteAPI(unittest.TestCase):
    def setUp(self):
        self.c = modulo_app.criar_app().test_client()

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
        self.assertEqual(self.c.get("/api/admin/painel", headers=h).json["total_membros"], 234)
        m = self.c.get("/api/admin/membros?status=inativos", headers=h).json["membros"]
        self.assertTrue(all(not x["ativo"] for x in m))
        r = self.c.patch("/api/admin/membros/4", headers=h, json={"ativo": True})
        self.assertTrue(r.json["ativo"])
        self.c.patch("/api/admin/membros/4", headers=h, json={"ativo": False})
        self.assertEqual(self.c.get("/api/admin/membros/999", headers=h).status_code, 404)
        self.assertEqual(len(self.c.get("/api/admin/planos", headers=h).json["planos"]), 4)
        self.assertIn("recebimentos", self.c.get("/api/admin/financeiro", headers=h).json)


if __name__ == "__main__":
    unittest.main()

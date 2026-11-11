# -*- coding: utf-8 -*-
"""Testes do validate_spec.py (sem rede; specs em JSON, arquivos temporários)."""

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import validate_spec as vs  # noqa: E402


def fixture_path(name):
    return os.path.join(FIXTURES, name)


def load(name):
    with open(fixture_path(name), encoding="utf-8") as fh:
        return json.load(fh)


class JsonYaml(object):
    """PyYAML falso: aceita JSON (que é YAML válido) para testar o caminho .yaml sem a dependência."""

    @staticmethod
    def safe_load(text):
        return json.loads(text)


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="validate_spec_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.n = 0

    def write(self, spec, name=None, raw=None):
        self.n += 1
        path = os.path.join(self.tmp, name or ("spec%d.json" % self.n))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(raw if raw is not None else json.dumps(spec, ensure_ascii=False))
        return path

    def run_cli(self, argv, yaml_module=False):
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                code = vs.main(argv, yaml_module=yaml_module)
            except SystemExit as exc:
                code = exc.code
        raw = buf.getvalue()
        try:
            return code, json.loads(raw), raw
        except ValueError:
            return code, None, raw

    def check(self, spec, *flags):
        code, out, _ = self.run_cli([self.write(spec)] + list(flags))
        return code, out

    def mutated(self, fn, base="spec_valid.json", *flags):
        spec = load(base)
        fn(spec)
        return self.check(spec, *flags)

    @staticmethod
    def rules(out, severity=None):
        return [f["id_regra"] for f in out["data"]["findings"] if severity in (None, f["severidade"])]

    def assertRule(self, out, rule, path=None, severity=None):
        found = [f for f in out["data"]["findings"] if f["id_regra"] == rule]
        self.assertTrue(found, "regra %s não apareceu; achados: %s" % (rule, self.rules(out)))
        if path is not None:
            self.assertTrue(any(f["caminho"] == path for f in found),
                            "%s sem caminho %s: %s" % (rule, path, [f["caminho"] for f in found]))
        if severity is not None:
            self.assertTrue(any(f["severidade"] == severity for f in found))

    def assertNoRule(self, out, rule):
        self.assertNotIn(rule, self.rules(out))


class ContratoDeSaidaTests(Base):

    def test_spec_valido_devolve_valid_exit_0_e_contrato_json(self):
        """Dado um spec aprovado e correto, quando valida, então status valid, exit 0 e as 5 chaves do contrato."""
        code, out, _ = self.run_cli([fixture_path("spec_valid.json")])
        self.assertEqual(code, 0)
        self.assertEqual(set(out), {"ok", "status", "data", "problems", "next_steps"})
        self.assertEqual((out["ok"], out["status"]), (True, "valid"))
        self.assertEqual(out["data"]["findings"], [])
        self.assertEqual(out["data"]["counts"]["sections"], 3)
        self.assertEqual(out["data"]["counts"]["items"], 4)
        self.assertEqual(out["problems"], [])

    def test_exemplo_completo_do_form_spec_e_valido(self):
        """Dado o exemplo completo do FORM-SPEC.md extraído, quando valida, então valid ou valid_with_warnings."""
        code, out, _ = self.run_cli([fixture_path("spec_example.json"), "--for-build"])
        self.assertIn(out["status"], ("valid", "valid_with_warnings"))
        self.assertEqual(code, 0)
        self.assertEqual(out["data"]["counts"]["sections"], 3)
        self.assertEqual(out["data"]["counts"]["items"], 8)

    def test_achado_tem_os_quatro_campos(self):
        """Dado um spec com erro, quando valida, então cada achado traz id_regra, severidade, caminho e mensagem."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][0].update(title="Pergunta sem título"))
        f = out["data"]["findings"][0]
        self.assertTrue({"id_regra", "severidade", "caminho", "mensagem"} <= set(f))
        self.assertIn(f["severidade"], ("erro", "aviso"))
        self.assertTrue(f["id_regra"].startswith("SPEC-"))

    def test_todo_id_emitido_existe_no_catalogo(self):
        """Dado um spec cheio de problemas, quando valida, então todos os ids emitidos estão em RULES."""
        def ruin(s):
            s["sections"][0]["items"][0]["type"] = "xyz"
            s["sections"][1]["items"].append({"id": "q1", "type": "short_text", "title": "Senha", "use": ""})
            s["status"] = "nope"
        _, out = self.mutated(ruin)
        for r in self.rules(out):
            self.assertIn(r, vs.RULES)

    def test_formato_texto_e_legivel(self):
        """Dado --format text, quando valida spec com erro, então imprime linhas ERRO com id e caminho (não JSON)."""
        spec = load("spec_valid.json")
        spec["sections"][0]["items"][0]["title"] = ""
        code, out, raw = self.run_cli([self.write(spec), "--format", "text"])
        self.assertIsNone(out)
        self.assertEqual(code, 1)
        self.assertIn("Status: invalid", raw)
        self.assertIn("ERRO  SPEC-TIT-01 sections[0].items[0].title", raw)

    def test_rules_lista_catalogo(self):
        """Dado --rules, quando executa, então devolve o catálogo com ids estáveis e exit 0."""
        code, out, _ = self.run_cli(["--rules"])
        self.assertEqual(code, 0)
        ids = [r[0] for r in out["data"]["rules"]]
        self.assertEqual(len(ids), len(vs.RULES))
        for needed in ("SPEC-ID-01", "SPEC-NAV-09", "SPEC-SEC-01", "SPEC-APR-04"):
            self.assertIn(needed, ids)


class EntradaTests(Base):

    def test_arquivo_inexistente_e_usage_error(self):
        """Dado caminho que não existe, quando valida, então usage_error e exit 2."""
        code, out, _ = self.run_cli([os.path.join(self.tmp, "nada.json")])
        self.assertEqual((code, out["status"], out["ok"]), (2, "usage_error", False))

    def test_extensao_nao_suportada_e_usage_error(self):
        """Dado um .txt, quando valida, então usage_error orientando converter."""
        code, out, _ = self.run_cli([self.write({}, "spec.txt")])
        self.assertEqual((code, out["status"]), (2, "usage_error"))
        self.assertIn("JSON", " ".join(out["next_steps"]))

    def test_sem_argumento_e_usage_error_em_json(self):
        """Dado nenhum argumento, quando executa, então usage_error em JSON e exit 2."""
        code, out, _ = self.run_cli([])
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_flag_desconhecida_e_usage_error_em_json(self):
        """Dado uma flag inexistente, quando executa, então argparse vira JSON usage_error exit 2."""
        code, out, _ = self.run_cli(["--nada"])
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_yaml_sem_pyyaml_explica_converter_ou_instalar(self):
        """Dado .yaml e PyYAML ausente, quando valida, então usage_error com as duas saídas (JSON ou pip install pyyaml)."""
        path = self.write(None, "spec.yaml", raw="spec_version: 1\n")
        code, out, _ = self.run_cli([path], yaml_module=None)
        self.assertEqual((code, out["status"]), (2, "usage_error"))
        text = " ".join(out["problems"] + out["next_steps"])
        self.assertIn("PyYAML", text)
        self.assertIn("JSON", text)
        self.assertIn("pip install pyyaml", text)

    def test_yaml_com_pyyaml_injetado_valida_normalmente(self):
        """Dado .yml e um carregador YAML disponível, quando valida, então segue o mesmo caminho do JSON."""
        path = self.write(load("spec_valid.json"), "spec.yml")
        code, out, _ = self.run_cli([path], yaml_module=JsonYaml)
        self.assertEqual((code, out["status"]), (0, "valid"))

    def test_yaml_real_se_pyyaml_instalado(self):
        """Dado PyYAML real instalado, quando a data de aprovação vem sem aspas, então vira ISO e valida."""
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML não instalado")
        raw = "spec_version: 1\n"
        spec = load("spec_valid.json")
        spec["approved_at"] = "2026-11-11"
        path = self.write(spec, "real.yaml", raw=yaml.safe_dump(spec, allow_unicode=True).replace("'2026-11-11'", "2026-11-11"))
        code, out, _ = self.run_cli([path])
        self.assertEqual(out["status"], "valid", out["problems"])

    def test_yaml_invalido_vira_invalid_e_nao_crash(self):
        """Dado YAML que o carregador rejeita, quando valida, então invalid com SPEC-IO-01."""
        class Boom(object):
            @staticmethod
            def safe_load(text):
                raise ValueError("mapping values are not allowed here")
        code, out, _ = self.run_cli([self.write(None, "x.yaml", raw="a: b: c")], yaml_module=Boom)
        self.assertEqual((code, out["status"]), (1, "invalid"))
        self.assertRule(out, "SPEC-IO-01")

    def test_json_malformado_e_invalid_io01(self):
        """Dado JSON quebrado, quando valida, então invalid com SPEC-IO-01 (não usage_error)."""
        code, out, _ = self.run_cli([self.write(None, "bad.json", raw="{ não é json")])
        self.assertEqual((code, out["status"]), (1, "invalid"))
        self.assertRule(out, "SPEC-IO-01")

    def test_raiz_que_nao_e_objeto_e_invalid(self):
        """Dado JSON cuja raiz é lista, quando valida, então SPEC-IO-01."""
        code, out, _ = self.run_cli([self.write([1, 2])])
        self.assertEqual(out["status"], "invalid")
        self.assertRule(out, "SPEC-IO-01")

    def test_chave_duplicada_no_json(self):
        """Dado JSON com chave repetida, quando valida, então SPEC-IO-02 aponta o caminho."""
        raw = json.dumps(load("spec_valid.json"), ensure_ascii=False).replace('"version": 1,', '"version": 1, "version": 2,', 1)
        code, out, _ = self.run_cli([self.write(None, "dup.json", raw=raw)])
        self.assertEqual(out["status"], "invalid")
        self.assertRule(out, "SPEC-IO-02", "version")

    def test_spec_vazio_nao_quebra(self):
        """Dado {} como spec, quando valida, então invalid com erros estruturais, sem exceção."""
        code, out = self.check({})
        self.assertEqual((code, out["status"]), (1, "invalid"))
        self.assertRule(out, "SPEC-STR-01")
        self.assertRule(out, "SPEC-ID-03")

    def test_tipos_errados_nao_quebram(self):
        """Dado campos com tipos absurdos, quando valida, então invalid sem exceção."""
        spec = {"spec_version": 1, "status": [], "meta": "x", "brief": 3, "build": [], "privacy": "p", "settings": 7,
                "quiz": "q", "publish": 1, "responses": [], "sections": [1, {"id": 5, "items": "x"}, {"id": "s1", "items": [3, {"id": [], "type": {}}]}]}
        code, out = self.check(spec)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "invalid")


class EstruturaTests(Base):

    def test_id_de_item_fora_do_formato(self):
        """Dado item com id 'x1', quando valida, então SPEC-ID-01 no caminho do id."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][0].update(id="x1"))
        self.assertRule(out, "SPEC-ID-01", "sections[0].items[0].id")

    def test_id_de_secao_fora_do_formato_e_zero_a_esquerda(self):
        """Dado seção 's02' e item 'q01', quando valida, então SPEC-ID-01 nos dois."""
        def m(s):
            s["sections"][1]["id"] = "s02"
            s["sections"][0]["items"][0]["id"] = "q01"
            s["sections"][0]["items"][1]["options"][1]["go_to"] = "s3"
        _, out = self.mutated(m)
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-ID-01"]
        self.assertIn("sections[1].id", paths)
        self.assertIn("sections[0].items[0].id", paths)

    def test_id_duplicado_entre_itens(self):
        """Dado dois itens com q2, quando valida, então SPEC-ID-02 no segundo."""
        _, out = self.mutated(lambda s: s["sections"][1]["items"][0].update(id="q2"))
        self.assertRule(out, "SPEC-ID-02", "sections[1].items[0].id")

    def test_id_duplicado_entre_secoes(self):
        """Dado duas seções s3, quando valida, então SPEC-ID-02."""
        _, out = self.mutated(lambda s: s["sections"][1].update(id="s3"))
        self.assertRule(out, "SPEC-ID-02", "sections[2].id")

    def test_ids_fora_de_ordem_sao_aviso(self):
        """Dado q4 antes de q3, quando valida, então SPEC-ID-04 como aviso."""
        def m(s):
            s["sections"][1]["items"][0]["id"] = "q9"
            s["sections"][2]["items"][0]["id"] = "q4"
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-ID-04", severity="aviso")

    def test_pular_numeros_e_permitido(self):
        """Dado q1,q3,q7 crescentes com saltos, quando valida, então sem SPEC-ID-04 (q2 pode ter sido removido)."""
        def m(s):
            s["sections"][0]["items"][1]["id"] = "q3"
            s["sections"][1]["items"][0]["id"] = "q5"
            s["sections"][2]["items"][0]["id"] = "q7"
        _, out = self.mutated(m)
        self.assertNoRule(out, "SPEC-ID-04")

    def test_sem_s1(self):
        """Dado spec sem seção s1, quando valida, então SPEC-ID-03."""
        def m(s):
            s["sections"][0]["id"] = "s9"
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-ID-03")

    def test_secao_sem_itens(self):
        """Dado seção com items vazio, quando valida, então SPEC-STR-03."""
        _, out = self.mutated(lambda s: s["sections"][1].update(items=[]))
        self.assertRule(out, "SPEC-STR-03", "sections[1].items")

    def test_limite_de_300_itens(self):
        """Dado 301 itens, quando valida, então SPEC-LIM-01; com 300 não."""
        def fill(n):
            def m(s):
                base = s["sections"][2]["items"]
                for i in range(n - 4):
                    base.append({"id": "q%d" % (100 + i), "type": "title_description", "title": "Bloco %d" % i})
            return m
        _, out = self.mutated(fill(301))
        self.assertRule(out, "SPEC-LIM-01")
        _, out = self.mutated(fill(300))
        self.assertNoRule(out, "SPEC-LIM-01")

    def test_limite_de_75_secoes(self):
        """Dado 76 seções lineares, quando valida, então SPEC-LIM-02; com 75 não."""
        def fill(n):
            def m(s):
                s["sections"] = [{"id": "s%d" % i, "title": "Seção %s" % chr(65 + i % 26) * 1 + str(i), "items": [
                    {"id": "q%d" % i, "type": "short_text", "title": "Pergunta útil %d" % i, "use": "x"}]} for i in range(1, n + 1)]
            return m
        _, out = self.mutated(fill(76))
        self.assertRule(out, "SPEC-LIM-02")
        _, out = self.mutated(fill(75))
        self.assertNoRule(out, "SPEC-LIM-02")

    def test_titulo_padrao_e_vazio(self):
        """Dado títulos 'Pergunta sem título' e vazio, quando valida, então SPEC-TIT-01 em ambos."""
        def m(s):
            s["sections"][0]["items"][0]["title"] = "Pergunta sem título"
            s["sections"][1]["items"][0]["title"] = "   "
        _, out = self.mutated(m)
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-TIT-01"]
        self.assertIn("sections[0].items[0].title", paths)
        self.assertIn("sections[1].items[0].title", paths)

    def test_opcao_padrao(self):
        """Dado opção 'Opção 1', quando valida, então SPEC-TIT-01 no value."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"][0]["options"].__setitem__(0, {"value": "Opção 1"}))
        self.assertRule(out, "SPEC-TIT-01", "sections[2].items[0].options[0].value")

    def test_secao_alem_da_primeira_sem_titulo(self):
        """Dado s2 sem título, quando valida, então SPEC-TIT-02; s1 sem título é permitido."""
        _, out = self.mutated(lambda s: s["sections"][1].update(title=None))
        self.assertRule(out, "SPEC-TIT-02", "sections[1].title")
        self.assertNotIn("sections[0].title", [f["caminho"] for f in out["data"]["findings"]])

    def test_titulo_do_formulario_vazio(self):
        """Dado meta.title vazio, quando valida, então SPEC-STR-01."""
        _, out = self.mutated(lambda s: s["meta"].update(title=""))
        self.assertRule(out, "SPEC-STR-01", "meta.title")

    def test_use_ausente(self):
        """Dado pergunta sem use, quando valida, então SPEC-USE-01; título/imagem não exigem."""
        def m(s):
            s["sections"][0]["items"][0]["use"] = ""
            s["sections"][1]["items"].append({"id": "q8", "type": "title_description", "title": "Atenção"})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-USE-01", "sections[0].items[0].use")
        self.assertEqual(self.rules(out).count("SPEC-USE-01"), 1)

    def test_brief_goal_ausente(self):
        """Dado brief.goal vazio, quando valida, então SPEC-USE-02."""
        _, out = self.mutated(lambda s: s["brief"].update(goal=""))
        self.assertRule(out, "SPEC-USE-02")


class OpcoesETiposTests(Base):

    def test_opcoes_repetidas(self):
        """Dado opções 'Sim' e ' sim ', quando valida, então SPEC-OPT-01 (ignora caixa/espaços/acento)."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"][0].update(options=[{"value": "Sim"}, {"value": " sim "}]))
        self.assertRule(out, "SPEC-OPT-01")

    def test_multipla_escolha_com_uma_opcao(self):
        """Dado multiple_choice com 1 opção, quando valida, então SPEC-OPT-02."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][1].update(options=[{"value": "Sim", "go_to": "s3"}]))
        self.assertRule(out, "SPEC-OPT-02")

    def test_dropdown_com_uma_opcao(self):
        """Dado dropdown com 1 opção, quando valida, então SPEC-OPT-02."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"][0].update(type="dropdown", options=[{"value": "Só"}]))
        self.assertRule(out, "SPEC-OPT-02")

    def test_checkboxes_sem_options(self):
        """Dado checkboxes sem options, quando valida, então SPEC-OPT-03."""
        def m(s):
            del s["sections"][2]["items"][0]["options"]
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-OPT-03")

    def test_opcao_como_texto_puro_e_erro(self):
        """Dado opção escrita como string, quando valida, então SPEC-OPT-03."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"][0].update(options=["A", "B"]))
        self.assertRule(out, "SPEC-OPT-03")

    def test_tipo_invalido(self):
        """Dado type 'radio', quando valida, então SPEC-TYPE-01."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][0].update(type="radio"))
        self.assertRule(out, "SPEC-TYPE-01", "sections[0].items[0].type")

    def test_campo_exigido_pelo_tipo_ausente(self):
        """Dado linear_scale sem scale e grade sem grid, quando valida, então SPEC-TYPE-02 em cada um."""
        def m(s):
            del s["sections"][0]["items"][0]["scale"]
            s["sections"][2]["items"].append({"id": "q8", "type": "mc_grid", "title": "Avalie", "use": "x"})
        _, out = self.mutated(m)
        self.assertEqual(self.rules(out).count("SPEC-TYPE-02"), 2)

    def test_campo_que_nao_se_aplica_ao_tipo_e_aviso(self):
        """Dado short_text com options, quando valida, então SPEC-TYPE-03 aviso."""
        _, out = self.mutated(lambda s: s["sections"][1]["items"][0].update(options=[{"value": "a"}, {"value": "b"}]))
        self.assertRule(out, "SPEC-TYPE-03", severity="aviso")

    def test_other_em_dropdown(self):
        """Dado dropdown com other: true, quando valida, então SPEC-TYPE-04."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"][0].update(type="dropdown", other=True))
        self.assertRule(out, "SPEC-TYPE-04")

    def test_campo_desconhecido_e_aviso(self):
        """Dado 'requierd' no item, quando valida, então SPEC-TYPE-05 aviso."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][0].update(requierd=True))
        self.assertRule(out, "SPEC-TYPE-05", "sections[0].items[0].requierd", "aviso")

    def test_required_nao_booleano(self):
        """Dado required: 'sim', quando valida, então SPEC-TYPE-06."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][0].update(required="sim"))
        self.assertRule(out, "SPEC-TYPE-06")

    def test_escala_limites(self):
        """Dado low 2, high 11 e sem rótulo, quando valida, então SPEC-CFG-07 para cada falha."""
        def m(s):
            s["sections"][0]["items"][0]["scale"] = {"low": 2, "high": 11, "low_label": "a"}
        _, out = self.mutated(m)
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-CFG-07"]
        self.assertIn("sections[0].items[0].scale.low", paths)
        self.assertIn("sections[0].items[0].scale.high", paths)
        self.assertIn("sections[0].items[0].scale.high_label", paths)

    def test_escala_high_2_na_ui_e_valido(self):
        """Dado high 2 com build.path ui, quando valida, então sem erro e sem PENDENTE_UI."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][0]["scale"].update(high=2))
        self.assertEqual(out["status"], "valid")

    def test_escala_high_2_no_apps_script_vira_pendente_ui_aviso(self):
        """Dado high 2 e build.path apps_script, quando valida, então SPEC-BLD-04 aviso (não erro), status valid_with_warnings."""
        def m(s):
            s["build"]["path"] = "apps_script"
            s["theme"]["color"] = None
            s["sections"][0]["items"][0]["scale"]["high"] = 2
        code, out = self.mutated(m)
        self.assertRule(out, "SPEC-BLD-04", "sections[0].items[0].scale.high", "aviso")
        self.assertEqual((code, out["status"]), (0, "valid_with_warnings"))
        self.assertEqual(out["data"]["counts"]["pending_ui"], 1)
        self.assertEqual(len(out["data"]["pending_ui"]), 1)
        self.assertIn("PENDENTE_UI", out["data"]["findings"][0]["mensagem"])

    def test_escala_high_3_no_apps_script_nao_pende(self):
        """Dado high 3 no apps_script, quando valida, então nenhum PENDENTE_UI de escala."""
        def m(s):
            s["build"]["path"] = "apps_script"
            s["theme"]["color"] = None
            s["sections"][0]["items"][0]["scale"]["high"] = 3
        _, out = self.mutated(m)
        self.assertNoRule(out, "SPEC-BLD-04")

    def test_rating_invalido(self):
        """Dado rating com 11 níveis e ícone 'foguete', quando valida, então SPEC-CFG-07 duas vezes."""
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "rating", "title": "Nota geral", "use": "x", "rating": {"levels": 11, "icon": "foguete"}})
        _, out = self.mutated(m)
        self.assertEqual(self.rules(out).count("SPEC-CFG-07"), 2)

    def test_imagem_e_video(self):
        """Dado imagem sem source, largura 900 e vídeo fora do YouTube, quando valida, então SPEC-TYPE-02."""
        def m(s):
            s["sections"][2]["items"] += [
                {"id": "q8", "type": "image", "image": {"alt_text": "x", "width": 900}},
                {"id": "q9", "type": "video", "video": {"youtube_url": "https://vimeo.com/1"}}]
        _, out = self.mutated(m)
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-TYPE-02"]
        self.assertIn("sections[2].items[1].image.source", paths)
        self.assertIn("sections[2].items[1].image.width", paths)
        self.assertIn("sections[2].items[2].video.youtube_url", paths)

    def test_grade_com_linhas_repetidas(self):
        """Dado grade com linhas iguais, quando valida, então SPEC-OPT-01."""
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "mc_grid", "title": "Avalie os itens", "use": "x",
                                              "grid": {"rows": ["Som", "Som"], "columns": ["Bom", "Ruim"]}})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-OPT-01")

    def test_file_upload_exige_ui(self):
        """Dado file_upload com build.path apps_script, quando valida, então SPEC-BLD-01 erro; com ui não."""
        def item(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "file_upload", "title": "Envie o comprovante", "use": "Conferir pagamento",
                                              "description": "É preciso entrar com a conta Google.",
                                              "file_upload": {"types": ["pdf"], "max_files": 1, "max_size": "10MB"}})

        def apps(s):
            item(s)
            s["build"]["path"] = "apps_script"
            s["theme"]["color"] = None
        _, out = self.mutated(apps)
        self.assertRule(out, "SPEC-BLD-01", severity="erro")
        _, out = self.mutated(item)
        self.assertNoRule(out, "SPEC-BLD-01")
        self.assertEqual(out["status"], "valid")

    def test_file_upload_sem_aviso_de_login(self):
        """Dado file_upload sem aviso de login na descrição, quando valida, então SPEC-CFG-04 aviso heurístico."""
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "file_upload", "title": "Envie o comprovante", "use": "x",
                                              "file_upload": {"types": ["pdf"], "max_files": 1, "max_size": "10MB"}})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-CFG-04", severity="aviso")
        self.assertTrue(out["data"]["findings"][0].get("heuristica"))

    def test_file_upload_valores_nao_confirmados(self):
        """Dado max_files 3, quando valida, então SPEC-CFG-08 aviso."""
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "file_upload", "title": "Envie", "use": "x", "description": "Entre com login Google.",
                                              "file_upload": {"types": ["pdf"], "max_files": 3, "max_size": "10MB"}})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-CFG-08", severity="aviso")


class ValidacaoDeRespostaTests(Base):

    def val(self, itype, validation, options=None, base_item=None):
        def m(s):
            it = {"id": "q8", "type": itype, "title": "Campo de teste", "use": "x", "validation": validation}
            if options:
                it["options"] = options
            s["sections"][2]["items"].append(it)
        return self.mutated(m)[1]

    def test_kind_incompativel_com_tipo(self):
        """Dado paragraph com kind number, quando valida, então SPEC-VAL-01."""
        out = self.val("paragraph", {"kind": "number", "rule": "gt", "value": 1, "error": "e"})
        self.assertRule(out, "SPEC-VAL-01")

    def test_validation_em_tipo_sem_suporte(self):
        """Dado validation em date, quando valida, então SPEC-VAL-01."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"].append(
            {"id": "q8", "type": "date", "title": "Quando", "use": "x", "validation": {"kind": "text", "rule": "email", "error": "e"}}))
        self.assertRule(out, "SPEC-VAL-01")

    def test_checkboxes_aceita_so_selection(self):
        """Dado checkboxes com kind length, quando valida, então SPEC-VAL-01; com selection válido passa."""
        out = self.val("checkboxes", {"kind": "length", "rule": "max_chars", "value": 3, "error": "e"}, [{"value": "a"}, {"value": "b"}])
        self.assertRule(out, "SPEC-VAL-01")
        out = self.val("checkboxes", {"kind": "selection", "rule": "at_most", "value": 2, "error": "Escolha até 2."}, [{"value": "a"}, {"value": "b"}])
        self.assertEqual(out["status"], "valid")

    def test_rule_inexistente_para_kind(self):
        """Dado kind length com rule 'gt', quando valida, então SPEC-VAL-02."""
        out = self.val("short_text", {"kind": "length", "rule": "gt", "value": 1, "error": "e"})
        self.assertRule(out, "SPEC-VAL-02")

    def test_value_com_formato_errado(self):
        """Dado between com um número só, quando valida, então SPEC-VAL-03; com [10, 1] também."""
        out = self.val("short_text", {"kind": "number", "rule": "between", "value": 5, "error": "e"})
        self.assertRule(out, "SPEC-VAL-03")
        out = self.val("short_text", {"kind": "number", "rule": "between", "value": [10, 1], "error": "e"})
        self.assertRule(out, "SPEC-VAL-03")

    def test_number_valido_e_whole_number_sem_value(self):
        """Dado between [1,10] e whole_number sem value, quando valida, então nenhum erro."""
        out = self.val("short_text", {"kind": "number", "rule": "between", "value": [1, 10], "error": "Digite de 1 a 10."})
        self.assertEqual(out["status"], "valid")
        out = self.val("short_text", {"kind": "number", "rule": "whole_number", "value": None, "error": "Digite um inteiro."})
        self.assertEqual(out["status"], "valid")

    def test_email_com_value_e_erro(self):
        """Dado text/email com value preenchido, quando valida, então SPEC-VAL-03."""
        out = self.val("short_text", {"kind": "text", "rule": "email", "value": "x@y", "error": "e"})
        self.assertRule(out, "SPEC-VAL-03")

    def test_length_exige_inteiro(self):
        """Dado max_chars 0 ou texto, quando valida, então SPEC-VAL-03."""
        out = self.val("short_text", {"kind": "length", "rule": "max_chars", "value": 0, "error": "e"})
        self.assertRule(out, "SPEC-VAL-03")
        out = self.val("short_text", {"kind": "length", "rule": "max_chars", "value": "10", "error": "e"})
        self.assertRule(out, "SPEC-VAL-03")

    def test_validation_sem_mensagem_de_erro(self):
        """Dado validation sem error, quando valida, então SPEC-VAL-04."""
        out = self.val("short_text", {"kind": "length", "rule": "max_chars", "value": 10})
        self.assertRule(out, "SPEC-VAL-04")

    def test_regex_que_nao_compila_e_aviso_heuristico(self):
        """Dado regex '([a-z', quando valida, então SPEC-VAL-05 aviso heurístico."""
        out = self.val("short_text", {"kind": "regex", "rule": "matches", "value": "([a-z", "error": "Formato inválido."})
        self.assertRule(out, "SPEC-VAL-05", severity="aviso")
        self.assertEqual(out["status"], "valid_with_warnings")

    def test_selection_maior_que_numero_de_opcoes(self):
        """Dado at_least 5 com 2 opções, quando valida, então SPEC-VAL-03."""
        out = self.val("checkboxes", {"kind": "selection", "rule": "at_least", "value": 5, "error": "e"}, [{"value": "a"}, {"value": "b"}])
        self.assertRule(out, "SPEC-VAL-03")


class NavegacaoTests(Base):

    def test_go_to_para_secao_inexistente(self):
        """Dado go_to 's9', quando valida, então SPEC-NAV-01 no caminho da opção."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][1]["options"][0].update(go_to="s9"))
        self.assertRule(out, "SPEC-NAV-01", "sections[0].items[1].options[0].go_to")

    def test_after_section_para_secao_inexistente(self):
        """Dado after_section 'fim', quando valida, então SPEC-NAV-01."""
        _, out = self.mutated(lambda s: s["sections"][1].update(after_section="fim"))
        self.assertRule(out, "SPEC-NAV-01", "sections[1].after_section")

    def test_go_to_s1_proibido(self):
        """Dado go_to s1, quando valida, então SPEC-NAV-02."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][1]["options"][1].update(go_to="s1"))
        self.assertRule(out, "SPEC-NAV-02")

    def test_after_section_s1_proibido(self):
        """Dado after_section s1, quando valida, então SPEC-NAV-02."""
        _, out = self.mutated(lambda s: s["sections"][2].update(after_section="s1"))
        self.assertRule(out, "SPEC-NAV-02", "sections[2].after_section")

    def test_go_to_em_tipo_nao_ramificavel(self):
        """Dado go_to em checkboxes, quando valida, então SPEC-NAV-03."""
        _, out = self.mutated(lambda s: s["sections"][2]["items"][0]["options"][0].update(go_to="submit"))
        self.assertRule(out, "SPEC-NAV-03")

    def test_go_to_so_em_algumas_opcoes(self):
        """Dado go_to em uma opção e não na outra, quando valida, então SPEC-NAV-04."""
        def m(s):
            del s["sections"][0]["items"][1]["options"][1]["go_to"]
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-NAV-04")

    def test_go_to_com_other(self):
        """Dado item com go_to e other true, quando valida, então SPEC-NAV-05."""
        _, out = self.mutated(lambda s: s["sections"][0]["items"][1].update(other=True))
        self.assertRule(out, "SPEC-NAV-05")

    def test_duas_perguntas_com_go_to_na_mesma_secao(self):
        """Dado duas perguntas com go_to em s1, quando valida, então SPEC-NAV-06."""
        def m(s):
            s["sections"][0]["items"].append({"id": "q9", "type": "dropdown", "title": "E agora?", "use": "x",
                                              "options": [{"value": "A", "go_to": "s3"}, {"value": "B", "go_to": "s3"}]})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-NAV-06")

    def test_secao_com_go_to_e_after_section(self):
        """Dado s1 com go_to e after_section, quando valida, então SPEC-NAV-07."""
        _, out = self.mutated(lambda s: s["sections"][0].update(after_section="s2"))
        self.assertRule(out, "SPEC-NAV-07", "sections[0].after_section")

    def test_secao_inalcancavel(self):
        """Dado s2 que ninguém aponta, quando valida, então SPEC-NAV-08 em s2."""
        code, out, _ = self.run_cli([fixture_path("spec_unreachable.json")])
        self.assertEqual((code, out["status"]), (1, "invalid"))
        self.assertRule(out, "SPEC-NAV-08", "sections[1]")

    def test_ciclo_na_navegacao(self):
        """Dado s2 -> s3 -> s2, quando valida, então SPEC-NAV-09 citando o laço."""
        code, out, _ = self.run_cli([fixture_path("spec_cycle.json")])
        self.assertEqual((code, out["status"]), (1, "invalid"))
        self.assertRule(out, "SPEC-NAV-09", severity="erro")
        msg = [f["mensagem"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-NAV-09"][0]
        self.assertIn("s2", msg)
        self.assertIn("s3", msg)

    def test_auto_laco_e_ciclo(self):
        """Dado after_section apontando para a própria seção, quando valida, então SPEC-NAV-09."""
        _, out = self.mutated(lambda s: s["sections"][1].update(after_section="s2"))
        self.assertRule(out, "SPEC-NAV-09")

    def test_navegacao_para_tras_sem_ciclo_e_aviso(self):
        """Dado go_to de s3 de volta a s2 mas s2 só vai ao envio, quando valida, então SPEC-NAV-10 aviso (sem ciclo)."""
        def m(s):
            s["sections"][1]["after_section"] = "submit"
            s["sections"][2]["after_section"] = "s2"
            s["sections"][0]["items"][1]["options"][0]["go_to"] = "s3"
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-NAV-10", severity="aviso")
        self.assertNoRule(out, "SPEC-NAV-09")

    def test_pergunta_opcional_com_go_to_tambem_segue_para_proxima(self):
        """Dado pergunta de ramificação opcional, quando valida o grafo, então há aresta implícita para a próxima seção."""
        def m(s):
            s["sections"][0]["items"][1]["required"] = False
            s["sections"][0]["items"][1]["options"] = [{"value": "Sim", "go_to": "s3"}, {"value": "Não", "go_to": "s3"}]
        _, out = self.mutated(m)
        self.assertNoRule(out, "SPEC-NAV-08")
        self.assertIn("s2", out["data"]["section_graph"]["s1"])

    def test_grafo_do_spec_valido(self):
        """Dado o spec válido, quando valida, então data.section_graph descreve s1->s2,s3; s2->s3; s3->submit."""
        _, out, _ = self.run_cli([fixture_path("spec_valid.json")])
        self.assertEqual(out["data"]["section_graph"], {"s1": ["s2", "s3"], "s2": ["s3"], "s3": ["submit"]})


class QuizTests(Base):

    def quiz(self, fn, enabled=True):
        def m(s):
            s["quiz"] = {"enabled": enabled, "release": "immediately"}
            fn(s)
        return self.mutated(m)[1]

    def test_campos_de_quiz_sem_quiz_ligado(self):
        """Dado points com quiz.enabled false, quando valida, então SPEC-QUIZ-01."""
        out = self.quiz(lambda s: s["sections"][2]["items"][0].update(points=2), enabled=False)
        self.assertRule(out, "SPEC-QUIZ-01")

    def test_pontuacao_em_tipo_nao_pontuavel(self):
        """Dado points em linear_scale com quiz ligado, quando valida, então SPEC-QUIZ-02."""
        out = self.quiz(lambda s: s["sections"][0]["items"][0].update(points=1, answer_key=["3"]))
        self.assertRule(out, "SPEC-QUIZ-02")

    def test_gabarito_com_valor_inexistente(self):
        """Dado answer_key 'Talvez' fora de options, quando valida, então SPEC-QUIZ-03."""
        out = self.quiz(lambda s: s["sections"][2]["items"][0].update(points=1, answer_key=["Talvez"]))
        self.assertRule(out, "SPEC-QUIZ-03", "sections[2].items[0].answer_key[0]")

    def test_multipla_escolha_com_duas_corretas(self):
        """Dado multiple_choice com 2 corretas, quando valida, então SPEC-QUIZ-03."""
        out = self.quiz(lambda s: s["sections"][0]["items"][1].update(points=1, answer_key=["Sim", "Não"]))
        self.assertRule(out, "SPEC-QUIZ-03")

    def test_quiz_valido_com_feedback(self):
        """Dado checkboxes com 2 corretas, pontos e feedback, quando valida, então sem erro."""
        out = self.quiz(lambda s: s["sections"][2]["items"][0].update(
            points=2, answer_key=["Presencial", "Online"], feedback={"right": "Certo!", "wrong": "Releia."}))
        self.assertEqual(out["status"], "valid", out["problems"])

    def test_feedback_right_sem_gabarito(self):
        """Dado feedback.right em short_text, quando valida, então SPEC-QUIZ-02."""
        out = self.quiz(lambda s: s["sections"][1]["items"][0].update(feedback={"right": "ok"}))
        self.assertRule(out, "SPEC-QUIZ-02")

    def test_points_invalido(self):
        """Dado points -1, quando valida, então SPEC-QUIZ-04."""
        out = self.quiz(lambda s: s["sections"][2]["items"][0].update(points=-1, answer_key=["Online"]))
        self.assertRule(out, "SPEC-QUIZ-04")

    def test_points_sem_gabarito_e_aviso(self):
        """Dado points sem answer_key, quando valida, então SPEC-QUIZ-05 aviso."""
        out = self.quiz(lambda s: s["sections"][2]["items"][0].update(points=1))
        self.assertRule(out, "SPEC-QUIZ-05", severity="aviso")

    def test_liberacao_manual_exige_coleta_de_email(self):
        """Dado after_manual_review com collect_email none, quando valida, então SPEC-QUIZ-06."""
        def m(s):
            s["quiz"] = {"enabled": True, "release": "after_manual_review"}
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-QUIZ-06")

    def test_gabarito_com_go_to_no_apps_script_e_pendente_ui(self):
        """Dado answer_key em item com go_to e build apps_script, quando valida, então SPEC-BLD-06 aviso."""
        def m(s):
            s["build"]["path"] = "apps_script"
            s["theme"]["color"] = None
            s["quiz"] = {"enabled": True, "release": "immediately"}
            s["sections"][0]["items"][1].update(points=1, answer_key=["Sim"])
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-BLD-06", severity="aviso")
        self.assertEqual(out["status"], "valid_with_warnings")


class ConfiguracaoTests(Base):

    def test_enum_invalido(self):
        """Dado collect_email 'sempre', quando valida, então SPEC-CFG-01."""
        _, out = self.mutated(lambda s: s["settings"].update(collect_email="sempre"))
        self.assertRule(out, "SPEC-CFG-01", "settings.collect_email")

    def test_build_path_invalido(self):
        """Dado build.path 'playwright', quando valida, então SPEC-CFG-01."""
        _, out = self.mutated(lambda s: s["build"].update(path="playwright"))
        self.assertRule(out, "SPEC-CFG-01", "build.path")

    def test_send_copy_exige_coleta_de_email(self):
        """Dado send_copy always e collect_email none, quando valida, então SPEC-CFG-02."""
        _, out = self.mutated(lambda s: s["settings"].update(send_copy="always"))
        self.assertRule(out, "SPEC-CFG-02")

    def test_audiencia_domain_so_em_workspace(self):
        """Dado audience domain em conta pessoal, quando valida, então SPEC-CFG-03; em workspace passa."""
        _, out = self.mutated(lambda s: s["publish"].update(audience="domain"))
        self.assertRule(out, "SPEC-CFG-03")
        def ws(s):
            s["publish"]["audience"] = "domain"
            s["brief"]["account_type"] = "workspace"
        _, out = self.mutated(ws)
        self.assertNoRule(out, "SPEC-CFG-03")

    def test_audiencia_specific_sem_responders(self):
        """Dado audience specific sem responders, quando valida, então SPEC-CFG-03."""
        _, out = self.mutated(lambda s: s["publish"].update(audience="specific"))
        self.assertRule(out, "SPEC-CFG-03", "publish.responders")

    def test_limit_one_response_sem_aviso_de_login(self):
        """Dado limit_one_response sem aviso, quando valida, então SPEC-CFG-04 aviso; com aviso na descrição não."""
        _, out = self.mutated(lambda s: s["settings"].update(limit_one_response=True))
        self.assertRule(out, "SPEC-CFG-04", severity="aviso")
        def ok(s):
            s["settings"]["limit_one_response"] = True
            s["meta"]["description"] += " É preciso entrar com sua conta Google."
        _, out = self.mutated(ok)
        self.assertNoRule(out, "SPEC-CFG-04")

    def test_encerramento_com_dois_criterios(self):
        """Dado close.at e response_limit juntos, quando valida, então SPEC-CFG-05."""
        _, out = self.mutated(lambda s: s["settings"]["close"].update(at="2026-12-01T18:00:00-03:00", response_limit=10))
        self.assertRule(out, "SPEC-CFG-05", "settings.close")

    def test_encerramento_data_invalida_e_limite_invalido(self):
        """Dado at 'amanhã' e limit 0, quando valida, então SPEC-CFG-05 em cada campo."""
        _, out = self.mutated(lambda s: s["settings"]["close"].update(at="amanhã"))
        self.assertRule(out, "SPEC-CFG-05", "settings.close.at")
        _, out = self.mutated(lambda s: s["settings"]["close"].update(response_limit=0))
        self.assertRule(out, "SPEC-CFG-05", "settings.close.response_limit")

    def test_encerramento_valido_por_data(self):
        """Dado close.at ISO com fuso, quando valida, então sem SPEC-CFG-05."""
        def m(s):
            s["settings"]["close"]["at"] = "2026-12-01T18:00:00-03:00"
        _, out = self.mutated(m)
        self.assertNoRule(out, "SPEC-CFG-05")

    def test_cor_do_tema_com_baixo_contraste_e_aviso(self):
        """Dado cor amarela, quando valida, então SPEC-CFG-06 aviso; o índigo #3f51b5 passa."""
        _, out = self.mutated(lambda s: s["theme"].update(color="#ffeb3b"))
        self.assertRule(out, "SPEC-CFG-06", "theme.color", "aviso")
        self.assertAlmostEqual(vs.contrast_with_white("#3f51b5"), 6.87, places=1)

    def test_cor_invalida(self):
        """Dado cor 'azul', quando valida, então SPEC-CFG-06."""
        _, out = self.mutated(lambda s: s["theme"].update(color="azul"))
        self.assertRule(out, "SPEC-CFG-06")

    def test_formulario_nao_publicado_e_aviso(self):
        """Dado published false, quando valida, então SPEC-CFG-06 aviso."""
        _, out = self.mutated(lambda s: s["publish"].update(published=False))
        self.assertRule(out, "SPEC-CFG-06", "publish.published", "aviso")

    def test_planilha_existente_sem_referencia(self):
        """Dado responses.sheet existing sem sheet_ref, quando valida, então SPEC-CFG-01."""
        _, out = self.mutated(lambda s: s["responses"].update(sheet="existing"))
        self.assertRule(out, "SPEC-CFG-01", "responses.sheet_ref")


class CaminhoDeConstrucaoTests(Base):

    def test_recursos_so_ui_no_apps_script_viram_pendente_ui(self):
        """Dado tema, cópia ao respondente e limite de respostas no apps_script, quando valida, então SPEC-BLD-03 avisos e exit 0."""
        def m(s):
            s["build"]["path"] = "apps_script"
            s["settings"]["collect_email"] = "responder_input"
            s["settings"]["send_copy"] = "always"
            s["settings"]["close"]["response_limit"] = 50
            s["privacy"] = {"personal_data": "personal", "inventory": [{"item": "collect_email", "data": "e-mail", "purpose": "Enviar a cópia"}],
                            "legal_basis": [{"purpose": "Enviar a cópia", "basis": "Consentimento (art. 7º I)"}],
                            "controller": "Org", "contact": "p@example.org", "retention": "30 dias", "sharing": "ninguém", "decided_by": "owner"}
            s["meta"]["description"] += " Seus dados servem só para enviar a cópia (privacidade: p@example.org)."
        code, out = self.mutated(m)
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-BLD-03"]
        self.assertEqual(sorted(paths), ["settings.close", "settings.send_copy", "theme.color"])
        self.assertEqual((code, out["status"]), (0, "valid_with_warnings"), out["problems"])
        self.assertEqual(out["data"]["counts"]["pending_ui"], 3)

    def test_video_caption_e_shuffle_rows_no_apps_script(self):
        """Dado legenda de vídeo e shuffle_rows no apps_script, quando valida, então SPEC-BLD-05 e SPEC-BLD-07 avisos."""
        def m(s):
            s["build"]["path"] = "apps_script"
            s["theme"]["color"] = None
            s["sections"][2]["items"] += [
                {"id": "q8", "type": "video", "video": {"youtube_url": "https://www.youtube.com/watch?v=abc", "caption": "Veja"}},
                {"id": "q9", "type": "mc_grid", "title": "Avalie", "use": "x", "grid": {"rows": ["A", "B"], "columns": ["Bom", "Ruim"], "shuffle_rows": True}}]
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-BLD-05", severity="aviso")
        self.assertRule(out, "SPEC-BLD-07", severity="aviso")
        self.assertEqual(out["status"], "valid_with_warnings")

    def test_api_sem_suporte_e_erro(self):
        """Dado spec com validação, mensagem de confirmação e tema em build.path api, quando valida, então SPEC-BLD-02 erros."""
        _, out = self.mutated(lambda s: s["build"].update(path="api"))
        self.assertEqual(out["status"], "invalid")
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-BLD-02"]
        self.assertIn("theme.color", paths)
        self.assertIn("settings.confirmation_message", paths)
        self.assertIn("sections[1].items[0].validation", paths)

    def test_ui_aceita_tudo(self):
        """Dado build.path ui com tema, validação e navegação, quando valida, então nada de BLD."""
        _, out = self.mutated(lambda s: s["settings"]["close"].update(response_limit=10))
        self.assertFalse([r for r in self.rules(out) if r.startswith("SPEC-BLD")])

    def test_rating_no_apps_script_e_nao_verificado(self):
        """Dado rating no apps_script, quando valida, então SPEC-BLD-08 aviso."""
        def m(s):
            s["build"]["path"] = "apps_script"
            s["theme"]["color"] = None
            s["sections"][2]["items"].append({"id": "q8", "type": "rating", "title": "Nota geral", "use": "x", "rating": {"levels": 5, "icon": "star"}})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-BLD-08", severity="aviso")


class DadosPessoaisTests(Base):

    PRIV = {"personal_data": "personal",
            "inventory": [{"item": "q5", "data": "nome", "purpose": "Identificar na lista"}],
            "legal_basis": [{"purpose": "Identificar na lista", "basis": "Consentimento (art. 7º I) — decidido pelo dono"}],
            "controller": "Org Exemplo", "contact": "privacidade@example.org", "retention": "90 dias", "sharing": "ninguém",
            "decided_by": "owner"}

    def personal(self, fn=None):
        def m(s):
            s["privacy"] = copy.deepcopy(self.PRIV)
            s["meta"]["description"] += " Usamos seu nome só para a lista; dúvidas sobre seus dados: privacidade@example.org."
            s["sections"][0]["items"].insert(0, {"id": "q1", "type": "short_text", "title": "Como podemos te chamar?", "use": "Identificar", "personal": True})
            # renumera para manter a ordem crescente dos ids
            s["sections"][0]["items"][1]["id"] = "q2"
            s["sections"][0]["items"][2]["id"] = "q3"
            s["sections"][1]["items"][0]["id"] = "q4"
            s["sections"][2]["items"][0]["id"] = "q6"
            s["privacy"]["inventory"][0]["item"] = "q1"
            if fn:
                fn(s)
        return self.mutated(m)

    def test_caso_pessoal_correto_passa(self):
        """Dado dado pessoal inventariado, com base legal do dono e aviso, quando valida, então valid."""
        code, out = self.personal()
        self.assertEqual((code, out["status"]), (0, "valid"), out["problems"])

    def test_personal_true_fora_do_inventario(self):
        """Dado personal:true sem entrada no inventário, quando valida, então SPEC-PRIV-01."""
        _, out = self.personal(lambda s: s["privacy"].update(inventory=[{"item": "collect_email", "data": "x", "purpose": "y"}]))
        self.assertRule(out, "SPEC-PRIV-01", "sections[0].items[0].personal")

    def test_collect_email_sem_inventario(self):
        """Dado collect_email verified sem item collect_email no inventário, quando valida, então SPEC-PRIV-01."""
        _, out = self.personal(lambda s: s["settings"].update(collect_email="responder_input"))
        self.assertRule(out, "SPEC-PRIV-01", "settings.collect_email")

    def test_inventario_orfao(self):
        """Dado inventário citando q99 inexistente, quando valida, então SPEC-PRIV-01."""
        _, out = self.personal(lambda s: s["privacy"]["inventory"].append({"item": "q99", "data": "x", "purpose": "y"}))
        self.assertRule(out, "SPEC-PRIV-01", "privacy.inventory[1].item")

    def test_inventario_collect_email_com_coleta_none(self):
        """Dado inventário com collect_email e settings none, quando valida, então SPEC-PRIV-01."""
        _, out = self.personal(lambda s: s["privacy"]["inventory"].append({"item": "collect_email", "data": "e", "purpose": "y"}))
        self.assertRule(out, "SPEC-PRIV-01", "privacy.inventory[1].item")

    def test_inventario_sem_finalidade(self):
        """Dado entrada sem purpose, quando valida, então SPEC-PRIV-03."""
        _, out = self.personal(lambda s: s["privacy"]["inventory"][0].update(purpose=""))
        self.assertRule(out, "SPEC-PRIV-03", "privacy.inventory[0].purpose")

    def test_personal_data_none_com_item_pessoal(self):
        """Dado personal_data none e item personal, quando valida, então SPEC-PRIV-02."""
        _, out = self.personal(lambda s: s["privacy"].update(personal_data="none"))
        self.assertRule(out, "SPEC-PRIV-02")

    def test_personal_data_sem_nenhum_dado(self):
        """Dado personal_data personal sem item nem e-mail, quando valida, então SPEC-PRIV-02."""
        _, out = self.mutated(lambda s: s["privacy"].update(personal_data="personal"))
        self.assertRule(out, "SPEC-PRIV-02")

    def test_campos_de_privacidade_vazios(self):
        """Dado controller vazio e legal_basis vazio, quando valida, então SPEC-PRIV-03 (vazio é erro; pending_owner é outra coisa)."""
        _, out = self.personal(lambda s: s["privacy"].update(controller="", legal_basis=[]))
        paths = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-PRIV-03"]
        self.assertIn("privacy.controller", paths)
        self.assertIn("privacy.legal_basis", paths)

    def test_decided_by_deve_ser_owner(self):
        """Dado decided_by agent, quando valida, então SPEC-PRIV-03."""
        _, out = self.personal(lambda s: s["privacy"].update(decided_by="agent"))
        self.assertRule(out, "SPEC-PRIV-03", "privacy.decided_by")

    def test_descricao_sem_aviso_de_privacidade_e_aviso_heuristico(self):
        """Dado dado pessoal e descrição sem aviso, quando valida, então SPEC-PRIV-04 aviso heurístico."""
        _, out = self.personal(lambda s: s["meta"].update(description="Leva 2 minutos."))
        self.assertRule(out, "SPEC-PRIV-04", severity="aviso")

    def test_email_pedido_duas_vezes_com_validacao_e_erro(self):
        """Dado collect_email e pergunta com validação email, quando valida, então SPEC-PRIV-06 erro."""
        def m(s):
            s["settings"]["collect_email"] = "responder_input"
            s["privacy"]["inventory"].append({"item": "collect_email", "data": "e-mail", "purpose": "Contato"})
            s["sections"][2]["items"].append({"id": "q8", "type": "short_text", "title": "Seu contato", "use": "x", "personal": True,
                                              "validation": {"kind": "text", "rule": "email", "error": "Digite um e-mail válido."}})
            s["privacy"]["inventory"].append({"item": "q8", "data": "e-mail", "purpose": "Contato"})
        _, out = self.personal(m)
        self.assertRule(out, "SPEC-PRIV-06", severity="erro")

    def test_email_no_titulo_com_coleta_e_aviso_heuristico(self):
        """Dado título 'Qual seu e-mail?' com collect_email ligado, quando valida, então SPEC-PRIV-06 aviso."""
        def m(s):
            s["settings"]["collect_email"] = "responder_input"
            s["privacy"]["inventory"].append({"item": "collect_email", "data": "e-mail", "purpose": "Contato"})
            s["sections"][2]["items"].append({"id": "q8", "type": "short_text", "title": "Qual é o seu e-mail?", "use": "x", "personal": True})
            s["privacy"]["inventory"].append({"item": "q8", "data": "e-mail", "purpose": "Contato"})
        _, out = self.personal(m)
        self.assertRule(out, "SPEC-PRIV-06", severity="aviso")

    def test_dado_sensivel_pedido_e_aviso(self):
        """Dado pergunta de CPF, quando valida, então SPEC-PRIV-05 aviso heurístico."""
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "short_text", "title": "Qual é o seu CPF?", "use": "x", "personal": True})
            s["privacy"]["inventory"].append({"item": "q8", "data": "CPF", "purpose": "Identificar"})
        _, out = self.personal(m)
        self.assertRule(out, "SPEC-PRIV-05", severity="aviso")

    def test_item_que_parece_pessoal_com_personal_false(self):
        """Dado 'Telefone' sem personal true, quando valida, então SPEC-PRIV-07 aviso."""
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "short_text", "title": "Qual é o seu telefone?", "use": "x"})
        _, out = self.mutated(m)
        self.assertRule(out, "SPEC-PRIV-07", severity="aviso")

    def test_dado_sensivel_sem_prefiro_nao_responder(self):
        """Dado personal_data sensitive sem opção 'Prefiro não responder', quando valida, então SPEC-PRIV-08."""
        _, out = self.personal(lambda s: s["privacy"].update(personal_data="sensitive"))
        self.assertRule(out, "SPEC-PRIV-08", severity="aviso")


class SegurancaTests(Base):

    def titled(self, title):
        def m(s):
            s["sections"][2]["items"].append({"id": "q8", "type": "short_text", "title": title, "use": "x"})
        return self.mutated(m)[1]

    def test_titulos_que_pedem_credenciais_reprovam(self):
        """Dado títulos pedindo senha, token, código de verificação e cartão, quando valida, então SPEC-SEC-01 erro heurístico em cada."""
        for title in ("Qual é a sua senha?", "Informe o token de acesso", "Digite o código de verificação enviado por SMS",
                      "Número do cartão de crédito", "CVV", "Password", "Cole sua API key"):
            out = self.titled(title)
            self.assertRule(out, "SPEC-SEC-01", severity="erro")
            self.assertEqual(out["status"], "invalid", title)
            f = [x for x in out["data"]["findings"] if x["id_regra"] == "SPEC-SEC-01"][0]
            self.assertTrue(f["heuristica"])
            self.assertTrue(f["mensagem"].startswith("Heurística"))

    def test_titulos_comuns_nao_sao_falso_positivo(self):
        """Dado títulos com 'código do pedido', 'senhor' e 'cidade', quando valida, então sem SPEC-SEC-01."""
        for title in ("Qual é o código do pedido?", "Como você avalia o atendimento do senhor João?", "Qual a sua cidade?"):
            self.assertNoRule(self.titled(title), "SPEC-SEC-01")

    def test_sem_acento_tambem_e_pego(self):
        """Dado 'SENHA do wifi' em maiúsculas sem acento, quando valida, então SPEC-SEC-01."""
        self.assertRule(self.titled("SENHA do banco"), "SPEC-SEC-01")


class AprovacaoTests(Base):

    def test_draft_correto_e_valid_sem_for_build(self):
        """Dado spec draft correto, quando valida sem --for-build, então valid exit 0."""
        code, out, _ = self.run_cli([fixture_path("spec_draft.json")])
        self.assertEqual((code, out["status"]), (0, "valid"))

    def test_draft_com_for_build_reprova(self):
        """Dado spec draft e --for-build, quando valida, então invalid, SPEC-APR-04 e orientação de apresentar ao dono."""
        code, out, _ = self.run_cli([fixture_path("spec_draft.json"), "--for-build"])
        self.assertEqual((code, out["status"], out["ok"]), (1, "invalid", False))
        self.assertRule(out, "SPEC-APR-04", "status", "erro")
        self.assertIn("aprova", " ".join(out["next_steps"]).lower())
        self.assertTrue(out["data"]["for_build"])

    def test_approved_com_for_build_passa(self):
        """Dado spec approved correto e --for-build, quando valida, então valid exit 0 com passo 'pode construir'."""
        code, out, _ = self.run_cli([fixture_path("spec_valid.json"), "--for-build"])
        self.assertEqual((code, out["status"]), (0, "valid"))
        self.assertIn("construir", " ".join(out["next_steps"]).lower())

    def test_approved_com_warnings_for_build_ok(self):
        """Dado approved com apenas avisos, quando valida com --for-build, então valid_with_warnings e exit 0."""
        _, out = self.mutated(lambda s: s["publish"].update(published=False), "spec_valid.json", "--for-build")
        self.assertEqual(out["status"], "valid_with_warnings")

    def test_approved_sem_data(self):
        """Dado approved sem approved_at, quando valida, então SPEC-APR-02."""
        _, out = self.mutated(lambda s: s.update(approved_at=None))
        self.assertRule(out, "SPEC-APR-02")

    def test_approved_com_data_invalida(self):
        """Dado approved_at 'ontem', quando valida, então SPEC-APR-02."""
        _, out = self.mutated(lambda s: s.update(approved_at="ontem"))
        self.assertRule(out, "SPEC-APR-02")

    def test_status_invalido(self):
        """Dado status 'aprovado', quando valida, então SPEC-APR-01."""
        _, out = self.mutated(lambda s: s.update(status="aprovado"))
        self.assertRule(out, "SPEC-APR-01")

    def test_draft_com_data_de_aprovacao_e_aviso(self):
        """Dado draft com approved_at, quando valida, então SPEC-APR-05 aviso."""
        _, out = self.mutated(lambda s: s.update(status="draft"))
        self.assertRule(out, "SPEC-APR-05", severity="aviso")

    def test_pending_owner_bloqueia_com_status_proprio(self):
        """Dado draft com pending_owner na privacidade, quando valida, então status pending_owner, exit 1, caminhos listados."""
        code, out, _ = self.run_cli([fixture_path("spec_pending_owner.json")])
        self.assertEqual((code, out["status"], out["ok"]), (1, "pending_owner", False))
        self.assertIn("privacy.controller", out["data"]["pending_owner"])
        self.assertEqual(out["data"]["counts"]["pending_owner"], 5)
        self.assertEqual(out["data"]["counts"]["errors"], 0)
        self.assertTrue(out["problems"])
        self.assertIn("dono", " ".join(out["next_steps"]))

    def test_pending_owner_com_for_build_continua_pending_owner(self):
        """Dado draft com pending_owner e --for-build, quando valida, então o status segue pending_owner (a pendência é o bloqueio mais informativo)."""
        code, out, _ = self.run_cli([fixture_path("spec_pending_owner.json"), "--for-build"])
        self.assertEqual((code, out["status"]), (1, "pending_owner"))
        self.assertRule(out, "SPEC-APR-04")

    def test_approved_com_pending_owner_e_erro(self):
        """Dado status approved com pending_owner, quando valida, então SPEC-APR-03 e invalid."""
        spec = load("spec_pending_owner.json")
        spec["status"] = "approved"
        spec["approved_at"] = "2026-11-11"
        code, out = self.check(spec)
        self.assertEqual((code, out["status"]), (1, "invalid"))
        self.assertRule(out, "SPEC-APR-03")

    def test_pending_owner_em_enum_e_aceito(self):
        """Dado collect_email 'pending_owner', quando valida, então sem SPEC-CFG-01 (valor válido em campos do dono)."""
        _, out = self.mutated(lambda s: s["settings"].update(collect_email="pending_owner", ) or s.update(status="draft", approved_at=None))
        self.assertNoRule(out, "SPEC-CFG-01")
        self.assertEqual(out["status"], "pending_owner")

    def test_erro_vence_pending_owner(self):
        """Dado pending_owner e um erro estrutural, quando valida, então invalid (corrigir erros primeiro) e a pendência continua listada."""
        spec = load("spec_pending_owner.json")
        spec["sections"][0]["items"][0]["title"] = ""
        code, out = self.check(spec)
        self.assertEqual(out["status"], "invalid")
        self.assertTrue(out["data"]["pending_owner"])


class VersaoETests(Base):

    def test_spec_version_diferente_de_1_e_aviso(self):
        """Dado spec_version 2, quando valida, então SPEC-STR-02 aviso (contrato desconhecido)."""
        _, out = self.mutated(lambda s: s.update(spec_version=2))
        self.assertRule(out, "SPEC-STR-02", "spec_version", "aviso")

    def test_version_invalida_e_aviso(self):
        """Dado version 0, quando valida, então SPEC-STR-04 aviso."""
        _, out = self.mutated(lambda s: s.update(version=0))
        self.assertRule(out, "SPEC-STR-04", "version", "aviso")

    def test_cada_pending_owner_gera_um_achado_own01(self):
        """Dado 5 campos pending_owner, quando valida, então 5 achados SPEC-OWN-01 com o caminho de cada campo."""
        _, out, _ = self.run_cli([fixture_path("spec_pending_owner.json")])
        own = [f["caminho"] for f in out["data"]["findings"] if f["id_regra"] == "SPEC-OWN-01"]
        self.assertEqual(len(own), 5)
        self.assertIn("privacy.legal_basis[0].basis", own)


if __name__ == "__main__":
    unittest.main()

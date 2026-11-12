# -*- coding: utf-8 -*-
"""Testes do build_delivery_doc.py (conversor, montagem, validação, PDF).

Fixtures em fixtures/delivery_ok (delivery.json + capturas sintéticas) e um template/CSS mínimos
(delivery_min_*). O teste de integração usa o template REAL e Chrome de verdade (skip sem Chromium).
"""

import copy
import json
import os
import re
import shutil
import tempfile
import unittest

from helpers import FIXTURES, run_main
import build_delivery_doc as bd

OK_DIR = os.path.join(FIXTURES, "delivery_ok")
MIN_TPL = os.path.join(FIXTURES, "delivery_min_template.html")
MIN_CSS = os.path.join(FIXTURES, "delivery_min_styles.css")
STAMP = "01/01/2026 00:00"


def load_ok():
    with open(os.path.join(OK_DIR, "delivery.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


class Workdir(object):
    """Cópia temporária de delivery_ok, com mutação opcional do JSON."""

    def __init__(self, mutate=None):
        self.tmp = tempfile.mkdtemp(prefix="gforms-test-")
        self.dir = os.path.join(self.tmp, "w")
        shutil.copytree(OK_DIR, self.dir)
        self.path = os.path.join(self.dir, "delivery.json")
        if mutate:
            d = load_ok()
            mutate(d)
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False)

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def build(mutate=None, extra=None, template=MIN_TPL, css=MIN_CSS, work=None):
    w = work or Workdir(mutate)
    out_html = os.path.join(w.tmp, "out.html")
    argv = [w.path, "--html-only", "--html", out_html, "--generated-at", STAMP]
    if template:
        argv += ["--template", template]
    if css:
        argv += ["--css", css]
    argv += extra or []
    code, payload, _ = run_main(bd.main, argv, None)
    html_text = None
    if os.path.isfile(out_html):
        with open(out_html, "r", encoding="utf-8") as fh:
            html_text = fh.read()
    w.cleanup_later = w
    return code, payload, html_text, w


def conv(md, captures=None, section="visao-geral"):
    issues = bd.Issues()
    caps = {}
    for rel in captures or []:
        caps[rel] = {"file": rel, "masked": True, "form_version": "1.2"}
    ctx = bd.Ctx(OK_DIR, {"version": "1.2"}, caps, issues)
    c = bd.Converter(ctx, section, "Visão geral")
    return c.convert(md), ctx, issues


class MarkdownInlineTests(unittest.TestCase):

    def test_html_cru_do_usuario_e_escapado(self):
        """Dado texto com <script> e & cru, quando converte, então nada vira tag."""
        h, _, _ = conv('Olá <script>alert(1)</script> & <b>x</b>')
        self.assertNotIn("<script>", h)
        self.assertNotIn("<b>", h)
        self.assertIn("&lt;script&gt;", h)
        self.assertIn("&amp;", h)

    def test_negrito_italico_e_codigo(self):
        """Dado **a**, *b* e `c <d>`, quando converte, então strong, em e code com conteúdo escapado."""
        h, _, _ = conv("**a** e *b* e `c <d>`")
        self.assertIn("<strong>a</strong>", h)
        self.assertIn("<em>b</em>", h)
        self.assertIn("<code>c &lt;d&gt;</code>", h)

    def test_asterisco_dentro_de_codigo_nao_vira_enfase(self):
        """Dado `*x*` em código, quando converte, então o asterisco permanece literal."""
        h, _, _ = conv("veja `*x*` aqui")
        self.assertIn("<code>*x*</code>", h)
        self.assertNotIn("<em>", h)

    def test_tecla_kbd(self):
        """Dado [[Ctrl]], quando converte, então vira <kbd class="kbd">."""
        h, _, _ = conv("Use [[Ctrl]] + [[P]]")
        self.assertIn('<kbd class="kbd">Ctrl</kbd>', h)
        self.assertIn('<kbd class="kbd">P</kbd>', h)

    def test_link_interno(self):
        """Dado link para #ancora, quando converte, então vira <a class="xref" href="#ancora">."""
        h, _, iss = conv("[ver](#visao-geral)")
        self.assertIn('<a class="xref" href="#visao-geral">ver</a>', h)
        self.assertEqual(iss.errors, [])

    def test_link_externo_https_tem_marca_visual_e_rel(self):
        """Dado link https, quando converte, então external, noopener e a seta ↗."""
        h, _, iss = conv("[site](https://example.com/a?b=1&c=2)")
        self.assertIn('class="external"', h)
        self.assertIn('rel="noopener noreferrer"', h)
        self.assertIn("&amp;c=2", h)
        self.assertIn("↗", h)
        self.assertEqual(iss.errors, [])

    def test_links_nao_permitidos_viram_erro_e_texto(self):
        """Dado http, javascript:, mailto e relativo, quando converte, então erro e sem <a>."""
        for url in ("http://x.com", "javascript:void", "mailto:a@b.com", "pasta/arq.pdf"):
            h, _, iss = conv("[t](%s)" % url)
            self.assertNotIn("<a ", h, url)
            self.assertTrue(iss.errors, url)

    def test_javascript_com_parenteses_nunca_vira_link(self):
        """Dado [t](javascript:alert(1)), quando converte, então não existe <a> (texto escapado)."""
        h, _, _ = conv("[t](javascript:alert(1))")
        self.assertNotIn("<a ", h)

    def test_citacao_de_item_ganha_id_de_backlink(self):
        """Dado link para #item-q1, quando converte, então o <a> recebe id cit-N e é registrado."""
        h, ctx, _ = conv("[P1](#item-q1)")
        self.assertIn('id="cit-1"', h)
        self.assertEqual(ctx.cites[0]["target"], "item-q1")


class MarkdownBlockTests(unittest.TestCase):

    def test_titulos_viram_h3_h4_com_id_e_entram_no_sumario(self):
        """Dado ## e ###, quando converte, então h3/h4 com id e entradas de sumário nível 2 e 3."""
        h, ctx, _ = conv("## Um título\n\n### Sub título {#meu-id}\n\ntexto")
        self.assertIn('<h3 id="visao-geral-um-titulo">Um título</h3>', h)
        self.assertIn('<h4 id="meu-id">Sub título</h4>', h)
        self.assertEqual([(l, t) for _, l, t, _ in ctx.toc], [(2, "Um título"), (3, "Sub título")])

    def test_titulo_repetido_ganha_sufixo_unico(self):
        """Dado dois ## iguais, quando converte, então os ids automáticos não colidem."""
        h, _, _ = conv("## Igual\n\n## Igual")
        self.assertIn('id="visao-geral-igual"', h)
        self.assertIn('id="visao-geral-igual-2"', h)

    def test_titulo_nivel_1_e_erro(self):
        """Dado # Título, quando converte, então registra erro (nível reservado)."""
        _, _, iss = conv("# Grande")
        self.assertTrue(any("nível 1" in e for e in iss.errors))

    def test_paragrafos_juntam_linhas(self):
        """Dado linhas consecutivas e uma em branco, quando converte, então dois parágrafos."""
        h, _, _ = conv("a\nb\n\nc")
        self.assertEqual(h.count("<p>"), 2)
        self.assertIn("<p>a b</p>", h)

    def test_lista_nao_ordenada_com_um_nivel_aninhado(self):
        """Dado lista com subitem indentado, quando converte, então <ul> dentro do <li>."""
        h, _, _ = conv("- a\n  - a1\n- b")
        self.assertEqual(h, "<ul><li>a<ul><li>a1</li></ul></li><li>b</li></ul>")

    def test_lista_ordenada_respeita_inicio(self):
        """Dado lista que começa em 3., quando converte, então <ol start="3">."""
        h, _, _ = conv("3. c\n4. d")
        self.assertIn('<ol start="3">', h)

    def test_tabela_com_alinhamento(self):
        """Dado tabela pipe com :--: e ---:, quando converte, então table.data com thead e alinhamento."""
        h, _, _ = conv("| A | B | C |\n|---|:--:|--:|\n| 1 | **2** | 3 |")
        self.assertIn('<table class="data"><thead>', h)
        self.assertIn('<th scope="col" style="text-align:center">B</th>', h)
        self.assertIn('<td style="text-align:right">3</td>', h)
        self.assertIn("<strong>2</strong>", h)

    def test_imagem_vira_figure_numerada_por_ordem(self):
        """Dado duas imagens, quando converte, então figure.screenshot com id fig-<arquivo> e número por ordem."""
        h, ctx, iss = conv("![Figura: Primeira](capturas/01-respondente-desktop.png)\n\n"
                           "![Segunda](capturas/02-respondente-celular.png)",
                           captures=["capturas/01-respondente-desktop.png", "capturas/02-respondente-celular.png"])
        self.assertEqual(iss.errors, [])
        self.assertIn('<figure class="screenshot" id="fig-01-respondente-desktop">', h)
        self.assertIn("<figcaption>Primeira</figcaption>", h)  # prefixo "Figura:" removido
        self.assertIn("data:image/png;base64,", h)
        self.assertEqual([f["n"] for f in ctx.figures], [1, 2])

    def test_imagem_sem_legenda_e_erro(self):
        """Dado ![](x.png) sem legenda, quando converte, então erro de figura sem legenda."""
        _, _, iss = conv("![](capturas/01-respondente-desktop.png)", captures=["capturas/01-respondente-desktop.png"])
        self.assertTrue(any("sem legenda" in e for e in iss.errors))

    def test_imagem_inexistente_e_erro(self):
        """Dado caminho de imagem que não existe, quando converte, então erro e marcador, sem quebrar."""
        h, _, iss = conv("![Legenda](capturas/nao-existe.png)", captures=["capturas/nao-existe.png"])
        self.assertTrue(any("inexistente" in e for e in iss.errors))
        self.assertIn("imagem ausente", h)

    def test_imagem_fora_da_pasta_ou_com_url_e_erro(self):
        """Dado ../x.png, /abs.png e https://, quando converte, então todas recusadas."""
        for p in ("../x.png", "/abs.png", "https://x.com/a.png"):
            _, _, iss = conv("![L](%s)" % p)
            self.assertTrue(any("não permitido" in e for e in iss.errors), p)

    def test_imagem_nao_registrada_em_captures_e_erro(self):
        """Dado imagem existente mas fora de captures, quando converte, então erro de privacidade."""
        _, _, iss = conv("![L](capturas/01-respondente-desktop.png)", captures=[])
        self.assertTrue(any("não registrada" in e for e in iss.errors))

    def test_par_de_telas_exige_duas_imagens(self):
        """Dado ::: screens-pair com 2 imagens, então desktop+mobile; com 1, erro."""
        caps = ["capturas/01-respondente-desktop.png", "capturas/02-respondente-celular.png"]
        h, _, iss = conv("::: screens-pair\n![A](capturas/01-respondente-desktop.png)\n"
                         "![B](capturas/02-respondente-celular.png)\n:::", captures=caps)
        self.assertEqual(iss.errors, [])
        self.assertIn('<div class="screens-pair">', h)
        self.assertIn("screenshot desktop", h)
        self.assertIn("screenshot mobile", h)
        _, _, iss = conv("::: screens-pair\n![A](capturas/01-respondente-desktop.png)\n:::", captures=caps)
        self.assertTrue(any("screens-pair" in e for e in iss.errors))

    def test_passos_numerados_com_titulo_e_conteudo(self):
        """Dado dois ::: step, quando converte, então .step com data-n 1 e 2 e título."""
        h, _, iss = conv("::: step Abra\nClique em **Abrir**.\n:::\n\n::: step Envie\ntexto\n:::")
        self.assertEqual(iss.errors, [])
        self.assertIn('<div class="step" data-n="1"><h3 class="step-title">Abra</h3>', h)
        self.assertIn('data-n="2"', h)
        self.assertIn("<strong>Abrir</strong>", h)

    def test_bloco_sem_fechamento_e_desconhecido_sao_erros(self):
        """Dado ::: step sem fim e ::: foo, quando converte, então erros."""
        self.assertTrue(conv("::: step A\ntexto")[2].errors)
        self.assertTrue(conv("::: foo\ntexto\n:::")[2].errors)

    def test_titulo_dentro_de_passo_e_erro(self):
        """Dado ## dentro de step, quando converte, então erro (não polui o sumário)."""
        _, ctx, iss = conv("::: step A\n## nope\n:::")
        self.assertTrue(iss.errors)
        self.assertEqual(ctx.toc, [])

    def test_callouts_dos_quatro_tipos(self):
        """Dado cada [!TIPO], quando converte, então div.callout com a classe certa e o texto."""
        for tipo, cls in (("NOTE", "note"), ("TIP", "tip"), ("WARNING", "warning"), ("IMPORTANT", "important")):
            h, _, _ = conv("> [!%s]\n> Texto **forte**\n> segunda linha" % tipo)
            self.assertIn('<div class="callout %s"' % cls, h)
            self.assertIn("<strong>forte</strong>", h)

    def test_bloco_de_codigo_escapa(self):
        """Dado cerca ```, quando converte, então <pre><code> com conteúdo escapado e sem markdown."""
        h, _, _ = conv("```\n<b>*x*</b>\n```")
        self.assertEqual(h, "<pre><code>&lt;b&gt;*x*&lt;/b&gt;</code></pre>")


class SchemaTests(unittest.TestCase):

    def check(self, mutate):
        d = load_ok()
        mutate(d)
        iss = bd.Issues()
        bd.validate_schema(d, iss)
        return iss.errors

    def test_fixture_valida(self):
        """Dado o delivery_ok, quando valida o esquema, então sem erros."""
        self.assertEqual(self.check(lambda d: None), [])

    def test_secao_obrigatoria_ausente_e_ordem(self):
        """Dado sem 'privacidade', ou com ordem trocada, então erro."""
        self.assertTrue(any("privacidade" in e for e in self.check(
            lambda d: d["sections"].__setitem__(slice(None), [s for s in d["sections"] if s["id"] != "privacidade"]))))
        self.assertTrue(any("ordem" in e for e in self.check(lambda d: d["sections"].reverse())))

    def test_secao_capa_ou_custom_nao_permitida(self):
        """Dado sections com id capa ou inventado, então erro."""
        self.assertTrue(self.check(lambda d: d["sections"].append({"id": "capa", "title": "x", "body_md": "y"})))
        self.assertTrue(self.check(lambda d: d["sections"].append({"id": "extra", "title": "x", "body_md": "y"})))

    def test_goes_to_inexistente_e_item_com_secao_invalida(self):
        """Dado destino de ramificação ou seção de item inexistentes, então erro."""
        self.assertTrue(self.check(lambda d: d["items"][0]["options"][0].__setitem__("goes_to", "s9")))
        self.assertTrue(self.check(lambda d: d["items"][0].__setitem__("section", "s9")))

    def test_link_nao_https_e_veredito_invalido(self):
        """Dado respondent_url http e veredito fora da lista, então erro."""
        self.assertTrue(self.check(lambda d: d["meta"]["links"].__setitem__("respondent_url", "http://x.com")))
        self.assertTrue(self.check(lambda d: d["meta"]["ux_verdict"].__setitem__("verdict", "TALVEZ")))


class BuildTests(unittest.TestCase):

    def setUp(self):
        self.addCleanup(lambda: None)

    def run_ok(self, **kw):
        code, payload, text, w = build(**kw)
        self.addCleanup(w.cleanup)
        return code, payload, text

    def test_montagem_com_template_minimo(self):
        """Dado o delivery_ok e o template mínimo, quando gera HTML, então html_only, ids reservados e CSS inline."""
        code, p, text = self.run_ok()
        self.assertEqual(code, 0, p["problems"])
        self.assertEqual(p["status"], "html_only")
        for rid in bd.RESERVED_IDS:
            self.assertIn('id="%s"' % rid, text, rid)
        self.assertIn("font-family:sans-serif", text)
        self.assertNotIn("{{", text)
        self.assertIn('--doc-title:"Inscrição no workshop \\"de\\" IA"', text)

    def test_imagens_embutidas_como_data_uri(self):
        """Dado as capturas, então o HTML não referencia arquivos externos."""
        _, _, text = self.run_ok()
        self.assertEqual(text.count("data:image/png;base64,"), 2)
        self.assertNotRegex(text, r'src="capturas/')

    def test_sumario_lista_secoes_subtitulos_e_figuras(self):
        """Dado ##/###, seções e figuras, então o sumário linka tudo."""
        _, _, text = self.run_ok()
        toc = re.search(r'<ol class="toc-list">(.*?)</ol>', text, re.S).group(1)
        for sid in bd.BODY_ORDER:
            self.assertIn('<a href="#%s">' % sid, toc, sid)
        self.assertIn('<li class="l2"><a href="#passo-tela-1">Tela 1', toc)
        self.assertIn('<li class="l3"><a href="#passo-a-passo-respondente-se-escolher-outro-setor">', toc)
        self.assertIn('<a href="#fig-01-respondente-desktop">Lista de figuras</a>', toc)
        self.assertIn("Figura 2 — Tela 1 no celular", toc)
        self.assertIn('href="#secao-s2">Seção 2 — Detalhes', toc.replace("<a href=\"#secao-s2\">", '<a href="#secao-s2">'))

    def test_fichas_ancoras_e_badges(self):
        """Dado itens e seções, então item-card com ids item-/secao-, badges e 'Para que serve'."""
        _, _, text = self.run_ok()
        self.assertIn('id="item-q1"', text)
        self.assertIn('id="secao-s1"', text)
        self.assertIn('<span class="badge required">Obrigatória</span>', text)
        self.assertIn('<span class="badge branch">Ramificação</span>', text)
        self.assertIn('<span class="badge optional">Opcional</span>', text)
        self.assertIn("Para que serve:", text)
        self.assertIn("Mensagem de erro: «Informe um CEP com 8 dígitos.»", text)

    def test_glossario_e_backlinks_citada_em(self):
        """Dado termo e item citados no corpo, então 'Citada em'/'Citado em' apontam para ids cit-N existentes."""
        _, _, text = self.run_ok()
        self.assertIn('<dt id="termo-ramificacao">', text)
        self.assertIn("Citado em:", text)
        self.assertIn("Citada em", text)
        for cid in re.findall(r'href="#(cit-\d+)"', text):
            self.assertIn('id="%s"' % cid, text)

    def test_cada_secao_termina_com_voltar_ao_sumario(self):
        """Dado as 12 seções, então cada uma tem o backlink para #sumario."""
        _, _, text = self.run_ok()
        self.assertGreaterEqual(text.count('<p class="backlink"><a href="#sumario">'), 12)

    def test_tokens_meta_sao_expandidos_no_corpo(self):
        """Dado {{meta.owner}} e {{links.respondent_url}} no corpo, então valores substituídos."""
        _, _, text = self.run_ok()
        self.assertIn("Responsável: Maria Exemplo", text)
        self.assertIn('href="https://docs.google.com/forms/d/e/EXEMPLO/viewform"', text)

    # ---- validação
    def test_link_interno_quebrado_invalida_e_nao_grava(self):
        """Dado [x](#nao-existe), quando monta, então invalid, exit 1 e nenhum HTML gravado."""
        def m(d):
            d["sections"][0]["body_md"] += "\n\n[x](#nao-existe)"
        code, p, text, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertEqual(p["status"], "invalid")
        self.assertTrue(any("nao-existe" in e for e in p["data"]["errors"]))
        self.assertIsNone(text)

    def test_id_duplicado_invalida(self):
        """Dado título com {#visao-geral} repetido, então erro de id duplicado."""
        def m(d):
            d["sections"][0]["body_md"] += "\n\n## Outro {#visao-geral}"
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("Id duplicado: visao-geral" in e for e in p["data"]["errors"]))

    def test_imagem_inexistente_invalida(self):
        """Dado captura registrada mas arquivo removido, então erro de imagem inexistente."""
        w = Workdir()
        os.remove(os.path.join(w.dir, "capturas", "02-respondente-celular.png"))
        code, p, _, _ = build(work=w)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("Imagem inexistente" in e for e in p["data"]["errors"]))

    def test_captura_nao_mascarada_ou_de_outra_versao_invalida(self):
        """Dado masked=false ou form_version diferente, então erro (privacidade/versão)."""
        code, p, _, w = build(lambda d: d["captures"][0].__setitem__("masked", False))
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("masked" in e for e in p["data"]["errors"]))
        code, p, _, w = build(lambda d: d["captures"][1].__setitem__("form_version", "0.9"))
        self.addCleanup(w.cleanup)
        self.assertTrue(any("versão" in e for e in p["data"]["errors"]))

    def test_numero_de_figura_citado_deve_bater(self):
        """Dado [Figura 2] apontando para a figura 1, então erro de número."""
        def m(d):
            d["sections"][2]["body_md"] = d["sections"][2]["body_md"].replace(
                "[Figura 1](#fig-01-respondente-desktop)", "[Figura 2](#fig-01-respondente-desktop)")
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("que é a Figura 1" in e for e in p["data"]["errors"]))

    def test_figura_nunca_citada_invalida(self):
        """Dado figura sem nenhuma citação no texto, então erro."""
        def m(d):
            for s in d["sections"]:
                s["body_md"] = s["body_md"].replace("[Figura 1](#fig-01-respondente-desktop)", "a primeira tela")
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("nunca é citada" in e for e in p["data"]["errors"]))

    def test_secao_vazia_invalida(self):
        """Dado body_md em branco numa seção escrita, então erro de seção vazia."""
        code, p, _, w = build(lambda d: d["sections"][4].__setitem__("body_md", "  \n"))
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("Seção vazia: particularidades" in e for e in p["data"]["errors"]))

    def test_template_sem_id_reservado_invalida(self):
        """Dado template sem id=\"sumario\", então erro de id reservado ausente."""
        tmp = tempfile.mkdtemp(prefix="gforms-tpl-")
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(MIN_TPL, "r", encoding="utf-8") as fh:
            t = fh.read().replace('id="sumario"', "")
        tpl = os.path.join(tmp, "t.html")
        with open(tpl, "w", encoding="utf-8") as fh:
            fh.write(t)
        code, p, _, w = build(template=tpl)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("Id reservado ausente no documento: sumario" in e for e in p["data"]["errors"]))

    def test_placeholder_desconhecido_no_template_invalida(self):
        """Dado {{inventado}} no template, então erro explícito."""
        tmp = tempfile.mkdtemp(prefix="gforms-tpl-")
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(MIN_TPL, "r", encoding="utf-8") as fh:
            t = fh.read().replace("{{owner}}", "{{inventado}}")
        tpl = os.path.join(tmp, "t.html")
        with open(tpl, "w", encoding="utf-8") as fh:
            fh.write(t)
        code, p, _, w = build(template=tpl)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("inventado" in e for e in p["data"]["errors"]))

    def test_token_desconhecido_no_corpo_invalida(self):
        """Dado {{meta.xyz}} no corpo, então erro."""
        code, p, _, w = build(lambda d: d["sections"][0].__setitem__("body_md", "oi {{meta.xyz}}"))
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertTrue(any("meta.xyz" in e for e in p["data"]["errors"]))

    # ---- avisos
    def test_jargao_de_agente_gera_aviso_e_strict_reprova(self):
        """Dado 'snapshot' e 'FORM-SPEC' no texto, então aviso (ok) e, com --strict, invalid."""
        def m(d):
            d["sections"][4]["body_md"] = "Veja o snapshot e o FORM-SPEC, ref=e12 e browser_click."
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 0)
        joined = " ".join(p["problems"])
        for termo in ("snapshot", "FORM-SPEC", "ref=", "browser_*"):
            self.assertIn(termo, joined)
        self.assertTrue(all(x.startswith("Aviso:") for x in p["problems"]))
        code, p, _, w = build(m, extra=["--strict"])
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 1)
        self.assertEqual(p["status"], "invalid")

    def test_email_real_gera_aviso_de_privacidade_mas_exemplo_nao(self):
        """Dado ana@gmail.com no texto, então aviso; ana@exemplo.com e x@example.org não avisam."""
        def m(d):
            d["sections"][4]["body_md"] = "Fale com joao.silva@gmail.com ou ana@exemplo.com ou x@example.org."
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 0)
        mails = [x for x in p["problems"] if "e-mail" in x]
        self.assertEqual(len(mails), 1)
        self.assertIn("gmail.com", mails[0])
        self.assertNotIn("joao.silva", mails[0])  # o aviso não repete o endereço inteiro

    def test_email_colado_entre_celulas_de_tabela_nao_gera_falso_positivo(self):
        """Dado tabela com «ana@exemplo.com» e «12/03» em células vizinhas, então nenhum aviso de e-mail real."""
        def m(d):
            d["sections"][4]["body_md"] = ("| Quem | Quando |\n|---|---|\n"
                                           "| ana@exemplo.com | 12/03 |\n")
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 0, p["problems"])
        self.assertEqual([x for x in p["problems"] if "e-mail" in x], [])

    def _historico(self, caveats=None, pending=None):
        def m(d):
            uv = d["meta"]["ux_verdict"]
            uv.pop("accepted_caveats", None)
            if caveats is not None:
                uv["accepted_caveats"] = caveats
            if pending is not None:
                uv["pending_decisions"] = pending
        code, p, text, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 0, p["problems"])
        return text

    def test_pending_decisions_titulos_conforme_as_listas(self):
        """Dado ressalvas e/ou pendências, então o título do bloco acompanha o que existe."""
        t = self._historico(caveats=["Aceita."], pending=["Base legal do aviso."])
        self.assertIn("<strong>Ressalvas aceitas pelo dono</strong>", t)
        self.assertIn("<strong>Decisões pendentes do dono</strong>", t)
        self.assertIn("Base legal do aviso.", t)
        t = self._historico(caveats=[], pending=["Base legal do aviso."])
        self.assertIn("<strong>Ressalvas e decisões pendentes do dono</strong>", t)
        self.assertNotIn("<strong>Ressalvas aceitas pelo dono</strong>", t)
        t = self._historico(caveats=[], pending=[])
        self.assertIn("<strong>Ressalvas aceitas pelo dono</strong>", t)
        self.assertIn("Nenhuma ressalva registrada.", t)
        self.assertNotIn("Decisões pendentes do dono", t)

    def test_pending_decisions_exige_lista_de_textos(self):
        """Dado pending_decisions que não é lista de textos, então erro de esquema."""
        for bad in ("texto solto", [1, 2], {"a": "b"}):
            d = load_ok()
            d["meta"]["ux_verdict"]["pending_decisions"] = bad
            iss = bd.Issues()
            bd.validate_schema(d, iss)
            self.assertTrue(any("pending_decisions" in e for e in iss.errors), bad)

    def test_item_e_termo_nunca_citados_geram_aviso(self):
        """Dado ficha e termo sem citação no corpo, então avisos."""
        def m(d):
            for s in d["sections"]:
                s["body_md"] = re.sub(r"\[([^\]]*)\]\(#(item-q2|termo-ramificacao)\)", r"\1", s["body_md"])
            d["items"].append({"id": "q9", "section": "s2", "number": 9, "type_label": "Texto", "title": "Extra", "use": "x"})
        code, p, _, w = build(m)
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 0, p["problems"])
        self.assertTrue(any("q9" in x for x in p["problems"]))


class CliTests(unittest.TestCase):

    def test_sem_out_nem_html_only_e_usage_error(self):
        """Dado só o delivery.json, quando roda, então usage_error e exit 2."""
        code, p, _ = run_main(bd.main, [os.path.join(OK_DIR, "delivery.json")], None)
        self.assertEqual((code, p["status"]), (2, "usage_error"))

    def test_arquivo_inexistente_e_usage_error(self):
        """Dado caminho que não existe, então usage_error exit 2."""
        code, p, _ = run_main(bd.main, ["/nao/existe.json", "--html-only"], None)
        self.assertEqual((code, p["status"]), (2, "usage_error"))

    def test_argumento_invalido_devolve_json_exit_2(self):
        """Dado flag desconhecida, então JSON de uso inválido e exit 2."""
        code, p, _ = run_main(bd.main, ["x.json", "--bogus"], None)
        self.assertEqual((code, p["status"]), (2, "usage_error"))

    def test_json_invalido_e_invalid(self):
        """Dado delivery.json corrompido, então invalid exit 1."""
        tmp = tempfile.mkdtemp(prefix="gforms-bad-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "delivery.json")
        with open(path, "w") as fh:
            fh.write("{nao e json")
        code, p, _ = run_main(bd.main, [path, "--html-only"], None)
        self.assertEqual((code, p["status"]), (1, "invalid"))

    def test_out_e_html_only_juntos_e_usage_error(self):
        """Dado --out e --html-only, então usage_error."""
        code, p, _ = run_main(bd.main, [os.path.join(OK_DIR, "delivery.json"), "--out", "x.pdf", "--html-only"], None)
        self.assertEqual((code, p["status"]), (2, "usage_error"))


class PdfHelpersTests(unittest.TestCase):

    def test_inspect_pdf_conta_paginas_e_links_inclusive_em_stream_comprimido(self):
        """Dado PDF sintético com /Link em claro e em stream Flate, então conta ambos e as páginas."""
        import zlib
        inner = b"<< /Type /Annot /Subtype /Link /Dest /x >>"
        stream = zlib.compress(inner)
        data = (b"%PDF-1.4\n1 0 obj << /Type /Pages >> endobj\n2 0 obj << /Type /Page >> endobj\n"
                b"3 0 obj << /Type /Page >> endobj\n4 0 obj << /Subtype /Link >> endobj\n"
                b"5 0 obj << /Filter /FlateDecode >>\nstream\n" + stream + b"\nendstream\nendobj\n")
        tmp = tempfile.mkdtemp(prefix="gforms-pdf-t-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "a.pdf")
        with open(path, "wb") as fh:
            fh.write(data)
        info = bd.inspect_pdf(path)
        self.assertEqual((info["valid"], info["pages"], info["links"]), (True, 2, 2))

    def test_inspect_pdf_rejeita_arquivo_sem_cabecalho(self):
        """Dado arquivo que não começa com %PDF, então valid False."""
        tmp = tempfile.mkdtemp(prefix="gforms-pdf-t-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "a.pdf")
        with open(path, "wb") as fh:
            fh.write(b"<html>")
        self.assertFalse(bd.inspect_pdf(path)["valid"])

    def test_sister_script_override_inexistente_e_erro_e_existente_vale(self):
        """Dado GFORMS_HTML_TO_PDF, então inexistente = erro; existente = esse caminho."""
        path, err = bd.find_sister_script({bd.SISTER_ENV: "/nao/existe.py"})
        self.assertIsNone(path)
        self.assertIn("inexistente", err)
        path, err = bd.find_sister_script({bd.SISTER_ENV: __file__})
        self.assertEqual((path, err), (__file__, None))

    def test_sister_script_e_achado_na_pasta_irma_da_skill(self):
        """Dado ../generate-pdf-report/pt-BR/scripts/html_to_pdf.py relativo à skill, então é encontrado."""
        tmp = tempfile.mkdtemp(prefix="gforms-skills-")
        self.addCleanup(shutil.rmtree, tmp, True)
        skill = os.path.join(tmp, "productivity", "google-forms", "pt-BR")
        os.makedirs(skill)
        sister = os.path.join(tmp, "productivity", "generate-pdf-report", "pt-BR", "scripts")
        os.makedirs(sister)
        target = os.path.join(sister, "html_to_pdf.py")
        open(target, "w").close()
        old = bd.SKILL_DIR
        bd.SKILL_DIR = skill
        try:
            path, err = bd.find_sister_script({})
        finally:
            bd.SKILL_DIR = old
        self.assertEqual(os.path.realpath(path), os.path.realpath(target))


class DetectBrowserFromPlaywrightMcpTests(unittest.TestCase):
    """O build não carrega detect_browser próprio: usa o da skill playwright-mcp, achada como no check_setup."""

    def _fake_pm(self):
        tmp = tempfile.mkdtemp(prefix="gforms-pm-")
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "check_setup.py"), "w") as fh:
            fh.write("")
        return tmp

    def test_carrega_o_modulo_da_pasta_apontada_pela_variavel(self):
        """Dado GFORMS_PLAYWRIGHT_MCP_DIR com um detect_browser.py, então o build carrega esse módulo."""
        pm = self._fake_pm()
        with open(os.path.join(pm, "scripts", "detect_browser.py"), "w") as fh:
            fh.write("MARCA = 'falso'\n")
        module, why = bd.load_detect_browser({"GFORMS_PLAYWRIGHT_MCP_DIR": pm})
        self.assertIsNone(why)
        self.assertEqual(module.MARCA, "falso")

    def test_variavel_invalida_vira_motivo_legivel(self):
        """Dado GFORMS_PLAYWRIGHT_MCP_DIR vazio de conteúdo, então não carrega e cita a variável."""
        module, why = bd.load_detect_browser({"GFORMS_PLAYWRIGHT_MCP_DIR": self._fake_pm() + "-nao-existe"})
        self.assertIsNone(module)
        self.assertIn("GFORMS_PLAYWRIGHT_MCP_DIR", why)

    def test_render_sem_playwright_mcp_nem_pdf_irmao_avisa_e_falha_sem_travar(self):
        """Dado nenhuma skill irmã, quando renderiza, então devolve None com aviso sobre a playwright-mcp."""
        tmp = tempfile.mkdtemp(prefix="gforms-render-")
        self.addCleanup(shutil.rmtree, tmp, True)
        html_path = os.path.join(tmp, "a.html")
        with open(html_path, "w") as fh:
            fh.write("<html></html>")
        old = bd.SKILL_DIR
        bd.SKILL_DIR = os.path.join(tmp, "isolado", "google-forms", "pt-BR")
        try:
            renderer, problems, usage = bd.render_pdf(html_path, os.path.join(tmp, "a.pdf"), {})
        finally:
            bd.SKILL_DIR = old
        self.assertEqual((renderer, usage), (None, False))
        self.assertTrue(any("playwright-mcp" in p for p in problems), problems)


def _chromium_for_render():
    """Há um Chromium que não seja o Brave (o Brave headless trava no --print-to-pdf no macOS)?"""
    detect_browser, _ = bd.load_detect_browser()
    if detect_browser is None:
        return False
    try:
        payload = detect_browser.detect(detect_browser.SystemEnv())[1]
    except Exception:  # noqa: BLE001
        return False
    return any(e.get("id") != "brave" and e.get("chromium") and e.get("executable")
               for e in (payload.get("data") or {}).get("installed", []))


@unittest.skipUnless(_chromium_for_render(), "sem Chrome/Edge/Chromium para renderizar")
@unittest.skipUnless(os.path.isfile(bd.DEFAULT_TEMPLATE), "template real ausente")
class IntegrationPdfTests(unittest.TestCase):

    def test_gera_pdf_de_verdade_com_o_template_real(self):
        """Dado o delivery_ok e o template real, quando roda --out, então PDF válido com páginas e links clicáveis."""
        w = Workdir()
        self.addCleanup(w.cleanup)
        out = os.path.join(w.tmp, "entrega", "doc.pdf")
        code, p, _ = run_main(bd.main, [w.path, "--out", out, "--generated-at", STAMP], None)
        self.assertEqual(code, 0, p["problems"])
        self.assertEqual(p["status"], "built")
        with open(out, "rb") as fh:
            self.assertEqual(fh.read(4), b"%PDF")
        d = p["data"]
        self.assertGreaterEqual(d["pages"], 3)
        self.assertGreaterEqual(d["link_annotations"], d["internal_links"])
        self.assertTrue(os.path.isfile(d["html"]))
        self.assertTrue(d["renderer"])


EXAMPLE_DIR = os.path.join(bd.SKILL_DIR, "templates", "delivery-doc", "example")


def warnings_of(mutate=None, work=None):
    code, p, _, w = build(mutate, work=work)
    return code, p["data"].get("warnings", []), p, w


def _set_body(d, sid, body):
    for s in d["sections"]:
        if s["id"] == sid:
            s["body_md"] = body


class ContentWarningTests(unittest.TestCase):
    """Avisos de conteúdo: nunca viram erro (o PDF sai), mas mandam corrigir o que o contrato exige."""

    def test_faq_fora_de_6_a_12_avisa(self):
        """Dado a fixture com 1 pergunta na FAQ, quando monta, então avisa a contagem e o status segue html_only."""
        code, warns, p, w = warnings_of()
        self.addCleanup(w.cleanup)
        self.assertEqual(code, 0)
        self.assertEqual(p["status"], "html_only")
        self.assertTrue(any("Perguntas frequentes tem 1 perguntas" in x for x in warns), warns)

    def test_faq_com_6_perguntas_nao_avisa(self):
        """Dado uma FAQ com 6 títulos ##, quando monta, então não há aviso de contagem."""
        faq = "\n\n".join("## Pergunta %d?\n\nResposta." % i for i in range(6))
        code, warns, _, w = warnings_of(lambda d: _set_body(d, "perguntas-frequentes", faq))
        self.addCleanup(w.cleanup)
        self.assertFalse(any("Perguntas frequentes" in x for x in warns), warns)

    def test_visao_geral_sem_tabela_e_sem_caixa_avisa(self):
        """Dado visão geral sem tabela e not_verified preenchido sem a caixa, quando monta, então dois avisos."""
        _, warns, _, w = warnings_of()
        self.addCleanup(w.cleanup)
        self.assertTrue(any("«Em resumo»" in x for x in warns), warns)
        self.assertTrue(any("O que ainda não foi conferido" in x for x in warns), warns)

    def test_acesso_sem_link_do_respondente_por_extenso_avisa(self):
        """Dado acesso-e-links sem a URL do respondente, quando monta, então avisa; com o marcador, não."""
        _, warns, _, w = warnings_of(lambda d: _set_body(d, "acesso-e-links", "Só texto."))
        self.addCleanup(w.cleanup)
        self.assertTrue(any("link do respondente por extenso" in x for x in warns), warns)
        _, warns2, _, w2 = warnings_of(lambda d: _set_body(
            d, "acesso-e-links", "{{links.respondent_url}} e {{links.edit_url}}"))
        self.addCleanup(w2.cleanup)
        self.assertFalse(any("por extenso" in x for x in warns2), warns2)

    def test_despublicado_exige_caixa_de_atencao_e_restrito(self):
        """Dado form_status despublicado sem as caixas, quando monta, então avisa as duas ausências."""
        def mut(d):
            d["meta"]["form_status"] = "despublicado"
            _set_body(d, "acesso-e-links", "Link: {{links.respondent_url}} e {{links.edit_url}}.")
        _, warns, _, w = warnings_of(mut)
        self.addCleanup(w.cleanup)
        self.assertTrue(any("despublicado: Acesso e links precisa" in x for x in warns), warns)
        self.assertTrue(any("começa com «Restrito»" in x for x in warns), warns)

    def test_ramificacao_sem_tabela_de_caminhos_avisa(self):
        """Dado itens com goes_to e passo a passo sem tabela, quando monta, então avisa o mapa de caminhos."""
        _, warns, _, w = warnings_of(lambda d: _set_body(d, "passo-a-passo-respondente", "Texto sem tabela."))
        self.addCleanup(w.cleanup)
        self.assertTrue(any("mapa de caminhos" in x for x in warns), warns)

    def test_glossario_sem_termos_minimos_avisa(self):
        """Dado glossário só com «Ramificação», quando monta, então pede Carimbo, Despublicado e Link para as Planilhas."""
        _, warns, _, w = warnings_of()
        self.addCleanup(w.cleanup)
        for nome in ("Carimbo de data/hora", "Despublicado", "Link para as Planilhas"):
            self.assertTrue(any("«%s»" % nome in x for x in warns), (nome, warns))


class CitationWarningTests(unittest.TestCase):

    def _warns(self, body):
        _, warns, _, w = warnings_of(lambda d: _set_body(d, "funcionalidades", body))
        self.addCleanup(w.cleanup)
        return [x for x in warns if "citada sem link" in x or "sem link para o glossário" in x]

    def test_pergunta_n_fora_de_link_avisa(self):
        """Dado «Pergunta 1» solta no texto, quando monta, então avisa a citação sem link."""
        got = self._warns("Veja a Pergunta 1 para o setor.")
        self.assertEqual(len(got), 1, got)
        self.assertIn("Pergunta 1", got[0])

    def test_pergunta_n_com_link_no_mesmo_paragrafo_nao_avisa(self):
        """Dado «Pergunta 1» linkada e repetida sem link no mesmo parágrafo, quando monta, então não avisa."""
        got = self._warns("A [Pergunta 1 — Qual é o seu setor?](#item-q1) decide o caminho; a Pergunta 1 é obrigatória.")
        self.assertEqual(got, [])

    def test_titulo_e_legenda_nao_geram_aviso(self):
        """Dado «Pergunta 1» em um título ##, quando monta, então não avisa (título não é citação corrida)."""
        got = self._warns("## Sobre a Pergunta 1 {#func-x}\n\nTexto.")
        self.assertEqual(got, [])

    def test_figura_n_fora_de_link_avisa(self):
        """Dado «Figura 2» solta, quando monta, então avisa."""
        got = self._warns("Como mostra a Figura 2, tudo certo.")
        self.assertEqual(len(got), 1, got)

    def test_termo_do_glossario_sem_link_na_secao_avisa(self):
        """Dado o termo «Ramificação» no texto sem link, quando monta, então avisa; com link na seção, não."""
        got = self._warns("A Ramificação muda a tela seguinte.")
        self.assertEqual(len(got), 1, got)
        ok = self._warns("A [Ramificação](#termo-ramificacao) muda a tela; a Ramificação segue valendo.")
        self.assertEqual(ok, [])

    def test_termo_entre_aspas_angulares_nao_conta(self):
        """Dado o termo dentro de «», quando monta, então não avisa (é nome de botão ou de tela)."""
        got = self._warns("Clique em «Ramificação».")
        self.assertEqual(got, [])


@unittest.skipUnless(os.path.isfile(os.path.join(EXAMPLE_DIR, "delivery.json")), "exemplo completo ausente")
class ExemploCompletoTests(unittest.TestCase):

    def test_exemplo_completo_sai_sem_avisos_de_conteudo(self):
        """Dado o exemplo completo da skill, quando monta com o modelo real, então status html_only e zero avisos."""
        tmp = tempfile.mkdtemp(prefix="gforms-ex-")
        self.addCleanup(shutil.rmtree, tmp, True)
        work = os.path.join(tmp, "w")
        shutil.copytree(EXAMPLE_DIR, work)
        code, p, _ = run_main(bd.main, [os.path.join(work, "delivery.json"), "--html-only", "--html",
                                         os.path.join(tmp, "o.html"), "--generated-at", STAMP], None)
        self.assertEqual(code, 0, p["problems"])
        self.assertEqual(p["status"], "html_only")
        self.assertEqual(p["data"]["errors"], [])
        self.assertEqual(p["data"]["warnings"], [])
        self.assertEqual(p["data"]["figures"], 11)

    def test_exemplo_nao_tem_dado_real(self):
        """Dado o exemplo, quando lê o JSON, então só e-mails de exemplo e URLs com EXEMPLO."""
        with open(os.path.join(EXAMPLE_DIR, "delivery.json"), "r", encoding="utf-8") as fh:
            raw = fh.read()
        for m in re.finditer(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)", raw):
            self.assertTrue(m.group(1).startswith("exemplo."), m.group(0))
        for u in re.findall(r"https://docs\.google\.com/[^\"\s)\]]*", raw):
            self.assertIn("EXEMPLO", u)


class ContratoDocumentadoTests(unittest.TestCase):

    def test_delivery_doc_cita_todos_os_ids_reservados(self):
        """Dado o DELIVERY-DOC.md, quando procura cada id reservado, então todos aparecem (evita deriva do esquema)."""
        with open(os.path.join(bd.SKILL_DIR, "DELIVERY-DOC.md"), "r", encoding="utf-8") as fh:
            doc = fh.read()
        for sid in bd.BODY_ORDER:
            self.assertIn("`%s`" % sid, doc, sid)

    def test_readme_do_modelo_so_cita_badges_que_o_build_emite(self):
        """Dado o README do modelo, quando lista badges, então nenhum alias inalcançável (validacao)."""
        with open(os.path.join(bd.SKILL_DIR, "templates", "delivery-doc", "README.md"), "r", encoding="utf-8") as fh:
            readme = fh.read()
        self.assertNotIn("validacao", readme)
        self.assertNotIn("lab/", readme)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Exemplo completo de gerador do documento de revisão de segurança (conteúdo FICTÍCIO).

Copie este arquivo para a pasta do documento e substitua o conteúdo pelo do seu quadro de afirmações.
Fonte única: este script (conteúdo + estilo); o HTML e o PDF são gerados.

Uso:  python3 build_doc.example.py <pasta-de-saída>
      CHROME_PATH=/caminho/do/chrome python3 build_doc.example.py out/    (override opcional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))  # ajuste ao copiar
from doc_lib import (DocConfig, build, callout, cards, chip, cover, diagram_pages, kpi, section, table,
                     toc_html, xref)

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
OUT.mkdir(parents=True, exist_ok=True)

cfg = DocConfig(
    product="Acme Pay – Portal do Lojista",              # forma COMPLETA do produto (regra de nomes)
    doc_type="Documentação para a Segurança da Informação",
    version="1.0", date_long="1 de janeiro de 2030", date_short="01/01/2030",
    eyebrow="Cliente Exemplo × Autor Exemplo",
    subtitle="Documentação do produto, da arquitetura de referência e dos controles de segurança e privacidade.",
    meta_rows=[("Destinatário", "Time de Segurança da Informação do Cliente Exemplo"),
               ("Elaborado por", "Autor Exemplo · Responsável Técnico")],
)

# Chips de origem (renomeie conforme o projeto; mantenha a taxonomia de provenance-tags.md)
SEC = chip("si", "Reunião de segurança · 01/12/2029")
INF = chip("inf", "Padrão da infra · 15/12/2029")
DES = chip("", "Desenho de arquitetura")
DOC = chip("doc", "Doc. do parceiro")
ENG = chip("eng", "Padrão de engenharia")
REQ = chip("req", "Requisito do desenho")
PROP = chip("prop", "Proposta · a confirmar")
PROD = chip("prod", "Comportamento do produto")

# (id, rótulo, título, tipo do eyebrow)
SECTIONS = [
    ("s1", "1", "Sobre este documento", "Seção"),
    ("s2", "2", "Visão geral do produto", "Seção"),
    ("s4", "3", "Arquitetura de referência", "Seção"),
    ("s7", "4", "Segurança", "Seção"),
    ("s8", "5", "Privacidade e LGPD", "Seção"),
    ("s11", "6", "Próximos passos", "Seção"),
    ("sa", "A", "Superfície de exposição (preliminar)", "Anexo"),
    ("sb", "B", "Glossário", "Anexo"),
]


def diagram_svg():
    """Diagrama fictício. No projeto real: SVG exportado do draw.io (use doc_lib.svg_inline(caminho))."""
    boxes = [(40, 140, "Navegador"), (260, 140, "CDN + WAF"), (480, 140, "Gateway de API"),
             (700, 140, "Serviço (pods)"), (920, 140, "Banco de dados")]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 320" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" font-family="Helvetica,Arial">']
    for i, (x, y, label) in enumerate(boxes):
        parts.append('<rect x="%d" y="%d" width="190" height="70" rx="8" fill="#E8EEFC" stroke="#1F4FD1"/>' % (x, y))
        parts.append('<text x="%d" y="%d" text-anchor="middle" font-size="18">%s</text>' % (x + 95, y + 42, label))
        if i < len(boxes) - 1:
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#14202E" stroke-width="2"/>' % (x + 190, y + 35, x + 220, y + 35))
            parts.append('<text x="%d" y="%d" font-size="16" fill="#1F4FD1">%d</text>' % (x + 198, y + 24, i + 1))
    parts.append("</svg>")
    return "".join(parts)


def body(pages):
    h = [cover(cfg)]
    h.append('<section class="sec-first"><div class="eyebrow">Controle do documento</div><h1>Sumário</h1>%s'
             '<h3>Controle de versão</h3>%s</section>'
             % (toc_html(SECTIONS, pages),
                table(["Versão", "Data", "Responsável", "Descrição"],
                      [[cfg.version, cfg.date_short, "Autor Exemplo", "Primeira emissão para a Segurança da Informação."]],
                      ["14%", "16%", "32%", "38%"], k=False)))

    h.append(section("s1", "Seção 1", "Sobre este documento", f"""
 <p class="lead">Este documento descreve o produto <b>Acme Pay – Portal do Lojista</b>, a arquitetura de referência e os controles de segurança e privacidade previstos.</p>
 <h2>Como ler a origem de cada afirmação</h2>
 <table><tbody>
  <tr><td style="width:44mm">{SEC}</td><td>Exigência ou orientação da área de segurança na reunião de 01/12/2029.</td></tr>
  <tr><td>{INF}</td><td>Padrão da infraestrutura do cliente informado ao autor.</td></tr>
  <tr><td>{DES}</td><td>Elemento do desenho de arquitetura ({xref('s4', 'seção 3')}).</td></tr>
  <tr><td>{DOC}</td><td>Regra da documentação oficial do parceiro.</td></tr>
  <tr><td>{ENG}</td><td>Prática de engenharia adotada no código.</td></tr>
  <tr><td>{REQ}</td><td>Requisito do projeto, aplicado pela infraestrutura.</td></tr>
  <tr><td>{PROD}</td><td>Comportamento conforme as jornadas do protótipo aprovado.</td></tr>
  <tr><td>{PROP}</td><td>Proposta do autor, ainda não validada pelo leitor ou pela infraestrutura.</td></tr>
 </tbody></table>
 {callout("<b>Natureza do documento.</b> A solução está em desenvolvimento. Os controles descrevem o desenho; serão confirmados em homologação, na análise de código e no teste de invasão. O documento é atualizado a cada mudança relevante.")}
"""))

    h.append(section("s2", "Seção 2", "Visão geral do produto", f"""
 <p class="lead">O portal permite que um lojista consulte e solicite serviços pela web, sem passar por uma loja.</p>
 {kpi([("Canal", "Web responsiva"), ("Primeira entrega", "Pessoa Jurídica"), ("Operação", "Sem operador")])}
 {table(["Sistema vizinho", "Relação com o produto"], [
   ["Acme Pay", "Plataforma de pagamentos existente do cliente. O portal <b>não substitui nem se confunde</b> com ela."],
   ["Gateway do parceiro", "Toda a comunicação de credenciamento passa por ele."]], ["26%", "74%"])}
 <p class="small">Fontes: reunião de segurança; jornadas do protótipo.</p>
""", ))

    h.append(diagram_pages("Seção 3 · Arquitetura de referência", "Visão geral da solução", diagram_svg(),
                           [("1", "O lojista chega pela CDN (HTTPS)."), ("2", "A CDN encaminha as chamadas ao gateway."),
                            ("3", "O gateway chama o serviço por link privado."), ("4", "O serviço acessa o banco (porta 5432).")],
                           note="O desenho está em vetor: dá para ampliar no leitor de PDF. A imagem em alta resolução segue em anexo.",
                           sid="s4"))

    h.append(section("s7", "Seção 4", "Segurança", f"""
 <h2>4.1 Borda e acesso</h2>
 {table(["Controle", "Como é tratado", "Origem"], [
   ["WAF à frente de tudo", "Toda API ou servidor web exposto à internet passa pelo WAF.", SEC],
   ["Gateway de API", f"Só as rotas necessárias ao navegador são expostas ({xref('sa', 'Anexo A')}).", SEC + DES],
   ["Cabeçalhos e CORS", "Cabeçalhos de segurança e CORS por allowlist de origens.", ENG],
   ["Segredos", "Guardados em cofre gerenciado; leitura pela identidade do pod.", SEC + DES]], ["24%", "58%", "18%"])}
 <h2>4.2 Dados em repouso</h2>
 {table(["Controle", "Como é tratado", "Origem"], [
   ["Banco de dados", "Criptografado em repouso, em duas zonas de disponibilidade.", DES],
   ["Retenção de arquivos", "Eliminação 7 dias depois do envio de cada arquivo (cobre análise de até 48 horas úteis, fim de semana e folga de 24 horas). Aguarda aprovação da privacidade.", PROP]],
   ["24%", "58%", "18%"])}
 <p class="small">Fontes: reunião de segurança; desenho de arquitetura; padrões de engenharia.</p>
"""))

    h.append(section("s8", "Seção 5", "Privacidade e LGPD", f"""
 {callout("<b>Alcance.</b> Esta seção descreve o tratamento e os controles técnicos. Não é parecer jurídico: papéis, base legal e retenção são alinhados com a privacidade e a segurança.", warn=True)}
 {table(["Categoria", "Dados", "Onde ficam", "Proteção"], [
   ["Empresa", "CNPJ, razão social.", "Banco do produto; parceiro.", "Cifra por campo; banco criptografado."]],
   ["15%", "30%", "25%", "30%"])}
 <p class="small">Fontes: nota de privacidade do projeto; desenho de arquitetura.</p>
"""))

    h.append(section("s11", "Seção 6", "Próximos passos", f"""
 {cards([("Do autor", "<ul><li>Atualizar este documento a cada mudança relevante.</li></ul>"),
         ("Da segurança e do cliente", "<ul><li>Devolutiva técnica sobre este documento.</li></ul>")])}
""", first=True))

    h.append(section("sa", "Anexo A", "Superfície de exposição (preliminar)", f"""
 {callout("<b>Estado.</b> O desenvolvimento ainda não começou. Este inventário é preliminar: lista o que o produto vai expor, não as rotas finais.", warn=True)}
 {table(["Capacidade", "Função", "Exposição"], [
   ["Cadastro (rascunho)", "Criar e atualizar o rascunho do pedido, de forma idempotente.", "Externa (via gateway de API)"],
   ["Verificações de saúde", "Sondas de vida e de prontidão do serviço.", "Interna (plataforma)"]], ["24%", "60%", "16%"])}
""", ))

    h.append(section("sb", "Anexo B", "Glossário", table(["Termo", "Significado"], [
        ["WAF", "Firewall de aplicação web."], ["CDN", "Rede de entrega de conteúdo."],
        ["DLQ", "Fila para onde vão as mensagens que falharam repetidamente."]], ["26%", "74%"]), first=True))
    return "\n".join(h)


if __name__ == "__main__":
    build(cfg, body, SECTIONS, str(OUT / "documento.html"), str(OUT / "documento.pdf"))

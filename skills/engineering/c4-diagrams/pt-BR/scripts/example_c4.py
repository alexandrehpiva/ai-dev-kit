"""Exemplo executável: gera os cinco tipos de diagrama C4 para um sistema FICTÍCIO
("Plataforma de Pedidos"). Substitua nomes, tecnologias e setas pelo que foi
confirmado no código/IaC/documentação do sistema real.

    python3 example_c4.py [pasta_de_saida]     # grava examples/*.drawio

Renderização (macOS, app do draw.io instalado):
    /Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 1 -o saida.png entrada.drawio
"""
import sys
from pathlib import Path

from c4_drawio_lib import C4Diagram

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("examples")
out.mkdir(parents=True, exist_ok=True)
SYS = "Plataforma de Pedidos"


def context():
    d = C4Diagram("context", SYS)
    cliente = d.person(60, 140, "Cliente", "Compra produtos e acompanha entregas")
    atend = d.person(60, 520, "Atendente", "Consulta e corrige pedidos de clientes")
    plat = d.system(640, 330, SYS, "Recebe pedidos, cobra e notifica o cliente", w=260, h=150)
    pag = d.system(1180, 140, "Gateway de Pagamento", "Processa cobranças de cartão e Pix", external=True)
    mail = d.system(1180, 520, "Serviço de E-mail", "Entrega e-mails transacionais", external=True)
    d.rel(cliente, plat, "Faz pedidos e acompanha entregas por", src_side="r", dst_side="t", via=[(770, 215)])
    d.rel(atend, plat, "Consulta e corrige pedidos em", src_side="r", dst_side="l")
    d.rel(plat, pag, "Solicita cobrança a", src_side="r", dst_side="l")
    d.rel(plat, mail, "Envia notificações por", src_side="b", dst_side="l", via=[(770, 585)])
    return d


def containers():
    d = C4Diagram("container", SYS)
    cliente = d.person(40, 150, "Cliente", "Compra produtos e acompanha entregas")
    atend = d.person(40, 560, "Atendente", "Consulta e corrige pedidos")
    d.boundary(440, 90, 1090, 730, SYS, "system")
    spa = d.container(500, 150, "Aplicação Web", "TypeScript, SPA no navegador",
                      "Catálogo, carrinho e acompanhamento de pedidos", shape="webapp")
    api = d.container(960, 150, "API de Pedidos", "Node.js, REST/JSON",
                      "Valida e registra pedidos; orquestra cobrança")
    db = d.container(960, 480, "Banco de Pedidos", "PostgreSQL",
                     "Pedidos, itens e histórico de status", shape="database")
    fila = d.container(1240, 380, "Fila de Eventos", "Mensageria AMQP",
                       "Eventos de pedido criado e pago", shape="queue", w=250)
    worker = d.container(1240, 640, "Worker de Notificações", "Node.js",
                         "Consome eventos e dispara e-mails", w=250)
    pag = d.system(1680, 150, "Gateway de Pagamento", "Processa cobranças de cartão e Pix", external=True)
    mail = d.system(1680, 640, "Serviço de E-mail", "Entrega e-mails transacionais", external=True)
    d.rel(cliente, spa, "Navega e faz pedidos em", "HTTPS", src_side="r", dst_side="l")
    d.rel(atend, spa, "Corrige pedidos em", "HTTPS", src_side="r", dst_side="b", via=[(620, 635)])
    d.rel(spa, api, "Envia pedidos para", "JSON/HTTPS", src_side="r", dst_side="l")
    d.rel(api, db, "Lê e grava pedidos em", "SQL/TCP", src_side="b", dst_side="t")
    d.rel(api, pag, "Solicita cobrança a", "REST/HTTPS", src_side="r", dst_side="l")
    d.rel(api, fila, "Publica 'pedido criado' em", "AMQP", asynchronous=True, src_side="b", dst_side="t",
          src_at=(0.85, 1), via=[(1164, 330), (1365, 330)])
    d.rel(fila, worker, "Entrega eventos a", "AMQP", asynchronous=True, src_side="b", dst_side="t")
    d.rel(worker, mail, "Envia confirmação por", "SMTP", src_side="r", dst_side="l")
    return d


def components():
    d = C4Diagram("component", "API de Pedidos")
    spa = d.container(40, 155, "Aplicação Web", "TypeScript, SPA no navegador",
                      "Catálogo, carrinho e acompanhamento", shape="webapp")
    d.boundary(480, 90, 800, 780, "API de Pedidos", "container")
    ctl = d.component(540, 160, "Controlador de Pedidos", "Node.js, REST controller",
                      "Recebe e valida requisições HTTP de pedidos")
    srv = d.component(540, 430, "Serviço de Pedidos", "TypeScript, classe de serviço",
                      "Regras de negócio: criar, pagar e cancelar pedido")
    repo = d.component(540, 700, "Repositório de Pedidos", "TypeScript, acesso a dados",
                       "Persiste e consulta pedidos")
    pub = d.component(960, 160, "Publicador de Eventos", "TypeScript, produtor AMQP",
                      "Publica eventos de domínio na fila")
    cobr = d.component(960, 430, "Cliente de Cobrança", "TypeScript, cliente HTTP",
                       "Encapsula a chamada ao gateway de pagamento")
    fila = d.container(1620, 155, "Fila de Eventos", "Mensageria AMQP", "Eventos de pedido", shape="queue", w=250)
    pag = d.system(1620, 425, "Gateway de Pagamento", "Processa cobranças de cartão e Pix", external=True, w=250)
    db = d.container(1620, 695, "Banco de Pedidos", "PostgreSQL", "Pedidos, itens e histórico",
                     shape="database", w=250)
    d.rel(spa, ctl, "Envia pedidos para", "JSON/HTTPS", src_side="r", dst_side="l")
    d.rel(ctl, srv, "Delega regras de pedido a", "chamada de método", src_side="b", dst_side="t")
    d.rel(srv, repo, "Persiste pedidos via", "chamada de método", src_side="b", dst_side="t")
    d.rel(srv, cobr, "Solicita cobrança por", "chamada de método", src_side="r", dst_side="l")
    d.rel(srv, pub, "Publica eventos via", "chamada de método", src_side="r", dst_side="l",
          src_at=(1, 0.15), via=[(870, 448), (870, 220)])
    d.rel(repo, db, "Lê e grava pedidos em", "SQL/TCP", src_side="r", dst_side="l")
    d.rel(pub, fila, "Publica eventos em", "AMQP", asynchronous=True, src_side="r", dst_side="l")
    d.rel(cobr, pag, "Solicita cobrança a", "REST/HTTPS", src_side="r", dst_side="l")
    return d


def dynamic():
    d = C4Diagram("dynamic", "Fazer pedido", title="Dynamic diagram for Fazer pedido (Plataforma de Pedidos)")
    cliente = d.person(40, 150, "Cliente", "Finaliza uma compra")
    spa = d.container(440, 150, "Aplicação Web", "TypeScript, SPA no navegador", "Coleta os dados do pedido",
                      shape="webapp")
    api = d.container(900, 150, "API de Pedidos", "Node.js, REST/JSON", "Valida e registra o pedido")
    pag = d.system(1380, 150, "Gateway de Pagamento", "Processa a cobrança", external=True)
    db = d.container(900, 450, "Banco de Pedidos", "PostgreSQL", "Armazena o pedido", shape="database")
    fila = d.container(1380, 450, "Fila de Eventos", "Mensageria AMQP", "Eventos de pedido", shape="queue")
    worker = d.container(1380, 720, "Worker de Notificações", "Node.js", "Dispara e-mails")
    mail = d.system(900, 720, "Serviço de E-mail", "Entrega e-mails", external=True)
    d.rel(cliente, spa, "Confirma o pedido em", "HTTPS", step=1, src_side="r", dst_side="l")
    d.rel(spa, api, "Envia dados do pedido para", "JSON/HTTPS", step=2, src_side="r", dst_side="l")
    d.rel(api, db, "Grava o pedido em", "SQL/TCP", step=3, src_side="b", dst_side="t")
    d.rel(api, pag, "Solicita cobrança a", "REST/HTTPS", step=4, src_side="r", dst_side="l")
    d.rel(api, fila, "Publica 'pedido criado' em", "AMQP", step=5, asynchronous=True, src_side="b", dst_side="t",
          src_at=(0.85, 1), via=[(1104, 365), (1500, 365)])
    d.rel(fila, worker, "Entrega evento a", "AMQP", step=6, asynchronous=True, src_side="b", dst_side="t")
    d.rel(worker, mail, "Envia confirmação por", "SMTP", step=7, src_side="l", dst_side="r")
    return d


def deployment():
    d = C4Diagram("deployment", f"{SYS} - Produção")
    d.node(40, 120, 380, 250, "Navegador do cliente", "Web browser")
    spa = d.container_instance(110, 190, "Aplicação Web", "TypeScript, SPA", "Executa no navegador")
    d.node(640, 120, 1180, 800, "Região de nuvem", "Cloud region")
    lb = d.infra_node(880, 200, "Balanceador de carga", "Load balancer", "Distribui o tráfego HTTPS")
    d.node(700, 420, 480, 470, "Cluster de aplicação", "Orquestrador de contêineres")
    api = d.container_instance(870, 510, "API de Pedidos (x2 instâncias)", "Node.js", "Atende as requisições", w=260)
    wk = d.container_instance(870, 700, "Worker de Notificações", "Node.js", "Consome a fila", w=260)
    d.node(1340, 400, 440, 190, "Banco gerenciado", "PostgreSQL gerenciado")
    db = d.container_instance(1430, 470, "Banco de Pedidos", "PostgreSQL", "Dados transacionais", w=260, h=100)
    d.node(1340, 670, 440, 200, "Mensageria gerenciada", "Broker AMQP gerenciado")
    fila = d.container_instance(1430, 740, "Fila de Eventos", "AMQP", "Eventos de pedido", w=260, h=100)
    d.rel(spa, lb, "Envia requisições para", "HTTPS", src_side="r", dst_side="l")
    d.rel(lb, api, "Encaminha tráfego para", "HTTP", src_side="b", dst_side="t")
    d.rel(api, db, "Lê e grava em", "SQL/TCP", src_side="r", dst_side="l", src_at=(1, 0.5), dst_at=(0, 0.5),
          via=[(1250, 565), (1250, 520)])
    d.rel(api, fila, "Publica em", "AMQP", asynchronous=True, src_side="b", dst_side="t",
          src_at=(0.9, 1), dst_at=(0.73, 0), via=[(1104, 630), (1620, 630)])
    d.rel(fila, wk, "Entrega eventos a", "AMQP", asynchronous=True, src_side="l", dst_side="r",
          src_at=(0, 0.85), dst_at=(1, 0.85), via=[(1280, 825), (1280, 794)])
    return d


for name, fn in [("c4-1-system-context", context), ("c4-2-container", containers),
                 ("c4-3-component", components), ("c4-dynamic-fazer-pedido", dynamic),
                 ("c4-deployment-producao", deployment)]:
    print(fn().save(out / f"{name}.drawio"))

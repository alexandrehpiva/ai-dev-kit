"""Exemplo executável: aplicação web genérica com CDN, API, fila e banco.
Gera `example_architecture.drawio` ao lado deste script. Todos os nomes são
fictícios; substitua pelos componentes confirmados no código/IaC (ver
`verify-against-reality.md`).

    python3 example_architecture.py [saida.drawio]
"""
import sys
from pathlib import Path

from drawio_arch_lib import (Diagram, add_actor, add_edge, add_external, add_group,
                             add_legend, add_notes, add_service, add_title)

out = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("example_architecture.drawio"))
d = Diagram("Arquitetura - app web", width=1700, height=950)

add_title(d, 40, 20, "App Web — arquitetura na nuvem", "Visão de componentes e fluxos principais")
add_legend(d, 1240, 4, [("main", "Fluxo síncrono (requisição/resposta)", False),
                         ("pink", "Fluxo assíncrono (evento/fila)", True)])

user = add_actor(d, 50, 208, "Usuário")

add_group(d, 150, 120, 1500, 630, "Nuvem", "cloud")
add_group(d, 190, 160, 560, 540, "Borda e entrada", "dashed")
add_group(d, 790, 160, 820, 540, "Aplicação", "network")

dns = add_service(d, 230, 200, "DNS", "Resolução do domínio", "route_53", "network")
cdn = add_service(d, 230, 330, "CDN", "Cache e TLS", "cloudfront", "network")
site = add_service(d, 230, 460, "Arquivos estáticos", "Front-end publicado", "s3", "storage")
waf = add_service(d, 230, 590, "Firewall de aplicação", "Regras de proteção", "waf", "security")

api = add_service(d, 830, 200, "API", "Roteia as requisições", "api_gateway", "integration")
fn = add_service(d, 830, 360, "Função de negócio", "Processa o pedido", "lambda", "compute")
queue = add_service(d, 1210, 360, "Fila", "Eventos de pedido", "sqs", "integration")
worker = add_service(d, 1210, 520, "Worker", "Consome a fila", "lambda", "compute")
db = add_service(d, 830, 520, "Banco relacional", "Dados transacionais", "rds", "database")
secrets = add_service(d, 1210, 200, "Segredos", "Credenciais da aplicação", "secrets_manager", "security")

ext = add_external(d, 1180, 790, "Provedor de pagamento", "API externa de cobrança", "purple", w=300)

add_edge(d, user, "r", dns, "l", "DNS", 1, "main")
add_edge(d, dns, "b", cdn, "t", "Aponta para a CDN", 2, "main")
add_edge(d, cdn, "b", site, "t", "Serve estáticos", 3, "main")
add_edge(d, waf, "t", site, "b", "Filtra", None, "red")
add_edge(d, cdn, "r", api, "l", "Chama a API", 4, "blue", via=[(770, 366), (770, 236)])
add_edge(d, api, "b", fn, "t", "Invoca", 5, "orange")
add_edge(d, fn, "b", db, "t", "Grava", 6, "orange")
add_edge(d, fn, "r", queue, "l", "Publica evento", 7, "pink", asynchronous=True)
add_edge(d, queue, "b", worker, "t", "Entrega", 8, "pink", asynchronous=True)
add_edge(d, secrets, "b", queue, "t", "Lê credenciais", None, "red")
add_edge(d, worker, "b", ext, "t", "Cobra", 9, "purple")

add_notes(d, 40, 790, [
    ("Fluxo de pedido", ["O front-end é servido pela CDN.", "A API valida e aciona a função."]),
    ("Assíncrono", ["Eventos vão para a fila.", "O worker reprocessa em caso de falha."]),
    ("Segurança", ["Credenciais ficam no cofre de segredos.", "O firewall protege a entrada."]),
], col_w=340, h=110)

print(d.save(out))

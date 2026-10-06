"""Exemplo executável do motor .drawio (também serve de teste de fumaça da lib).

Uso: python3 example_drawio.py [pasta-de-saída]   (padrão: pasta atual)
Gera `example-order-flow.drawio`. Fluxo fictício de pedido, só para mostrar o vocabulário:
raias, tarefa, gateway exclusivo com saídas rotuladas, evento de mensagem (assíncrono),
objeto de dado, repositório e os três status.
"""
import os
import sys

from drawio_bpmn_lib import (Diagram, add_data_object, add_data_store, add_edge,
                             add_event, add_gateway, add_lanes, add_task)

out = sys.argv[1] if len(sys.argv) > 1 else "."
dia = Diagram("Fluxo de pedido (exemplo)")

# 1) raias primeiro; 2) colunas (x) depois; 3) cada nó é posto na raia certa
lanes = add_lanes(dia, 20, 20, 1180, [("Cliente", 140), ("Aplicação", 260), ("Serviço de pagamento", 140)])
col = [260, 450, 640, 830, 1020]
cliente, app, pagto = lanes["Cliente"][2], lanes["Aplicação"][2], lanes["Serviço de pagamento"][2]

inicio = add_event(dia, col[0], cliente, "start", "Pedido iniciado")
enviar = add_task(dia, col[1], cliente, "Envia o pedido", "Carrinho + endereço")
validar = add_task(dia, col[1], app, "Valida o pedido", "Itens e estoque", status="confirmado")
gw = add_gateway(dia, col[2], app, "x")
cobrar = add_task(dia, col[3], app, "Solicita a cobrança")
retorno = add_event(dia, col[3], pagto, "intermediate", "Resultado do pagamento")
notificar = add_task(dia, col[4], app, "Notifica o cliente", "Reenvio não implementado", status="gap")
fim_ok = add_event(dia, col[4] + 125, app, "end", "Fim: pedido pago")
fim_rej = add_event(dia, col[2] + 80, app - 105, "end", "Fim: pedido rejeitado")
carrinho = add_data_object(dia, col[1] - 135, app, "Carrinho")
base = add_data_store(dia, col[2], app + 100, "Pedidos (BD)")

add_edge(dia, inicio, "r", enviar, "l")
add_edge(dia, enviar, "b", validar, "t")
add_edge(dia, validar, "r", gw, "l")
add_edge(dia, gw, "r", cobrar, "l", label="itens válidos")
add_edge(dia, gw, "t", fim_rej, "l", label="itens inválidos")
add_edge(dia, cobrar, "b", retorno, "t", kind="message", label="assíncrono")
add_edge(dia, retorno, "r", notificar, "b", kind="message")
add_edge(dia, notificar, "r", fim_ok, "l")
add_edge(dia, carrinho, "r", validar, "l", kind="association")
add_edge(dia, validar, "b", base, "l", kind="association")

print(dia.save(os.path.join(out, "example-order-flow.drawio")))

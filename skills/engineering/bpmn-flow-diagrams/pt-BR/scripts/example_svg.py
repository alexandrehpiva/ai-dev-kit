"""Exemplo executável do motor SVG (também serve de teste de fumaça da lib).

Uso: python3 example_svg.py [pasta-de-saída]   (padrão: pasta atual)
Gera `example-order-flow.svg` com o mesmo fluxo fictício do example_drawio.py. Aqui as
setas são polilinhas calculadas à mão a partir das âncoras que cada `add_*` devolve.
"""
import os
import sys

from svg_bpmn_lib import (Canvas, add_arrow, add_data_object, add_data_store, add_event,
                          add_gateway, add_pool, add_task)

out = sys.argv[1] if len(sys.argv) > 1 else "."
cv = Canvas(1220, 620, "Fluxo de pedido (exemplo)")

lanes = add_pool(cv, 20, 50, 1180, [("cli", "Cliente", 140), ("app", "Aplicação", 260), ("pay", "Serviço de pagamento", 140)])
col = [260, 450, 640, 830, 1020]
cli, app, pay = lanes["cli"][2], lanes["app"][2], lanes["pay"][2]

inicio = add_event(cv, col[0], cli, "start", "Pedido iniciado")
enviar = add_task(cv, col[1], cli, "Envia o pedido", "Carrinho + endereço")
validar = add_task(cv, col[1], app, "Valida o pedido", "Itens e estoque", status="confirmado")
gw = add_gateway(cv, col[2], app, "x")
cobrar = add_task(cv, col[3], app, "Solicita a cobrança")
retorno = add_event(cv, col[3], pay, "intermediate", "Resultado do pagamento")
notificar = add_task(cv, col[4], app, "Notifica o cliente", "Reenvio não implementado", status="gap")
fim_ok = add_event(cv, col[4] + 125, app, "end", "Fim: pedido pago")
fim_rej = add_event(cv, col[2] + 80, app - 105, "end", "Fim: pedido rejeitado")
carrinho = add_data_object(cv, col[1] - 135, app, "Carrinho")
base = add_data_store(cv, col[2], app + 100, "Pedidos (BD)")

add_arrow(cv, [inicio["r"], enviar["l"]])
add_arrow(cv, [enviar["b"], validar["t"]])
add_arrow(cv, [validar["r"], gw["l"]])
add_arrow(cv, [gw["r"], cobrar["l"]], label="itens válidos")
add_arrow(cv, [gw["t"], (gw["t"][0], fim_rej["c"][1]), fim_rej["l"]], label="itens inválidos")
add_arrow(cv, [cobrar["b"], retorno["t"]], kind="message", label="assíncrono")
add_arrow(cv, [retorno["r"], (notificar["b"][0], retorno["r"][1]), notificar["b"]], kind="message")
add_arrow(cv, [notificar["r"], fim_ok["l"]])
add_arrow(cv, [carrinho["r"], validar["l"]], kind="association")
add_arrow(cv, [validar["b"], (validar["b"][0], base["c"][1]), base["l"]], kind="association")

print(cv.save(os.path.join(out, "example-order-flow.svg")))

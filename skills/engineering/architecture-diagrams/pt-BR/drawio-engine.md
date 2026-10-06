# Motor `.drawio` com ícones `mxgraph.aws4`

## Diagnóstico do modo de falha

- **Reinventar o XML a cada diagrama.** O agente escreve o `.drawio` à mão, erra o estilo do ícone (aparece uma caixa em branco), o id de uma seta (arquivo abre quebrado) ou o escape do texto (o rótulo mostra `<br>` literal) — e só descobre ao abrir.
- **Nome de ícone chutado.** `mxgraph.aws4.<nome>` com o nome errado renderiza um quadrado vazio, sem erro. É a variante "ícone invisível" do diagnóstico do `SKILL.md`.
- **Entregar sem renderizar.** O XML estar bem formado não prova que o layout está legível.

## O que usar

`scripts/drawio_arch_lib.py` (só biblioteca padrão do Python) implementa os padrões de `visual-patterns.md`. Não reescreva o script: importe-o. `scripts/example_architecture.py` é um exemplo executável completo e genérico; copie e substitua pelos componentes confirmados.

| Função | Para quê |
|---|---|
| `Diagram(name, width, height)` / `.save(path)` | Documento; `save` valida XML e ids das setas |
| `add_title(dia, x, y, titulo, subtitulo)` | Cabeçalho |
| `add_group(dia, x, y, w, h, rotulo, kind)` | `cloud`, `network` ou `dashed` (tracejado cinza; use também para "fora da nuvem") |
| `add_actor(dia, x, y, rotulo)` | Usuário/cliente de origem |
| `add_service(dia, x, y, titulo, desc, icon, category)` | Cartão com ícone oficial; `icon` é o nome depois de `mxgraph.aws4.`; `category` colore |
| `add_external(dia, x, y, titulo, funcao, color)` | Caixa pastel de sistema externo |
| `add_edge(dia, src, lado, dst, lado, label, step, theme, asynchronous, via)` | Seta numerada; lados `l r t b`; `via` = pontos intermediários |
| `add_legend(dia, x, y, [(tema, texto, assincrono)])` | Legenda |
| `add_notes(dia, x, y, [(titulo, [linhas])])` | Cartões de nota no rodapé |

Ordem de criação = empilhamento: grupos primeiro, cartões depois, setas por último. Para um ícone novo, use o nome da forma na biblioteca AWS do próprio draw.io (painel de formas; "Editar estilo" mostra o `resIcon`) e **confirme na imagem renderizada** que o glifo apareceu; ver `icon-selection.md` para ícones que a biblioteca não tem (outros provedores, marcas de terceiros).

## Passo a passo

1. Copie `example_architecture.py`, troque componentes, posições e setas. Grade de 40 px entre cartões, coluna de ~330 px, mantém tudo alinhado.
2. Rode `python3 meu_diagrama.py saida.drawio`.
3. Renderize para PNG e **leia a imagem**:

```bash
# macOS (o app do draw.io traz a CLI); em outros sistemas use o binário `drawio` do pacote
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 1 -o saida.png saida.drawio
```

Se a CLI do draw.io não existir, entregue só o `.drawio` e diga isso — o usuário abre no draw.io e não pode confiar em nada que você não viu renderizado.

4. Passe o portão do `SKILL.md`. Os defeitos mais comuns na primeira leitura: rótulo de seta sobre caixa (aumente o espaçamento ou use `via`), seta atravessando um cartão (use `via`), nota maior que o conteúdo (reduza `h`).
5. Entregue `.drawio` (fonte, versionável) + `.png` + a tabela de evidências.

## Estrutura no repositório

```
docs/diagrams/
  architecture.py        # fonte de verdade; a imagem é derivada
  architecture.drawio
  architecture.png
  README.md              # como regerar (comandos acima)
```

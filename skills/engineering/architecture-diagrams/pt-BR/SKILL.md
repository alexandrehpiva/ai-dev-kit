---
name: architecture-diagrams
description: Gera diagramas de arquitetura estilo docs oficiais de cloud (ícones reais, boxes, setas) para qualquer solução/projeto, via código (lib Python `diagrams` + Graphviz), com disciplina para evitar os três defeitos mais comuns — ícone errado/enganoso, ícone invisível, texto vazando da caixa — e para garantir que as conexões desenhadas batem com a arquitetura real. Usar quando o usuário pedir "desenho de arquitetura", "diagrama estilo AWS docs", "diagrama com ícones e setas", "desenha a arquitetura desse projeto", ou pedir para corrigir/ajustar um diagrama já gerado (ícones sumidos, texto cortado, seta errada/faltando).
---

# architecture-diagrams

**Princípio central:** um diagrama de arquitetura é uma afirmação técnica verificável — cada caixa e cada seta tem que corresponder a algo real no código/IaC, não a uma suposição de como "provavelmente" funciona. Ícone errado, ícone invisível ou seta que não existe de verdade são todos o mesmo tipo de erro: o diagrama mentiu.

## Diagnóstico do modo de falha

Gerado sem essa disciplina, o diagrama comete um destes erros, todos observados na prática:
- **Ícone enganoso**: usar o ícone de um serviço AWS (ex. Route53) para representar outro provedor (ex. Cloudflare) só porque "parece" DNS — o leitor lê a marca errada.
- **Ícone invisível**: ao perceber o erro acima, "corrigir" trocando por um placeholder sem nenhum ícone (`Blank`/genérico vazio) — troca uma mentira por uma caixa vazia, que o usuário reporta como "ícone faltando".
- **Texto vazando da caixa**: labels longos e descritivos direto no nó (ex. `"Lambda FastAPI+Mangum (container arm64, us-east-1)"`) estouram a largura do box.
- **Seta que não existe**: desenhar uma conexão lógica/assumida (ex. "frontend fala com backend através do CDN") sem checar o código — a integração real pode pular etapas que o diagrama mostra, ou usar um caminho completamente diferente (ex. SPA chamando a API diretamente, sem passar pelo CDN).

Cada um desses já aconteceu numa sessão real de geração de diagrama e só foi corrigido depois do usuário apontar visualmente o defeito — esta skill existe para pegar os quatro **antes** de entregar.

## Ferramenta

Use a lib Python [`diagrams`](https://github.com/mingrammer/diagrams) (ícones oficiais AWS/GCP/Azure/K8s/SaaS via Graphviz). Não crie/adote uma nova ferramenta (frontend+backend+MCP) para isso — `diagrams` cobre o caso de uso completo sem infra adicional. Ver `setup-and-workflow.md` para instalação isolada (venv) e estrutura do script/README de regeneração.

## Procedimento

1. **Levante a arquitetura real antes de desenhar.** Leia `verify-against-reality.md` — nunca desenhe uma conexão, domínio ou fluxo de dados por suposição; confirme no código/IaC/config.
2. **Inventarie componentes e agrupe em clusters lógicos** (ex.: frontend, auth, backend, CI/CD, custo) — um `Cluster` por fronteira de responsabilidade, não por serviço individual.
3. **Escolha o ícone certo para cada componente.** Leia `icon-selection.md` — a regra central é: ícone real e correto > ícone real mais próximo disponível (documentado como substituição) > nunca um placeholder sem ícone.
4. **Escreva labels curtos, mova detalhe para o título do cluster ou para a label da edge**, e ajuste espaçamento/fontsize. Leia `layout-and-labels.md`.
5. **Gere e revise visualmente** (leia o PNG gerado) antes de entregar — confira os três defeitos do diagnóstico acima e se cada seta ainda corresponde à arquitetura real.
6. **Entregue o PNG/SVG ao usuário** e pergunte se resolveu — trate feedback ("vazou", "sumiu", "falta uma conexão") como reabertura do passo relevante (3, 4 ou 1), não como retrabalho do zero.

## Portão de decisão — pronto para entregar?

Todos devem ser verdadeiros antes de mandar o diagrama:
- [ ] Nenhum nó usa ícone de marca errada (ex. ícone AWS para representar serviço de outro provedor)
- [ ] Nenhum nó usa placeholder sem ícone (`Blank` ou equivalente) — todo nó tem um glifo visível e honesto
- [ ] Nenhum label visualmente ultrapassa a borda do seu box/cluster (checado na imagem renderizada, não só no código)
- [ ] Toda seta desenhada corresponde a uma integração confirmada no código/IaC — não a uma suposição de "como deveria funcionar"
- [ ] O diagrama foi de fato lido (`Read` na imagem gerada) antes de ser enviado, não só "deveria estar certo"

## Assets

- `icon-selection.md` — como escolher/substituir ícone sem mentir nem deixar invisível
- `layout-and-labels.md` — tuning de espaçamento, fontsize e onde colocar texto longo
- `setup-and-workflow.md` — venv isolado, estrutura de script/README, comando de regeneração
- `verify-against-reality.md` — como confirmar conexões reais antes de desenhá-las

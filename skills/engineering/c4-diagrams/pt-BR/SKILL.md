---
name: c4-diagrams
description: Desenha diagramas C4 (contexto, contêineres, componentes, dinâmico, implantação) como `.drawio` editável com lib Python stdlib que aplica as regras de notação do c4model.com (título com escopo, legenda automática, tipo/descrição/tecnologia em cada elemento, seta rotulada e unidirecional) e recusa gravar diagrama que as viole. Usar ao pedir "diagrama C4", "diagrama de contexto", "diagrama de contêineres", "desenha a arquitetura em C4", "context/container/component diagram", ou ao revisar um diagrama C4 existente contra o checklist oficial.
license: Regras e citações de c4model.com (Simon Brown), CC BY 4.0, em `c4-notation.md`. Lib, tokens, exemplos e texto restante são autorais.
---

**Princípio central:** um diagrama C4 conta uma história de um nível de abstração para um público; cada caixa e cada seta é uma afirmação técnica confirmável, e o diagrama precisa se sustentar sem narrador (título, legenda, tipo, descrição e tecnologia visíveis).

## Diagnóstico do modo de falha

Sem disciplina, o agente produz diagramas que parecem C4 e violam o C4:
- **Níveis misturados:** componentes num diagrama de contexto, "contêiner" usado como sinônimo de Docker/pacote, um diagrama gigante que mistura tudo.
- **Seta decorativa:** "Usa" sem direção nem intenção, sem protocolo entre contêineres, ou conexão presumida que o código não tem.
- **Diagrama mudo:** sem título/escopo, sem legenda, sem tecnologia; a cor carrega sozinha o significado (falha em impressão P&B e daltonismo).
- **Texto sobre borda:** rótulo de seta que cobre caixa, legenda sobre o conteúdo, duas setas opostas que viram uma linha bidirecional. Só aparece ao renderizar.

## Procedimento

1. **Escolha o diagrama pela pergunta que ele responde**, não por completude. Leia `c4-notation.md` (obrigatório) para a tabela de diagramas, "recomendado?" e as definições de pessoa/sistema/contêiner/componente. Regra da fonte: contexto e contêineres bastam para a maioria dos times; componentes só se agregarem valor; código quase nunca.
2. **Levante os fatos antes de desenhar** no código/IaC/documentação e registre a fonte de cada seta. Seta não confirmada fica fora ou tracejada com a marca "não confirmado". Formato da tabela de evidências: `EVIDENCE-TABLE-FORMAT.md` da skill `architecture-diagrams` (soft).
3. **Fixe escopo e nível:** um sistema por diagrama de contexto/contêineres, um contêiner por diagrama de componentes, um ambiente por diagrama de implantação. Sistema grande: vários diagramas no mesmo nível, cada um com um foco.
4. **Escreva o script** com `scripts/c4_drawio_lib.py`; leia `engine.md` (obrigatório) para a API, os tokens visuais e as lições de layout. Parta de `scripts/example_c4.py`.
5. **Rode, renderize e leia a imagem** (comando em `engine.md`); passe o checklist de 21 perguntas de `c4-notation.md`. Ajuste layout e releia; não entregue o primeiro render sem leitura.
6. **Entregue** `.drawio` (fonte editável), `.png`, o script e a tabela de evidências.

## Portão — pronto para entregar?

Todas verdadeiras:
- [ ] O tipo e o escopo estão no título; há legenda.
- [ ] Todo elemento tem tipo, nome e descrição curta; contêiner/componente tem tecnologia.
- [ ] Toda seta é unidirecional, tem rótulo específico (não "Usa") e, entre contêineres, protocolo/tecnologia.
- [ ] Nenhum elemento de nível errado para o tipo de diagrama.
- [ ] Cada seta tem fonte confirmada ou está marcada "não confirmado".
- [ ] A imagem renderizada foi lida: nada de texto sobre borda, legenda fora do conteúdo, setas distinguíveis.

Se a lib recusar gravar (`lint()`), corrija a causa; não contorne a regra.

## Composição com outras skills

- Infraestrutura de nuvem com ícones de provedor: `architecture-diagrams`. Processo com raias e gateways: `bpmn-flow-diagrams` (o C4 não cobre processos de negócio nem fluxos de estado).
- Documento de arquitetura em seções (contexto, blocos, decisões): `architecture-docs`, que mapeia C4 para arc42.

## Assets

| Quando | Leia |
|---|---|
| Sempre, antes de escolher o diagrama | `c4-notation.md` |
| Antes de escrever o script | `engine.md` |
| Exemplos executáveis | `scripts/example_c4.py` e `scripts/examples/` (5 diagramas de um sistema fictício, `.drawio` + `.png`) |

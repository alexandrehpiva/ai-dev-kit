# Criar e manter o design system de um projeto

Quando o projeto ainda não tem um design system documentado mas existe uma referência real a espelhar (um app irmão, uma POC, um produto já em produção do mesmo cliente), criar esse documento é o que evita que cada rodada de trabalho redescubra os mesmos tokens de memória — e diverja um pouco mais a cada vez. Isso vale tanto para o primeiro protótipo quanto para qualquer trabalho de UI subsequente no mesmo projeto: o documento é a fonte de verdade entre sessões, não a lembrança do agente.

## Diagnóstico do modo de falha

Sem um design system escrito, o agente reconstrói a paleta/tipografia/espaçamento de memória a cada sessão — e memória de sessão não persiste entre conversas. O resultado: cor de acento um tom diferente, ícone de outro estilo visual, raio de borda que não bate, espaçamento "parecido" mas não igual. Nenhuma mudança isolada chama atenção; a divergência só fica óbvia quando alguém compara o protótipo lado a lado com a referência real — e a essa altura já se acumulou em vários componentes.

## Quando criar

- Existe uma referência real (app irmão, POC, produto em produção) mas nenhum arquivo captura os tokens dela ainda.
- O projeto vai ganhar um segundo protótipo/tela que precisa dos mesmos tokens do primeiro — sinal de que "lembrar de cabeça" não escala.

Se não existe nenhuma referência real (o design é original, sem produto irmão para espelhar), não force um design system prematuro — as escolhas de paleta/tipo/layout desta skill (ver [`aesthetic-direction.md`](aesthetic-direction.md)) resolvem esse caso; o design system nasce quando o *próprio* protótipo vira a referência para telas futuras dele mesmo.

## Como extrair os tokens da referência real

Não invente valor. Todo token do design system vem de uma fonte inspecionável:
- Código-fonte da referência (CSS/tokens/tema, componentes compartilhados) quando acessível.
- Inspeção visual direta (DevTools do browser, extração de cor de screenshot) quando só há o produto rodando, sem acesso ao código.
- Documentação de marca formal, se existir.

Registre a fonte de cada bloco de token (ex.: "extraído de `client/src/index.css` do repo X" ou "inspecionado via DevTools em <url> em <data>") — isso importa quando a referência mudar e for preciso saber o que re-sincronizar.

## Estrutura do documento

Salve como `design-system.md` (ou `DESIGN-SYSTEM.md`) na raiz do projeto ou em `docs/`. Seções mínimas:

```markdown
# Design System — <nome do projeto>

Fonte: <referência real espelhada + como os tokens foram extraídos>

## Tokens de cor
| Token | Valor | Uso |
|---|---|---|
| --color-primary | #... | ... |

## Tipografia
Família, pesos, escala (display/corpo/dado), line-height por família.

## Espaçamento e raio
Escala de espaçamento (ex.: 4/8/12/16/24/32px) e raios de borda por categoria de componente (botão vs. card vs. input).

## Componentes
Um bloco por componente reutilizável: estados (default/hover/active/disabled), variantes, e onde ele é definido (arquivo/seletor) se o projeto já foi dividido (ver `split-into-files.md`).

## Efeitos
Sombras, transições, easings — só o que é reusado por mais de um componente.
```

Ajuste as seções ao que a referência real de fato define — não preencha uma seção que a referência não tem conteúdo para sustentar.

## Manutenção

- Componente ou token novo, que ainda não existe no design system do projeto: documentar **nele primeiro**, com o valor real (extraído da referência, nunca inventado), e só então usar o componente nas telas — esta é a mesma regra do corpo do `SKILL.md`, repetida aqui porque é o ponto onde a disciplina mais costuma falhar (parece mais rápido só usar o valor direto no CSS da tela).
- Se a referência real mudar (nova versão do app irmão, novo componente na POC), re-sincronizar o token/componente afetado e anotar a mudança — não deixar o design system do projeto congelado numa versão antiga da referência sem sinalizar a defasagem.

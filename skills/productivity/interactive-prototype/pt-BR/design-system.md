# Criar e manter o design system de um projeto

Quando o projeto ainda não tem um design system documentado mas existe uma referência real a espelhar (um app irmão, uma POC, um produto já em produção do mesmo cliente), criar esse documento é o que evita que cada rodada de trabalho redescubra os mesmos tokens de memória — e diverja um pouco mais a cada vez. Isso vale tanto para o primeiro protótipo quanto para qualquer trabalho de UI subsequente no mesmo projeto: o documento é a fonte de verdade entre sessões, não a lembrança do agente.

## Diagnóstico do modo de falha

Sem um design system escrito, o agente reconstrói a paleta/tipografia/espaçamento de memória a cada sessão — e memória de sessão não persiste entre conversas. O resultado: cor de acento um tom diferente, ícone de outro estilo visual, raio de borda que não bate, espaçamento "parecido" mas não igual. Nenhuma mudança isolada chama atenção; a divergência só fica óbvia quando alguém compara o protótipo lado a lado com a referência real — e a essa altura já se acumulou em vários componentes.

## Quando criar

- **Protótipo novo:** o design system **nasce junto** com o protótipo — o scaffold ([`scaffold-new-prototype.md`](scaffold-new-prototype.md)) já entrega `styles/tokens.css` e `docs/design-system.md` com a estrutura completa e valores `PLACEHOLDER`; a direção visual aprovada substitui os placeholders **nos dois arquivos na mesma rodada**.
- **Existe referência real** (app irmão, POC, produto em produção) mas nenhum arquivo captura os tokens dela: extrair (seção abaixo) e preencher.
- **Projeto sem referência real:** o design é original; os valores vêm das escolhas de [`aesthetic-direction.md`](aesthetic-direction.md) e o próprio protótipo passa a ser a referência das telas seguintes.

## Como extrair os tokens da referência real

Não invente valor. Todo token do design system vem de uma fonte inspecionável:
- Código-fonte da referência (CSS/tokens/tema, componentes compartilhados) quando acessível.
- Inspeção visual direta (DevTools do browser, extração de cor de screenshot) quando só há o produto rodando, sem acesso ao código.
- Documentação de marca formal, se existir.

Registre a fonte de cada bloco de token (ex.: "extraído de `client/src/index.css` do repo X" ou "inspecionado via DevTools em <url> em <data>") — isso importa quando a referência mudar e for preciso saber o que re-sincronizar.

## Estrutura do documento

Fica em `docs/design-system.md` (modelo completo em `templates/design-system.md`). Seções: **1 Filosofia** · **2 Cores** (tabela token/valor/uso/contraste) · **3 Tipografia** · **4 Espaçamento, raio e sombra** · **5 Componentes** (prefixo de classe, onde é definido, estados) · **6 Animações** · **7 Responsividade obrigatória** (375/768/1280 px) · **8 Como manter**. Ajuste ao que o projeto realmente define; não preencha seção sem conteúdo real.

Regras da estrutura:
- **Sincronia tokens ↔ documento:** `styles/tokens.css` e a tabela de cores/tipografia/escala andam juntos; valor mudou num, muda no outro na mesma rodada.
- **Prefixo de classe** por projeto (`@@PREFIX@@-` no template → ex. `abc-btn-primary`) para componentes de produto; utilitários estruturais sem prefixo.
- **Camadas de CSS:** tokens → base → components → layout → responsive (um arquivo por camada, `@media` só em `responsive.css`).
- **Catálogo de componentes:** cada componente lista variantes, estados (hover, foco, desabilitado, erro, carregando) e arquivo de origem. Componente de domínio (usado em uma tela só) fica colocated; reutilizado em ≥2 telas sobe para `components.css` e entra no catálogo.

## Manutenção

- Componente ou token novo, que ainda não existe no design system do projeto: documentar **nele primeiro**, com o valor real (extraído da referência, nunca inventado), e só então usar o componente nas telas — esta é a mesma regra do corpo do `SKILL.md`, repetida aqui porque é o ponto onde a disciplina mais costuma falhar (parece mais rápido só usar o valor direto no CSS da tela).
- Se a referência real mudar (nova versão do app irmão, novo componente na POC), re-sincronizar o token/componente afetado e anotar a mudança — não deixar o design system do projeto congelado numa versão antiga da referência sem sinalizar a defasagem.
- **Auditoria cruzada ao fim de cada rodada que mexeu em estilo:** todo token de `tokens.css` está documentado e todo token documentado existe em `tokens.css`; nenhuma cor/espaçamento literal em tela ou componente. Em modo grupo, essa auditoria também cobre mudanças vindas de outras pessoas (ver [`group-mode.md`](group-mode.md)).

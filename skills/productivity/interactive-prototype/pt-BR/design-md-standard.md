# DESIGN.md como padrão de referência visual (awesome-design-md)

Ler quando o usuário cita uma marca, produto ou "estilo X" como referência, quando falta design system e uma referência de mercado ajudaria a fundamentá-lo, ou ao montar/atualizar `docs/design-system.md` e `styles/tokens.css` de um protótipo novo.

> Fonte: https://github.com/VoltAgent/awesome-design-md (MIT; conceito de DESIGN.md atribuído no README ao Google Stitch). Esta skill **referencia** o repositório e não copia arquivos dele.

## Diagnóstico do modo de falha

Sem uma referência estruturada, o agente "descreve de memória" o estilo de uma marca (ou de "um SaaS moderno"): cores aproximadas, fonte errada, espaçamento inventado, e o protótipo sai com cara de template. Com a referência decorada de uma sessão passada, o oposto: usa valores que a marca já mudou. Um DESIGN.md é o remédio: um arquivo de texto com cores, tipografia, componentes, espaçamento, elevação, regras e responsividade que o agente consegue seguir sem adivinhar. A regra é buscá-lo **na hora**, nunca de memória.

## O que o repositório é (conferido em 2026-10-28; reconferir ao usar)

- Coleção curada de arquivos `DESIGN.md`, um por marca, agrupados por categoria (IA, ferramentas de desenvolvimento, backend/DevOps, produtividade/SaaS, design, fintech, e-commerce, mídia, automotivo e retrô). Cada entrada aponta para `getdesign.md/<marca>/design-md`.
- Formato de cada arquivo (9 seções): 1 Visual Theme & Atmosphere · 2 Color Palette & Roles · 3 Typography Rules · 4 Component Stylings · 5 Layout Principles · 6 Depth & Elevation · 7 Do's and Don'ts · 8 Responsive Behavior · 9 Agent Prompt Guide. Cada marca traz também `preview.html` e `preview-dark.html` (catálogo visual de cores, tipos, botões e cards).
- Há uma página para **pedir** o DESIGN.md de um site que não está na lista.
- O README declara que os tokens são valores CSS publicamente visíveis, que o material é "as is" e que o projeto não reivindica a identidade visual de ninguém.
- **Não confirmado:** CLI, link raw estável e processo de atualização. Não assumir nenhum; abrir a página da marca e ler o que ela oferece.

## Fluxo

1. **Buscar na hora.** Abrir o README (ou `getdesign.md/<marca>/design-md`) com a ferramenta de web/browser; achar a marca; ler o DESIGN.md e o `preview.html`. O catálogo muda: o que ele tem hoje vale mais do que esta lista. Se a marca não está lá, usar [`design-research.md`](design-research.md) (ou o pedido de DESIGN.md do site, se o usuário quiser esperar).
2. **Registrar a fonte** onde o valor for usado: URL, data de acesso e, se aparecer, a versão ou data do arquivo. Sem isso o valor é palpite.
3. **Confirmar a intenção com o usuário** em uma pergunta curta se houver dúvida: "usar o estilo X como **base** (tokens e estrutura) ou só como **inspiração** (princípios)?". Padrão sem resposta: inspiração.
4. **Mapear para o projeto**, sem importar identidade alheia:

| DESIGN.md | Vai para |
|---|---|
| 1 Atmosfera, 5 Layout, 6 Elevação | `docs/design-system.md` §1 Filosofia e §4 Espaçamento/raio/sombra |
| 2 Cores e papéis | `styles/tokens.css` + tabela de cores (§2), com contraste conferido |
| 3 Tipografia | §3 e `tokens.css` (se a fonte for proprietária, escolher substituta e dizer isso) |
| 4 Componentes | §5 Componentes e `components.css`, com os estados |
| 7 Do's and Don'ts | regras do design system do projeto |
| 8 Responsivo | §7 (375/768/1280 px) |
| 9 Agent Prompt Guide | fica como consulta; não entra no produto |

5. **Embelezar com a skill:** o DESIGN.md dá a base; as regras de [`aesthetic-direction.md`](aesthetic-direction.md) (evitar os defaults de IA, um momento memorável, tipografia deliberada) e [`ux-ui-principles.md`](ux-ui-principles.md) decidem o que fica de fora, o que se adapta ao produto e o acabamento. Copiar uma marca inteira é o oposto de direção autoral.
6. **Pontos de atenção:**
   - Protótipo de **cliente**: não replicar logotipo, nome, imagens nem a identidade reconhecível de uma terceira marca; usar a referência para estrutura, ritmo e princípios. Se o cliente pediu "igual ao X", dizer isso ao usuário e deixar a decisão com ele.
   - Marca do próprio cliente ou design system existente do projeto **vencem** qualquer DESIGN.md (ver "Projeto com design system versionado" no `SKILL.md`).
   - Fontes e imagens têm licença própria: não embutir arquivo de fonte ou imagem de terceiro sem checar a licença.
7. **Atualização:** quando o usuário pedir "atualiza o estilo" ou a referência parecer ter mudado, repetir o passo 1 e anotar a diferença no design system (mesma regra de re-sincronização de [`design-system.md`](design-system.md)).

## DESIGN.md do próprio projeto (opcional)

O arquivo canônico do projeto continua sendo `docs/design-system.md`. Se o time usa agentes que leem `DESIGN.md` na raiz, **propor** (com confirmação, como toda documentação nova) um `DESIGN.md` gerado a partir do design system, nas 9 seções acima, em vez de manter dois documentos divergentes: um é gerado do outro, nunca editado em paralelo.

## Verificação

- [ ] Cada token vindo de DESIGN.md tem URL e data de acesso registradas.
- [ ] Nenhum valor foi escrito de memória sobre a marca.
- [ ] A intenção (base ou inspiração) foi dita ao usuário.
- [ ] Nada de identidade de terceiro no protótipo de cliente sem decisão do usuário.
- [ ] Contraste e responsividade conferidos depois da adaptação ([`UX-REVIEW.md`](UX-REVIEW.md)).

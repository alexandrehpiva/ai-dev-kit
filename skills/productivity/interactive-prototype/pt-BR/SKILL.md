---
name: interactive-prototype
description: Cria e evolui protótipos navegáveis em HTML/CSS/JS: gera o repositório completo (scaffold com estrutura em camadas, build para arquivo único, hot reload, design system, README, badge/changelog, jornadas), com direção estética distintiva, fundamentos de UX/UI, versionamento aprovado antes do commit, documentação e PDF de jornadas e modo opcional de trabalho em grupo. Usar quando o usuário pedir "criar protótipo novo", "repositório do protótipo", "protótipo navegável", criar/editar/redesenhar tela, fluxo ou landing page; "direção visual", "isso parece genérico"; "design system"; "subir/servir o protótipo"; "versionar/commitar o protótipo"; "jornadas de usuário", "PDF das jornadas"; "isso está responsivo?"; "modo grupo", "sincronizar o protótipo".
license: Apache License 2.0 (ver LICENSE.txt) para aesthetic-direction.md, adaptado de anthropics/skills (skills/frontend-design); explore-directions.md adaptado de "HTML Mockup Sketcher" (Nous Research); demais conteúdo e assets de autoria de Alexandre Piva.
---

# Interactive Prototype

**Princípio:** um protótipo navegável é produto de processo, não de inspiração — direção visual deliberada, design system como fonte de verdade, cada estado e cada largura de tela verificados, e histórico (versão, changelog, jornadas) que só afirma o que de fato foi entregue.

## Roteamento — leia o asset antes de agir

| Se o pedido envolve… | Ler |
|---|---|
| Direção visual ainda indefinida / "compare opções" / "esboça umas telas" | [`explore-directions.md`](explore-directions.md) |
| Criar ou redesenhar UI (paleta, tipo, layout, hero, copy) | [`aesthetic-direction.md`](aesthetic-direction.md) |
| UX, estados, formulários, responsividade, acessibilidade, acabamento | [`ux-ui-principles.md`](ux-ui-principles.md) |
| **Criar um protótipo/repositório novo** | [`scaffold-new-prototype.md`](scaffold-new-prototype.md) — obrigatório; roda `scripts/scaffold.py` |
| Criar tela/fluxo/campo/componente, mexer em `js/` | [`app-architecture.md`](app-architecture.md) |
| Criar/manter o design system do projeto | [`design-system.md`](design-system.md) |
| Estrutura de pastas, ou migrar um single-file | [`split-into-files.md`](split-into-files.md) |
| "Subir"/"servir"/"rodar" com hot reload | [`dev-server-hot-reload.md`](dev-server-hot-reload.md) |
| Commit, versão, badge, changelog, artefato exportado, link de preview | [`versioning-and-changelog.md`](versioning-and-changelog.md) |
| Mudança de navegação/sequência entre telas | [`user-journey-docs.md`](user-journey-docs.md) |
| PDF das jornadas | [`JOURNEY-PDF-STYLE.md`](JOURNEY-PDF-STYLE.md) + [`journeys-to-pdf.py`](journeys-to-pdf.py) |
| `prototype.config.json` com `groupMode: true`, ou pedido de sincronizar/trabalhar em grupo | [`group-mode.md`](group-mode.md) — obrigatório antes de qualquer commit |
| Antes de entregar qualquer rodada | [`UX-REVIEW.md`](UX-REVIEW.md) |

Pedido típico de ajuste numa tela já existente: design system do projeto → `aesthetic-direction.md`/`ux-ui-principles.md` conforme o tema → implementar nos arquivos-fonte → rebuild → `UX-REVIEW.md` → changelog `Pendente` → relatório e aguardar aprovação de commit.

## Projeto com design system versionado — consultar antes de mudar

Se o projeto já tem um design system próprio documentado (ex.: um `design-system.md`/`DESIGN-SYSTEM.md` na raiz ou em `docs/`, um arquivo de tokens, um Storybook) — ou já tem uma referência real a espelhar, como um app irmão/POC/produto em produção do mesmo cliente — **esse material é a fonte de verdade para esse projeto e vem antes das diretrizes genéricas desta skill**, não depois. Modo de falha que isso evita: sem essa disciplina, o agente aplica os princípios gerais de "direção estética distinta" desta skill como se estivesse desenhando do zero, e diverge silenciosamente de decisões de marca/token já tomadas — cor levemente diferente, ícone de outro estilo, raio de borda diferente, cada mudança um pouco mais longe do padrão real, sem que ninguém perceba até comparar lado a lado.

Procedimento:
1. Antes de qualquer mudança visual, procurar e ler o design system do projeto (se existir) e/ou a referência real a espelhar.
2. Tratar tokens, componentes e convenções documentados ali como restrições, não como sugestões — a criatividade desta skill se aplica onde o design system do projeto deixa espaço livre, não para reinventar o que já está definido.
3. Se for preciso um componente ou token que ainda não existe no design system do projeto: adicionar/documentar **nele primeiro**, com o valor real (extraído da referência, não inventado), e só então usar o componente nas telas.
4. Se o design system do projeto não existir ainda mas há uma referência real (outro app do mesmo produto, uma POC, um design em produção): ver [`design-system.md`](design-system.md) para como extrair os tokens e estruturar o documento antes de prosseguir com mudanças maiores.

## Pedido cria/altera/apaga jornada(s) de usuário — sincronizar documentação (opcional)

Quando o pedido adiciona uma tela/etapa a uma sequência existente, remove uma, muda a ordem/ramificação de navegação entre telas, ou cria um fluxo multi-tela inteiramente novo — não para mudanças visuais dentro de uma única tela —, trate a documentação de jornadas como parte do trabalho, não como opcional silencioso. Vale tanto quando esta skill é acionada manualmente quanto quando um agente a aciona de forma dinâmica/automática: em ambos os casos, sem exceção, peça confirmação ao usuário antes de criar documentação nova (alterar documentação já existente segue a mesma régua — confirmar antes). Ver [`user-journey-docs.md`](user-journey-docs.md) para onde procurar documentação de jornadas já existente (repo atual, repo irmão de e2e, gerenciador de tarefas/wiki com pista explícita) e para a estrutura padrão a propor quando não existir. Quando o pedido for gerar ou atualizar o **PDF das jornadas**, seguir a seção "Compilar jornadas em PDF" desse arquivo: o estilo canônico está em [`JOURNEY-PDF-STYLE.md`](JOURNEY-PDF-STYLE.md) e o gerador pronto em [`journeys-to-pdf.py`](journeys-to-pdf.py) — ler o estilo e usar o script antes de escrever qualquer HTML, sem imitar PDF antigo do projeto.

## Modo trabalho em grupo (opcional, ligado por configuração no repositório)

No início de toda rodada que possa terminar em commit, verifique se existe `prototype.config.json` na raiz do protótipo com `"groupMode": true`. Se sim, leia [`group-mode.md`](group-mode.md) antes de commitar: depois de cada commit aprovado a sincronização com o time é obrigatória (buscar novidades **antes** de numerar a versão, integrar, conferir versões, reconstruir, enviar). Conflito que muda o que o cliente final vê ou faz — telas, ordem, textos, botões, cores — vai ao usuário via `grill-me` **em linguagem de produto, sem jargão de versionamento** e com print quando for visual; o que é burocracia (changelog, número de versão, `dist/`) o agente resolve e relata. Sem sincronização possível: sem número de versão novo e sem artefato publicado.

## Estrutura padrão de protótipo — sempre dividido em arquivos, gerado por script

Todo protótipo novo nasce do scaffold ([`scaffold-new-prototype.md`](scaffold-new-prototype.md)), nunca montado de memória: `index.html` + `styles/` + `js/` + `build.py` + `docs/design-system.md` + README + `.claude/launch.json` + `.gitignore` + `prototype.config.json`. Sem fase "single-file primeiro". `dist/` é gerado pelo `build.py` (stdlib) e **ignorado no git**. Árvore e princípios de divisão: [`split-into-files.md`](split-into-files.md).

## Regras que não se negociam

- **Nunca numerar versão nem commitar sem aprovação explícita do usuário** — trabalho em andamento vive na entrada `Pendente (não commitado)` do changelog ([`versioning-and-changelog.md`](versioning-and-changelog.md)).
- **Nunca editar `dist/index.html` à mão** — toda mudança entra pelos arquivos-fonte e passa pelo build.
- **Nunca declarar pronto sem renderizar** — [`UX-REVIEW.md`](UX-REVIEW.md) exige olhar as larguras e os estados de verdade; o que não pôde ser verificado é dito como tal.
- **Documentação nova (jornadas, design system) só com confirmação do usuário.**
- **Em modo grupo, nunca numerar versão antes de sincronizar, nunca forçar envio e nunca decidir sozinho conflito de sequência de telas, texto ou regra visível.**

## Skills relacionadas

`grill-me` (decisões ambíguas de escopo/preview), `qa-e2e-testing` (testes e2e a partir das jornadas), `task-writing` (histórias a partir das jornadas).

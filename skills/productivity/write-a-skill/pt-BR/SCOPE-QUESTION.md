# Pergunta de escopo da skill nova

Contrato da pergunta que o agente faz no Passo 2 do `SKILL.md`, antes de criar qualquer arquivo de uma skill nova.

## Diagnóstico do modo de falha

- **O agente decide sozinho.** Cria a skill onde é mais conveniente para ele (geralmente local, no repositório aberto) e o usuário descobre depois que ela não aparece nos outros projetos — ou o contrário: publica no repositório público algo que era pessoal.
- **O agente pergunta sem contexto.** Uma pergunta seca ("oficial, custom ou local?") obriga o usuário a lembrar o que cada opção significa, o que é publicado, onde fica versionado e como se instala. Ele responde no automático, e a resposta automática é a errada com frequência.

A pergunta existe para que o usuário escolha **sabendo as consequências**, e com uma recomendação fundamentada para o caso concreto.

## O que a pergunta precisa ter

Todas estas condições devem ser verdadeiras:

1. **Uma linha sobre a skill** — o nome proposto e o que ela faz, para o usuário saber de qual skill se trata.
2. **As três opções, cada uma com o contexto** — o que é, quem enxerga, onde fica versionado, como é instalada/atualizada e quando costuma ser a escolha certa (bloco abaixo, adaptado ao caso).
3. **Recomendação explícita** com o porquê ligado a esta skill específica (ex.: "recomendo custom: usa um CLI que só existe na sua máquina, mas você vai querer em outros projetos").
4. **Alertas que mudam a decisão**, quando existirem: o conteúdo tem dado pessoal ou de cliente (pesa contra oficial); já existe skill oficial com o mesmo nome (a custom passaria a ter precedência na CLI); o repositório atual não tem pasta de skills (local criaria uma).
5. **Uma pergunta só, fácil de responder** — opções rotuladas (A/B/C ou equivalente da ferramenta de perguntas do harness), com a recomendada primeiro.

## Contexto de cada opção

<contexto-das-opcoes>
**Oficial no ai-dev-kit** — vai para `skills/<bucket>/<nome>/pt-BR/` no repositório do ai-dev-kit, que é **público**. Entra no histórico do git, é registrada no `AGENTS.md`, nos READMEs e no `CHANGELOG.md`, e incrementa a versão do kit. Qualquer pessoa que usa o kit pode instalá-la e recebe atualizações com `ai-dev-kit update`. Exige conteúdo genérico: nada pessoal, de cliente ou de projeto privado. Boa escolha quando a skill resolve um problema que qualquer dev teria.

**Custom no AIDK** — vai para `skills/custom/<nome>/` dentro do store do ai-dev-kit. Essa pasta é **ignorada pelo repositório público**: a skill não é publicada nem registrada nos READMEs/CHANGELOG. Continua instalável pela CLI em **qualquer projeto desta máquina** (`ai-dev-kit skills install --skills custom/<nome>`), via symlink, e uma edição vale para todos os projetos onde estiver instalada. Pode conter contexto pessoal (CLIs próprios, convenções suas). Boa escolha para utilitários pessoais reaproveitáveis ou para uma skill ainda imatura que talvez vire oficial depois.

**Local no repositório atual** — vai direto para a pasta de skills deste repositório (`.claude/skills/<nome>/` ou `.cursor/skills/<nome>/`), como arquivo comum. **Não** é gerenciada pela CLI: não existe em outros projetos, e é versionada (e compartilhada) junto com este repositório, por quem tiver acesso a ele. Boa escolha quando a skill só faz sentido aqui — regras do projeto, do time, do cliente.
</contexto-das-opcoes>

Adapte o texto ao caso: corte o que não muda a decisão e acrescente o que muda (ex.: "este repositório é compartilhado com o time do cliente", "você já tem 12 skills custom deste tipo"). Não invente fatos sobre o ambiente — verifique (`cat ~/.config/ai-dev-kit/config.json`, existência de `skills/custom/`, pastas de skills do repositório atual) antes de afirmar.

## Exemplo

<exemplo-de-pergunta>
Vou criar a skill `invoice-export` — gera o CSV mensal de notas a partir do CLI `nf-cli`. Onde ela deve ficar?

**A) Custom no AIDK (recomendado)** — fica em `skills/custom/invoice-export/` no seu ai-dev-kit, fora do repositório público. Você instala em qualquer projeto desta máquina com `ai-dev-kit skills install --skills custom/invoice-export`, e uma edição vale para todos. Recomendo porque depende do `nf-cli`, que só existe no seu ambiente, mas você comentou que usa isso em mais de um projeto.

**B) Oficial no ai-dev-kit** — fica em `skills/productivity/invoice-export/pt-BR/`, publicada no repositório público, registrada nos READMEs/CHANGELOG, com nova versão do kit. Exigiria tirar a dependência do `nf-cli` e qualquer dado seu.

**C) Local neste repositório** — fica em `.claude/skills/invoice-export/` só deste projeto, versionada com ele, sem passar pela CLI. Não aparece nos seus outros projetos.
</exemplo-de-pergunta>

## Quando não perguntar

- O usuário já disse o escopo de forma inequívoca no pedido.
- A tarefa é **alterar** uma skill existente: ela fica onde já está (para mudar de escopo, o usuário pede explicitamente — aí trate como promoção e faça a varredura de [`security-and-privacy.md`](security-and-privacy.md) se o destino for oficial).
- Sem resposta possível (execução sem usuário disponível): crie como **local** e diga isso no relatório final.

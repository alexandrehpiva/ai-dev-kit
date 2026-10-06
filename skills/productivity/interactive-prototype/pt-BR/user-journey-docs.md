# Documentação de jornadas de usuário

Guia de domínio para a feature descrita em `SKILL.md` → "Pedido cria/altera/apaga jornada(s) de usuário — sincronizar documentação". Cobre quando a feature dispara, onde procurar documentação existente, o que fazer com o que for encontrado (ou não), e a estrutura padrão a propor quando não existir nada.

## Modo de falha que isto evita

Sem essa disciplina, o agente implementa a mudança de fluxo no código e segue em frente — a documentação de jornadas (quando existe) fica desatualizada silenciosamente, e quando não existe, a oportunidade de registrar a jornada nova para apoiar QA/BDD futuro se perde. Meses depois, ninguém sabe se o comportamento documentado ainda é o real, ou não há registro nenhum do fluxo para basear um teste e2e.

## Quando disparar

Só quando o pedido envolve pelo menos um destes:
- adicionar uma tela/etapa a uma sequência existente;
- remover uma tela/etapa de uma sequência existente;
- mudar a ordem de navegação ou uma ramificação/condição entre telas;
- criar um fluxo multi-tela inteiramente novo.

Não dispara para mudança visual dentro de uma única tela (cor, copy, layout, componente) sem impacto em navegação/sequência.

Mesma regra independente de quem aciona: usuário manualmente ou um agente de forma dinâmica. Nos dois casos, criar documentação nova sempre exige confirmação explícita do usuário antes de escrever qualquer arquivo.

## Onde procurar documentação já existente

Busca em ordem, parando na primeira fonte com conteúdo relevante:

1. **Repositório atual** — pastas plausíveis: `docs/user-journeys/`, `docs/ux/`, `docs/qa/`, ou qualquer estrutura de documentação de fluxo já usada no projeto.
2. **Repositório irmão nomeado para e2e/QA** (ex.: `<produto>-e2e`, `<produto>-qa`) — barato de checar quando existe: mesmo diretório pai, nome previsível.
3. **Gerenciador de tarefas ou wiki do time (ex.: ClickUp, Jira, Confluence — via CLI ou MCP disponível no ambiente)** — só tentar quando houver uma pista explícita já no repositório (ex.: link para o gerenciador/wiki em README, comentário, ou arquivo de config) **ou** o usuário confirmar ao vivo que a documentação mora lá. Nunca consultar essas fontes de forma especulativa/cega.

## Classificando o que foi encontrado

- **Documentação de jornadas de fato** (mapeia telas/etapas/fluxo do usuário, mesmo que informal) → conta como "existe". Prosseguir para "Documentação já existe".
- **Documentação parcial ou não relacionada** (ex.: só tokens visuais, só backlog de bugs, só um design system sem fluxo) → conta como "**não existe**" para fins desta feature. Prosseguir para "Documentação não existe", mencionando o que já existe como contexto (não como substituto).

## Documentação já existe

Perguntar/confirmar com o usuário se deve atualizar essa documentação para refletir a mudança de jornada, antes de editar. Seguir o formato e a convenção já em uso nesse projeto — não impor a estrutura padrão abaixo por cima de um padrão já estabelecido.

## Documentação não existe

Perguntar/confirmar com o usuário se pode criar a documentação, propondo a estrutura padrão abaixo. Só criar arquivos após confirmação explícita.

### Estrutura padrão

```
docs/user-journeys/
  README.md                      ← índice: lista de jornadas, status, links
  <journey-slug>.md              ← uma jornada por arquivo
  _archived/
    <journey-slug>.md            ← jornadas removidas, nunca deletadas
```

Jornada removida nunca é apagada — mover o arquivo para `_archived/` preservando o conteúdo original, com uma nota no topo indicando data e motivo da arquivagem — princípio "nunca apagar, arquivar": documentação de produto removida continua sendo evidência de decisões passadas, e apagá-la elimina a única explicação de por que algo existiu. Isso preserva o histórico de raciocínio de por que a jornada existiu e por que saiu.

`README.md` mantém uma tabela simples: jornada, status (`active`/`archived`), link para o arquivo.

### Template por jornada (`<journey-slug>.md`)

O slug do arquivo segue o código da jornada, sem o prefixo de produto/área: `<persona>-j<nn>-<tipo>.md` (ex.: `cp-j00-fp.md`, `pf-j01-fp.md`, `pj-j02-fa01.md`). Jornadas de uma persona específica podem viver numa subpasta com o código da persona em minúsculas (`pf/`, `pj/`); jornadas na raiz pertencem à persona compartilhada.

```markdown
# [<PROD>-<ÁREA>-<PERSONA>-J00-FP] <Nome da jornada>

persona: <código da persona — ex.: CP | PF | PJ>
tipo: FP | FA<nn> | FE<nn>
status: active | archived
última atualização: <data>

## Objetivo
<o que o usuário tenta fazer, 1-2 frases>

## Ator(es)
<quem executa esta jornada — ex.: cliente pessoa física / sócio / procurador / administrador>

## Pré-condições
<estado necessário antes de começar>

## Etapas
| # | Tela/Rota | Ação do usuário | Sistema responde |
|---|-----------|------------------|-------------------|
| 1 | ...       | ...              | ...               |

## Fluxos alternativos / bifurcações
<condições que desviam do caminho principal, com referência cruzada ao código da jornada alternativa>

## Critérios de aceite (BDD)
**Cenário: <nome>**
Dado ...
Quando ...
Então ...

## Casos de erro / adversos
<o que quebra o fluxo e como o sistema deve reagir>

## Cobertura de testes
| Tipo | Status | Referência |
|------|--------|------------|
| e2e  | ...    | ...        |
| unit | ...    | ...        |

## Histórico de mudanças
| Data | Mudança | Motivo |
|------|---------|--------|
```

O formato de Critérios de aceite segue Given/When/Then (Dado/Quando/Então), consistente com o padrão de BDD já usado no restante do ecossistema de skills (`task-writing`, `qa-e2e-testing`). A seção "Cobertura de testes" existe para dar um ponto de partida rastreável à construção futura de testes e2e/unitários — não é obrigatório preenchê-la no momento da criação da jornada, mas o campo deve existir desde o início.

**Convenção de código de jornada:**
- Formato: `[<PROD>-<ÁREA>-<PERSONA>-J<nn>-<TIPO>]`, onde:
  - `<PROD>` = sigla curta do produto (ex.: `ACME`);
  - `<ÁREA>` = sigla do fluxo documentado (ex.: `ONB` para onboarding, `CHK` para checkout);
  - `<PERSONA>` = prefixo obrigatório de persona. As personas do projeto (código, rótulo, subpasta) ficam definidas no `README.md` de `docs/user-journeys/` e na config do PDF (ver `JOURNEY-PDF-STYLE.md`). Exemplo de um onboarding de conta brasileiro: `CP` (compartilhada PF+PJ), `PF` (pessoa física), `PJ` (pessoa jurídica);
  - `<TIPO>` = `FP` (fluxo principal), `FA<nn>` (fluxo alternativo) ou `FE<nn>` (fluxo de exceção).
- Exemplo: `[ACME-ONB-PJ-J00-FP]`, `[ACME-ONB-PF-J01-FA01]`, `[ACME-ONB-CP-J02-FE01]`.
- Ordem de exibição (índice e PDF) é a que o produto definir (ex.: PJ, PF e CP, com a numeração das jornadas começando em J00 e seguindo nessa ordem). Ao renumerar, registrar um de-para (código antigo → novo) no README e no histórico de cada jornada.

---

## Compilar jornadas em PDF

Quando o usuário pedir um PDF das jornadas (ex.: "gera um PDF das jornadas", "compila as jornadas para apresentação", "atualiza o `jornadas-usuario-<produto>.pdf`"), **antes de qualquer HTML**:

1. Ler [`JOURNEY-PDF-STYLE.md`](JOURNEY-PDF-STYLE.md): contrato completo de estilo (página, paleta, capa, sumário, cabeçalho, badges FP/FA/FE, ordem, regras de conteúdo, verificação).
2. Validar as `.md` de jornada contra o protótipo atual (telas, rótulos, numeração de etapas) e corrigir o que divergir; remover referências a código do texto.
3. Gerar com o script [`journeys-to-pdf.py`](journeys-to-pdf.py) (Chrome headless, dois passos para os números do sumário). Não reescrever o conversor e não copiar o estilo de um PDF antigo em `docs/`: ele pode estar defasado ou ter errado.

Modo de falha coberto: reconstruir o HTML de memória visual (cabeçalho com cor errada, capa numerada, sem rodapé, código dentro das células, badge de exceção inexistente) e/ou converter Markdown direto com `weasyprint`/`pandoc` sem verificar se funcionam.

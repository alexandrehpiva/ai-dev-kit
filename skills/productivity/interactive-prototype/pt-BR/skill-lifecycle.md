# Ciclo de vida da skill — Passo 0, versão e migração

Ler **a cada ativação e reativação** da skill, antes de qualquer alteração no protótipo. A skill evolui; o protótipo guarda a versão da skill com a qual foi preparado e é atualizado quando ela muda.

## Diagnóstico do modo de falha

Uma skill em evolução, com protótipos já criados por versões antigas, produz três falhas: (1) o agente aplica regras novas a um protótipo que não tem a estrutura delas (config sem `members`, sem artefatos registrados) e improvisa; (2) o agente "esquece" as skills auxiliares (`grill-me`, `hallucination-guard`) quando a conversa fica longa, e passa a decidir sozinho e a gravar suposições como fato; (3) uma pessoa com a skill instalada numa versão mais antiga que a do protótipo "corrige" o que parece fora do padrão e desfaz a evolução.

## Dependências críticas — recarregar sempre

`grill-me` e `hallucination-guard` são **dependências hard** (declaradas em `dependencies:` no frontmatter, o CLI do ai-dev-kit as instala junto). Sem elas a skill não funciona corretamente.

**Obrigatório, sem exceção, mesmo que consuma mais tokens:** em cada acionamento e reacionamento da skill (comando `/interactive-prototype` ou disparo automático), invocar de novo as duas skills pela ferramenta de skills **antes de qualquer outra ação** e seguir as instruções que carregarem. Além disso, recarregar ambas:

- antes de **compartilhar** com o time e antes de **promover** (portões críticos);
- ao perceber **sinal de compactação ou retomada de sessão** (resumo no início do contexto, sessão-continuação, pedido do usuário para "revalidar").

Se uma delas não estiver disponível: **parar**, explicar em linguagem de produto que falta instalar uma ferramenta do fluxo de trabalho e pedir que o responsável o instale. Não prosseguir "sem".

## A versão da skill

- A versão da skill está em `version:` no frontmatter do `SKILL.md` (semver).
- O protótipo registra a versão com que foi preparado em `skill.version` no `prototype.config.json`. **Config sem o bloco `skill`, ou protótipo sem config, conta como versão `1.0.0` (legado).**
- Mudança que exige alterar protótipos existentes (chaves novas do config, arquivos novos, nova estrutura) incrementa a versão da skill **e** ganha uma entrada em [`MIGRATIONS.md`](MIGRATIONS.md) e um salto implementado em `scripts/migrate.py`. Mudança que não afeta protótipos existentes (texto de asset, correção) só incrementa `patch`/`minor` sem entrada em `MIGRATIONS.md`: o protótipo aparece como desatualizado e `migrate.py` aplica apenas o passo `version-bump` (atualiza `skill.version`, sem perguntas), ainda com a aprovação do promoter.

## Passo 0 — rodar sempre, nesta ordem

Os comandos estão em [`checklists.md`](checklists.md) → C0. Resumo do que cada resultado significa:

| Resultado de `scripts/skill-status.py` | O que fazer |
|---|---|
| `UP_TO_DATE` | seguir para o próximo passo do Passo 0 |
| `PROTOTYPE_LEGACY` / `PROTOTYPE_OUTDATED` / `NO_CONFIG` (com `index.html`) | **migração obrigatória** antes de qualquer alteração (seção abaixo). Enquanto não migrar: só consulta |
| `SKILL_OUTDATED` (protótipo mais novo que a skill instalada) | **modo consulta**. Explicar que a skill instalada nesta máquina é mais antiga que a usada no protótipo e pedir para atualizá-la (`ai-dev-kit update`). Nunca "corrigir" o protótipo para parecer o padrão antigo |
| `NOT_A_PROTOTYPE` | não é um protótipo gerado por esta skill: seguir o fluxo normal (criação ou protótipo avulso), sem modo grupo |

## Migração

Regra: **uma aprovação, executada por script, só por promoter** (em grupo). Nunca migrar silenciosamente: a migração altera arquivos do projeto e cria configuração nova.

1. **Plano:** `python3 <skill>/scripts/migrate.py --repo <pasta> --plan`. Sem escrever nada, devolve os passos e as **perguntas obrigatórias**.
2. **Perguntar** (via `grill-me`, uma vez, em linguagem de produto, com a recomendação):
   - **Qual papel sugerir ao aprovar alguém?** `policy.promoters`: `all-members` (padrão) sugere promoter; `listed` sugere colaborador. O papel real de cada pessoa é decidido na aprovação e fica em `roles`; é só ele que dá o poder de publicar para o cliente.
   - **Posso manter a documentação do protótipo atualizada sozinho** (design system, catálogo de componentes, regras de negócio e jornadas já existentes) **sem perguntar a cada rodada?** Registra `docs.autoMaintain`. Mudar ou remover etapas de uma jornada continua exigindo confirmação, qualquer que seja a resposta.
   - Em modo grupo, **para cada versão compartilhada (oficial e de testes), já existe um link de demonstração para reaproveitar, ou crio um novo?**
3. **Apresentar o plano ao usuário** (o que será criado e alterado, em linguagem de produto) e pedir **uma aprovação**.
4. **Executar:** `migrate.py --execute --answers-json '<respostas>' --actor-name <nome> --actor-email <e-mail>`. O script é idempotente: rodar duas vezes não duplica nada.
5. **Validar:** `config-validate.py` e `skill-status.py` devem retornar `VALID` e `UP_TO_DATE`. Relatar o resultado em linguagem de produto.
6. **Seguir o ciclo normal** (compartilhar a migração com o time pelo fluxo de [`group-sync.md`](group-sync.md): a migração é um lote como qualquer outro).

Em modo grupo, **só um promoter migra**. As demais pessoas ficam em consulta até a migração chegar à beta e elas trazerem as novidades. Pessoa sem papel de promoter que encontrar o protótipo desatualizado: explicar que um responsável precisa atualizar primeiro.

## Boas práticas ao evoluir a skill (para quem mantém a skill)

- Cada migração tem um id (`<de>-><para>`), é **idempotente**, tem `--dry-run`/`--plan` e nunca sobrescreve arquivo do usuário.
- O que pode virar script, vira script (detecção de versão, validação de config, identidade, sincronização). O texto da skill diz **quando** rodar e **como agir sobre a saída**, não repete o que o script faz.
- Toda regra crítica tem um item de checklist verificável em [`checklists.md`](checklists.md).

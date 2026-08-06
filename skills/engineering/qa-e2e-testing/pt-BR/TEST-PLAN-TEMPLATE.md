# Formato do plano de testes de QA

Salvar como `<projeto>/qa-plan-<data>.md` (ou local equivalente do projeto). Uma seção por tela/feature.

```markdown
# Plano de Testes E2E — <produto> (<data>)

## Escopo
<o que entra e o que fica de fora deste ciclo, e por quê>

## Mapa de telas/features
| Tela/rota | Ações com efeito colateral | Depende de / afeta |
|---|---|---|
| ... | ... | ... |

## Tela: <nome>
### Cenários
| # | Categoria | Dado / Quando / Então | Prioridade |
|---|---|---|---|
| T1 | golden path | ... | alta |
| T2 | consistência de estado | ... | alta |
| T3 | adverso | ... | média |
| T4 | tier/plano | ... | alta |

### Decisões fechadas no grill-me
- <decisão> — <por quê>

## Execução
- Comando: `<como rodar a suíte>`
- Ambiente: <local/staging/prod-like>

## Resultado
| Cenário | Status | Achado | Ação |
|---|---|---|---|
| T1 | passou | — | — |
| T2 | falhou | <descrição do bug> | corrigido em <commit> / débito técnico #<task> |
```

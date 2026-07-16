# VALIDATION — Evidência antes de declarar pronto

## Obrigatório

1. **Testes do orquestrador** (pelo menos): interpolação de portas, grafo/ondas (incl. ciclo), `up`/`down` com launcher fake + state file.
2. **`list`** mostra a stack MVP e os serviços do catálogo.
3. **`up <stack>`** (ou equivalente) sobe a jornada; falhas de pré-requisito são mensagens claras, não stack trace cru sem contexto.
4. **`status <stack>`** reflete health real (HTTP/TCP) alinhado ao que a jornada usa.
5. **`down <stack>`** libera as portas dos apps e para a infra Compose listada.

## Preferencial (quando a jornada tiver)

6. Rodar o script de verificação da própria jornada (ex.: `npm run check:stack`, smoke E2E, curl pack documentado) e colar/registrar o resultado.
7. Confirmar hot reload: editar um arquivo trivial e ver o processo reiniciar na janela correspondente (smoke manual ok).

## Honestidade

- Se iTerm2/Docker/API não puderam ser exercitados neste ambiente, diga o que foi testado (unitário) e o que falta o usuário validar na máquina.
- Não declare “100%” sem a evidência acima.
- Documente gotchas descobertos na validação (comando Angular, WSGI, portas conflitantes) em `docs/` do orquestrador.

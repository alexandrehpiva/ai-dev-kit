# Instalar os hooks (uma vez por projeto ou global)

Leia antes de aplicar: isto altera configuração do Claude Code (`settings.json`); peça confirmação ao usuário se ele não autorizou.

1. Defina o caminho: `GUARD=<pasta de skills>/session-limit-guard/scripts/limit_guard.py` (instalada no projeto, p.ex. `.claude/skills/session-limit-guard/scripts/limit_guard.py`).
2. Em `.claude/settings.json` do projeto (ou `~/.claude/settings.json`), **mescle** (não substitua os hooks existentes):

```json
{
  "hooks": {
    "StopFailure":      [{"hooks": [{"type": "command", "command": "python3 \"$GUARD\" hook"}]}],
    "SessionStart":     [{"hooks": [{"type": "command", "command": "python3 \"$GUARD\" hook"}]}],
    "PostToolUse":      [{"hooks": [{"type": "command", "command": "python3 \"$GUARD\" hook"}]}],
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 \"$GUARD\" hook"}]}]
  },
  "statusLine": {"type": "command", "command": "python3 \"$GUARD\" statusline"}
}
```

Troque `$GUARD` pelo caminho absoluto. `statusLine` só entra se o usuário não tiver outra; o campo `rate_limits` só vem para assinantes claude.ai.
3. Verifique: abra uma sessão nova e rode `limit_guard.py status`; use `LIMIT_GUARD_DRYRUN=1` para testar o hook sem agendar. Hooks de settings só valem em sessões iniciadas depois da mudança.
4. Variáveis: `LIMIT_GUARD_WARN_PCT` (85), `LIMIT_GUARD_STOP_PCT` (95), `LIMIT_GUARD_MARGIN_S` (120), `LIMIT_GUARD_MAX_TRIES` (6), `LIMIT_GUARD_PERMISSION_MODE` (acceptEdits).

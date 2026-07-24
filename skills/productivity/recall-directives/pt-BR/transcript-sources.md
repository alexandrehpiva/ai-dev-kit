# Localizando o transcript completo, por harness

Cada harness agêntico decide sozinho **onde e como** persiste o histórico da conversa em disco — e o formato muda entre versões. Trate o que segue como **pontos de partida a verificar antes de confiar**, nunca como caminho garantido. Se qualquer verificação falhar (arquivo não existe, schema diferente do esperado), não force: caia no fallback da seção final.

## Como detectar o harness atual

- Se o próprio ambiente já identifica o harness (nome do CLI/app, ferramentas disponíveis, variáveis de ambiente típicas, caminhos de config visíveis), use isso.
- Se não for óbvio e o ganho justificar, pergunte ao usuário qual harness está em uso.
- Se não houver como saber com confiança, vá direto para o fallback.

## Claude Code (CLI da Anthropic)

- Sessões ficam em `~/.claude/projects/<cwd-com-separadores-trocados-por-hifen>/<sessionId>.jsonl`, um evento JSON por linha.
- O próprio resumo de compactação do harness costuma citar esse caminho explicitamente (algo como "read the full transcript at: ...") — **prefira essa citação** a tentar reconstruir o path manualmente a partir do nome do projeto.
- Extraia as entradas com papel de usuário (`role: user` ou equivalente) do JSONL para focar nos prompts originais, sem a perda da sumarização.

## Cursor

- O histórico de chat vive em bancos SQLite dentro do workspace storage do editor, indexado por workspace (não por sessão isolada), em local e schema que mudam entre versões do Cursor.
- Não assuma um schema de tabela sem antes confirmar que o arquivo existe e inspecionar a estrutura real.
- Se o ambiente expuser o histórico via alguma ferramenta própria (MCP, comando de contexto), prefira essa via a abrir o banco SQLite diretamente.

## GitHub Copilot Chat (VS Code)

- Sessões de chat ficam em arquivos JSON no workspace storage do VS Code, um arquivo por sessão, também sujeitos a mudança de formato entre versões da extensão.
- Mesmo cuidado do Cursor: confirmar existência e formato antes de depender disso.

## Qualquer outro harness, ou quando nada acima se aplica

- **Não invente um caminho.** Se não houver forma confiável e já confirmada de acessar o histórico completo neste ambiente, isso não é uma falha — é o caso comum.
- Trabalhe com o que já está disponível no contexto atual: os turnos visíveis mais qualquer resumo de compactação já injetado pelo harness. É o fallback padrão desta skill (ver `SKILL.md`, passo 1).

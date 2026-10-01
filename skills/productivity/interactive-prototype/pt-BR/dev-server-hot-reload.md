# Servir protótipo com hot reload durante desenvolvimento

Quando o usuário pedir para "subir", "servir" ou "rodar" o protótipo com hot reload (ou quando for necessário verificar mudanças no browser durante o desenvolvimento), usar `npx concurrently` com `chokidar-cli` e `live-server` — zero dependência de arquivo local, zero `package.json`, funciona em qualquer máquina onde Node esteja instalado.

## Como funciona

O ciclo: `chokidar-cli` assiste `js/`, `styles/` e `index.html`; a cada mudança dispara `python3 build.py` (que gera `dist/index.html`); `live-server` serve `dist/` e detecta a mudança no arquivo gerado, recarregando o browser automaticamente.

## Iniciar (Claude Code)

Registrar uma entrada no `.claude/launch.json` do repositório onde o protótipo vive (ver "Adicionar ao `.claude/launch.json`" abaixo) e usar `preview_start` com o nome dessa entrada:

```
preview_start({ name: "<nome-do-prototipo>" })
```

Isso sobe os dois processos na porta configurada na entrada (ex.: **8850**) e abre uma aba no browser pane. Em outro harness sem `preview_start`, usar o comando manual abaixo.

## Iniciar (terminal manual — portátil, sem package.json)

```bash
cd <raiz-do-prototipo>
npx --yes concurrently \
  "npx --yes chokidar-cli 'js/**/*.js' 'styles/**/*.css' 'index.html' -c 'python3 build.py'" \
  "npx --yes live-server dist --port=8850 --no-browser"
```

Substitua `8850` pela porta desejada. O `--yes` no `npx` instala os pacotes na primeira execução sem pedir confirmação. O `--no-browser` evita que `live-server` abra uma aba no browser do sistema (o Claude Code abre a própria aba via `preview_start`).

## Adicionar ao `.claude/launch.json` do repositório (novo protótipo)

```json
{
  "name": "<nome-do-projeto>",
  "runtimeExecutable": "bash",
  "runtimeArgs": [
    "-c",
    "cd <caminho-absoluto-do-projeto> && npx --yes concurrently \"npx --yes chokidar-cli 'js/**/*.js' 'styles/**/*.css' 'index.html' -c 'python3 build.py'\" \"npx --yes live-server dist --port=<porta> --no-browser\""
  ],
  "port": <porta>
}
```

## Diagnóstico de problemas comuns

| Sintoma | Causa provável | Fix |
|---------|---------------|-----|
| Porta em uso | Outro processo na porta | Matar com `lsof -i :<porta> -t \| xargs kill -9` e subir de novo |
| Reload não dispara | Arquivo salvo fora de `js/`/`styles/`/`index.html` | Verificar que o arquivo está na árvore assistida |
| Build falhou | Erro de sintaxe no JS/CSS | Corrigir o arquivo e salvar novamente |
| `npx` lento na 1ª vez | Download inicial dos pacotes | Normal; nas próximas execuções está em cache do npx |

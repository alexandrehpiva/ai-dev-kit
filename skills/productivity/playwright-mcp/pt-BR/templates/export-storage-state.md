# Exportar a sessão (storageState e sessionStorage) pelo próprio MCP

> Legenda: **verificado ao vivo** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157;
> `@playwright/mcp` 0.0.85 / playwright-core 1.66.0-alpha). Nada aqui é copiado para o chat: os
> resultados contêm cookies e tokens. Trate o arquivo gerado como senha (`chmod 600`, apague depois).

O `@playwright/mcp` 0.0.85 não tem ferramenta nem flag para exportar o estado (`--save-session` grava só a
transcrição das chamadas). O caminho é a ferramenta `browser_run_code_unsafe`, que recebe o parâmetro
`code` com uma função `async (page) => ...` executada no processo do servidor Playwright.

Antes de exportar: abra (só leitura) uma aba de cada site que deve ir junto. Cookies de todos os domínios
saem sempre; localStorage e IndexedDB só das origens carregadas nas abas do contexto. **[verificado ao vivo]**

## 1. storageState (cookies + localStorage + IndexedDB): grave direto em arquivo

**Forma recomendada.** Chame `browser_run_code_unsafe` com:

```json
{"code": "async (page) => { const s = await page.context().storageState({ path: 'state.json', indexedDB: true }); return JSON.stringify({ cookies: s.cookies.length, origins: s.origins.length }); }"}
```

- O Playwright grava o arquivo no processo do servidor MCP e a função devolve **só contagens**: os cookies
  nunca passam pelo modelo nem ficam no transcript da sessão. **[verificado ao vivo]** em MCP headless/isolado;
  em modo extensão o `path` **[não verificado]**.
- O caminho precisa ficar sob a pasta de trabalho do MCP (o cwd/raiz do workspace) **[verificado ao vivo]**; fora dela
  não foi testado. Use um nome relativo (`state.json`) ou um caminho dentro dessa pasta.
- Logo depois: `chmod 600 state.json` (Windows: pasta do usuário, sem sincronização) e **mova o arquivo para
  fora do projeto** (pasta fora de repositório git/nuvem), ou apague ao terminar. Confira com
  `check_setup.py --mode headless-state --state-file <arquivo>` (lê só contagens e permissão).
- Inclui cookies HttpOnly e Secure e os de sessão (`expires: -1`). Não inclui sessionStorage.

**Evitar:** `async (page) => JSON.stringify(await page.context().storageState({ indexedDB: true }))`. O
resultado volta como texto em `### Result`, ou seja, **todos os cookies entram no contexto do modelo e no
transcript** (um dos riscos que a skill existe para evitar). Só use com aceite explícito do usuário, quando
o `path` não for possível (ex.: modo extensão onde ele falhe); então o agente grava o texto devolvido (uma
string JSON dentro de JSON: `json.loads` duas vezes) e avisa o usuário de que os cookies ficaram no transcript. Dentro do código,
`require` não existe: a função não grava arquivo por conta própria além do `path` do Playwright.

## 2. sessionStorage (por origem)

Chame `browser_run_code_unsafe` com:

```json
{"code": "async (page) => { const out = {}; for (const p of page.context().pages()) { try { const o = await p.evaluate(() => [location.origin, Object.fromEntries(Object.entries(sessionStorage))]); if (o[0] && o[0] !== 'null' && Object.keys(o[1]).length) out[o[0]] = o[1]; } catch (e) {} } return JSON.stringify(out); }"}
```

Devolve `{"https://site": {"chave": "valor"}}` das abas abertas **[verificado ao vivo]**. **Esses valores
passam pelo modelo** (não há como gravá-los em arquivo a partir da função): faça só com aceite explícito do
usuário, só para os sites necessários, e prefira não usar sessionStorage se o login funcionar sem ele. Salve em
`session-storage.json` (`chmod 600`) e gere o init-script:

```
python3 <pasta-da-skill>/scripts/make_init_script.py --input session-storage.json --output init-session.js
```

(Windows: `py -3 <pasta-da-skill>\scripts\make_init_script.py ...`)

## 3. Reabrir em headless

```
npx -y @playwright/mcp@0.0.85 --headless --isolated --storage-state state.json --init-script init-session.js \
  --executable-path "<caminho do navegador>" --output-dir "<pasta fora do projeto>"
```

`--storage-state` só vale com `--isolated` (sem ele o arquivo é ignorado). O init-script restaura só o
sessionStorage; sozinho, não traz cookies. **[verificado ao vivo]**

Se o site bloquear o user agent `HeadlessChrome` (ex.: Cloudflare), acrescente `--user-agent "<UA normal do
mesmo navegador>"`. **[verificado ao vivo]**

## 4. Limpeza

Apague `state.json`, `session-storage.json`, `init-session.js` e a pasta de saída do MCP (`--output-dir`;
sem essa flag, `.playwright-mcp/` no diretório de trabalho: acumula snapshots de páginas logadas) ao terminar.

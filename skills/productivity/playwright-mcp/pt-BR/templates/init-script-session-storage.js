// Reidrata o sessionStorage por origem (o storageState do Playwright NÃO leva sessionStorage).
// Gerado de verdade por scripts/make_init_script.py; este arquivo é o modelo com dados de exemplo.
// Uso no MCP: --isolated --storage-state <state.json> --init-script <este arquivo>
// Só grava a chave se ela ainda não existir (troque OVERWRITE por true para forçar).
(() => {
  const DATA = {"https://exemplo.com": {"chave-de-exemplo": "valor-de-exemplo"}};
  const OVERWRITE = false;
  const items = DATA[location.origin];
  if (!items) return;
  try {
    for (const [k, v] of Object.entries(items)) {
      if (OVERWRITE || sessionStorage.getItem(k) === null) sessionStorage.setItem(k, v);
    }
  } catch (e) { /* sessionStorage indisponível nesta origem (about:blank, iframe sandbox) */ }
})();

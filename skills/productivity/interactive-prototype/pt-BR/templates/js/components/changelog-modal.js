/* ⚠️  PROTÓTIPO — Changelog e modal de versões (prototype-only).
   NÃO migrar para o produto final. Este componente e seus dados são exclusivos do protótipo.

   Formato de cada entrada: { version, date: 'YYYY-MM-DD', changes: ['descrição', ...] }
   Ordem: decrescente — a entrada mais recente fica no TOPO do array.

   Workflow de atualização (obrigatório — ver versioning-and-changelog.md da skill):
   1. Trabalho em andamento, NÃO aprovado para commit, entra na entrada especial
      version:'Pendente (não commitado)', no topo. Ela é um ESPELHO DO WORKTREE (diff em relação ao
      último commit real), não um diário: reversão remove a linha, ajuste parcial edita a linha,
      só mudança nova vira linha nova. NUNCA numerar versão antes da aprovação.
   2. Só quando o usuário aprova o lote para commit: renomear 'Pendente' para o próximo semver real,
      atualizar o badge em index.html (#prototype-version-badge) para o mesmo número, rebuild
      (python3 build.py) e só então commitar.
   Bugs conhecidos e não resolvidos entram na lista marcados com ⚠️, nunca omitidos. */

const CHANGELOG = [
  { version: 'Pendente (não commitado)', date: '@@DATE@@', changes: [
    'Esqueleto inicial gerado pelo scaffold da skill interactive-prototype (shell, estilos, roteador, stepper, badge/changelog, botão Demo e telas de exemplo).',
  ] },
];

function renderChangelog(){
  document.getElementById('changelogBody').innerHTML = CHANGELOG.map(e =>
    `<div class="changelog-entry"><h3>${escapeHtml(e.version)}<span class="date">${escapeHtml(e.date)}</span></h3>
     <ul>${e.changes.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul></div>`).join('');
}

function openChangelog(){
  renderChangelog();
  document.getElementById('changelogOverlay').classList.add('open');
}

function closeChangelog(ev){
  if (ev && ev.target !== ev.currentTarget) return;  // clique dentro do modal não fecha
  document.getElementById('changelogOverlay').classList.remove('open');
}

document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeChangelog(); });

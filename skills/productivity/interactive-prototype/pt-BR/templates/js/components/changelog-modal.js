/**
 * @purpose Janela com o histórico de versões do protótipo (lista CHANGELOG), aberta pelo badge de versão; exclusivo do protótipo, não migra para o produto.
 * @props nenhuma — openChangelog() sem argumentos; os dados vêm da constante CHANGELOG deste arquivo.
 * @slots nenhum — o conteúdo é a lista de entradas montada por changelogBodyHTML() e entregue ao slot de corpo do modal genérico (modal.js).
 * @state uncontrolled — dono: o modal genérico (aberto/fechado interno); CHANGELOG é dado constante, sem estado de tela.
 * @events nenhum próprio — herda modal:open e modal:close do modal genérico.
 * @a11y herda do modal genérico: role="dialog" rotulado pelo título "Histórico de versões", foco preso e devolvido ao badge, Escape fecha; versão e data de cada entrada em texto, sem depender de cor.
 */

/* Formato de cada entrada: { version, date: 'YYYY-MM-DD', changes: ['descrição', ...] }
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

function changelogBodyHTML(){
  return CHANGELOG.map(e =>
    `<div class="changelog-entry"><h3>${escapeHtml(e.version)}<span class="date">${escapeHtml(e.date)}</span></h3>
     <ul>${e.changes.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul></div>`).join('');
}

/* Reconstrói o modal a cada abertura para refletir o CHANGELOG atual. */
function openChangelog(){
  document.getElementById('changelogHost').innerHTML =
    modalHTML({ id: 'changelog', title: 'Histórico de versões', bodyHTML: changelogBodyHTML() });
  modalOpen('changelog');
}

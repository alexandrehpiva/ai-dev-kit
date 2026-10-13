/**
 * @purpose Janela modal genérica (overlay + cartão com cabeçalho, corpo e rodapé) para confirmações, formulários curtos e detalhes; fecha por Escape, clique no fundo ou botão ×.
 * @props modalHTML({ id, title, bodyHTML = '', footerHTML = '', size = 'md', dismissible = true, open }) — id: [A-Za-z0-9_-]+, único na página; title: texto puro; size: 'sm' | 'md' | 'lg'; dismissible=false remove o ×, o Escape e o clique no fundo; open (boolean) é opcional: presente ⇒ modo controlado. Imperativo: modalOpen(id), modalClose(id), modalSync(id).
 * @slots bodyHTML (corpo; rola por dentro quando longo); footerHTML (ações, alinhadas à direita; omitido se vazio); cabeçalho = title + botão × (quando dismissible). Não é escapado: quem chama escapa o conteúdo variável com escapeHtml().
 * @state hybrid — sem `open`, o próprio modal é dono do aberto/fechado (classe is-open no overlay); com `open`, a tela dona decide: modalOpen/modalClose só pedem a mudança pelos eventos modal:request-* e a tela renderiza de novo (modalSync(id) após o render devolve o foco ao lugar certo).
 * @events CustomEvent no overlay (borbulha; detail: { id }): modal:open e modal:close (modo interno, depois da mudança); modal:request-open e modal:request-close (modo controlado).
 * @a11y role="dialog" com aria-modal e aria-labelledby apontando para o título; ao abrir, o foco vai ao primeiro elemento focável do cartão e Tab/Shift+Tab ficam presos nele; ao fechar, o foco volta ao elemento que abriu; Escape fecha o modal do topo quando dismissible; botão × com aria-label.
 */

const _MODAL_FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
const _modalReturnFocus = {};  // id → elemento que tinha o foco antes de abrir

function modalHTML({ id, title, bodyHTML = '', footerHTML = '', size = 'md', dismissible = true, open } = {}){
  const safeId = String(id).replace(/[^\w-]/g, '');
  const controlled = typeof open === 'boolean';
  const cls = '@@PREFIX@@-modal-overlay' + (controlled && open ? ' is-open' : '');
  return `<div class="${cls}" id="${safeId}" data-modal data-controlled="${controlled}" data-dismissible="${!!dismissible}" onclick="_modalBackdrop(event)">
    <div class="@@PREFIX@@-modal is-${escapeHtml(size)}" role="dialog" aria-modal="true" aria-labelledby="${safeId}-title" tabindex="-1">
      <div class="@@PREFIX@@-modal-head">
        <h2 id="${safeId}-title">${escapeHtml(title)}</h2>
        ${dismissible ? `<button class="@@PREFIX@@-modal-close" type="button" onclick="modalClose('${safeId}')" aria-label="Fechar">×</button>` : ''}
      </div>
      <div class="@@PREFIX@@-modal-body">${bodyHTML}</div>
      ${footerHTML ? `<div class="@@PREFIX@@-modal-foot">${footerHTML}</div>` : ''}
    </div>
  </div>`;
}

function _modalEmit(el, name){
  el.dispatchEvent(new CustomEvent(name, { bubbles: true, detail: { id: el.id } }));
}

function _modalActivate(el){
  if (!(el.id in _modalReturnFocus)) _modalReturnFocus[el.id] = document.activeElement;
  const card = el.querySelector('[role="dialog"]');
  if (!card.contains(document.activeElement)) (card.querySelector(_MODAL_FOCUSABLE) || card).focus();
}

function _modalDeactivate(el){
  const back = _modalReturnFocus[el.id];
  delete _modalReturnFocus[el.id];
  if (back && back.focus && document.contains(back)) back.focus();
}

function modalOpen(id){
  const el = document.getElementById(id);
  if (!el) return;
  if (el.dataset.controlled === 'true'){ _modalEmit(el, 'modal:request-open'); return; }
  if (el.classList.contains('is-open')) return;
  el.classList.add('is-open');
  _modalActivate(el);
  _modalEmit(el, 'modal:open');
}

function modalClose(id){
  const el = document.getElementById(id);
  if (!el) return;
  if (el.dataset.controlled === 'true'){ _modalEmit(el, 'modal:request-close'); return; }
  if (!el.classList.contains('is-open')) return;
  el.classList.remove('is-open');
  _modalDeactivate(el);
  _modalEmit(el, 'modal:close');
}

/* Modo controlado: a tela chama depois de renderizar de novo, para aplicar (ou devolver) o foco. */
function modalSync(id){
  const el = document.getElementById(id);
  if (!el) return;
  if (el.classList.contains('is-open')) _modalActivate(el); else _modalDeactivate(el);
}

function _modalBackdrop(ev){
  const el = ev.currentTarget;
  if (ev.target === el && el.dataset.dismissible === 'true') modalClose(el.id);
}

function _modalTop(){
  const opened = document.querySelectorAll('[data-modal].is-open');
  return opened[opened.length - 1] || null;
}

document.addEventListener('keydown', ev => {
  const el = _modalTop();
  if (!el) return;
  if (ev.key === 'Escape'){
    if (el.dataset.dismissible === 'true'){ ev.preventDefault(); modalClose(el.id); }
    return;
  }
  if (ev.key !== 'Tab') return;
  const card = el.querySelector('[role="dialog"]');
  const items = [...card.querySelectorAll(_MODAL_FOCUSABLE)];
  const active = document.activeElement;
  if (!items.length){ ev.preventDefault(); card.focus(); return; }
  const first = items[0], last = items[items.length - 1];
  if (!card.contains(active)){ ev.preventDefault(); first.focus(); }
  else if (ev.shiftKey && (active === first || active === card)){ ev.preventDefault(); last.focus(); }
  else if (!ev.shiftKey && active === last){ ev.preventDefault(); first.focus(); }
});

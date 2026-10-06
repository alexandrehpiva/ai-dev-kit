/* Helpers puros / de DOM compartilhados por várias telas. Sem estado próprio (estado vive em state.js). */

function escapeHtml(s){
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

/* Campo de texto padrão. opts: { type, placeholder, required, value } */
function fieldHTML(id, label, opts = {}){
  const { type = 'text', placeholder = '', required = false, value = formState[id] ?? '' } = opts;
  return `<div class="field">
    <label for="${id}">${escapeHtml(label)}${required ? ' *' : ''}</label>
    <input class="@@PREFIX@@-input" id="${id}" type="${type}" placeholder="${escapeHtml(placeholder)}" value="${escapeHtml(value)}"
      oninput="formState['${id}']=this.value;clearFieldError('${id}')">
    <div class="field-error" id="${id}-error" hidden></div>
  </div>`;
}

function showFieldError(id, msg){
  const input = document.getElementById(id), err = document.getElementById(id + '-error');
  if (input) input.classList.add('has-error');
  if (err){ err.textContent = msg; err.hidden = false; }
}

function clearFieldError(id){
  const input = document.getElementById(id), err = document.getElementById(id + '-error');
  if (input) input.classList.remove('has-error');
  if (err) err.hidden = true;
}

let _toastTimer;
function showToast(msg){
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 2400);
}

/* Stepper numerado (componente genérico). Lê FLOWS/flow/screenOrder/cursor de state.js.
   Não aparece nas telas fora do fluxo ('welcome' e 'resultado'). */

function renderStepper(){
  const wrap = document.getElementById('stepperWrap');
  const id = screenOrder[cursor];
  const steps = FLOWS[flow].steps, labels = FLOWS[flow].labels;
  const idx = steps.indexOf(id);
  if (idx < 0){ wrap.innerHTML = ''; return; }
  wrap.innerHTML = `<ol class="stepper" aria-label="Etapas">` + labels.map((label, i) =>
    `<li class="${i < idx ? 'done' : i === idx ? 'current' : ''}" ${i === idx ? 'aria-current="step"' : ''}>
       <span class="bar"></span><span>${i + 1}. ${escapeHtml(label)}</span></li>`).join('') + `</ol>`;
}

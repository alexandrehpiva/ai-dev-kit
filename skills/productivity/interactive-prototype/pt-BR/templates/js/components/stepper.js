/**
 * @purpose Indicador numerado das etapas do fluxo atual, com a etapa corrente destacada; não aparece nas telas fora do fluxo ('welcome' e 'resultado').
 * @props nenhuma — lê FLOWS, flow, screenOrder e cursor de state.js; renderiza dentro de #stepperWrap.
 * @slots nenhum
 * @state controlled — dono: state.js (flow, screenOrder, cursor); o componente só reflete esses valores a cada renderAll().
 * @events nenhum
 * @a11y lista ordenada com aria-label "Etapas"; a etapa corrente leva aria-current="step"; rótulos em texto visível (o progresso não depende só da barra colorida).
 */

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

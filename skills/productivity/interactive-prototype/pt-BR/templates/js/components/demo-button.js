/**
 * @purpose Botão "Demo" que preenche a tela atual com dados fictícios plausíveis para demonstrações; exclusivo do protótipo, não migra para o produto.
 * @props nenhuma — a tela atual vem de screenOrder/cursor (state.js); os dados vêm do registro DEMO_FILLERS deste arquivo (um filler por id de tela, o mesmo id de js/screens/index.js).
 * @slots nenhum
 * @state controlled — dono: state.js (cursor, formState); o botão não guarda estado próprio, só aparece quando a tela atual tem filler.
 * @events nenhum — usa showToast() para avisar que a tela foi preenchida.
 * @a11y botão nativo com texto visível "Demo", oculto (atributo hidden) nas telas sem filler; o preenchimento é anunciado pelo toast (região aria-live).
 */

/* Manutenção: ao criar/alterar/remover um campo de formulário, ajustar o filler da tela
   correspondente na mesma rodada. Tela nova com campos preenchíveis ⇒ nova entrada em
   DEMO_FILLERS. Tela sem campo (seleção por card, upload, assinatura) ⇒ sem entrada; o botão não
   aparece lá. Nunca preencher só parte dos campos obrigatórios: engana quem demonstra. */

const DEMO_FILLERS = {
  'exemplo-formulario': () => {
    demoSetField('nome', 'Pessoa de Exemplo');
    demoSetField('email', 'pessoa@exemplo.com');
  },
};

function demoSetField(id, value){
  formState[id] = value;
  const el = document.getElementById(id);
  if (el) el.value = value;
  clearFieldError(id);
}

function demoHasFillableFields(){ return !!DEMO_FILLERS[screenOrder[cursor]]; }

function updateDemoButton(){
  const btn = document.getElementById('demoBtn');
  if (btn) btn.hidden = !demoHasFillableFields();
}

function runDemoFill(){
  const fill = DEMO_FILLERS[screenOrder[cursor]];
  if (fill){ fill(); showToast('Tela preenchida com dados fictícios'); }
}

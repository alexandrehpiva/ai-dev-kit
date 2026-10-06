/* ⚠️  PROTÓTIPO — botão "Demo" (prototype-only). NÃO migrar para o produto.

   Preenche a tela atual com dados fictícios plausíveis para agilizar demonstrações. Toda a lógica
   vive neste arquivo, num único registro DEMO_FILLERS (uma função de preenchimento por tela, com
   o mesmo id usado em js/screens/index.js).

   >>> MANUTENÇÃO OBRIGATÓRIA: ao criar/alterar/remover um campo de formulário, ajustar o filler da
   tela correspondente na mesma rodada. Tela nova com campos preenchíveis ⇒ nova entrada em
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

/* Navegação entre telas e render principal. Estado vem de state.js; telas de js/screens/index.js. */

function buildScreenOrder(){ screenOrder = ['welcome', ...FLOWS[flow].steps, 'resultado']; }

function goNext(){
  const id = screenOrder[cursor];
  const validate = screenValidators[id];
  if (validate && !validate()) return;
  if (cursor < screenOrder.length - 1){ cursor++; navDirection = 'forward'; renderAll(); window.scrollTo({ top: 0 }); }
}

function goBack(){
  if (cursor > 0){ cursor--; navDirection = 'back'; renderAll(); window.scrollTo({ top: 0 }); }
}

function resetFlow(){ cursor = 0; navDirection = 'back'; renderAll(); }

function renderAll(){
  const id = screenOrder[cursor];
  const root = document.getElementById('screenRoot');
  root.innerHTML = screens[id]();
  root.classList.remove('screen-enter-forward', 'screen-enter-back');
  void root.offsetWidth;  // reinicia a animação de entrada
  root.classList.add(navDirection === 'forward' ? 'screen-enter-forward' : 'screen-enter-back');
  renderStepper();
  renderFooter(id);
  updateDemoButton();
}

function renderFooter(id){
  const nav = document.getElementById('footerNav');
  const last = screenOrder.length - 1;
  if (id === 'resultado'){
    nav.innerHTML = `<span></span><button class="@@PREFIX@@-btn-primary" onclick="resetFlow()">Recomeçar</button>`;
    return;
  }
  const back = cursor > 0 ? `<button class="@@PREFIX@@-btn-ghost" onclick="goBack()">Voltar</button>` : '<span></span>';
  const label = cursor === last - 1 ? 'Concluir' : id === 'welcome' ? 'Começar' : 'Continuar';
  nav.innerHTML = `${back}<button class="@@PREFIX@@-btn-primary" onclick="goNext()">${label}</button>`;
}

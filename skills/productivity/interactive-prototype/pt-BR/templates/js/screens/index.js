/* Mapa de telas — ÚNICO arquivo que "conhece" todas as telas. A chave é o id usado em
   FLOWS (state.js) e em DEMO_FILLERS (demo-button.js). screenValidators: validação opcional
   por tela, chamada antes de avançar. */

const screens = {
  'welcome':             screenWelcome,
  'exemplo-formulario':  screenExemploFormulario,
  'resultado':           screenResultado,
};

const screenValidators = {
  'exemplo-formulario':  validateExemploFormulario,
};

/* Estado mutável global — ÚNICO arquivo dono de estado (primeiro <script> da lista).
   Constantes de fluxo (FLOWS) e estado de navegação vivem aqui; dados digitados pelo usuário
   ficam em formState, indexados pelo id do campo. */

/* FLOWS: um fluxo por variante do produto (ex.: pf/pj). Cada fluxo lista os ids das telas do
   stepper (ids = chaves do mapa `screens` em js/screens/index.js) e os rótulos exibidos. A tela
   inicial ('welcome') e a final ('resultado') ficam fora do stepper. */
const FLOWS = {
  main: {
    steps: ['exemplo-formulario'],
    labels: ['Dados'],
  },
};

let flow = 'main';
let screenOrder = [];      // ['welcome', ...FLOWS[flow].steps, 'resultado'] — montado por buildScreenOrder()
let cursor = 0;            // índice da tela atual em screenOrder
let navDirection = 'forward';

const formState = {};      // { [idDoCampo]: valor }

/**
 * export-responses.gs — exporta as respostas de um formulário para uma Planilha nova
 * (e, opcionalmente, para um CSV) no Drive do dono, e loga as URLs.
 *
 * STATUS (verificado ao vivo em 2026-11-11, conta Workspace, UI em pt-BR): EXECUTADO com 1 resposta (e-mail por "Entrada do participante",
 *   texto, escala, múltipla escolha, grade de caixas, data, parágrafo, caixas): Planilha nova com
 *   cabeçalho e linha corretos; grade sai como "Sábado: Manhã | Domingo: Tarde".
 *   NÃO EXECUTADO AINDA: GERAR_CSV = true (DriveApp.createFile), mc_grid, upload de arquivo, quiz.
 *
 * Uso: preencha FORM_ID (o trecho entre /d/ e /edit na URL do editor), escolha
 * `exportarRespostas` e execute.
 * Escopos: o Apps Script pede todo escopo cujo serviço aparece no código, mesmo em ramo que não
 * executa (aqui DriveApp aparece no ramo do CSV -> drive). Fixe o manifesto (oauthScopes):
 * forms + spreadsheets; acrescente drive só com GERAR_CSV = true.
 * Dados de respostas podem conter dados pessoais: o arquivo fica no Drive do dono;
 * não copie conteúdo para o chat nem para logs além do necessário.
 * Ao terminar, revogue o acesso do projeto em myaccount.google.com/permissions ("Terceiros com
 * acesso à conta"; confira o nome do menu na tela): a autorização continua valendo depois da execução.
 */
var FORM_ID = 'COLE_O_ID_AQUI';
var GERAR_CSV = false;            // true cria também um .csv no Drive
var NOME_BASE = 'Respostas exportadas';

function exportarRespostas() {
  var form = FormApp.openById(FORM_ID);
  var items = form.getItems();
  // Só itens que geram resposta (ignora blocos de texto, imagem, vídeo, quebra de página).
  var perguntas = items.filter(function (it) {
    var t = it.getType();
    return t !== FormApp.ItemType.SECTION_HEADER && t !== FormApp.ItemType.PAGE_BREAK &&
           t !== FormApp.ItemType.IMAGE && t !== FormApp.ItemType.VIDEO;
  });
  var coletaEmail = safe_(function () { return form.collectsEmail(); }, false);

  // Cabeçalho: títulos podem repetir, então usa-se o ID do item como chave e o título (+ nº se repetido) como rótulo.
  var cont = {};
  var rotulos = perguntas.map(function (it) {
    var t = it.getTitle() || '(sem título)';
    cont[t] = (cont[t] || 0) + 1;
    return cont[t] > 1 ? t + ' (' + cont[t] + ')' : t;
  });
  var cab = ['ID da resposta', 'Data/hora'];
  if (coletaEmail) cab.push('E-mail');
  cab = cab.concat(rotulos);

  var linhas = [cab];
  form.getResponses().forEach(function (r) {
    var porItem = {};
    r.getItemResponses().forEach(function (ir) { porItem[ir.getItem().getId()] = ir.getResponse(); });
    var linha = [r.getId(), r.getTimestamp()];
    if (coletaEmail) linha.push(safe_(function () { return r.getRespondentEmail(); }, ''));
    perguntas.forEach(function (it) { linha.push(celula_(porItem[it.getId()], linhasDaGrade_(it))); });
    linhas.push(linha);
  });

  var titulo = form.getTitle() || FORM_ID;   // título vazio (form sem setTitle) cai no ID
  var ss = SpreadsheetApp.create(NOME_BASE + ' - ' + titulo);
  var sh = ss.getSheets()[0];
  sh.getRange(1, 1, linhas.length, cab.length).setValues(linhas.map(normalizar_(cab.length)));
  sh.setFrozenRows(1);
  Logger.log('Respostas exportadas: ' + (linhas.length - 1));
  Logger.log('Planilha: ' + ss.getUrl());

  if (GERAR_CSV) {
    var csv = linhas.map(function (l) { return l.map(csvCampo_).join(','); }).join('\n');
    var f = DriveApp.createFile(NOME_BASE + ' - ' + titulo + '.csv', csv, MimeType.CSV);
    Logger.log('CSV: ' + f.getUrl());
  }
}

// Grade devolve um array por linha (na ordem das linhas); checkbox devolve array; itens sem resposta vêm omitidos.
// Na grade, a célula leva o rótulo da linha ("Sábado: Manhã | Domingo: Tarde"); sem ele a associação se perde
// (visto ao vivo: sem rótulo a célula saía "Manhã | Tarde").
function celula_(valor, linhas) {
  if (valor === undefined || valor === null) return '';
  if (Array.isArray(valor)) {
    return valor.map(function (v, i) {
      var txt = Array.isArray(v) ? v.join(' / ') : (v === null ? '' : String(v));
      return linhas ? linhas[i] + ': ' + txt : txt;
    }).join(' | ');
  }
  return String(valor);
}
function linhasDaGrade_(it) {
  var t = it.getType();
  if (t === FormApp.ItemType.GRID) return it.asGridItem().getRows();
  if (t === FormApp.ItemType.CHECKBOX_GRID) return it.asCheckboxGridItem().getRows();
  return null;
}

// Evita injeção de fórmula na Planilha/CSV (valor que começa com = + - @).
function seguro_(v) {
  if (typeof v === 'string' && /^[=+\-@]/.test(v)) return "'" + v;
  return v;
}
function normalizar_(n) {
  return function (linha) {
    var l = linha.map(seguro_);
    while (l.length < n) l.push('');
    return l;
  };
}
function csvCampo_(v) {
  if (v instanceof Date) v = v.toISOString();
  v = String(seguro_(v === undefined || v === null ? '' : v));
  return '"' + v.replace(/"/g, '""') + '"';
}
function safe_(fn, fallback) { try { return fn(); } catch (e) { return fallback; } }

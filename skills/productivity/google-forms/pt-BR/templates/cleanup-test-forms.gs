/**
 * cleanup-test-forms.gs — manda para a lixeira do Drive SOMENTE os formulários de teste
 * registrados no inventário da sessão (FORM_IDS), com o prefixo de teste como filtro adicional.
 *
 * STATUS (verificado ao vivo em 2026-11-11, conta Workspace, UI em pt-BR): EXECUTADO em DRY_RUN e execução real com 3 forms do inventário,
 *   TRASH_LINKED_SHEETS = true (Planilhas vinculadas também foram para a lixeira) e um ID inexistente
 *   (logado como "não encontrado", sem abortar). NÃO EXERCITADO: arquivo de outro dono e nome sem o prefixo
 *   (os ramos de recusa existem, mas não houve caso real no teste ao vivo).
 *
 * Regra da skill: o prefixo NÃO autoriza excluir; a autorização vem do inventário da sessão
 * (testing-and-cleanup.md). Por isso a entrada obrigatória é a lista de IDs.
 * Cada ID só vai para a lixeira se:
 *   1. o nome do arquivo COMEÇA com TEST_PREFIX;
 *   2. é um Google Form (ou, com TRASH_LINKED_SHEETS, a Planilha de destino desse form);
 *   3. o dono do arquivo é o usuário que executa o script (arquivo compartilhado por outra
 *      pessoa é ignorado; arquivo de Drive compartilhado, sem dono, também é ignorado).
 * DRY_RUN = true só lista. Segundo a Ajuda do Drive, itens na lixeira ficam recuperáveis por até 30 dias (não confirmado
 * para Forms); este script NÃO esvazia a lixeira. Falha FECHADO: se não conseguir identificar o dono do
 * Drive (e-mail vazio), não apaga nada.
 *
 * Ao terminar, revogue o acesso do projeto em myaccount.google.com/permissions ("Terceiros com acesso
 * à conta"; confira o nome do menu na tela): o escopo drive dá acesso a todo o Drive.
 *
 * Escopos: o Apps Script pede todo escopo cujo serviço aparece no código (DriveApp -> drive,
 * FormApp -> forms), mesmo em ramo que não executa. Fixe o manifesto (oauthScopes: drive, forms).
 */
var FORM_IDS = [];                   // IDs do inventário da sessão (trecho entre /d/ e /edit). Obrigatório.
var TEST_PREFIX = '[TESTE] ';        // filtro adicional; mínimo de 4 caracteres
var DRY_RUN = true;                  // true = só lista
var TRASH_LINKED_SHEETS = false;     // true = manda também a Planilha de respostas vinculada (mesmas regras)

function limparFormulariosDeTeste() {
  if (!FORM_IDS || !FORM_IDS.length) {
    throw new Error('FORM_IDS vazio: informe os IDs do inventário da sessão. Nada foi apagado.');
  }
  if (!TEST_PREFIX || TEST_PREFIX.trim().length < 4) {
    throw new Error('TEST_PREFIX muito curto: recusado para evitar apagar formulários reais.');
  }
  // Dono do "Meu Drive" = usuário que executa. Session.getEffectiveUser().getEmail() exigiria o escopo
  // extra userinfo.email (erro visto ao vivo: "As permissões especificadas não são suficientes").
  var raiz = DriveApp.getRootFolder().getOwner();
  var eu = raiz ? raiz.getEmail() : '';
  if (!eu) {
    Logger.log('ERRO: não consegui identificar o dono do Drive (e-mail vazio). Nada foi apagado.');
    throw new Error('Não consegui identificar o dono do Drive; nada foi apagado.');
  }
  var tag = DRY_RUN ? '[DRY-RUN] ' : '';
  Logger.log(tag + 'IDs recebidos: ' + FORM_IDS.length + ' | prefixo exigido: "' + TEST_PREFIX + '"');
  var n = 0;
  FORM_IDS.forEach(function (id) {
    var f;
    try { f = DriveApp.getFileById(id); } catch (e) { Logger.log(' - ' + id + ': não encontrado (' + e + ')'); return; }
    if (!elegivel_(f, eu, MimeType.GOOGLE_FORMS)) return;
    Logger.log(' - ' + f.getName() + ' | id=' + id + ' | atualizado=' + f.getLastUpdated().toISOString());
    if (TRASH_LINKED_SHEETS) {
      try {
        var form = FormApp.openById(id);
        if (form.getDestinationType() === FormApp.DestinationType.SPREADSHEET) {
          var sf = DriveApp.getFileById(form.getDestinationId());
          if (elegivel_(sf, eu, MimeType.GOOGLE_SHEETS)) {
            Logger.log('   planilha vinculada: ' + sf.getName() + ' | id=' + sf.getId());
            if (!DRY_RUN) { sf.setTrashed(true); Logger.log('   -> planilha enviada para a lixeira'); }
          }
        }
      } catch (e) { Logger.log('   (planilha vinculada não resolvida: ' + e + ')'); }
    }
    if (!DRY_RUN) { f.setTrashed(true); Logger.log('   -> enviado para a lixeira'); }
    n++;
  });
  Logger.log(tag + 'Formulários elegíveis: ' + n + (DRY_RUN ? '. Nada foi apagado. Mude DRY_RUN para false depois que o dono confirmar a lista.' : ''));
}

function elegivel_(f, eu, mime) {
  var nome = f.getName();
  if (f.isTrashed()) { Logger.log(' - ' + nome + ': já está na lixeira; ignorado'); return false; }
  if (f.getMimeType() !== mime) { Logger.log(' - ' + nome + ': tipo ' + f.getMimeType() + ' inesperado; ignorado'); return false; }
  if (nome.indexOf(TEST_PREFIX) !== 0) { Logger.log(' - ' + nome + ': sem o prefixo de teste; ignorado'); return false; }
  var dono = f.getOwner();
  var emailDono = dono ? dono.getEmail() : '';
  if (!emailDono || emailDono !== eu) { Logger.log(' - ' + nome + ': dono diferente do usuário (ou Drive compartilhado); ignorado'); return false; }
  return true;
}

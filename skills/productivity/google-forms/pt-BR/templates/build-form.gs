/**
 * build-form.gs — constrói um Google Form a partir de um objeto SPEC equivalente ao
 * FORM-SPEC.md (YAML convertido em literal JS). Esquema de referência: FORM-SPEC.md,
 * bloco <form-spec-schema>. Este arquivo NÃO define convenções próprias.
 *
 * STATUS (verificado ao vivo em 2026-11-11, conta Workspace, UI em pt-BR, com o SPEC de exemplo abaixo):
 *   VALIDADO: create + setTitle + setDescription; setEmailCollectionType(RESPONDER_INPUT);
 *   setAllowResponseEdits, setLimitOneResponsePerUser(false), setProgressBar, setShuffleQuestions(false),
 *   setConfirmationMessage, setPublishingSummary(false); seções (addPageBreakItem + título/descrição);
 *   go_to por opção em 2 passadas (Sim -> s2, Não -> s3) e after_section (s2 -> s3) conferidos no
 *   editor e respondendo; short_text/paragraph com validação de comprimento; linear_scale 1-5 com rótulos;
 *   checkbox_grid; date; checkboxes; required; Planilha nova + setDestination; setPublished(false),
 *   isPublished(), getPublishedUrl(). O form NASCE PUBLICADO no FormApp.create: o script despublica.
 *   NÃO EXECUTADO AINDA: quiz (pontos/gabarito/feedback), dropdown, mc_grid, time/duration/datetime,
 *   title_description/image/video, validações number/text/regex/selection, one_per_column, other,
 *   shuffle_options, collect_email verified, responses.sheet existing, caminho OPTS.publish = true
 *   (setPublished(true), setAcceptingResponses, addPublishedReaders). Esses ficam em try/catch quando
 *   o suporte é incerto e, se falharem, viram PENDENTE_UI.
 *
 * Como usar (no editor em script.google.com):
 *  1. Gere o arquivo com `python3 <pasta-da-skill>/scripts/spec_to_gs.py <spec> --out <arquivo>.gs`
 *     (Windows: `py -3`), que troca só o bloco entre SPEC:BEGIN e SPEC:END pelo FORM-SPEC APROVADO.
 *     Não edite o resto à mão. O SPEC de exemplo deste template está como `draft` e é RECUSADO se
 *     for colado sem passar pelo gerador (de propósito: não cria formulário de exemplo por engano).
 *  2. Cole o arquivo gerado, inteiro, num projeto novo.
 *  3. Escolha a função `criarFormulario` e clique em Executar.
 *  4. Se aparecer "Google não verificou este app": quem autoriza é o DONO da conta, nunca o agente.
 *  5. Leia o Registro de execução: ID, Editar, Responder, AVISOS, MAPA e a lista PENDENTE_UI
 *     (o que o agente ainda precisa completar pela interface).
 *
 * Escopos: o Apps Script pede todo escopo cujo serviço aparece no código, mesmo em ramo que não
 *   executa (UrlFetchApp -> script.external_request; SpreadsheetApp -> spreadsheets; e ainda
 *   script.container.ui, visto ao vivo). Fixe o manifesto appsscript.json (oauthScopes) com o mínimo:
 *   forms; + spreadsheets se responses.sheet new|existing; + script.external_request só com
 *   OPTS.fetchImages. Confira em Visão geral > "Escopos do OAuth do projeto" antes de executar.
 *
 * Proteções: recusa spec com status != approved ou com 'pending_owner' (salvo OPTS.allowDraft,
 * só para teste local); valida ids e destinos de go_to/after_section ANTES de criar o form;
 * o form nasce NÃO publicado a menos que OPTS.publish seja true E spec.publish.published != false.
 *
 * Campos do spec que o script NÃO aplica (informativos, ficam com o agente): spec_version, version,
 * status, approved_at, brief.*, privacy.*, meta.owner_notes, meta.language, item.personal.
 */

// ---------- Configuração de execução (não faz parte do spec) ----------
var OPTS = {
  titlePrefix: '',        // sobrepõe build.test_name_prefix; ex.: '[TESTE] ' (facilita o cleanup)
  publish: false,         // true só depois da confirmação explícita do dono
  allowDraft: false,      // true só em teste local: aceita status draft e pending_owner
  fetchImages: false,     // true baixa image.source http(s) via UrlFetchApp (escopo extra)
  warnings: [],           // preenchido na execução
  pending: [],            // linhas "PENDENTE_UI: <campo> <valor>"
  idMap: []               // linhas "q1 -> <itemId> | título"
};

// ---------- SPEC: exemplo do FORM-SPEC.md ("Exemplo completo"), YAML -> JS ----------
// >>> SPEC:BEGIN — bloco gerado por scripts/spec_to_gs.py (não edite à mão; o exemplo abaixo é substituído)
var SPEC = {
  spec_version: 1,
  version: 2,
  status: 'draft',   // o gerador troca este bloco inteiro pelo spec aprovado

  meta: {
    title: 'Inscrição: Workshop de Introdução à Análise de Dados',
    description: 'Inscreva-se para o workshop presencial de 6 de dezembro. Leva cerca de 3 minutos. '
      + 'Usamos seu nome e e-mail só para confirmar a inscrição, enviar avisos do evento e, '
      + 'se você pedir, emitir o certificado. As respostas são apagadas 90 dias após o evento. '
      + 'Quem coleta: Organização Exemplo. Dúvidas ou pedidos sobre seus dados: privacidade@example.org.',
    language: 'pt-BR',
    document_title: '2026-12-06 Inscrição - Workshop Análise de Dados',
    owner_notes: 'v2: dono trocou a escala de 1-10 para 1-5. Defaults do agente: sem imagem de '
      + 'cabeçalho, barra de progresso ligada (3 seções), confirmação escrita pelo agente.'
  },

  brief: {
    goal: 'Fechar a lista de presença (30 vagas), montar as turmas por disponibilidade e emitir certificados.',
    audience: 'Público externo adulto, ~60 interessados; sem menores.',
    channel: 'Link por e-mail e QR code no cartaz.',
    account_type: 'personal',
    estimated_minutes: 3
  },

  build: { path: 'apps_script', test_name_prefix: null },

  privacy: {
    personal_data: 'personal',
    inventory: [
      { item: 'q1', data: 'nome', purpose: 'Lista de presença' },
      { item: 'collect_email', data: 'e-mail (coletado pelas Configurações)', purpose: 'Confirmar inscrição e avisos do evento' },
      { item: 'q5', data: 'nome completo para o certificado', purpose: 'Emitir o certificado' },
      { item: 'q9', data: 'aceite de receber novidades (vinculado ao e-mail)', purpose: 'Divulgar próximos workshops' }
    ],
    legal_basis: [
      { purpose: 'Lista de presença, confirmação, avisos e certificado',
        basis: 'Procedimentos preliminares a pedido do titular (art. 7º V) — decidido pelo dono' },
      { purpose: 'Divulgar próximos workshops',
        basis: 'Consentimento (art. 7º I), opcional e revogável — decidido pelo dono' }
    ],
    controller: 'Organização Exemplo',
    contact: 'privacidade@example.org',
    retention: 'Respostas apagadas 90 dias após o evento; lista de novidades até a revogação.',
    sharing: 'Ninguém fora da equipe organizadora.',
    decided_by: 'owner'
  },

  settings: {
    collect_email: 'responder_input', // "Entrada do participante": já valida o formato; sem pergunta de e-mail
    send_copy: 'never',
    allow_edit: true,
    limit_one_response: false,
    progress_bar: true,
    shuffle_questions: false,
    confirmation_message: 'Inscrição recebida. Você vai receber a confirmação da vaga por e-mail até 28 de novembro.',
    show_summary: false,
    disable_autosave: false,
    accepting_responses: true,
    close: { at: null, response_limit: 60 }
  },

  quiz: { enabled: false },

  theme: { header_image: null, color: '#3f51b5', background_color: null, font: null },

  publish: { published: true, audience: 'anyone_with_link', responders: [], notify_responders: false },

  responses: { sheet: 'new', sheet_ref: null, sheet_access: 'Só o dono e 1 organizadora (editora).' },

  sections: [
    {
      id: 's1', title: null, description: null,
      items: [
        { id: 'q1', type: 'short_text', title: 'Como você quer ser chamado(a)?',
          required: true, personal: true },
        { id: 'q3', type: 'linear_scale', title: 'Qual é a sua experiência com planilhas e análise de dados?',
          required: true,
          scale: { low: 1, high: 5, low_label: 'Nunca usei', high_label: 'Uso no dia a dia' } },
        { id: 'q4', type: 'multiple_choice', title: 'Vai precisar de certificado de participação?',
          required: true,
          options: [ { value: 'Sim', go_to: 's2' }, { value: 'Não', go_to: 's3' } ] }
      ]
    },
    {
      id: 's2', title: 'Dados do certificado',
      description: 'O certificado é enviado por e-mail em até 10 dias após o workshop.',
      after_section: 's3',
      items: [
        { id: 'q5', type: 'short_text', title: 'Nome completo como deve aparecer no certificado',
          required: true, personal: true,
          validation: { kind: 'length', rule: 'max_chars', value: 80,
                        error: 'Use até 80 caracteres. Abrevie nomes do meio, se precisar.' } }
      ]
    },
    {
      id: 's3', title: 'Disponibilidade',
      description: 'Vamos montar as turmas com base nestas respostas.',
      after_section: 'submit',
      items: [
        { id: 'q6', type: 'checkbox_grid', title: 'Em quais períodos você pode participar?',
          description: 'Marque todos os que servem. Se não puder em um dia, marque "Não posso" naquela linha.', required: true,
          grid: { rows: ['Sábado', 'Domingo'], columns: ['Manhã', 'Tarde', 'Não posso'],
                  one_per_column: false, shuffle_rows: false } },
        { id: 'q7', type: 'date', title: 'A partir de que data você consegue começar?',
          required: false, date: { include_year: true, include_time: false } },
        { id: 'q8', type: 'paragraph', title: 'Algo que precisamos saber para receber você bem? (opcional)',
          description: 'Ex.: necessidade de acessibilidade. Não inclua dados de saúde ou de outras pessoas.',
          required: false,
          validation: { kind: 'length', rule: 'max_chars', value: 500, error: 'Use até 500 caracteres.' } },
        { id: 'q9', type: 'checkboxes', title: 'Novidades (opcional)',
          required: false, personal: true,
          options: [ { value: 'Quero receber por e-mail avisos de próximos workshops. Posso cancelar quando quiser.' } ] }
      ]
    }
  ]
};
// <<< SPEC:END

// ---------- Ponto de entrada ----------
function criarFormulario() {
  var form = buildForm_(SPEC, OPTS);
  Logger.log('ID: ' + form.getId());
  Logger.log('Título (getTitle): ' + form.getTitle());
  Logger.log('Editar: ' + form.getEditUrl());
  Logger.log('Responder (publishedUrl): ' + safe_(function () { return form.getPublishedUrl(); }, '(indisponível)'));
  Logger.log('Publicado: ' + safe_(function () { return form.isPublished(); }, '(não foi possível ler)'));
  Logger.log('Coleta de e-mail: ' + safe_(function () { return form.getEmailCollectionType(); },
    safe_(function () { return form.collectsEmail(); }, '(não foi possível ler)')));
  if (OPTS.warnings.length) Logger.log('AVISOS:\n- ' + OPTS.warnings.join('\n- '));
  if (OPTS.idMap.length) Logger.log('MAPA id -> itemId | título:\n' + OPTS.idMap.join('\n'));
  Logger.log('PENDENTES PELA INTERFACE (' + OPTS.pending.length + '):' +
    (OPTS.pending.length ? '\n' + OPTS.pending.join('\n') : ' nenhum'));
  return form;
}

// ---------- Construtor ----------
function buildForm_(spec, opts) {
  opts.warnings = []; opts.pending = []; opts.idMap = [];
  checkSpec_(spec, opts);   // lança erro ANTES de criar qualquer coisa

  var meta = spec.meta || {}, st = spec.settings || {}, quiz = spec.quiz || {};
  var prefix = opts.titlePrefix || (spec.build && spec.build.test_name_prefix) || '';
  var form = FormApp.create(prefix + meta.title);
  // FormApp.create(nome) define o NOME DO ARQUIVO; em teste ao vivo, form.getTitle() voltou vazio sem setTitle
  // (o editor e o viewform exibem o nome do arquivo como alternativa). Defina o título explicitamente.
  form.setTitle(prefix + meta.title);
  if (meta.description) form.setDescription(meta.description);
  if (meta.document_title) pend_(opts, 'meta.document_title', meta.document_title);

  // Quiz precisa ser ligado ANTES de pontuar/definir gabarito.
  if (quiz.enabled) {
    form.setIsQuiz(true);
    pend_(opts, 'quiz.release', quiz.release || 'immediately');
    pend_(opts, 'quiz.respondent_sees', quiz.respondent_sees || '(padrão do editor)');
  }

  // collect_email: none | verified | responder_input. FormApp só tem liga/desliga.
  // Tenta setEmailCollectionType (VERIFIED | RESPONDER_INPUT | DO_NOT_COLLECT); se não existir,
  // cai para setCollectEmail (liga/desliga) e registra PENDENTE_UI do tipo.
  if (st.collect_email) {
    var ECT = { none: 'DO_NOT_COLLECT', verified: 'VERIFIED', responder_input: 'RESPONDER_INPUT' }[st.collect_email];
    try {
      form.setEmailCollectionType(FormApp.EmailCollectionType[ECT]);
    } catch (e) {
      form.setCollectEmail(st.collect_email !== 'none');
      if (st.collect_email !== 'none')
        pend_(opts, 'settings.collect_email', st.collect_email + ' (setEmailCollectionType falhou: ' + e + ')');
    }
  }
  if (st.send_copy && st.send_copy !== 'never') pend_(opts, 'settings.send_copy', st.send_copy);
  if (st.allow_edit != null) form.setAllowResponseEdits(!!st.allow_edit);
  if (st.limit_one_response != null) form.setLimitOneResponsePerUser(!!st.limit_one_response);
  if (st.progress_bar != null) form.setProgressBar(!!st.progress_bar);
  if (st.shuffle_questions != null) form.setShuffleQuestions(!!st.shuffle_questions);
  if (st.confirmation_message) form.setConfirmationMessage(st.confirmation_message);
  if (st.show_summary != null) tryDo_(opts, 'settings.show_summary', st.show_summary,
    function () { form.setPublishingSummary(!!st.show_summary); });
  if (st.disable_autosave) pend_(opts, 'settings.disable_autosave', true);
  if (st.close && st.close.at) pend_(opts, 'settings.close.at', st.close.at);
  if (st.close && st.close.response_limit) pend_(opts, 'settings.close.response_limit', st.close.response_limit);

  var th = spec.theme || {};
  ['header_image', 'color', 'background_color', 'font'].forEach(function (k) {
    if (th[k]) pend_(opts, 'theme.' + k, th[k]);
  });

  var sections = spec.sections || [];
  var pageBreaks = {};   // section_id -> PageBreakItem (s1 = null: a 1ª seção não tem PageBreakItem)
  var pendingNav = [];   // [{item, spec}] resolvidos na 2ª passada

  // ---- 1ª passada: seções e itens ----
  sections.forEach(function (sec, i) {
    if (i === 0) {
      pageBreaks[sec.id] = null;
      if (sec.title || sec.description)
        opts.warnings.push(sec.id + ': a 1ª seção usa meta.title/description; title/description da seção ignorados.');
    } else {
      var pb = form.addPageBreakItem();
      if (sec.title) pb.setTitle(sec.title);
      if (sec.description) pb.setHelpText(sec.description);
      pageBreaks[sec.id] = pb;
    }
    (sec.items || []).forEach(function (it) {
      var created = addItem_(form, it, quiz, opts);
      if (!created) return;
      opts.idMap.push(it.id + ' -> ' + created.getId() + ' | ' + it.title);
      if (hasNav_(it)) pendingNav.push({ item: created, spec: it });
    });
  });

  // ---- 2ª passada: go_to por opção (choice -> PageBreakItem) ----
  pendingNav.forEach(function (p) { applyGoTo_(p.item, p.spec, pageBreaks, quiz, opts); });

  // ---- after_section: vale a seção que termina; o FormApp guarda no PageBreakItem da PRÓXIMA seção ----
  sections.forEach(function (sec, i) {
    var a = sec.after_section;
    if (!a || a === 'next') return;
    if (i === sections.length - 1) {
      if (a !== 'submit') pend_(opts, sec.id + '.after_section', a + ' (última seção; só submit faz sentido)');
      return;
    }
    var nextPb = pageBreaks[sections[i + 1].id];
    var target = a === 'submit' ? FormApp.PageNavigationType.SUBMIT : pageBreaks[a];
    try { nextPb.setGoToPage(target); }
    catch (e) { pend_(opts, sec.id + '.after_section', a + ' (setGoToPage falhou: ' + e + ')'); }
  });

  // ---- Destino das respostas ----
  var rs = spec.responses || {};
  if (rs.sheet === 'new' || rs.sheet === 'existing') {
    try {
      var ss;
      if (rs.sheet === 'new') ss = SpreadsheetApp.create(prefix + meta.title + ' (respostas)');
      else if (/^https?:\/\//.test(rs.sheet_ref || '')) ss = SpreadsheetApp.openByUrl(rs.sheet_ref);
      else throw new Error('responses.sheet_ref precisa ser URL; por nome, vincule pela interface');
      form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
      Logger.log('Planilha de respostas: ' + ss.getUrl());
    } catch (e) { pend_(opts, 'responses.sheet', rs.sheet + ' ' + (rs.sheet_ref || '') + ' (falhou: ' + e + ')'); }
    if (rs.sheet_access) pend_(opts, 'responses.sheet_access', rs.sheet_access);
  }

  // ---- Publicação (defensiva; só com OPTS.publish === true E publish.published != false) ----
  var pub = spec.publish || {};
  var wantsPublish = opts.publish === true && pub.published !== false;
  if (wantsPublish) {
    try {
      form.setPublished(true);
      if (st.accepting_responses != null) form.setAcceptingResponses(!!st.accepting_responses);
    } catch (e) { opts.warnings.push('Publicação: ' + e); }
    if (pub.audience === 'specific' && pub.responders && pub.responders.length) {
      tryDo_(opts, 'publish.responders', pub.responders, function () { form.addPublishedReaders(pub.responders); });
    } else if (pub.audience) {
      pend_(opts, 'publish.audience', pub.audience + ' (conferir "Acesso geral" em Publicar)');
    }
    if (pub.notify_responders) pend_(opts, 'publish.notify_responders', true);
  } else {
    // FormApp.create() nasce PUBLICADO (visto ao vivo em 2026-11-11: isPublished() = true).
    // Sem autorização para publicar, despublica explicitamente.
    try { form.setPublished(false); }
    catch (e) {
      // FormApp.create() nasce publicado: se a despublicação falhar, o form segue ABERTO ao público.
      Logger.log('ATENÇÃO: formulário PUBLICADO e não consegui despublicar (' + e + '). ID=' + form.getId() +
                 ' | editar: ' + form.getEditUrl() + ' | despublique AGORA pela interface.');
      throw new Error('Formulário criado mas ainda PUBLICADO (setPublished(false) falhou: ' + e + '). ' +
                      'Abra ' + form.getEditUrl() + ' e despublique agora.');
    }
    if (pub.published !== false)
      opts.warnings.push('Formulário despublicado (OPTS.publish = false). Publicar só com confirmação do dono.');
  }

  return form;
}

// ---------- Checagens antes de criar ----------
var TIPOS_ = ['short_text', 'paragraph', 'multiple_choice', 'checkboxes', 'dropdown', 'linear_scale',
  'rating', 'mc_grid', 'checkbox_grid', 'date', 'time', 'file_upload', 'title_description', 'image', 'video'];

function checkSpec_(spec, opts) {
  var errs = [];
  if (!spec || !spec.meta || !spec.meta.title) errs.push('meta.title ausente');
  if (!opts.allowDraft) {
    if (spec.status !== 'approved') errs.push('status != approved (use OPTS.allowDraft só em teste local)');
    if (JSON.stringify(spec).indexOf('pending_owner') >= 0) errs.push('spec contém pending_owner');
  }
  if (spec.build && spec.build.path && spec.build.path !== 'apps_script')
    opts.warnings.push('build.path = ' + spec.build.path + ' (este script é o caminho apps_script; confira o plano).');
  var secIds = {}, itemIds = {}, sections = spec.sections || [];
  if (!sections.length || sections[0].id !== 's1') errs.push('a 1ª seção deve ter id s1');
  sections.forEach(function (s) {
    if (secIds[s.id]) errs.push('id de seção repetido: ' + s.id);
    secIds[s.id] = true;
    if (!(s.items || []).length) errs.push('seção sem itens: ' + s.id);
  });
  sections.forEach(function (s, i) {
    if (s.after_section && s.after_section !== 'next' && s.after_section !== 'submit' &&
        (!secIds[s.after_section] || s.after_section === 's1'))
      errs.push(s.id + '.after_section inválido (inexistente ou s1): ' + s.after_section);
    var withGoTo = 0;
    (s.items || []).forEach(function (it) {
      if (itemIds[it.id]) errs.push('id de item repetido: ' + it.id);
      itemIds[it.id] = true;
      if (TIPOS_.indexOf(it.type) < 0) errs.push(it.id + ': tipo desconhecido ' + it.type);
      if (!it.title && it.type !== 'image') errs.push(it.id + ': título vazio');
      if (hasNav_(it)) {
        withGoTo++;
        if (it.other) errs.push(it.id + ': other e go_to são incompatíveis');
        it.options.forEach(function (o) {
          if (!o.go_to) errs.push(it.id + ': se uma opção tem go_to, todas têm (use next)');
          else if (o.go_to !== 'next' && o.go_to !== 'submit' && (!secIds[o.go_to] || o.go_to === 's1'))
            errs.push(it.id + ': go_to inválido (inexistente ou s1): ' + o.go_to);
        });
      } else if ((it.options || []).some(function (o) { return o && o.go_to; })) {
        errs.push(it.id + ': go_to só vale em multiple_choice e dropdown');
      }
    });
    if (withGoTo > 1) errs.push(s.id + ': mais de uma pergunta com go_to');
    if (withGoTo && s.after_section) opts.warnings.push(s.id + ': after_section convive com go_to; a navegação por resposta prevalece.');
  });
  if (errs.length) throw new Error('SPEC inválido:\n- ' + errs.join('\n- '));
}

// ---------- Itens ----------
function addItem_(form, it, quiz, opts) {
  var item, t = it.type;
  switch (t) {
    case 'short_text':        item = form.addTextItem(); break;
    case 'paragraph':         item = form.addParagraphTextItem(); break;
    case 'multiple_choice':   item = form.addMultipleChoiceItem(); break;
    case 'checkboxes':        item = form.addCheckboxItem(); break;
    case 'dropdown':          item = form.addListItem(); break;
    case 'linear_scale':      item = form.addScaleItem(); break;
    case 'mc_grid':           item = form.addGridItem(); break;
    case 'checkbox_grid':     item = form.addCheckboxGridItem(); break;
    case 'date':
      item = (it.date && it.date.include_time) ? form.addDateTimeItem() : form.addDateItem(); break;
    case 'time':
      item = (it.time && it.time.duration) ? form.addDurationItem() : form.addTimeItem(); break;
    case 'title_description': item = form.addSectionHeaderItem(); break;
    case 'image':             item = form.addImageItem(); break;
    case 'video':             item = form.addVideoItem(); break;
    case 'rating':
      pend_(opts, it.id + ' (rating)', JSON.stringify(it.rating || {}) + ' título "' + it.title + '" — item AUSENTE no form; criar na posição do ' + it.id);
      return null;
    case 'file_upload':
      pend_(opts, it.id + ' (file_upload)', JSON.stringify(it.file_upload || {}) + ' título "' + it.title + '" — item AUSENTE no form; criar na posição do ' + it.id);
      return null;
    default:
      opts.warnings.push('Tipo não suportado ignorado: ' + t + ' (' + it.id + ')');
      return null;
  }
  if (it.title) item.setTitle(it.title);
  if (it.description) item.setHelpText(it.description);
  if (it.required && typeof item.setRequired === 'function') item.setRequired(true);

  if (t === 'multiple_choice' || t === 'checkboxes' || t === 'dropdown') addChoices_(item, it, quiz, opts);

  if (t === 'linear_scale') {
    var sc = it.scale || {};
    var low = sc.low != null ? sc.low : 1, high = sc.high != null ? sc.high : 5;
    if (high < 3) { pend_(opts, it.id + '.scale', JSON.stringify(sc) + ' (FormApp exige high de 3 a 10; ajustar pela interface)'); high = 3; }
    item.setBounds(low, high);
    if (sc.low_label || sc.high_label) item.setLabels(sc.low_label || '', sc.high_label || '');
  }

  if (t === 'mc_grid' || t === 'checkbox_grid') {
    var g = it.grid || {};
    item.setRows(g.rows || []).setColumns(g.columns || []);
    if (g.one_per_column) tryDo_(opts, it.id + '.grid.one_per_column', true, function () {
      var gv = (t === 'mc_grid') ? FormApp.createGridValidation() : FormApp.createCheckboxGridValidation();
      item.setValidation(gv.requireLimitOneResponsePerColumn().build());
    });
    if (g.shuffle_rows) pend_(opts, it.id + '.grid.shuffle_rows', true);
  }

  if (t === 'date' && it.date && it.date.include_year === false) item.setIncludesYear(false);

  if (t === 'image') {
    var im = it.image || {};
    if (im.alt_text) tryDo_(opts, it.id + '.image.alt_text', im.alt_text, function () { item.setAltText(im.alt_text); });
    if (im.width) tryDo_(opts, it.id + '.image.width', im.width, function () { item.setWidth(im.width); });
    if (opts.fetchImages && /^https?:\/\//.test(im.source || '')) {
      tryDo_(opts, it.id + '.image.source', im.source, function () { item.setImage(UrlFetchApp.fetch(im.source).getBlob()); });
    } else {
      pend_(opts, it.id + '.image.source', im.source || '(vazio)');
    }
  }

  if (t === 'video') {
    var vd = it.video || {};
    if (vd.youtube_url) item.setVideoUrl(vd.youtube_url);
    if (vd.caption) pend_(opts, it.id + '.video.caption', vd.caption + ' (FormApp não tem legenda própria)');
  }

  if (it.validation) applyValidation_(item, it, opts);
  if (quiz.enabled) applyQuiz_(item, it, opts);
  return item;
}

function addChoices_(item, it, quiz, opts) {
  var os = it.options || [], t = it.type;
  var key = (quiz.enabled && it.answer_key) ? it.answer_key : null;
  if (hasNav_(it)) {
    item.setChoiceValues(os.map(function (o) { return o.value; })); // provisório; navegação na 2ª passada
  } else if (key) {
    item.setChoices(os.map(function (o) { return item.createChoice(o.value, key.indexOf(o.value) >= 0); }));
  } else {
    item.setChoiceValues(os.map(function (o) { return o.value; }));
  }
  if (it.other && (t === 'multiple_choice' || t === 'checkboxes')) item.showOtherOption(true);
  if (it.shuffle_options) {
    if (typeof item.setShuffleOptions === 'function') item.setShuffleOptions(true);
    else pend_(opts, it.id + '.shuffle_options', true);
  }
}

function hasNav_(it) {
  return (it.type === 'multiple_choice' || it.type === 'dropdown') &&
    (it.options || []).some(function (o) { return o && o.go_to; });
}

// ---------- go_to por opção ----------
function applyGoTo_(item, it, pageBreaks, quiz, opts) {
  var N = FormApp.PageNavigationType;
  if (quiz.enabled && it.answer_key)
    pend_(opts, it.id + '.answer_key', JSON.stringify(it.answer_key) + ' (createChoice não aceita gabarito junto com navegação; marcar pela interface)');
  item.setChoices(it.options.map(function (o) {
    var dest = o.go_to === 'next' ? N.CONTINUE : (o.go_to === 'submit' ? N.SUBMIT : pageBreaks[o.go_to]);
    return item.createChoice(o.value, dest);
  }));
}

// ---------- Validação ----------
function applyValidation_(item, it, opts) {
  var v = it.validation, t = it.type;
  try {
    var b, val = v.value;
    if (t === 'checkboxes') {
      if (v.kind !== 'selection') throw new Error('checkboxes só aceita kind selection');
      b = FormApp.createCheckboxValidation();
      if (v.rule === 'at_least') b.requireSelectAtLeast(val);
      else if (v.rule === 'at_most') b.requireSelectAtMost(val);
      else if (v.rule === 'exactly') b.requireSelectExactly(val);
      else throw new Error('rule desconhecida: ' + v.rule);
    } else if (t === 'short_text' || t === 'paragraph') {
      b = (t === 'paragraph') ? FormApp.createParagraphTextValidation() : FormApp.createTextValidation();
      var kind = v.kind, rule = v.rule;
      if (kind === 'number' && t === 'short_text') {
        if (rule === 'gt') b.requireNumberGreaterThan(val);
        else if (rule === 'gte') b.requireNumberGreaterThanOrEqualTo(val);
        else if (rule === 'lt') b.requireNumberLessThan(val);
        else if (rule === 'lte') b.requireNumberLessThanOrEqualTo(val);
        else if (rule === 'eq') b.requireNumberEqualTo(val);
        else if (rule === 'neq') b.requireNumberNotEqualTo(val);
        else if (rule === 'between') b.requireNumberBetween(val[0], val[1]);
        else if (rule === 'not_between') b.requireNumberNotBetween(val[0], val[1]);
        else if (rule === 'is_number') b.requireNumber();
        else if (rule === 'whole_number') b.requireWholeNumber();
        else throw new Error('rule number desconhecida: ' + rule);
      } else if (kind === 'text' && t === 'short_text') {
        if (rule === 'contains') b.requireTextContains(val);
        else if (rule === 'not_contains') b.requireTextDoesNotContain(val);
        else if (rule === 'email') b.requireTextIsEmail();
        else if (rule === 'url') b.requireTextIsUrl();
        else throw new Error('rule text desconhecida: ' + rule);
      } else if (kind === 'length') {
        if (rule === 'max_chars') b.requireTextLengthLessThanOrEqualTo(val);
        else if (rule === 'min_chars') b.requireTextLengthGreaterThanOrEqualTo(val);
        else throw new Error('rule length desconhecida: ' + rule);
      } else if (kind === 'regex') {
        // Dialeto da regex: [não verificado]. Testar um valor válido e um inválido no form real.
        if (rule === 'contains') b.requireTextContainsPattern(val);
        else if (rule === 'not_contains') b.requireTextDoesNotContainPattern(val);
        else if (rule === 'matches') b.requireTextMatchesPattern(val);
        else if (rule === 'not_matches') b.requireTextDoesNotMatchPattern(val);
        else throw new Error('rule regex desconhecida: ' + rule);
      } else {
        throw new Error('kind ' + kind + ' não vale para ' + t);
      }
    } else {
      throw new Error('tipo ' + t + ' não aceita validation');
    }
    if (v.error) b.setHelpText(v.error);
    item.setValidation(b.build());
  } catch (e) {
    pend_(opts, it.id + '.validation', JSON.stringify(v) + ' (falhou: ' + e + ')');
  }
}

// ---------- Quiz: points, answer_key, feedback ----------
function applyQuiz_(item, it, opts) {
  var t = it.type;
  if (it.points != null) {
    if (typeof item.setPoints === 'function') item.setPoints(it.points);
    else pend_(opts, it.id + '.points', it.points);
  }
  if (it.answer_key && (t === 'short_text' || t === 'mc_grid' || t === 'checkbox_grid'))
    pend_(opts, it.id + '.answer_key', JSON.stringify(it.answer_key) + ' (FormApp não define gabarito neste tipo)');
  var fb = it.feedback;
  if (!fb) return;
  var canFb = (t === 'multiple_choice' || t === 'checkboxes' || t === 'dropdown') && it.answer_key;
  if (fb.right) {
    if (canFb) item.setFeedbackForCorrect(FormApp.createFeedback().setText(fb.right).build());
    else pend_(opts, it.id + '.feedback.right', fb.right);
  }
  if (fb.wrong) {
    if (canFb) item.setFeedbackForIncorrect(FormApp.createFeedback().setText(fb.wrong).build());
    else pend_(opts, it.id + '.feedback.wrong', fb.wrong);
  }
  if (fb.general) pend_(opts, it.id + '.feedback.general', fb.general);
}

// ---------- Utilidades ----------
function pend_(opts, field, value) {
  opts.pending.push('PENDENTE_UI: ' + field + ' ' + (typeof value === 'string' ? value : JSON.stringify(value)));
}
function tryDo_(opts, field, value, fn) {
  try { fn(); } catch (e) { pend_(opts, field, JSON.stringify(value) + ' (falhou: ' + e + ')'); }
}
function safe_(fn, fallback) { try { return fn(); } catch (e) { return fallback; } }

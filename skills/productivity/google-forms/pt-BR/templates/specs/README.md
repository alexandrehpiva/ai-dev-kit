# Modelos de FORM-SPEC

**Um modelo é um ponto de partida que já passa na estrutura do contrato; o que ele não pode ter pronto é a decisão do dono sobre dados pessoais.** Copie, adapte e só então apresente ao dono. O contrato é `FORM-SPEC.md`; os padrões de texto são de `style-guide.md`; a pauta de revisão é `ux-review.md`.

## Diagnóstico do modo de falha

- **Molde copiado sem adaptar.** O modelo de inscrição vira feedback e leva junto nome e telefone que ninguém usa. Por isso toda pergunta tem `use` e você corta a que não se liga ao seu `brief.goal`.
- **Base legal herdada do modelo.** Um valor preenchido parece decidido. Por isso, nos modelos com dado pessoal, base legal, controlador, contato, retenção e compartilhamento vêm `pending_owner`: quem decide é o dono do formulário (e o encarregado/DPO, se houver), nunca o agente. Enquanto houver `pending_owner`, o spec não pode ser aprovado.
- **Placeholder esquecido no texto do respondente.** O aviso de privacidade da descrição traz trechos `[PREENCHER: ...]` até o dono decidir. Publicar com eles é falha bloqueante.
- **Dados de exemplo tratados como reais.** Nomes, datas, vagas e e-mails dos modelos são fictícios (`example.com`, `example.org`).

## Os modelos

Todos: `status: draft`, `build.path: ui`, tema Roxo `#673ab7` ou Índigo `#3f51b5` (as únicas cores da paleta do Forms com contraste 4,5:1 com branco), ids estáveis e `use` em toda pergunta.

| Modelo (arquivo) | Quando usar | Itens / seções | Dados pessoais coletados | Caminho de construção recomendado |
|---|---|---|---|---|
| `nps-survey.yaml` | Medir NPS e satisfação de clientes após um atendimento, sem identificar ninguém | 7 itens, 2 seções, 4 obrigatórias; NPS 0-10, CSAT, facilidade, frequência, canal, 2 abertas opcionais | Nenhum (anônima: sem e-mail, sem login, sem upload). Texto livre avisa para não incluir dados | UI (tema). Sem ramificação: pode ir por `apps_script`, com a cor aplicada pela UI depois |
| `event-registration.yaml` | Inscrição com vagas limitadas: turma, dados de contato, necessidade de acessibilidade, novidades | 5 itens, 3 seções, 2 obrigatórias; limite de respostas = vagas; edição após envio ligada | Nome, e-mail (Configurações), texto livre de acessibilidade (pode ser sensível), aceite de novidades. Nível `sensitive` por cautela | UI (tema e limite de respostas só existem na UI) |
| `anonymous-internal-feedback.yaml` | Retrospectiva ou clima de um time, com promessa de anonimato verdadeira | 6 itens, 2 seções, 2 obrigatórias; grade 4x5, 2 escalas, começar/parar/continuar | Nenhum. Sem área, cargo nem tempo de casa; encerramento por data | UI (tema, encerramento por data) |
| `lead-signup.yaml` | Captar contato em troca de conteúdo, com consentimentos separados | 4 itens, 2 seções, 2 obrigatórias; interesse, nome, telefone opcional (regex), consentimento de marketing opcional | Nome, e-mail (Configurações), telefone opcional, aceite de conteúdos. Nível `personal` | UI (tema; regex também vai por `apps_script`) |
| `quiz-assessment.yaml` | Exercício de autoavaliação com nota imediata, gabarito e explicação por resposta | 6 itens, 2 seções, 5 obrigatórias; 7 pontos; múltipla escolha, caixas, resposta curta, 1 aberta sem pontos | Nenhum (sem identificação) | UI (liberação de nota e o que o respondente vê só existem na UI) |
| `academic-research-consent.yaml` | Pesquisa com consentimento (TCLE) e desvio para quem não concorda; bateria Likert e perfil no fim | 9 itens (3 de texto do TCLE), 3 seções, 2 obrigatórias; 2 caminhos (aceite / recusa) | Faixa etária, nível de ensino e texto livre (podem identificar em combinação). Nível `personal` por cautela; sem nome nem e-mail | UI (tema, encerramento por data) |
| `branching-triage.yaml` | Central de solicitações com 4 caminhos, um deles com segundo nível de desvio, trecho comum e upload | 16 itens, 8 seções, 15 obrigatórias; 5 rotas de seções para 4 tipos de pedido | E-mail verificado (login Google) e comprovante enviado em arquivo. Nível `personal` | UI obrigatória (upload de arquivo; tema). A API não cria upload e o Apps Script não tem |

Contagens conferidas em 2026-11-11 com um script estático local (itens, seções e obrigatórias de cada arquivo).

## Como adaptar

<o-que-fazer>

1. **Escolha o modelo pela tabela** e copie para a pasta de trabalho com o nome do seu formulário: `<nome-do-form>.form-spec.yaml`. Nunca edite o modelo no lugar.
2. **Ajuste `brief` e `meta`.** Reescreva `brief.goal` (a decisão que as respostas alimentam), `audience`, `channel` e `estimated_minutes`. Troque título, descrição e `document_title` (`AAAA-MM-DD Tipo - Assunto`). Mantenha a descrição com propósito, tempo e uso dos dados. Os comentários `ADAPTAR` no topo de cada arquivo listam o que mudar; apague os comentários quando terminar.
3. **Corte as perguntas sem `use` para o seu objetivo.** Para cada pergunta, escreva em uma frase a decisão que ela alimenta; se não conseguir, remova. Ao remover, não renumere: o id de item removido nunca é reaproveitado (o próximo novo é o maior id atual mais 1). Se um item sair de uma seção, confira que a seção não ficou vazia.
4. **Entreviste o dono sobre dados pessoais antes de preencher `privacy`.** Rode o Bloco 3 da entrevista do `FORM-SPEC.md`. Substitua cada `pending_owner` e cada `[PREENCHER: ...]` do texto do respondente pela resposta do dono. Se ele disser "decide você", ofereça as duas saídas do contrato (formulário sem dado pessoal ou ele responder). Nunca preencha base legal por conta própria.
5. **Mantenha o que o dono não decidiu como `pending_owner`.** Procure o que sobrou com `grep -n "pending_owner\|PREENCHER" <seu-arquivo>`. Qualquer resultado impede `status: approved`.
6. **Valide o esquema:** `python3 <pasta-da-skill>/scripts/validate_spec.py <seu-arquivo>` (Windows: `py -3 <pasta-da-skill>\scripts\validate_spec.py <seu-arquivo>`; `<pasta-da-skill>` é a pasta onde está o `SKILL.md`). Arquivo `.yaml` exige PyYAML: `python3 -m pip install --user pyyaml`; se o Python for gerenciado pelo sistema (erro `externally-managed-environment`), use um venv (`python3 -m venv .venv && .venv/bin/pip install pyyaml`; Windows: `.venv\Scripts\pip`) e rode o validador com o `python` do venv. Ou escreva o spec em JSON. Todo erro é corrigido ou vira pergunta ao dono; depois percorra a seção "Validação do spec" do `FORM-SPEC.md`.
7. **Passe pela revisão de UX do Modo E** (`ux-review.md`) com um revisor que não seja quem adaptou. Corrija bloqueantes e altos; `pending_owner` de privacidade aparece como pergunta ao dono, não como achado resolvido.
8. **Apresente o resumo ao dono** no formato do `FORM-SPEC.md` e espere o "aprovado" explícito. Só então `status: approved` e `approved_at`.
9. **Construa** pelo `build.path`, verifique item a item contra o spec e faça a revisão de UX do formulário real (Modo F).

</o-que-fazer>

## O que cada modelo ensina (e o que reconferir ao adaptar)

- **Satisfação/NPS:** a q1 é previsão por desenho da métrica (exceção declarada ao UX-C4); a promessa de "anônimas" só vale enquanto não houver e-mail, login obrigatório, upload nem pergunta que identifique (UX-H8).
- **Inscrição:** e-mail só pelas Configurações (não repita em pergunta, UX-A4); consentimento de novidades em seção própria, desmarcado e opcional (UX-H5); a q4 pode ser dado sensível: mantenha só com decisão do dono (UX-H6) e, se sair, não reaproveite o id. A mensagem de encerramento fica em `owner_notes` (o esquema não tem campo próprio).
- **Feedback interno:** link para "qualquer pessoa com o link" divulgado só em canal interno; restringir ao domínio exige login e a palavra "anônimo" cai (UX-H8). Em time pequeno, até o texto livre pode expor alguém.
- **Cadastro:** telefone só com uso declarado (UX-H2); regex tolerante, testada na visão do respondente (UX-E5); marketing separado do envio do conteúdo.
- **Quiz:** gabarito e pontos em toda pergunta pontuável, a posição da correta varia, distratores do mesmo tamanho; sem promessa de cronômetro (UX-F6). Para avaliar pessoas, mude para coleta de e-mail, nota após revisão manual e gabarito oculto (UX-J8), e preencha `privacy`.
- **Acadêmica:** o texto e a forma do TCLE dependem do comitê de ética [não verificado nesta skill]; os textos de riscos e benefícios são exemplo. A recusa vai direto para o envio, por isso a confirmação é neutra para os dois caminhos.
- **Triagem ramificada:** uma pergunta com `go_to` por seção, nenhuma dessas seções com `after_section`, destinos sempre para frente (nunca `s1`). Antes de construir, desenhe o mapa de caminhos (está no comentário do topo do arquivo) e, no formulário real, percorra cada caminho com Avançar e Voltar (UX-B4, UX-B5). Em Apps Script, `answer_key` e `go_to` no mesmo item não coexistem (PENDENTE_UI); este modelo não usa quiz.

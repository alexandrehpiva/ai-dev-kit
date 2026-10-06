# provenance-marking.md — marcar de onde veio cada afirmação

Guia para gravar conteúdo em base de conhecimento, documentação ou qualquer arquivo que outra sessão vá ler como fato.

## Diagnóstico do modo de falha

Um documento quase nunca é inteiro confirmado ou inteiro inventado: ele mistura o que o usuário disse, o que estava no código, e o que o agente deduziu para fechar a frase. Um aviso genérico no topo ("este conteúdo pode conter imprecisões") não resolve, porque o consumo real é por pedaço — alguém copia um parágrafo, um agente cita uma linha, um terceiro documento herda a afirmação. A marca de incerteza fica para trás e a inferência viaja sozinha, agora com cara de fato. É assim que a bola de neve começa: não com um documento errado, mas com **uma frase sem procedência dentro de um documento correto**.

## O que conta como fonte primária

**Conta:**
- Código, configuração ou dado **lido nesta sessão**, com path.
- Documentação oficial do produto/fornecedor lida nesta sessão, com URL ou path.
- Fala do usuário **nesta conversa**, citável por ID de diretiva (`U-n` no checklist).
- Saída de um comando **executado nesta sessão**, com o comando registrado.

**Não conta:**
- Outra nota da base de conhecimento — inclusive uma escrita pelo próprio agente.
- Memória do agente sobre o projeto, por mais convicta que seja.
- "É o padrão da indústria", "normalmente funciona assim", "deve ser".
- Resposta anterior do próprio agente nesta conversa.
- Saída de subagente, enquanto os identificadores não forem conferidos no disco pelo agente principal (ver `subagent-delegation.md`).
- Transcrição interpretada por ferramenta de IA, **quando usada para sustentar um fato técnico** — ver a regra de desempate abaixo.

### Transcrição interpretada tem dois papéis

Convenções de bases de conhecimento costumam dizer — corretamente — que a transcrição interpretada entregue pelo usuário **é a fonte primária da nota daquela reunião**: é o registro que o usuário entregou, e nenhum trecho dela pode ser descartado ao virar nota.

O que ela **não** é: fonte primária de um **fato técnico afirmado dentro dela**. "O endpoint aceita 100 itens", dito numa reunião e capturado por uma ferramenta que interpreta a fala, sustenta *"fulano afirmou que…"* — não sustenta o fato em si. Para o fato, a fonte é o código ou a documentação oficial. [não confirmado: se existir gravação original além da transcrição, não há convenção verificada nesta sessão sobre qual delas prevalece em caso de divergência — tratar como pergunta ao usuário quando o caso aparecer, não como regra já resolvida.]

**Desempate:** ao **registrar a reunião**, a transcrição manda. Ao **afirmar como o sistema funciona**, ela é relato, e a afirmação nasce atribuída a quem falou.

## Regra de ouro: documento não é prova

Ao se apoiar numa nota existente, cite **os dois**: o arquivo de onde veio e a fonte original que ele declara. Se a nota não declara fonte rastreável, o que for produzido a partir dela nasce marcado como **derivado não confirmado**, e a lacuna vira pergunta ao usuário via `grill-me`.

Isso vale mesmo quando a nota parece sólida, e especialmente quando o próprio agente a escreveu — é exatamente o elo da corrente onde a alucinação antiga se disfarça de conhecimento consolidado.

## Como marcar — dois lugares, não um

### 1. No cabeçalho do documento (permite varredura depois)

**A marca no topo é obrigatória sempre. O que varia é a forma — e a forma é decisão do projeto, não sua.** Inaugurar um campo que nenhuma outra nota usa é anti-padrão em base de conhecimento, e seria esta skill cometendo exatamente o que ela condena.

Ordem de preferência:

1. **O projeto já tem propriedade de proveniência** → use essa, sem criar outra. Exemplo: numa base de notas, um campo `fonte:` já aparece em vários tipos de nota (transcrição de reunião, documento de portal, página de wiki) — não é exclusivo de um tipo. Confira o que já existe em notas do mesmo tipo antes de propor campo novo.
2. **O projeto não tem propriedade para isso** → **não crie sozinho.** Proponha ao usuário, com o nome do campo e os valores, e registre a proposta na fila de dúvidas do checklist. **Enquanto ele não responder, a gravação não fica bloqueada:** use a marca inline (`[não confirmado: ...]`) no corpo — é o que a varredura por `grep` de fato encontra — e some um aviso destacado (callout) no topo só como reforço visual para quem abre o arquivo, nunca como substituto da marca inline.

Proposta típica **quando o projeto não tem nenhuma propriedade de proveniência ainda** (item 2 acima), para o usuário aprovar ou trocar:

```yaml
---
fonte: {origem real — URL, path do código, "usuário na sessão de {data}"}
verificado-em: {YYYY-MM-DD}
status-verificacao: verificado | parcial | nao-confirmado
---
```

**Se o projeto já usa `fonte:` (ou equivalente) por convenção anterior — caso do item 1 —, não a inclua nesta proposta.** Proponha só os campos genuinamente novos (no exemplo acima, `verificado-em` e `status-verificacao`; `fonte:` já existia e não entra em proposta nenhuma).

- `verificado` — toda afirmação do documento tem fonte primária rastreável.
- `parcial` — mistura; as partes frágeis estão marcadas inline.
- `nao-confirmado` — o documento inteiro é derivado ou inferido.

### 2. Na frase (sobrevive ao copiar/colar)

```markdown
O webhook reenvia por até 3 tentativas [não confirmado: inferido do nome do
campo `retry_count`, sem doc oficial lida].
```

Formato: `[não confirmado: {como você chegou nisso}]`. O motivo entra sempre — é ele que diz ao próximo leitor **o que fazer** para confirmar.

Variantes úteis:
- `[não confirmado: dito pelo usuário em reunião, sem doc]` — relato, não registro.
- `[não confirmado: derivado de {nota.md}, que não declara fonte]` — herança frágil.
- `[a confirmar com {quem}]` — quando já se sabe quem resolve.

## Bom / Ruim

Os identificadores dos exemplos abaixo (`api/batch.ts:42`, `MAX_BATCH`, `retry_count`, `docker-compose.yml:12`) são **fictícios** — ilustram a forma da marcação, não um sistema real.

| Ruim | Bom |
|---|---|
| "O endpoint aceita até 100 itens por lote." | "O endpoint aceita até 100 itens por lote (`api/batch.ts:42`, constante `MAX_BATCH`)." |
| "O endpoint provavelmente aceita 100 itens." | "O endpoint aceita 100 itens [não confirmado: inferido do limite do cliente, não da API]." |
| Callout `[!warning]` no topo e nada no corpo | Callout no topo **e** marca na frase específica |
| "Segundo a nota de arquitetura, o banco é Postgres." | "A nota `arquitetura.md` afirma Postgres; confirmado em `docker-compose.yml:12`." |
| Apagar a marca ao revisar o texto | Só apagar a marca junto com a evidência que a resolveu |

## Anti-padrões

- **Marcar tudo por precaução.** Se toda frase é "não confirmado", a marca perde sinal e o leitor ignora. Marque o que de fato não tem fonte — e busque a fonte antes de desistir.
- **Marcar em vez de perguntar.** A marca **não** substitui a pergunta ao usuário. Toda afirmação sem fonte rastreável é marcada **e** entra na fila de dúvidas do checklist; e tudo que depende da dúvida fica sem ser gravado até ela ser respondida — não só o que mudaria a conclusão do documento. Decidir que algo "é aceitável deixar aberto" é julgamento do agente, e é justamente o que está sob suspeita.
- **Usar a marca para se proteger.** Marcar uma afirmação e mesmo assim construir três documentos em cima dela é a bola de neve com rastreabilidade — não é melhor, só é documentada.
- **Remover a marca ao reusar.** Ao copiar um trecho marcado para outro documento, a marca vai junto. Sempre.

## Varredura posterior

Como as formas da marca são canônicas e poucas, o passivo é auditável a qualquer momento:

```bash
# toda variante da marca inline, em uma expressão só
grep -rnE --include='*.md' --exclude-dir=.git --exclude-dir=.claude \
  '\[(não confirmado|a confirmar)' .

# documentos inteiros frágeis — inclua 'parcial', que é onde mora a mistura
grep -rlE --include='*.md' --exclude-dir=.git --exclude-dir=.claude \
  '^status-verificacao: (parcial|nao-confirmado)' .
```

Ajuste o segundo comando ao campo que o projeto de fato usa. **Exclua cópias de worktree e diretórios de ferramenta** (`.git`, `.claude`, etc.): sem isso, um repositório com worktrees devolve cada ocorrência multiplicada e a varredura vira ruído.

Use isso antes de publicar, antes de basear uma decisão num conjunto de notas, e ao retomar um tema depois de semanas.

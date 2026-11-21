# Checklist núcleo

Vale para todo serviço, em qualquer stack. Os guias de `stacks/` acrescentam itens específicos às mesmas dimensões; eles não substituem este checklist. Leia antes da Fase 2 — é obrigatório.

Para cada item, marque **Conforme**, **Parcial**, **Não conforme** ou **Não verificado**, com evidência (`caminho:linha` ou comando). Pule uma seção só se não se aplicar, e diga por quê (ex.: "D — o serviço não tem banco").

## A. Arquitetura e camadas

- [ ] Padrão arquitetural identificado e **nomeado** (camadas, hexagonal, clean, monólito modular, vertical slice, MVC do framework…), com onde aparece no código e por que parece ter sido escolhido. Use `stacks/architecture/` para reconhecer.
- [ ] Regra de dependência entre camadas: existe? está **imposta** por ferramenta (lint de fronteiras, ArchUnit, import-linter, `internal/`)? Faça grep de violações: domínio importando framework, ORM, SDK ou HTTP; aplicação importando adaptadores concretos.
- [ ] Fronteiras entre módulos: cada módulo tem API pública (índice, interface, pacote exportado)? Há imports profundos de um módulo para dentro de outro?
- [ ] Ciclos de dependência medidos com a ferramenta da stack (madge, dependency-cruiser, `go vet`/`go list`, jdeps, pydeps) — número e comando no relatório.
- [ ] Pastas transversais (`common`, `shared`, `infra`, `utils`, `core`) são folhas, ou conhecem módulos de negócio?
- [ ] Tamanho e coesão: algum módulo concentra responsabilidades demais? Conte arquivos, casos de uso e linhas por módulo.
- [ ] Onde moram as regras de negócio? Entidades anêmicas são decisão consciente ou acidente?
- [ ] Dependências externas (banco, filas, APIs de terceiros, relógio, gerador de id) isoladas atrás de contratos substituíveis em teste?

## B. Estrutura de arquivos e convenções

- [ ] Organização por feature ou por tipo técnico, e se é consistente em todo o repositório.
- [ ] Nomes de arquivos e símbolos seguem uma convenção — verificada por lint ou só por costume? A convenção bate com a **versão** do framework (ver guia de stack)?
- [ ] Utilitários: há critério escrito para o que é compartilhado e o que é do módulo? Há pastas-depósito que acumulam o que não tem lugar?
- [ ] Pastas vazias, código morto, arquivos órfãos, exports não usados (knip, ts-prune, vulture, deadcode), TODOs sem dono nem prazo.
- [ ] Fonte da verdade duplicada: o mesmo enum, constante, schema ou tipo definido em dois lugares (ex.: enum do domínio e enum do ORM) sem teste que garanta igualdade.
- [ ] Código só de teste ou de simulação indo para o artefato de produção (build).
- [ ] Lógica duplicada entre serviços (módulo copiado de um repositório para outro): há teste de paridade que roda os mesmos casos nas duas cópias, com o caminho de configuração que ele espera resolvido nos dois ambientes? Sinal: arquivos de mesmo nome e conteúdo quase igual em repositórios irmãos (`diff -rq` ou hash). Sem teste de paridade → Média; se a cópia já divergiu em regra de negócio → Alta.

## C. Qualidade do código

- [ ] Rigor de tipos: modo estrito ligado? Quantos `any`/`Any`/`interface{}`/casts forçados/supressões de lint/`# type: ignore` em código de produção (conte com grep)?
- [ ] Complexidade: funções e arquivos longos, aninhamento profundo, parâmetros demais (meça com a ferramenta da stack quando houver).
- [ ] Tratamento de erros: erro de domínio separado de erro técnico; mapeamento para a resposta externa num lugar só; nenhum erro engolido em silêncio (`catch {}`, `except: pass`, `_ = err`); nenhuma mensagem interna, stack trace ou SQL vazando ao cliente.
- [ ] Decisão de erro por status ou código estruturado, nunca pelo **texto** da mensagem. Sinal: regex, `includes`, `startswith` ou `in` sobre `message`/`str(err)`/corpo de erro para escolher o caminho. Como checar: `grep -rnE "(message|msg|detail)\.(includes|startsWith|match)|re\.(search|match)\(.*(err|message)"`. Alta se decide fluxo; Média se só escolhe o texto exibido.
- [ ] Descartes e tetos silenciosos: campo, item ou resultado acima de um limite é descartado sem log e sem efeito visível, ou o limite esconde opção do usuário. Como checar: grep de `slice(0,`, `[:N]`, `limit`, `max` em caminhos de entrada e de resposta; para cada um, onde o descarte aparece (log, métrica, mensagem). Média; Alta se o descarte altera resultado de negócio.
- [ ] Defaults silenciosos de regra de negócio: o sistema assume o que a entrada não diz (valor padrão, condição ausente tratada como falsa, campo faltante preenchido). Como checar: grep de `??`, `||`, `.get(.., default)`, `default=` em regras de negócio; confira se a ausência vira pergunta, erro ou registro. Alta se afeta valor ou direito do usuário; Média caso contrário.
- [ ] Precisão e ordem de operações numéricas: arredondamento ou truncagem aplicado **antes** de comparar ou ordenar (empates falsos); dinheiro e quantidades arredondados só no ponto de pagamento ou de exibição, não nos passos intermediários. Como checar: grep de `round`, `floor`, `toFixed`, `quantize` e veja se o resultado alimenta comparação, soma ou ordenação; teste com valores que empatam depois de arredondar. Alta se afeta dinheiro; Média caso contrário.
- [ ] Laços e repetições com orçamento: nova tentativa, releitura, polling ou reformulação checam o prazo restante e têm teto de iterações; a mesma pergunta ou a mesma operação não é reapresentada sem ter mudado nada. Como checar: localize cada laço que chama rede ou modelo e confirme prazo, contador e backoff. Alta se pode estourar o tempo da requisição ou da fila; Média caso contrário.
- [ ] Concorrência e consistência: transações onde há invariante, idempotência em operações repetíveis, travas ou concorrência otimista onde há disputa; comentário explica o porquê nas decisões sutis.
- [ ] Logs: estruturados, com id de correlação, nível coerente, **sem dado pessoal nem segredo** (inclui cabeçalhos e corpos registrados automaticamente pelo middleware de log) e **diagnosticáveis**: trazem códigos, identificadores e a primeira diferença ou causa, sem gravar o texto livre do usuário. Se o log só ajuda quando contém o texto, o desenho do log é o achado.
- [ ] Configuração: lida num único lugar (há leitura de variável de ambiente espalhada pelo código?), validada no boot, padrões seguros (falha fechada: a ausência de uma variável desliga o recurso perigoso, não o liga).
- [ ] Tempo limite em **toda** chamada de rede (HTTP, SDKs de nuvem, banco, filas), inclusive na leitura do corpo da resposta.

## D. Dados e persistência (se houver banco)

- [ ] Schema: nomes consistentes, tipos nativos adequados (data com fuso, dinheiro em decimal, uuid), índices cobrindo chaves estrangeiras e as consultas reais.
- [ ] Integridade no banco, não só na aplicação: FK com `ON DELETE` explícito, `UNIQUE`, `CHECK`, `NOT NULL`.
- [ ] Migrations versionadas e revisáveis, **criadas pelo comando da ferramenta** (`migration:generate`, `migrate dev`, `alembic revision --autogenerate`, `dotnet ef migrations add`, `goose create`…), nunca com nome ou carimbo escritos à mão; onde a ferramenta gera o conteúdo a partir do modelo, o conteúdo gerado foi revisado, não reescrito (ajuste manual só com motivo, ex.: renomear em vez de apagar e recriar, carga de dados fixos). Evidência: em ferramentas com carimbo de data, compare o carimbo com a data do commit que introduziu o arquivo (`git log --diff-filter=A --format='%h %ad' -- <arquivo>`) — carimbo no futuro ou fora de ordem faz a ordem de aplicação divergir entre banco novo e bancos existentes; em ferramentas com cadeia de revisões (Alembic) ou versão sequencial (Flyway), confira cadeia única sem ramo nem lacuna (`alembic heads`, `flyway info`). Compatíveis com a versão anterior do código (expand/contract) quando há deploy sem parada; verificação de drift no CI.
- [ ] Retenção e dados pessoais: o que é guardado, por quanto tempo, cifrado ou mascarado, e como é excluído.
- [ ] Consultas: N+1, ausência de paginação, transações longas, I/O externo (HTTP, fila) dentro de transação ou de trava.
- [ ] NoSQL: modelagem orientada aos padrões de acesso **documentados** (cada tela de lista com filtros, busca, ordenações, paginação, contadores, volume e frescor), chaves de partição de alta cardinalidade, índices secundários justificados, itens/documentos sem crescimento ilimitado (ver `stacks/data/`, `nosql-access-patterns` e o guia do banco).
- [ ] Listas e busca (qualquer banco; peso maior em NoSQL): paginação no servidor por cursor, com teto de página e ordem estável (desempate único); nenhuma varredura nem "ler tudo e filtrar" no caminho de uma requisição de usuário; filtro pós-leitura proporcional (itens lidos ≈ devolvidos); contadores vindos do servidor quando há paginação; busca de texto com estratégia declarada (prefixo em índice, índice invertido, diretório compacto com teto, busca nativa, serviço de busca) e não `contains`/regex sobre tudo. "Volume pequeno" só passa com teto numérico, decisão registrada e gatilho de revisão — sem isso é achado, com isso é Observação. Evidência: grep da operação de varredura e de `filter`/`sort`/`slice`/`length` sobre a resposta inteira (backend e frontend), e teste com volume acima de uma página comparando itens lidos × devolvidos.

## E. Segurança e privacidade

- [ ] Autenticação e autorização existem e cobrem todas as rotas que precisam; o que é declarado (decorator, atributo) é de fato imposto (guard global, middleware)? Há rota pública por engano?
- [ ] Validação de entrada na borda; rejeição de campos desconhecidos; limites de tamanho de corpo, de arquivo e de lista.
- [ ] Cabeçalhos de segurança, CORS restritivo, limite de taxa — e o comportamento do limite com várias réplicas e atrás de proxy (de onde vem o IP do cliente? pode ser forjado?).
- [ ] Segredos: nada versionado (rode `gitleaks` ou equivalente no histórico), arquivo de exemplo sem valores reais, rotação possível.
- [ ] Dependências: vulnerabilidades conhecidas (`npm audit --omit=dev`, `pip-audit`, `govulncheck`, `dotnet list package --vulnerable`, OWASP dependency-check) e versões fora de suporte (runtime, framework).
- [ ] Dados pessoais fora de logs, mensagens de erro, URLs, filas e métricas.
- [ ] Superfícies de injeção: SQL montado com string, comando de shell, desserialização insegura, SSRF (URL vinda do usuário), path traversal, template injection, XSS (frontend).

## F. Integrações e mensageria (se houver)

- [ ] Garantia de entrega documentada (pelo menos uma vez / no máximo uma vez) e consumidores idempotentes.
- [ ] Outbox/inbox ou equivalente quando um efeito externo precisa acompanhar uma mudança de estado no banco.
- [ ] Retentativas com recuo exponencial e jitter, fila de mensagens mortas, reprocessamento possível, limite de tentativas.
- [ ] Desligamento ordenado (para de consumir, termina o que está em voo, fecha conexões); comportamento quando o terceiro cai ou fica lento.
- [ ] Contrato externo: o que está confirmado com o terceiro e o que é suposto? Suposições marcadas no código ou nos documentos?

## G. Testes

- [ ] Pirâmide: unitários, integração (com dependências reais quando faz diferença — banco, fila) e ponta a ponta. Conte os arquivos de cada tipo.
- [ ] Os testes provam comportamento e regras de fronteira (inclusive testes das próprias regras de lint/arquitetura).
- [ ] Nomes legíveis, fakes simples, sem dependência de ordem, de relógio real ou de dados de outras suítes.
- [ ] Cobertura: existe piso imposto? Caminhos de erro, concorrência e limites estão cobertos?
- [ ] Testes que dependem de infraestrutura externa identificados e isolados (tag, pasta, script próprio).
- [ ] Dados de amostra e geradores de teste realistas: nenhuma combinação impossível no domínio, e cada literal da regra (limiar, enumerador, formato) é exercitado por ao menos um caso. Como checar: leia fixtures e geradores com a lista de invariantes do domínio ao lado; liste literais de regra sem caso que os cubra. Média.

## H. Qualidade automatizada e processo

- [ ] Lint, formatação e typecheck rodam antes do commit e no CI; zero avisos tolerados? Rode-os e registre o resultado.
- [ ] Hooks impedem commit fora do padrão; há sinais de contorno (`--no-verify`, supressões em massa)?
- [ ] Convenção de commits, branches e revisão escrita e aplicada (confira no `git log`).
- [ ] Build reprodutível (lockfile, versão do runtime fixada), imagem de container enxuta, usuário sem privilégio, imagem base por digest, health e readiness corretos (readiness não depende do que não é crítico).
- [ ] Observabilidade: métricas, traces, alertas; runbooks para os modos de falha previstos.
- [ ] Documentação: o README permite subir do zero? Decisões registradas? Dívidas conhecidas listadas com motivo?

## I. Escolhas técnicas contra a documentação oficial

Tabela: `Escolha | O que a documentação oficial (na versão usada) e a comunidade fazem | Custo e benefício aqui | Veredito`. Cubra no mínimo: framework, ORM/acesso a dados, validação, configuração, mensageria e jobs em segundo plano, testes. Use os guias de `stacks/` como ponto de partida e diga a data de verificação de cada fonte.

## J. Frontend (se o serviço tem interface)

- [ ] Renderização (CSR, SSR, SSG, RSC) coerente com o produto; o que roda no servidor e no cliente está separado de propósito.
- [ ] Estado: estado do servidor (cache de dados remotos) separado do estado de UI; fonte única de verdade; estado que deveria estar na URL.
- [ ] Acessibilidade: semântica, rótulos, foco, contraste, navegação por teclado; lint de a11y e teste automático (axe) — e o que eles não pegam.
- [ ] Desempenho: tamanho do bundle e divisão por rota, imagens, Core Web Vitals medidos ou orçados.
- [ ] Segurança no cliente: XSS (HTML cru), segredos em variáveis públicas de build, tokens em armazenamento acessível a script, CSP.
- [ ] Contrato com o backend tipado (cliente gerado do OpenAPI ou tipos compartilhados) e tratamento uniforme de erro, carregamento e vazio.
- [ ] Estado em cache de UI (cache de dados remotos, memoização, itens derivados) chaveado por algo estável: a chave não inclui valor que muda durante o uso (trecho editado, texto digitado), o que geraria itens duplicados ou obsoletos. Como checar: leia as chaves de cache e de lista; edite o item e veja se a chave muda. Média.
- [ ] Estados que só têm saída por "suporte" ou por recarregar a página (becos sem saída de UX): liste os estados terminais e o texto de cada um. Alta quando o usuário não tem outra ação possível.
- [ ] Listas: o cliente pede página e cursor ao servidor; filtro, ordenação e contadores (abas, badges, totais) não são calculados sobre a resposta inteira, salvo decisão de volume pequeno registrada; vazio sem dados distinto de filtro sem resultado.

## K. Sistemas que usam LLM (se o serviço chama um modelo de linguagem)

Aplique quando o manifesto traz SDK de modelo, quando há pasta de prompts ou quando o repositório chama a API de um modelo por HTTP. Leia `stacks/architecture/llm-systems.md` — traz o como checar de cada item e os anti-padrões. Os itens de erro, descarte, default, precisão, laço, log, teste e UX acima (C, G, J) valem aqui com peso maior.

- [ ] **Linguagem natural decidida por código.** Procure regex, lista de palavras ou contagem de palavras sobre texto do usuário ou do modelo em código de produto. Sinal forte: o detector cresce com exceções por caso (`git log -p -S`). Checagem determinística só de estrutura (forma do JSON, números, igualdade literal, pontuação). Alta quando decide fluxo de negócio; correção: remover e mover a interpretação para prompt e contexto, não remendar.
- [ ] **Prompts como código.** Sem contradição entre arquivos de prompt do mesmo fluxo; sem exemplos copiados dos casos de teste de aceitação; orçamento de tamanho medido; versionados; gerados com golden file ou hash quando montados por código. Sem regras de palavras-gatilho nem condições específicas na instrução ao modelo ("se o texto disser X, Y ou Z, faça..."): é determinismo disfarçado dentro do prompt e induz erro fora dos casos listados. Quando o modelo erra o óbvio, a correção é achar e remover a instrução que induziu o erro e acrescentar fatos do sistema, não regra de palavras. Citação literal do dono ou do cliente não entra em prompt de produto. Alta para contradição ativa, exemplo copiado do teste ou lista de palavras-gatilho; Média para falta de orçamento.
- [ ] **Conhecimento do sistema para o modelo.** Existe asset do que o sistema faz e não faz (dados disponíveis, recursos inexistentes, o que bloqueia um processo), ligado ao código e atualizado; o modelo explica o porquê ao usuário e nunca oferece opção inviável nem algo que será desfeito depois. Alta se pode oferecer o inviável; Média se há lacuna de cobertura.
- [ ] **Sem beco sem saída.** Defeito do sistema não termina em "fale com o suporte": recuperação primeiro (tentar de novo, explicar), encaminhamento só após insistência em algo inviável, mostrando o que ficaria. Alta.
- [ ] **Variância tratada.** Fluxos com modelo têm cenários instáveis repetidos (duas ou três execuções) antes de serem dados como corrigidos; o texto que o usuário vê e os tempos são registrados por rodada; defeito do produto é separado de artefato da ferramenta de teste. Média.
- [ ] **Custo e tempo das chamadas.** Timeout, `max_tokens`, teto de iterações, concorrência limitada e prazo restante checado em laços; sem releitura nem reformulação sem orçamento. Alta se estoura o prazo do usuário; Média caso contrário.
- [ ] **Saída do modelo como entrada não confiável** e menor privilégio nas ferramentas expostas (E reforçada). Crítica se chega a execução ou escrita sem validação.
- [ ] **Logs sem texto do usuário nem prompt de sistema**, ainda diagnosticáveis (códigos, primeira diferença). Alta se grava o texto.

## Severidade

| Nível | Quando |
|---|---|
| **Crítica** | Vulnerabilidade explorável, perda ou vazamento de dados, corrupção por concorrência. |
| **Alta** | Violação de regra imposta ou central do projeto; risco operacional claro (travamento, indisponibilidade, fila presa); falta de proteção esperada para o tipo de dado. |
| **Média** | Dívida estrutural que encarece mudanças (módulo concentrado, acoplamento, duplicação de fonte da verdade). |
| **Baixa** | Polimento, legibilidade, convenção não imposta. |
| **Observação** | Decisão consciente e coerente, registrada só para ciência. |

Calibração para listas e busca: lista sem paginação ou com varredura no caminho de usuário e volume **sem teto** → Alta; contador do cliente coexistindo com paginação (número errado na tela) → Alta; busca de texto exigida por história ou protótipo sem estratégia → Alta; a mesma situação com teto declarado mas sem decisão registrada → Média; com teto, decisão e gatilho de revisão → Observação. Ausência da documentação de padrões de acesso → Média (processo).

Calibração para sistemas com LLM: regex ou lista de palavras decidindo fluxo de negócio a partir de texto livre → Alta (Média se só filtra apresentação); contradição entre prompts ou exemplos copiados dos testes → Alta; opção inviável ou beco sem saída alcançável pelo usuário → Alta; texto livre do usuário em log → Alta; laço com o modelo sem prazo nem teto → Alta se pode estourar o tempo do usuário, senão Média; cenário instável sem repetição → Média. Se o dono do produto registrou a decisão e o custo, o achado cai para Observação com a decisão citada.

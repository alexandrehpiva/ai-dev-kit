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

## C. Qualidade do código

- [ ] Rigor de tipos: modo estrito ligado? Quantos `any`/`Any`/`interface{}`/casts forçados/supressões de lint/`# type: ignore` em código de produção (conte com grep)?
- [ ] Complexidade: funções e arquivos longos, aninhamento profundo, parâmetros demais (meça com a ferramenta da stack quando houver).
- [ ] Tratamento de erros: erro de domínio separado de erro técnico; mapeamento para a resposta externa num lugar só; nenhum erro engolido em silêncio (`catch {}`, `except: pass`, `_ = err`); nenhuma mensagem interna, stack trace ou SQL vazando ao cliente.
- [ ] Concorrência e consistência: transações onde há invariante, idempotência em operações repetíveis, travas ou concorrência otimista onde há disputa; comentário explica o porquê nas decisões sutis.
- [ ] Logs: estruturados, com id de correlação, nível coerente, **sem dado pessoal nem segredo** (inclui cabeçalhos e corpos registrados automaticamente pelo middleware de log).
- [ ] Configuração: lida num único lugar (há leitura de variável de ambiente espalhada pelo código?), validada no boot, padrões seguros (falha fechada: a ausência de uma variável desliga o recurso perigoso, não o liga).
- [ ] Tempo limite em **toda** chamada de rede (HTTP, SDKs de nuvem, banco, filas), inclusive na leitura do corpo da resposta.

## D. Dados e persistência (se houver banco)

- [ ] Schema: nomes consistentes, tipos nativos adequados (data com fuso, dinheiro em decimal, uuid), índices cobrindo chaves estrangeiras e as consultas reais.
- [ ] Integridade no banco, não só na aplicação: FK com `ON DELETE` explícito, `UNIQUE`, `CHECK`, `NOT NULL`.
- [ ] Migrations versionadas e revisáveis, **criadas pelo comando da ferramenta** (`migration:generate`, `migrate dev`, `alembic revision --autogenerate`, `dotnet ef migrations add`, `goose create`…), nunca com nome ou carimbo escritos à mão; onde a ferramenta gera o conteúdo a partir do modelo, o conteúdo gerado foi revisado, não reescrito (ajuste manual só com motivo, ex.: renomear em vez de apagar e recriar, carga de dados fixos). Evidência: em ferramentas com carimbo de data, compare o carimbo com a data do commit que introduziu o arquivo (`git log --diff-filter=A --format='%h %ad' -- <arquivo>`) — carimbo no futuro ou fora de ordem faz a ordem de aplicação divergir entre banco novo e bancos existentes; em ferramentas com cadeia de revisões (Alembic) ou versão sequencial (Flyway), confira cadeia única sem ramo nem lacuna (`alembic heads`, `flyway info`). Compatíveis com a versão anterior do código (expand/contract) quando há deploy sem parada; verificação de drift no CI.
- [ ] Retenção e dados pessoais: o que é guardado, por quanto tempo, cifrado ou mascarado, e como é excluído.
- [ ] Consultas: N+1, ausência de paginação, transações longas, I/O externo (HTTP, fila) dentro de transação ou de trava.
- [ ] NoSQL: modelagem orientada aos padrões de acesso, chaves de partição de alta cardinalidade, índices secundários justificados, itens/documentos sem crescimento ilimitado (ver `stacks/data/`).

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

## Severidade

| Nível | Quando |
|---|---|
| **Crítica** | Vulnerabilidade explorável, perda ou vazamento de dados, corrupção por concorrência. |
| **Alta** | Violação de regra imposta ou central do projeto; risco operacional claro (travamento, indisponibilidade, fila presa); falta de proteção esperada para o tipo de dado. |
| **Média** | Dívida estrutural que encarece mudanças (módulo concentrado, acoplamento, duplicação de fonte da verdade). |
| **Baixa** | Polimento, legibilidade, convenção não imposta. |
| **Observação** | Decisão consciente e coerente, registrada só para ciência. |

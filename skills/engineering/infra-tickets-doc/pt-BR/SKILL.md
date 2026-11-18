---
name: infra-tickets-doc
description: Produz o lote de chamados de infraestrutura que um time de produto ou fornecedor entrega ao cliente para abrir junto à infra, SRE, DBA ou DevOps (ServiceNow, Jira Service Management ou outro catálogo) - um chamado por recurso (banco, filas, buckets, chaves, segredos, identidade da carga, esteira CI/CD, deploy em Kubernetes, CDN, API Gateway, cache, saída de rede, DNS/WAF, acessos de usuário ou grupo, observabilidade), cada um com "Texto para colar" escrito para quem cria o recurso, ordem de abertura e dependências, versão de homologação e versão de produção por mudança formal (GMUD/CAB), lacunas marcadas [A CONFIRMAR], gerado como HTML e PDF e acompanhado até o atendimento. Usar ao pedir "chamados de infra", "abrir chamados no ServiceNow", "pedir recursos à infra do cliente", "texto para o SRE", "lote de chamados", "leva de chamados", "PDF dos chamados", "ordem de abertura dos chamados", "chamado de ajuste", "chamado de acesso", "preparar GMUD" ou "o SRE não entendeu o chamado".
---

# infra-tickets-doc

**Um chamado de infraestrutura é lido por quem vai criar o recurso, não por quem entende a aplicação: diz o que criar, com que configuração, para quem, ligado a quê, e o que precisa voltar. Tudo que o SRE precisa para executar está escrito; nada que ele não usa está escrito.**

## Diagnóstico do modo de falha

O agente escreve chamados que parecem completos e travam na fila do SRE. As classes de erro que se repetem (pares Bom/Ruim em [`examples/paste-text-before-after.md`](examples/paste-text-before-after.md)):

1. **Explica a aplicação em vez de pedir.** Regra interna (migrations com trava, long polling, cookie, scripts) no lugar de nome, tamanho, rede, política e permissão. Confunde e irrita quem executa.
2. **Parágrafo longo.** Três fatos na mesma frase; o SRE perde o pedido no meio do texto.
3. **Cita o padrão do provedor.** "Rotação desligada", "janela de exclusão padrão", "sem CloudTrail": se não é configuração, não entra.
4. **Omite o que o SRE precisa para montar.** O caso mais caro: chamado de deploy que diz "dois Deployments da mesma imagem" sem repositório, Dockerfile, entrypoint, variáveis por Deployment e branch. O SRE entende dois repositórios e devolve o chamado.
5. **Inventa valor.** Classe, retenção, domínio, conta, centro de custo preenchidos por plausibilidade. Lacuna é `[A CONFIRMAR: o quê]`, em destaque.
6. **Pede produção junto com homologação.** Produção entra por mudança formal, depois da homologação aceita, com documento próprio.
7. **Pede acesso amplo.** "Acesso à conta" ou permissão de administrador, em vez de escopo por recurso, para usuário ou grupo, com o que fica de fora.
8. **Esquece dependências.** Pede a esteira antes do banco e dos segredos; pede permissão em recurso que ainda não existe; pede algo que cita um ARN que ninguém devolveu.
9. **Não diz o que precisa de volta.** Endpoint, ARN, ID, nome do segredo, nome DNS interno: sem a seção "Preciso de volta", ninguém devolve e o próximo chamado trava.
10. **Chamado e código divergem.** O código passa a exigir uma variável que o chamado não tem; o pod não sobe em homologação.

O antídoto é um processo fixo: **descoberta → inventário → ordem → redação por chamado → produção → HTML/PDF → revisão → entrega e acompanhamento.**

## Passo 0 - antes de escrever

Pergunte só o que o material não responde (lotes e recomendações em [`discovery.md`](discovery.md)). Sem os itens 1 a 4, não escreva.

- [ ] **1. Quem abre e quem executa.** Quem abre o chamado no catálogo (às vezes não é o autor) e quem lê o texto (SRE, DBA, segurança).
- [ ] **2. Onde abrir.** Caminho no catálogo, formulário e campos obrigatórios por ambiente; se exige vínculo com tarefa (Jira ou outro).
- [ ] **3. Ambiente e conta.** Homologação ou produção, conta/assinatura/projeto de nuvem, região, rede (VPN, VPC do cluster).
- [ ] **4. Arquitetura e código.** Desenho aprovado e o código (ou spec) que define o que cada recurso precisa: variáveis, portas, probes, permissões.
- [ ] 5. Padrões do cliente já conhecidos: nomes, tags, segredos, esteira, observabilidade, mudança formal.
- [ ] 6. Chamados já abertos ou atendidos (números e o que devolveram).
- [ ] 7. Dados do solicitante para o rodapé de cada texto (nome, usuário de rede, e-mail corporativo).

## Roteamento - leia o asset antes de agir

| Se você vai... | Ler (obrigatório) |
|---|---|
| Levantar catálogo, formulários, padrões do cliente e perguntar ao usuário | [`discovery.md`](discovery.md) |
| Inventariar recursos, montar dependências, ordem e levas | [`ordering-and-dependencies.md`](ordering-and-dependencies.md) |
| Redigir qualquer "Texto para colar" | [`writing-rules.md`](writing-rules.md) e o asset do caso em `cases/` |
| Montar o documento (capa, resumo, cartão de chamado, nomes de arquivo) | [`DOCUMENT-STRUCTURE.md`](DOCUMENT-STRUCTURE.md) |
| Preparar a versão de produção e a mudança formal | [`production-change.md`](production-change.md) |
| Revisar (SRE cego, conferência contra o código, lint, PDF) | [`review.md`](review.md) |
| Entregar, acompanhar, corrigir chamado já aberto | [`follow-up.md`](follow-up.md) |
| Gerar o HTML a partir da especificação | `templates/tickets.example.json` + `scripts/build_tickets_html.py` (usa `templates/tickets.template.html`, tema neutro; ao mudar os scripts, rode `python3 -m unittest discover -s scripts/tests`) |

**Assets por caso** (`cases/`): leia o do recurso antes de redigir o chamado dele. Cada um diz o que pedir, o que não citar, o que pedir de volta, tags e lacunas típicas.

| Recurso | Asset |
|---|---|
| Banco relacional gerenciado | [`cases/relational-database.md`](cases/relational-database.md) |
| Filas e DLQ | [`cases/queues.md`](cases/queues.md) |
| Bucket de objetos | [`cases/object-storage.md`](cases/object-storage.md) |
| Chaves de criptografia | [`cases/encryption-keys.md`](cases/encryption-keys.md) |
| Segredos | [`cases/secrets.md`](cases/secrets.md) |
| Identidade da carga (IRSA, workload identity) | [`cases/workload-identity.md`](cases/workload-identity.md) |
| Repositório e esteira CI/CD | [`cases/ci-cd-pipeline.md`](cases/ci-cd-pipeline.md) |
| Deploy em Kubernetes | [`cases/kubernetes-deploy.md`](cases/kubernetes-deploy.md) |
| Site estático e CDN | [`cases/static-site-cdn.md`](cases/static-site-cdn.md) |
| API Gateway e VPC Link | [`cases/api-gateway.md`](cases/api-gateway.md) |
| Cache (Redis, Valkey) | [`cases/cache.md`](cases/cache.md) |
| Saída de rede, e-mail e SMS de terceiros | [`cases/egress-and-third-parties.md`](cases/egress-and-third-parties.md) |
| DNS e WAF | [`cases/dns-and-waf.md`](cases/dns-and-waf.md) |
| Acessos humanos (usuário, grupo) | [`cases/human-access.md`](cases/human-access.md) |
| Observabilidade, logs e alertas | [`cases/observability.md`](cases/observability.md) |

Recurso sem asset: aplique `writing-rules.md` e a estrutura comum dos casos (o que pedir, não citar, preciso de volta, tags, lacunas). Se o caso se repetir, crie o asset.

## Fases

1. **Descobrir.** Passo 0, catálogo e padrões do cliente ([`discovery.md`](discovery.md)). Saída: quadro de fatos com fonte e lista de lacunas.
2. **Inventariar.** Um item por recurso, tirado do desenho e do código, nunca de memória. Saída: tabela recurso, chamado, depende de, devolve.
3. **Ordenar.** Grafo de dependências, levas (`p1`, `p2`...) e caminho crítico ([`ordering-and-dependencies.md`](ordering-and-dependencies.md)). Portão: nenhum chamado pede algo que ainda não existe ou que ninguém devolveu, salvo decisão explícita do autor de abrir antes.
4. **Redigir.** Um chamado por vez, com [`writing-rules.md`](writing-rules.md) e o asset do caso. Conferir cada variável, porta, probe e permissão contra o código.
5. **Produção.** No mesmo ciclo, a contraparte de produção de cada chamado, como rascunho para a mudança formal ([`production-change.md`](production-change.md)).
6. **Gerar.** Especificação JSON, `python3 scripts/build_tickets_html.py spec.json saida.html`, PDF com a skill `generate-pdf-report`. Contrato em [`DOCUMENT-STRUCTURE.md`](DOCUMENT-STRUCTURE.md).
7. **Revisar.** `python3 scripts/lint_tickets.py spec.json` com zero erros, revisor SRE cego, conferência contra o código e leitura das páginas do PDF ([`review.md`](review.md)).
8. **Entregar e acompanhar.** Abrir o PDF para o autor, registrar o que foi enviado, acompanhar respostas e tratar ajustes ([`follow-up.md`](follow-up.md)).

## Escapes de falha

- **Valor sem fonte** (classe, domínio, conta, centro de custo, retenção): `[A CONFIRMAR: o que falta e quem decide]`. Nunca preencha por plausibilidade.
- **Padrão do cliente desconhecido** (nome de usuário, região, mecanismo de segredo): escreva como sugestão e diga que vale o padrão deles. Quando a infra responder com o padrão, ele vira regra para os próximos chamados.
- **Documento já enviado:** não edite a leva enviada. O ajuste vira comentário no chamado aberto ou chamado de ajuste (`follow-up.md`).
- **O SRE devolveu o chamado ou pediu esclarecimento:** responda pelo autor com o texto pronto, corrija a especificação, a versão de produção e, se a lição for nova, o asset do caso.
- **O lint reprova duas vezes na mesma regra:** o problema é informação, não redação. Pergunte ao autor.

## Relação com outras skills

- `generate-pdf-report`: renderização do HTML em PDF (Chrome headless) e conferência visual. Não duplique o script.
- `avoid-ai-text-watermarks`: tom humano no texto dos chamados.
- `ask-with-context` / `grill-me`: perguntas e decisões ao autor, sempre com recomendação.
- `hallucination-guard`: antes de o documento virar verdade, verificador independente.
- `infosec-review-doc`: o documento de arquitetura e segurança para a SI do cliente; os chamados citam o desenho aprovado lá, não o reescrevem.
- `secure-credentials` ou equivalente: nenhum valor de segredo passa por chamado, chat ou documento.

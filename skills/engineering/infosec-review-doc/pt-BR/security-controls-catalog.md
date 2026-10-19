# Catálogo de controles de segurança (seção 7)

Menu de controles que a área de segurança costuma procurar, organizado por camada. **Não é lista para copiar:** cada linha só entra no documento se o quadro de afirmações lhe dá origem. Use o catálogo para *não esquecer de perguntar* e para encontrar lacunas.

## Diagnóstico do modo de falha

O agente conhece muito controle de segurança de cabeça e o escreve como se o projeto o tivesse. Pior, ao ver uma camada vazia, a preenche por simetria. A área de segurança lê "criptografado com chave gerenciada pelo cliente" como compromisso e verifica na implementação. O catálogo existe para transformar cada controle em **pergunta com fonte**, não em afirmação.

## Como usar

1. Para cada linha, procure a origem (ata, desenho, infra, doc do parceiro, padrão de engenharia, requisito do desenho).
2. Com origem → entra na tabela com chip. Sem origem → pergunta ao autor; se o autor quiser, entra como **proposta**; senão fica de fora.
3. Controle que é responsabilidade do cliente (auditoria da conta, detecção de ameaças) entra como tal, não como controle do produto.
4. Camada sem nenhum controle com origem: omita a subseção e liste a lacuna ao autor.

Formato de tabela: **Controle · Como é tratado · Origem**.

## 7.1 Borda e acesso

| Controle | Pergunta de fonte |
|---|---|
| Firewall de aplicação (WAF) à frente de tudo que é exposto | O cliente exige? Há saída que não passa pelo WAF? |
| Frontend estático por CDN | O desenho mostra? |
| Gateway de API; microsserviço sem tráfego direto da internet | A área de segurança orientou? Quais rotas são expostas? |
| Rede privada para serviços e dados; saída por NAT com IP fixo | O IP fixo é informado ao parceiro (allowlist)? |
| Cabeçalhos de segurança e CORS por allowlist | Padrão de engenharia do autor? |
| Limite de requisições (por rota e por IP; IP vindo do cabeçalho confiável do proxy) | Há limites próprios para rotas sensíveis? |
| Validação de entrada; erros que não repetem o valor enviado | Padrão do autor? |
| Sessão do usuário (cookie) e isolamento entre usuários | O parceiro exige isolamento de token? |

## 7.2 Identidade, segredos e chaves

| Controle | Pergunta de fonte |
|---|---|
| Segredos em cofre gerenciado; leitura pela identidade do workload, sem segredo em código | Quem administra o cofre (cliente ou autor)? |
| Credenciais do parceiro só no backend; nunca no navegador | A doc do parceiro exige? |
| Menor privilégio por identidade; administrador da chave não decifra | Requisito do desenho? |
| Allowlist de IP no parceiro (produção) | O parceiro exige? |
| Autenticação do usuário final / MFA, quando houver login | O produto tem login? |

## 7.3 Dados em repouso e em trânsito

| Controle | Pergunta de fonte |
|---|---|
| Banco criptografado em repouso, multi-zona | Qual banco foi aprovado pela infra? |
| Cifra por campo para dado pessoal (envelope com chave gerenciada) e busca por hash com chave secreta | Padrão do autor? Quais campos? |
| Bucket privado: bloqueio de acesso público, sem ACL, criptografia com chave exclusiva, política que nega acesso sem TLS | Requisitos de infra do bucket? |
| Separação de funções na chave (quem administra ≠ quem usa) | Requisito do desenho? |
| Acesso a documentos só pela identidade do serviço; pessoas sem leitura por padrão; acesso excepcional aprovado e auditado | **Normalmente proposta** |
| CORS do bucket restrito à origem da aplicação e ao método de envio | Há upload direto do navegador? |
| Versionamento e eliminação automática (ciclo de vida) com prazo explícito | Prazo é **proposta** até a privacidade aprovar |
| Rotação automática de chave | **Proposta** se a infra ainda não confirmou |
| TLS em todo o trânsito; chaves de objeto sem dado pessoal; URLs assinadas e dados pessoais fora do log | Padrão do autor / requisito do desenho |

## 7.4 Disponibilidade e consistência

Multi-zona; outbox transacional; filas com DLQ; consumidores idempotentes; repetição com espera crescente; encerramento ordenado dos workers; sondas de saúde independentes de uma fila específica. Cada item precisa de origem no desenho ou nos padrões de engenharia.

## 7.5 Ciclo de desenvolvimento seguro

| Controle | Pergunta de fonte |
|---|---|
| Análise de código (SAST e dependências) na esteira, com bloqueio de vulnerabilidades altas e críticas | A área de segurança do cliente exige? Quando o repositório precisa ser cadastrado? |
| Baseline de desenvolvimento seguro do cliente | Quem o envia e quando? |
| Esteira, ramos e deploy | Padrão da infraestrutura do cliente |
| Infraestrutura como código | Padrão da infra |
| Qualidade: lint de fronteiras entre camadas, testes automatizados, commits padronizados | Padrão do autor |
| Teste de invasão (pentest) | Quem conduz e quando? |

## O que *não* entra como controle do produto

- Auditoria e detecção de ameaças da conta, alarmes de plataforma, monitoração do cluster: responsabilidade da infraestrutura do cliente — escreva como tal ("fora do escopo do projeto").
- Controles que o autor decidiu não propor (por exemplo, um reforço de rede que cabe à área de segurança exigir): não aparecem, nem como sugestão.
- Certificações e conformidades que ninguém afirmou (ISO, PCI, SOC): só com origem.

## Pares Bom / Ruim

| Ruim | Bom |
|---|---|
| "Todos os dados são criptografados com AES-256." | "Banco criptografado em repouso com chave gerenciada; dados pessoais cifrados por campo (envelope)." + chips de desenho e padrão de engenharia |
| "O acesso é auditado." | "Acesso excepcional, aprovado e auditado (proposta ainda a confirmar com a infraestrutura)." + chip Proposta |
| "Segue as melhores práticas OWASP." | Citar o controle concreto (validação de entrada, cabeçalhos, limite de requisições) com origem. |

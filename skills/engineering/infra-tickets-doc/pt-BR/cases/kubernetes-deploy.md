# Caso: deploy em Kubernetes (EKS, GKE, AKS, OpenShift)

O chamado mais caro de errar. O SRE vai montar a esteira e os manifests a partir dele; o que faltar vira pergunta, e a pergunta trava o chamado.

## Seção obrigatória: "Build e deploy"

Todo chamado de deploy (e toda esteira que faz deploy) traz esta seção, com todos os itens. É o "como construir e rodar", e é o que o SRE mais precisa.

- [ ] **Repositório(s)**: URL de cada um e **quantos são**. Se um repositório gera mais de um Deployment, diga com todas as letras: "um repositório só, para a API e o worker".
- [ ] **Dockerfile**: caminho no repositório e argumentos de build, se houver ("sem argumentos de build").
- [ ] **Imagens**: quantas. "Uma imagem, usada pelos dois Deployments com a mesma tag."
- [ ] **Entrypoint/command**: o da imagem, igual ou diferente por Deployment. "Não sobrescrever `command`/`args`." Se o template do cliente exigir command explícito, dê o valor.
- [ ] **O que diferencia cada Deployment**: lista de variáveis com valor, por Deployment. "Os dois diferem só por estas variáveis."
- [ ] **Branch por ambiente**: qual branch dispara o deploy em homologação e qual em produção. "Branches de feature não disparam deploy."
- [ ] **Rollout conjunto**: se os Deployments precisam estar sempre na mesma versão, diga: "um pipeline atualiza os dois juntos, em rolling update", e o ajuste que evita indisponibilidade (`maxUnavailable: 0` na API).

O número de Deployments **não** é regra interna da aplicação quando o SRE vai criá-los. Escreva.

## Demais seções

- **Os Deployments**: nome de cada um, o que faz em uma linha, se recebe tráfego.
- **Namespace** (sugestão) e labels com as tags.
- **securityContext**: usuário do processo da imagem (`runAsUser`), quando a imagem não roda como root.
- **Probes e encerramento**: startup probe (com `periodSeconds` e `failureThreshold` que cobrem a inicialização mais lenta, ex. migrations), liveness e readiness por Deployment, com os caminhos reais; `terminationGracePeriodSeconds` maior que o maior processamento em curso.
- **Recursos e réplicas**: requests e limits por pod; HPA mínimo e máximo, alvo de CPU. Homologação: sem exigência de várias zonas.
- **Exposição interna**: balanceador interno usado pelo gateway (tipo à escolha da infra), sem exposição direta à internet; o que não é exposto.
- **Caminhos que não passam pelo gateway** (administração, documentação): por onde são alcançados (só VPN) e por onde não.
- **Variáveis de ambiente**: só as que o SRE precisa declarar, com valor, em bloco de código. Comuns aos Deployments e as específicas (que também aparecem em "Build e deploy").
- **Valores sensíveis**: mapeamento segredo, chave e variável ([`secrets.md`](secrets.md)).
- **Permissões do serviço**: identidade da carga ([`workload-identity.md`](workload-identity.md)).
- **Alcance de rede dos pods**: serviços da nuvem que precisam alcançar (endpoints de VPC ou saída), liberações de saída pedidas em outro chamado, security group do banco aceitando os nodes.

## Não citar

- Variável que tem padrão no código e só o autor ajusta (limites, flags de tuning).
- O que a aplicação faz sozinha e não exige nada do SRE ("sem Job de migration: a API aplica as migrations ao iniciar" sai; o tempo de startup que isso causa fica, como número na probe).
- Hipóteses sobre o modelo da esteira ("se o modelo só permite um Deployment por repositório, me indiquem como fica o worker").

## Preciso de volta

- ARN ou identificador do listener do balanceador interno (o chamado do gateway usa), tipo do balanceador e tempo de ociosidade, se a aplicação depende dele.
- Nome DNS interno dos caminhos alcançados só pela VPN.
- Nome do cluster, se o autor ainda não tem.

## Tags

`Component=api` e `Component=worker`; também como labels do namespace e dos pods.

## Lacunas típicas

Nome do cluster; mecanismo de segredos; arquitetura dos nodes e do agente de build (amd64 ou arm64) quando a imagem tem binário nativo.

<example>
Build e deploy
- Repositório: um só, para a API e o worker: https://git.example.com/acme/acme-orders-backend
- Dockerfile: na raiz do repositório, sem argumentos de build.
- Uma imagem, usada pelos dois Deployments com a mesma tag.
- Entrypoint: o da imagem, igual nos dois (/sbin/tini -- /app/docker/entrypoint.sh). Não sobrescrever command/args.
- O que muda entre os Deployments, só variáveis:
  - acme-orders-api-hml: CONSUMERS_ENABLED=false, MIGRATIONS_ON_BOOT=apply
  - acme-orders-worker-hml: CONSUMERS_ENABLED=true, MIGRATIONS_ON_BOOT=wait
- Porta 3000 nos dois. O worker não é exposto; a porta serve só às probes.
- Deploy disparado pelo merge na branch homolog (produção: main). Branches de feature não disparam deploy.
- Um pipeline atualiza os dois Deployments juntos, em rolling update, com maxUnavailable: 0 na API.

Probes e encerramento
- Startup probe em GET /health nos dois (periodSeconds 10, failureThreshold 36).
- API: liveness em GET /health; readiness em GET /health/ready (periodSeconds até 5).
- Worker: liveness em GET /health/loops; readiness em GET /health/ready.
- terminationGracePeriodSeconds de pelo menos 120.
</example>

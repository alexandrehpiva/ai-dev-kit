# Caso: repositório e esteira CI/CD (Jenkins, GitLab CI, GitHub Actions, Azure DevOps)

## Antes: repositórios e grupo

- Grupo ou organização do projeto: chamado só se o autor não tiver permissão de criar; pedir o papel do autor (Developer, Maintainer).
- Repositórios: o autor tenta criar; se não puder, chamado com nome, descrição e branches padrão do cliente.
- Esteira só depois de o código estar publicado na branch do ambiente **e** de os recursos e segredos que a aplicação lê ao subir existirem.

## O que pedir (esteira de aplicação em contêiner)

- Repositório (URL), branch que dispara cada ambiente e que o código já está nela.
- Modelo de esteira do cliente para o tipo de aplicação ("esteira padrão de vocês para API Node.js em contêiner").
- Etapas: build pelo Dockerfile, scan obrigatório do cliente (com a regra de bloqueio, ex.: alta ou crítica bloqueia), publicação no repositório de imagens, deploy.
- Repositório de imagens: nome sugerido ou o padrão.
- Arquivos de deploy (Helm, manifests): quem cria; se é a infra, diga quantos Deployments e aponte o chamado de deploy.
- **Seção "Build e deploy"** quando a esteira faz deploy: obrigatória, com os itens de [`kubernetes-deploy.md`](kubernetes-deploy.md). Esteira e deploy pedidos em chamados separados repetem os itens essenciais nos dois (repositório, Dockerfile, quantas imagens, branch); o SRE pode pegar só um deles.
- Tempo de espera do deploy maior que o startup mais lento (ex.: `helm --wait` acima de 6 minutos).
- Permissão do autor: merge na branch de homologação.

## O que pedir (esteira de front estático)

- Versão do runtime e comandos exatos: instalar (`pnpm install --frozen-lockfile --ignore-scripts`) e build (`pnpm build`, saída em `dist`).
- Publicação: sincronizar para o bucket com exclusão do que saiu (`aws s3 sync --delete`) e invalidar o CDN.
- Cache por arquivo: `index.html` com `no-cache`; arquivos com hash no nome com cache longo e `immutable`. Diga que a esteira coloca os cabeçalhos ao copiar; o SRE não precisa configurar no bucket.
- **Variáveis do build**, todas, com valor ou `[A CONFIRMAR]`; o build falha sem elas. Diga que nenhuma é segredo (vão para o pacote do navegador) e pergunte como a esteira recebe variáveis de build.
- Permissão da esteira restrita ao front: no bucket, `ListBucket` e nos objetos `PutObject`, `DeleteObject`, `GetObject`; na distribuição, `CreateInvalidation`.
- Que o Dockerfile do repositório, se houver, é só para uso local.

## Não citar

- Detalhes do Dockerfile que a esteira não precisa saber (BuildKit, imagens base, registries de pacotes), salvo quando a esteira do cliente comprovadamente não suporta.
- "Se a esteira exigir arquivo X no repositório, o modelo dele."
- Etapas de teste que exigem banco e serviços externos.

## Preciso de volta

- Nome do job e endereço da ferramenta; nome do repositório de imagens; arquitetura do agente de build, se a imagem tem binário nativo.

## Tags

No repositório de imagens: `Component=api`.

## Lacunas típicas

ID da distribuição do CDN (vem do chamado do front); valores das variáveis do build que dependem de licença ou domínio de terceiro.

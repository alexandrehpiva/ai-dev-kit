# verify-against-reality

## Diagnóstico do modo de falha

Num diagrama, a primeira versão desenhou `CDN --/api/*--> API`, uma suposição plausível (padrão comum: o CDN faz proxy de `/api/*` para o backend). A implementação real era outra: o front-end chamava a URL do gateway de API **diretamente do navegador**, sem passar pelo CDN — o que se confirma lendo a variável de base URL do cliente e o recurso do gateway no IaC (sem domínio customizado, sem origem associada no CDN). O erro só foi percebido quando alguém perguntou "cadê a conexão front→back?" e a resposta certa diferia do desenho.

**Toda seta do diagrama é uma afirmação técnica.** Se ela vem de "assim costuma funcionar" em vez de "eu confirmei isso no código", está arriscando estar errada.

## Como confirmar cada tipo de conexão antes de desenhar

- **Chamada de API entre dois serviços**: procure a env var/config de base URL do lado cliente (`grep -rn "API_URL\|BASE_URL\|VITE_\|NEXT_PUBLIC_"`) e confirme se ela aponta para o domínio do proxy/CDN ou direto para o serviço de origem.
- **Domínio customizado vs. URL padrão do provedor**: no IaC (Terraform/CDK/SAM), procure o recurso de domain mapping (recurso de domain mapping do gateway; distribuição do CDN com origem/comportamento para o path em questão). Ausência do recurso = não existe esse caminho, mesmo que pareça "natural" que existisse.
- **Autenticação federada (IdP)**: confirme no provider de auth (Cognito, Auth0, etc.) qual IdP está de fato configurado e com qual client, não assuma pelo nome do produto.
- **Pipeline CI/CD**: leia o workflow (`.github/workflows/*.yml`) para confirmar builda/publica/deploya exatamente o quê e em qual ordem — não infira do nome do repo.
- **Banco/storage**: confirme o recurso e a forma de acesso (SDK direto, camada de API própria) no código da aplicação, não só no IaC — o IaC prova que o recurso existe, não que o componente X é quem o acessa.

## Regra prática

Antes de desenhar uma seta entre dois nós, complete a frase: **"eu confirmei isso lendo `<arquivo:linha>` / `<comando>`."** Se não tiver como preencher a lacuna, ou a seta fica de fora, ou você investiga primeiro (grep/Read no código relevante) — nunca desenha por suposição "de como normalmente é feito".

## Ao corrigir uma seta reportada como errada/faltando

Trate como o mesmo processo, não como exceção: releia o código relevante, confirme a forma real da integração, e só depois ajuste a edge (origem, destino, label). Documente a fonte da confirmação no label da edge quando ajudar a explicar uma decisão não óbvia (ex.: `"direto, sem CDN"`), do jeito que um comentário de "por que não é o padrão esperado" ajudaria em código.

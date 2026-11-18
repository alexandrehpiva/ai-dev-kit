# Produção: contraparte de cada chamado e mudança formal

## Regra

- **Nenhum chamado de homologação pede recurso de produção.** Em muitas empresas produção só entra por mudança formal (GMUD, change, CAB), depois de toda a homologação aceita, com documento próprio. Confirme com a infra; até lá, assuma essa regra.
- **A versão de produção é preparada no mesmo ciclo da de homologação.** Cada chamado de homologação ganha a contraparte de produção como rascunho (`chamados-prd-pN`). Toda mudança num chamado de homologação atualiza a contraparte no mesmo ciclo.

## Como derivar o texto de produção

- Nomes: sufixo do ambiente trocado (`-hml` para `-prd`, caminho de segredos `.../hml/` para `.../prd/`), `Environment=prd` nas tags.
- Conta, região, domínio, certificado e centro de custo de produção: `[A CONFIRMAR]` até alguém informar.
- **Entra só em produção** (o que homologação deixa de fora por custo ou por ser padrão):
  - alta disponibilidade (Multi-AZ, réplicas em mais de uma zona);
  - crescimento automático de armazenamento e backup no padrão do cliente;
  - proteção contra exclusão [proposta];
  - rotação anual das chaves e política separando administração e uso;
  - eventos de dados na trilha de auditoria para bucket com dado pessoal;
  - retenção definitiva definida pela segurança e pela privacidade;
  - IP de saída na allowlist de parceiros;
  - classe do banco e réplicas definidas pelo teste de carga, não antes.
- **Não existe em produção**: acesso humano direto ao banco, escrita humana em segredos (salvo padrão do cliente), aumento temporário de classe para teste.
- **Nunca copie dado de homologação**: credenciais de parceiros, chaves aleatórias, usuário e senha de banco são novos.
- Ligar recurso de produção que muda comportamento (flag, varredor, integração real) só depois da confirmação do autor: `[A CONFIRMAR: autor libera antes do go-live]`.

## Documento da mudança formal (estrutura provável, a conferir com o modelo do cliente)

1. **Título e escopo**: lista de recursos com nomes de produção.
2. **Justificativa**: primeira publicação do produto, validado em homologação.
3. **Evidência da homologação**: chamados de homologação atendidos (números) e aceite do teste ponta a ponta.
4. **Impacto e risco**: serviço novo ou alteração; dependências externas.
5. **Plano de implantação**: na ordem dos chamados; esteira da branch de produção.
6. **Plano de verificação**: saúde do serviço, fluxo controlado, alertas.
7. **Plano de reversão**: retirar a rota pública, voltar a versão, manter dados.
8. **Janela, responsáveis e contatos**; congelamento de mudanças (datas de pico do negócio).
9. **Pendências externas**: IP liberado no parceiro, credenciais de produção, domínio e certificado.

Marque como `[NÃO CONFIRMADO]` qualquer item desse modelo que o cliente não mostrou. Pergunte se é uma mudança só ou uma por recurso.

## Arquivo de preparação

Mantenha uma nota viva "Produção: preparação da mudança" com uma linha por chamado: o que foi pedido em homologação e o que muda em produção. Quando um chamado de homologação mudar, a linha muda no mesmo ciclo.

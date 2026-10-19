# Fluxo do dado sensível (seção 6) e privacidade (seção 8)

Leia antes de escrever as seções 6 e 8, ou sempre que o produto recebe documento, biometria, dado financeiro ou qualquer dado pessoal.

## Diagnóstico do modo de falha

- **Privacidade escrita como parecer jurídico.** O agente afirma base legal, papéis (controlador/operador) e prazos legais que ninguém definiu. O leitor não é o advogado do autor.
- **O mesmo dado com três tratamentos.** "Não é guardada" numa seção, "fica no bucket" na tabela, "eliminada em 7 dias" no glossário. Costuma nascer de uma decisão tardia aplicada só em parte.
- **Fluxo que descreve a tela, não a transmissão.** A ordem em que o usuário vê as etapas é confundida com a ordem em que o dado chega ao terceiro, e a diferença é justamente o que o leitor precisa entender.
- **Sucesso confundido com aprovação.** "Registrado no parceiro" aparece como "aprovado", e o texto passa a prometer um resultado que só a análise posterior dá.

## Seção 6 — fluxo do dado sensível

Escreva-o como **passo a passo numerado**, seguido de uma tabela de controles. Responda, nesta ordem:

1. **Entrada:** como o dado chega (captura no navegador, upload do arquivo, componente de terceiro) e quem o valida.
2. **Passagem:** por onde passa e em que forma (URL assinada direto ao bucket; requisição síncrona pelo backend; memória apenas).
3. **Guarda:** onde fica, por quanto tempo, com que proteção (ou "não é guardado").
4. **Entrega:** a quem é enviado, em que ordem, como o sucesso é confirmado e o que acontece em falha.
5. **Eliminação:** como e quando o dado some.

Padrões frequentes (use só os que existem na fonte):

- **Upload direto por URL pré-assinada.** O navegador calcula o hash, pede ao backend uma URL (informando tipo e tamanho), envia o arquivo ao bucket com uma única requisição `PUT` (sem multipart), confirma ao backend, que confere o objeto, fixa versão e hash e enfileira a entrega. A URL expira em minutos e tem tamanho, tipo e hash assinados, e **nunca vai para o log**.
- **Dado só em memória.** Quando um dado de alto risco (como imagem de biometria) não deve ser guardado, diga isso com precisão: passa pela memória do backend na mesma requisição que o entrega ao destino e **não vai a bucket, banco, fila nem log**. A frase exata importa: "não é guardada" é diferente de "é guardada e eliminada depois".
- **Token de uso único.** Se o componente de captura devolve um token que vale uma vez e expira, não há nova tentativa automática: a falha aparece na hora e pede nova captura.
- **Registro ≠ aprovação.** Diga que o aceite do registro não significa aprovação e descreva o canal pelo qual a decisão volta (status, pendências, reenvio).
- **Ordem de entrega × ordem da tela.** Se a regra do destino exige uma ordem (ex.: biometria antes dos documentos) e a tela captura em outra, explique como a entrega é retida até a condição ser satisfeita.
- **Eliminação por ciclo de vida do bucket.** Versões atuais e antigas expiram; marcadores de exclusão são removidos; envios iniciados e não confirmados expiram em curto prazo; sem bloqueio de objeto (Object Lock), para permitir a eliminação.

Tabela de controles do fluxo: **Controle · Como funciona** (URL pré-assinada, bucket, identificação do arquivo sem dado pessoal, reenvio com nova versão, eliminação, falha de entrega).

### Prazo de retenção: proposta explícita

Prazo de guarda de arquivo é a decisão que mais gera discussão. Regras:

- Entra como **Proposta · a confirmar** até a privacidade/segurança aprovar.
- Justifique o prazo pela janela operacional real: tempo máximo de análise do destino, fim de semana, feriado prolongado, folga de segurança. Mostre a conta em uma frase; não escreva "padrão de mercado".
- Diga **de quando conta** (do envio de cada arquivo, não da proposta) e **o que acontece depois** (o sistema pede os documentos de novo).
- Registre no quadro de afirmações a data e a origem da decisão do autor.

## Seção 8 — privacidade e LGPD

Abra com um callout de alcance: esta seção descreve o tratamento e os controles técnicos; **não é parecer jurídico**; papéis, base legal e retenção são alinhados com a coordenação de privacidade e a área de segurança (item 8.4).

### 8.1 Dados tratados e finalidade

Declare a **finalidade** em uma frase. Depois, uma tabela **Categoria · Dados · Onde ficam · Proteção**, com uma linha por categoria que existe de fato (empresa, titulares, endereços, documentos, dado biométrico, aceites, identificação do dispositivo, contato). "Onde ficam" cobre banco do produto, bucket, o destino (parceiro) e provedores de mensageria. Cada linha deve bater com a seção 6, a tabela de controles da seção 7 e o glossário.

### 8.2 Princípios aplicados

Use só os que têm base: minimização; retenção curta de arquivos (proposta com prazo); segurança por padrão (cifra em repouso e em trânsito, menor privilégio); atendimento ao titular (eliminação por acesso excepcional, aprovado e auditado — proposta); termos e política de privacidade usados no fluxo, com registro de aceite; auditoria da conta como responsabilidade da infraestrutura do cliente.

### 8.3 Compartilhamento com terceiros

Tabela **Terceiro · Dados · Motivo**: o gateway do parceiro (e, por meio dele, o sistema que ele orquestra), o provedor de captura biométrica, os provedores de e-mail/SMS, o serviço de consulta de endereço. Só os que de fato recebem dado.

### 8.4 Pontos a alinhar com a privacidade e a segurança

Lista numerada de itens que **dependem de definição do cliente** e dos quais o desenho técnico precisa para fechar parâmetros:

1. **Papéis:** quem é controlador e quem é operador entre cliente, autor, parceiro e provedores.
2. **Base legal e classificação** de documento e de dado biométrico.
3. **Retenção:** aprovação da proposta de prazo dos arquivos e prazos de guarda dos dados cadastrais, incluindo exigência regulatória ou de política interna.
4. **RIPD:** necessidade do relatório e quem o elabora.
5. **Incidentes:** quem comunica a autoridade e os titulares e como o autor avisa o cliente.

Ajuste o conjunto ao que é verdade para o produto; não acrescente item de que o leitor não precisa.

## Checklist

- [ ] Cada categoria de dado aparece com o **mesmo tratamento** nas seções 6, 7, 8 e no glossário
- [ ] "Não é guardado" só para o que realmente não é; "eliminado em N" só com prazo e origem
- [ ] Registro de sucesso não é descrito como aprovação
- [ ] Prazo de retenção marcado como proposta, com a conta da janela operacional
- [ ] Callout de alcance (não é parecer jurídico) na abertura da seção 8
- [ ] 8.4 contém só o que depende do leitor

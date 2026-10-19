# Anexo A — superfície de exposição

Leia antes de responder a um pedido como "lista de endpoints internos e externos com a função de cada um". É o anexo onde mais se promete o que ainda não existe.

## Diagnóstico do modo de falha

- **Rotas copiadas de outro lugar.** Sem código novo, o agente aproveita as rotas de uma prova de conceito que usava outra arquitetura (outro parceiro, outro fluxo) e as apresenta como a superfície do produto. A área de segurança planeja teste em cima de rotas que nunca existirão.
- **Rotas finais prometidas antes da implementação.** Caminhos e métodos definidos "de cabeça" viram compromisso; qualquer mudança vira divergência entre documento e sistema.
- **Referência a datas de código.** "Conforme o código de 16/10" não faz sentido para o leitor e cria falsa sensação de implementação.
- **Inventário incompleto.** A lista cobre as telas óbvias e esquece sondas de saúde, consultas auxiliares, saídas para terceiros e rotas de apoio.
- **Convenção ≠ rota.** O texto mistura "convenções previstas" (prefixo, versão, formato de erro) com rotas específicas.

## Duas situações

| Situação | O que o anexo contém |
|---|---|
| **Desenvolvimento não começou** (ou a arquitetura mudou depois do código existente) | **Inventário de capacidades**: o que o produto vai expor, em linguagem funcional, sem caminho nem método. Um aviso diz que as rotas exatas serão definidas na implementação e entregues em nova versão do documento. |
| **Código existe e é a fonte da verdade** | **Tabela de rotas reais** (método, caminho, função, autenticação, exposição), extraída do código ou da especificação de API e conferida por varredura. A fonte é o código, não a memória. |

Na dúvida sobre qual é o caso, é o primeiro.

## Anexo com desenvolvimento não iniciado

Estrutura:

1. **Callout de estado:** o desenvolvimento ainda não começou; o inventário é preliminar e parte das jornadas do produto e da documentação de terceiros; lista o que o produto vai expor, não as rotas finais.
2. **A.1 — O que o produto expõe.** Tabela **Capacidade · Função · Exposição**, uma linha por capacidade, derivada das jornadas e da documentação do destino: cadastro/rascunho (com idempotência), confirmação de contato por código, termos e aceite, consulta auxiliar (endereço), emissão de URL de upload e confirmação, registro de dado sensível, envio para análise, consulta de status e pendências, reenvio, sondas de saúde. **Exposição** = externa (via gateway de API) ou interna (plataforma, não exposta ao usuário).
3. **Convenções previstas** (do padrão de engenharia): prefixo e versão das rotas de negócio, identificadores, formato de erro padronizado que não repete o valor enviado, limites de requisição globais e por rota sensível, documentação de API gerada só fora de produção.
4. **A.2 — Chamadas de saída.** Tabela **Destino · Rotas e uso** para o que o backend consome: o gateway do parceiro (rotas conforme a documentação do parceiro), provedores de mensageria, serviços auxiliares, sistema de chamados do cliente.
5. **Fontes:** jornadas do produto e documentação de terceiros; "ainda não implementado".

Regras:

- **Sem caminho, método ou versão** nas capacidades de entrada. As rotas de saída para terceiros podem citar caminhos **da documentação do terceiro**, porque são contrato externo.
- **Sem datas de código, nomes de pessoas ou promessas** ("será entregue em…").
- **Sondas de saúde:** liste-as como capacidade interna. Os nomes exatos só entram se forem decisão de engenharia confirmada; nomes copiados de exemplos de outra stack são palpite.
- Cada capacidade existe porque uma **jornada** a usa; cada capacidade de saída existe porque o **destino** a exige. Não liste "por segurança".

## Verificar completude

A pergunta do leitor é "são só esses ou haverá mais?". Responda com método, não com impressão:

1. **Jornadas → capacidades.** Percorra cada passo de cada jornada do produto; cada interação com o backend tem uma capacidade correspondente? (marque as que não têm).
2. **Destino → saídas.** Percorra a documentação do parceiro/provedor: toda chamada que o backend fará está em A.2?
3. **Plataforma → internas.** Sondas, métricas, documentação de API: estão classificadas como internas?
4. **Arquitetura → exposição.** Todo caminho de entrada do diagrama (CDN, gateway) tem capacidade; toda saída tem destino em A.2.
5. Registre o resultado ("N capacidades; M saídas; nenhuma jornada sem capacidade") no relatório de verificação e diga ao autor o que **pode surgir** na implementação (ex.: rota de apoio de UX).

## Quando o leitor pede mais precisão

Se a área de segurança pedir rotas finais antes do código, **não invente**: ofereça a versão 1.1 do documento após a definição da API (contrato da API aprovado) ou um esboço de contrato marcado como proposta. O autor decide.

## Checklist

- [ ] Estado do desenvolvimento escolhido (inventário × rotas reais) e dito no callout
- [ ] Nenhuma rota de entrada copiada de outra arquitetura ou prova de conceito
- [ ] Sem "código de DD/MM", pessoa nomeada ou promessa
- [ ] Jornada → capacidade, destino → saída, plataforma → interna: conferidos e registrados
- [ ] Convenções separadas das capacidades

# Caso: observabilidade (logs, métricas, APM, alertas)

## Logs

- Onde os logs dos pods vão no padrão do cliente (CloudWatch, Graylog, Loki, Elastic). Pergunte; não presuma.
- Formato que a aplicação escreve, em uma linha: "JSON na saída padrão do contêiner, com identificador de correlação". Se há linhas de métrica no log, diga o campo que as distingue e que o stream deve guardar todos os campos.
- Nível de log que não deve ser rebaixado, quando métricas ou alertas dependem dele.
- Stream ou grupo de log filtrado pelo namespace do projeto, e acesso de leitura ([`human-access.md`](human-access.md)).
- Não atestar o que o código não garante ("os logs não contêm dados pessoais"). Se a aplicação mascara campos, diga quais; se não sabe, não escreva.

## APM

- Pergunte como o cliente instrumenta (agente no node ou SDK com OTLP). Se a aplicação já exporta OTLP desligado por padrão, diga isso e peça o endereço do coletor e a autenticação, ou que fica desligado para não duplicar.
- Liberação de saída para o coletor, se for externo ([`egress-and-third-parties.md`](egress-and-third-parties.md)).

## Métricas de recursos

- Peça no chamado do recurso, quando a integração do APM com a conta não coleta por padrão (ex.: tamanho e idade da mensagem mais antiga das filas).

## Alertas

- Chamado próprio, depois de logs e métricas existirem.
- Precisa de decisão: quem recebe (equipe, fila de incidentes), por qual mecanismo (integração do APM, e-mail que abre incidente), com quais limiares.
- Sem decisão, registre o chamado como **pendente e sem texto** na ordem de abertura e na preparação de produção, com o que falta decidir.

## Preciso de volta

- Destino dos logs, nomes dos grupos ou do stream, endereço da ferramenta; endereço do coletor OTLP, se usado.

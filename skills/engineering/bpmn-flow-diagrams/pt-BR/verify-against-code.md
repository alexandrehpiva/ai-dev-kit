# verify-against-code

## Diagnóstico do modo de falha

Num fluxo de cadastro, um gateway foi desenhado perguntando "documento já cadastrado?" logo após o preenchimento do formulário. Parecia um ponto de decisão óbvio para esse tipo de fluxo. Mas, checando o backend, essa verificação não existia como decisão no código estudado: a duplicidade voltava como erro de submissão do sistema externo, não como um ramo controlado pela aplicação. O gateway descrevia um fluxo hipotético ("como seria natural funcionar"), não o real, e teria enganado quem estudasse o diagrama acreditando que existe uma lógica de verificação prévia que não existe.

**Todo elemento do diagrama (gateway, raia, evento) é uma afirmação sobre o processo real.** Se ela vem de "assim costuma funcionar" em vez de "eu confirmei na fonte", o risco de estar errada é alto.

## Como confirmar cada tipo de elemento antes de desenhar

- **Gateway (decisão):** ache o `if`/`switch`/condição no código que implementa aquele ponto, ou a frase explícita na documentação validada que descreve a condição. Sem isso, o losango fica de fora ou vira tarefa simples (passo sem ramificação).
- **Raia (quem executa):** identifique o arquivo/módulo responsável (componente de frontend, service/controller de backend) ou confirme que é o sistema externo quem dispara o passo. Não deduza a raia pelo nome do passo "parecer" ação de um ator.
- **Evento intermediário de mensagem (webhook, fila):** confirme no handler que o evento é de fato escutado e tratado. Se o evento existe na documentação da API mas não há tratamento no código, é **gap**, não evento comum (`status="gap"`, ver `shapes-and-colors.md`).
- **Caminho de erro/exceção:** procure tratamento de exceção, retry, timeout ou validação que rejeita. Não assuma que só existe o caminho feliz. Se a fonte não documenta o que acontece no erro, isso também é gap a marcar, não lacuna a preencher por suposição.

## Regra prática

Antes de desenhar qualquer losango, raia ou evento de mensagem, complete a frase: **"eu confirmei isso lendo `<arquivo:linha>` / `<seção da documentação validada>`."** Sem como preencher, marque `gap` ou investigue antes de desenhar. A frase preenchida é exatamente o que vai para a coluna "Fonte" da legenda (`LEGEND-FORMAT.md`).

## Ao corrigir um elemento reportado como errado ou faltando

Mesmo processo, sem exceção: releia a fonte, confirme a forma real do elemento e só então ajuste o script gerador (forma, raia, seta) e rode de novo. Quando a correção não for óbvia, registre a fonte da confirmação na `desc` do bloco (ex.: `desc="a validação checa o upload, não a ordem"`) ou na legenda, como um comentário de "por que não é o que parecia" num código.

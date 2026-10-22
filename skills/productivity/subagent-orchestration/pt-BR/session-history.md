# session-history — O histórico da sessão principal como fonte

## Diagnóstico do modo de falha

O que o usuário decidiu ao longo de uma sessão longa vive na conversa, não no resumo do principal. Resumos perdem nuance, trocam a palavra exata e, depois de compactação, esquecem decisões inteiras. Um subagente que só lê o resumo herda o erro do resumo.

## Como o principal passa o histórico

1. **Localize o transcript** da sessão em disco, quando o harness o expõe. Para achar por harness, leia `transcript-sources.md` da skill `recall-directives` (se instalada). Verifique que o arquivo existe antes de passar o caminho; se não houver forma confiável, não invente caminho: diga ao subagente que não há transcript e passe as citações literais no briefing.
2. **Passe o caminho absoluto** no briefing, junto com palavras-chave de busca específicas para aquele lote (termos, nomes de arquivos, números de história).
3. **Oriente a busca pontual**, nunca leitura inteira: `grep -n` por palavra-chave e, em transcript JSONL, `jq` para filtrar os eventos do usuário e imprimir só o texto. Pedir para ler o arquivo todo estoura o contexto e perde o foco.
4. **Hierarquia de fontes**: o transcript é fonte primária das decisões do usuário; o resumo do principal é secundário. Se divergirem, vale o transcript, e o subagente reporta a divergência.
5. **Citar a origem**: toda decisão que o subagente usar vem com trecho curto e a localização no transcript (linha ou carimbo), para o principal conferir.

## Privacidade

O transcript pode conter dados pessoais, de cliente e segredos. O subagente trata o conteúdo como confidencial: não envia a destinos externos, não o copia para documentos públicos, não grava segredo em relatório, e cita só o trecho mínimo necessário.

## Exemplo genérico de busca

```bash
# eventos do usuário que mencionam um termo (JSONL, um evento por linha)
jq -r 'select(.type=="user") | .message.content | if type=="string" then . else map(.text? // empty) | join(" ") end' "$TRANSCRIPT" | grep -n -i "termo"
```

Confirme o schema do arquivo antes de depender do `jq` acima; ajuste os campos se o formato for outro.

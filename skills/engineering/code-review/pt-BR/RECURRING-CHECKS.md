# RECURRING-CHECKS — checks de alta taxa de aceitação

Destilados de reviews reais que foram aceitas. Não exaustivo; aplique julgamento.

## Corretude em inputs externos / de borda

- **Acesso a dict em payloads externos (APIs de terceiros, webhooks, integrações) em Python**: prefira `data.get(key) or default`
  em vez de `data[key]`. Uma chave ausente levanta `KeyError` e quebra o fluxo — falha real.
  ```python
  # arriscado: KeyError se 'mother_name' estiver ausente
  mother_name=info['mother_name'] if info['mother_name'] else ""
  # seguro: cobre chave ausente E valor falsy
  mother_name=info.get('mother_name') or ""
  ```
- **Fallbacks de string vazia vs null**: `a ?? b` (JS) só faz fallback em null/undefined. Se uma
  string vazia `""` também deve fazer fallback (ex: resposta parcial de API sobrescrevendo um
  valor tipado), use `a || b`. Verifique a intenção.

## Reuso / simplificação

- **Regra de negócio duplicada** (mesma constante/lógica em dois lugares — ex: uma idade máxima
  `80.5` num validator e num date-picker): aponte. Extraia uma fonte única de verdade. É um nit
  que vale a pena e tende a ser aceito.
- **Padrões inconsistentes em call sites irmãos**: se um caminho já usa o idioma seguro/limpo e
  outro não, alinhe-os.

## Escopo / higiene (enquadre como perguntas)

- **Remoção de config/código não relacionada ao propósito do PR**: não afirme "risco de quebra".
  Pergunte se algo ainda referencia as chaves removidas (sugira um grep) e enquadre como higiene /
  "idealmente um PR de limpeza separado". Verifique com uma busca antes de atribuir severidade alta.

## Validators / helpers compartilhados

- Um **validator/helper com nome genérico** mas **mensagem hardcoded específica** (ex: diz "CPF"
  mas aceita qualquer documento) é uma armadilha futura — neutralize a mensagem padrão ou
  documente a suposição.

## Nits — mantenha proporcional

- Nits puramente cosméticos em PRs pequenos e focados têm baixa aceitação. Mencione levemente ou omita.

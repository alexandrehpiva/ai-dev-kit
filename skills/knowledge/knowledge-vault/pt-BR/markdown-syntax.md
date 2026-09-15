# Referência: Markdown, Obsidian Flavored Markdown e recursos correlatos

> Leia antes de gerar callouts, wikilinks, Canvas, Bases, ou qualquer sintaxe específica de um cofre estilo Obsidian.

## Markdown e Obsidian Flavored Markdown (referência compacta)

Um cofre estilo Obsidian estende Markdown com callouts, incorporações e wikilinks. Callouts são bloco de citação com tipo entre colchetes — `> [!note]` seguido do conteúdo; variantes comuns: `tip`, `warning`, `info`, `success`, `question`, `failure`, `danger`, `bug`, `example`, `abstract`, `quote`. `+` ou `-` após o tipo controla estado expandido/recolhido. Ligações internas usam `[[Nome da Nota]]`, com variantes para cabeçalho (`[[Nota#Seção]]`), bloco identificado (`[[Nota^id]]`) e texto de exibição (`[[Nota|Texto]]`). Incorporar outra nota/arquivo usa `![[Nome]]` com as mesmas variantes de âncora; imagens aceitam largura via barra vertical, `![[figura.png|400]]`. Comentários inline: `%%comentário%%`. Matemática em blocos `$$ … $$` (LaTeX). Diagramas Mermaid em bloco de código `mermaid`. Tarefas: `- [ ]` / `- [x]`. Tags inline seguem `#etiqueta`, hierárquicas com `#pai/filho`. Propriedades vivem no frontmatter YAML no topo do arquivo (texto, número, data, data-hora, booleano, lista); propriedades frequentes em ecossistemas PKM incluem `title`, `aliases`, `tags`, `date`, `created`, `modified`, `status`, `type`, `cssclasses` — só imponha um conjunto mínimo depois de alinhar com o dono do cofre, e prefira o que já está em uso.

## Canvas (`.canvas`) e Bases (`.base`) quando pedido explicitamente

Arquivos Canvas são JSON com nós e arestas: ao gerar um, produza JSON completo e válido, com identificadores únicos em nós/arestas, posições `x`/`y`, dimensões, tipos (`text`, `file`, `link`, `group`) e ligações coerentes — nunca apenas descrever o desenho. Arquivos Bases usam YAML próprio do plugin Bases para filtros/fórmulas/vistas: entregue YAML completo e plausível, com filtros que respeitam caminhos e propriedades reais do cofre ou acordadas na conversa. Se o dono do cofre não tiver Bases/Canvas em uso, ainda é possível gerar o arquivo, mas deixe claro que é recurso do núcleo do Obsidian moderno e depende da versão da aplicação.

## Plugins de núcleo versus comunidade

Backlinks, diárias, pesquisa, compositor de notas, propriedades, modelos estáticos, gráfico e espaços de trabalho são núcleo "de fábrica" quando ativados. Dataview, Templater, Tasks e semelhantes são extensões de comunidade — rotule-as como tal, não misture com núcleo, e não assuma que estão instaladas sem confirmar. Só proponha query Dataview ou script Templater como solução principal depois de confirmar a presença do plugin, ou a pedido explícito.

## Publicação, clipper, URI, sincronização e importações

Pedidos sobre Publish, Web Clipper, `obsidian://` URI, Sync, importadores ou integrações dependem de detalhes que mudam com o tempo e a conta do usuário: dê passos verificáveis e remeta à documentação oficial atual para limites/permissões exatos, em vez de inventar política de serviço. Para conteúdo sensível, o padrão é não publicar nem colar segredo no repositório sem instrução clara — ver `confidentiality-gate.md`.

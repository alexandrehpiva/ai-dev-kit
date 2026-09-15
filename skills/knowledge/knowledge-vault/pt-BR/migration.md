# Referência: migrar material externo para o cofre

> Leia antes de migrar ou absorver material externo (documentação antiga, repositório de notas descontinuado, anotações soltas, export de outra ferramenta) para o cofre.

## Diagnóstico do modo de falha

Sem esta disciplina, migração vira "copiar e colar" — a IA despeja conteúdo bruto ou só cria apontadores para a origem, sem reescrever para o padrão do cofre de destino. O resultado é um cofre com dois estilos coexistindo e conhecimento que não navega com o resto (sem tags, sem wikilinks, sem taxonomia por entidade).

## Requisito central

O cofre deve receber conhecimento **completo, contextualizado e navegável** — não apontadores para a origem. Isso significa: estudar cada nota/documento fonte, considerar data de criação/última atualização, decidir a pasta temática correta pela taxonomia por entidade (ver `SKILL.md`), criar ou atualizar notas de destino com conteúdo substantivo, e usar `#tags` como chave de conexão quando não for prático editar muitas notas para criar wikilinks individuais.

## Fluxo para migrações grandes

1. **Inventário antes de migrar.** Mantenha uma nota de progresso com a lista de arquivos/documentos fonte, status de leitura, datas relevantes, destino escolhido e observações. Não comece a escrever notas de destino sem esse inventário para migração com mais de ~10 itens.
2. **Ciclos pequenos com leitura humana**, não script que despeja conteúdo sem interpretação. Cada item passa por: ler → classificar entidade/pasta → decidir se enriquece nota existente ou cria nova → escrever → marcar como migrado no inventário.
3. **Subpastas quando houver massa crítica.** Se um ramo da taxonomia acumular muitas notas, crie subpastas temáticas de segundo/terceiro nível (ex.: `Software/<área>/<subárea>/`) em vez de deixar tudo raso, e adicione nota-mapa quando ajudar a navegação.
4. **Checar duplicação antes de criar.** Busque por palavra-chave se já existe nota correspondente no cofre; se existir, enriqueça sem duplicar; se a informação nova contradiz a antiga por estar desatualizada (não por estar errada), preserve o histórico e adicione a informação nova com data — só remova sem rastro se a informação anterior era simplesmente incorreta.
5. **Fonte verificada.** Toda migração de conteúdo técnico deve manter ou recuperar a referência ao arquivo/repositório de origem real, não inventar caminho.

## Portão de segurança

Migração não é isenta do portão de confidencialidade — ver `confidentiality-gate.md`. Material externo pode conter segredo, PII ou dado sensível de terceiro que não deveria entrar no cofre de destino, ou deveria entrar já marcado como confidencial. Classifique antes de escrever, não depois.

# Segurança, privacidade e atribuição em skills

Skills são arquivos versionáveis, compartilháveis e publicáveis. Trate-as como código de repositório — mesmo que sejam privadas hoje, porque a próxima pessoa a empacotá-las para compartilhar raramente relê cada linha.

## Diagnóstico do modo de falha

- **Contexto do autor vaza para a skill.** A skill nasce resolvendo um problema concreto, e o agente escreve com os nomes daquele caso: o cliente, o produto, o path da máquina, o e-mail, o ID do workspace. Funciona perfeitamente para o autor e expõe dados dele no primeiro compartilhamento.
- **Autorização local vira autorização de distribuição.** Um dado incluído com permissão para uso privado continua lá quando a skill é publicada, e ninguém lembra que a permissão era só local.
- **Conteúdo de terceiros entra sem crédito.** Um trecho adaptado de outra coleção de skills, de um artigo ou de um template é incorporado como se fosse autoral, e a licença de origem (que pode exigir atribuição ou proibir redistribuição) é ignorada.

## O que não entra sem autorização explícita e específica

Os itens abaixo só podem entrar numa skill com autorização explícita do usuário para aquele uso concreto:

- **Segredos:** tokens, API keys, senhas, passphrases, JWTs, chaves privadas, strings de conexão com credencial.
- **Dados pessoais:** e-mail, nome, documento de identificação, telefone, endereço — mesmo que "só para exemplo".
- **Contexto pessoal ou de cliente:** paths absolutos com dados do usuário, nomes de conta, IDs de workspace, URLs de instância privada, nomes de cliente, produto ou projeto não público, datas e incidentes que identificam um projeto.

Antes de incluir qualquer item dessa lista, confirme com o usuário: *"Você quer que [dado X] fique fixo na skill?"* — não assuma que ele percebeu a implicação. A autorização vale por dado e por skill; uma permissão anterior não se transfere.

**Default sem autorização:** o dado fica fora da skill. Contexto do usuário vai para a memória do agente ou para o prompt da tarefa — a skill instrui *como* obter o dado (qual comando, qual arquivo de configuração, qual pergunta fazer), não *qual* é o dado.

## Generalizar em vez de remover

Quando o conteúdo veio de um caso real, generalize em vez de apagar — o caso real costuma ser a melhor motivação que a skill tem:

- Nomes de entidade viram placeholders ou exemplos neutros (`<PROD>`, `ACME`, `meu-produto`).
- Incidentes viram diagnóstico do modo de falha sem identificar projeto, cliente ou data ("num protótipo de onboarding, a versão foi numerada antes da aprovação…").
- Valores que eram constantes do caso viram parâmetros com default sensato (um argumento de linha de comando, um arquivo de configuração, uma variável de ambiente).
- Caminhos de máquina viram detecção por sistema operacional ou path relativo ao repositório.

Teste de pronto: um leitor sem nenhum contexto do caso de origem consegue aplicar cada item sem substituir nomes mentalmente, e nada no texto permite identificar de onde ele veio.

## Conteúdo de terceiros: atribuição e licença

Se qualquer parte da skill (texto, asset, script, template) foi adaptada de fonte externa:

1. Identifique a origem e a licença antes de publicar. Sem licença conhecida, o padrão é **não** redistribuir o texto: reescreva com palavras próprias e cite a fonte como referência.
2. Licença que exige atribuição (Apache 2.0, MIT, CC BY): mantenha o aviso exigido (ex.: um `LICENSE.txt` ao lado do asset), registre a origem e diga quais modificações foram feitas (tradução, reorganização, generalização).
3. Declare a origem no campo `license:` do frontmatter quando a skill mistura conteúdo próprio e de terceiros — dizendo qual asset vem de onde e que o restante é autoral.
4. Prefira estudo com paráfrase a cópia literal: análise com palavras próprias, exemplos próprios e link para o original é mais útil e não carrega a licença de terceiros.

Não presuma autoria: se a skill de origem tem histórico incerto, verifique (cabeçalho do arquivo, notas de origem, histórico do repositório) antes de declarar o conteúdo como próprio.

## Varredura antes de compartilhar ou publicar

Antes de commitar num repositório público, empacotar ou mover uma skill de uso privado para distribuição:

1. **Releia tudo** — `SKILL.md`, cada asset, cada script, cada exemplo dentro de bloco de código. Exemplos e comentários de script são onde o contexto do autor mais se esconde.
2. **Busque termos de risco** com `grep -rniE` na pasta da skill: nomes de cliente, produto e pessoa conhecidos do contexto; `/Users/`, `/home/`, `C:\\Users`; domínios internos; `@` seguido de domínio; prefixos de token comuns. Cada ocorrência é classificada como (a) intencional e autorizada, (b) falso positivo, ou (c) a generalizar.
3. **Rode um scanner de segredos** na pasta, por exemplo `gitleaks dir <pasta-da-skill>`.
4. **Confirme com o usuário** se há itens incluídos com autorização só para uso local que não devem ir para distribuição.
5. **Confira atribuições** (seção anterior) e o campo `license:`.

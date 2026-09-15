# Portão de confidencialidade do cofre (criticidade máxima)

## Diagnóstico do modo de falha

Sem esta disciplina, o agente trata o cofre como qualquer outra fonte de contexto e reproduz trechos privados (reuniões, avaliações, dados internos) em destinos externos "porque dá contexto" — task de board, PR, mensagem, prompt a terceiro. O vazamento nunca é intencional; é um efeito colateral de otimizar clareza do artefato externo sem parar para classificar a origem da informação.

## Princípio

Todo conteúdo de um cofre de conhecimento (pessoal ou de time) é **privado por padrão** até que o dono do cofre autorize um uso específico. **Ler o cofre para adquirir contexto é livre.** A restrição é sobre **expor**: nenhum trecho pode ser reproduzido, citado, parafraseado ou usado como insumo em destino externo (issue tracker, PR, chat de terceiros, e-mail, prompt a outro serviço, qualquer saída visível a outras pessoas) sem autorização explícita **para aquele uso**. Ausência de objeção não é autorização.

## Postura

Antes de qualquer escrita externa, pergunte: *"o que estou prestes a enviar contém, deriva de, ou revela algo privado do cofre?"* Sim ou talvez → aplique a regra do menor vazamento abaixo ou pergunte. Silêncio do usuário = não autorizado. Propague esta restrição a qualquer subagente que produza artefato externo a partir deste cofre.

## Classificação

**Privado-crítico — nunca sai sem autorização explícita; segredos nunca saem.**
Transcrições de reunião sensíveis (lideranças, 1:1s), avaliações/remuneração/desempenho de qualquer pessoa, assuntos pessoais, e qualquer senha/token/chave/credencial.

**Sensível-de-ambiente — abstrair antes de expor.**
Caminhos locais de máquina, nomes de arquivo/estrutura de diretório do dono, referências a "conforme minha nota X" (o leitor externo não tem acesso), PII de terceiros e dado interno não destinado ao artefato em questão.

**Público-seguro — pode compor o artefato externo.**
Fato técnico genérico, decisão já acordada para aquele artefato específico, conteúdo que o próprio usuário pediu para publicar ali.

## Regra do menor vazamento

Quando o objetivo legítimo exige artefato externo com contexto vindo do cofre: inclua só o estritamente necessário e sanitize o resto. Substitua caminho local por descrição genérica; extraia só a decisão neutra de uma transcrição, nunca cole trecho bruto; nunca cite "conforme a nota X" — reescreva o fato de forma autossuficiente ou omita. Restando dúvida após sanitizar → trate como sensível, não exponha, pergunte.

## Convenção de marcação no cofre

Notas sensíveis marcam o risco em três camadas:

1. **Frontmatter:** `confidencial: true` e `sensibilidade: alta|media`.
2. **Tag:** `#confidencial` inline ou item de lista, respeitando o estilo já usado no arquivo.
3. **Callout no topo do corpo**, logo após o frontmatter:

   ```
   > [!danger] 🔒 CONFIDENCIAL — sensibilidade ALTA. {motivo curto}. Não reproduzir, citar ou usar como insumo em destino externo sem autorização explícita do dono do cofre.
   ```

   `[!danger]` para ALTA, `[!warning]` para MÉDIA. Ao encontrar esse banner ou `confidencial: true`, trate com a cautela máxima descrita acima — sinal de que já houve triagem.

Marcar não substitui a regra default-deny: todo o cofre é privado por padrão; o marcador só eleva o alerta nos casos de maior risco.

## Exemplos

- **Bom:** numa issue pública, descrever o contrato `{id, estado}` e o fluxo de transição — fato técnico público-seguro para aquele board.
- **Ruim:** colar na mesma issue um trecho da transcrição do 1:1 onde se discutiu a promoção de alguém, "para dar contexto".
- **Bom:** num PR, referenciar `src/app/.../pipe.ts` do próprio repositório onde o PR vive.
- **Ruim:** num PR ou mensagem de chat, escrever "ver `/Users/.../nota.md`" — caminho local que ninguém mais acessa.

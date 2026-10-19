# Origem de cada afirmação (chips) e itens "proposta"

Leia antes de preencher qualquer tabela de controles. A origem é o que permite ao leitor confiar no documento e separar o que o autor sabe do que o autor propõe.

## Diagnóstico do modo de falha

Documento sem origem trata igual um requisito da área de segurança, uma regra de um terceiro e um palpite do autor. O leitor aprova achando que tudo é compromisso, ou desconfia de tudo. Com origem em cada linha, ele sabe o que pode questionar e o que precisa responder.

## O que é o chip

Pequena etiqueta colorida ao fim de cada linha de controle (coluna **Origem** das tabelas). A seção 1 traz a legenda completa. Use **uma classe por origem real**; pode haver mais de uma na mesma linha (ex.: exigência do leitor + elemento do desenho).

| Classe (nome sugerido) | Quando usar | Cor sugerida (token) |
|---|---|---|
| **Reunião de segurança · data** | Exigência ou orientação dada pela área do leitor | rosa |
| **Padrão da infra · data** | Padrão da infraestrutura do cliente, informado ao autor | azul-claro |
| **Desenho de arquitetura** | Elemento do diagrama da seção 4 | azul (padrão) |
| **Doc. do parceiro** | Regra da documentação oficial de um terceiro | verde |
| **Padrão de engenharia** | Prática adotada no código do autor | roxo |
| **Comitê de arquitetura · data** | Decisão registrada de comitê | azul (padrão) |
| **Requisito do desenho** | Requisito do projeto para o desenho e o código que a infraestrutura aplica | verde |
| **Comportamento do produto** | Conforme as jornadas/protótipo aprovado | laranja |
| **Proposta · a confirmar** | Controle proposto pelo autor, ainda não validado pelo leitor ou pela infraestrutura | âmbar |

Renomeie as classes conforme o projeto (datas e nomes reais de reuniões entram aqui), mas **mantenha a taxonomia**: uma classe para exigência do leitor, uma para padrão do cliente, uma para o desenho, uma para terceiros, uma para prática do autor, uma para proposta.

## Regras

1. **Toda linha de controle tem pelo menos um chip.** `lint_doc.py` falha se uma célula de "Origem" estiver vazia.
2. **Sem origem não entra.** Se o fato não tem classe, ele é `lacuna` no quadro de afirmações: vira pergunta ao autor ou proposta explícita.
3. **"Proposta · a confirmar" é um estado, não um adjetivo.** Cada proposta indica, na própria linha, o que precisa ser validado e por quem (leitor, privacidade, infraestrutura). Ao final, a seção 8.4 e a seção 11 devolvem ao leitor a lista das propostas como perguntas.
4. **Não inflar a origem.** "Doc. do parceiro" só se a documentação do parceiro diz aquilo; não vale "o parceiro costuma".
5. **Uma decisão do autor nesta sessão** que não está em outra fonte é, para o documento, **proposta** (a menos que o autor mande tratá-la como requisito).
6. **Datas nos chips** só para eventos reais e verificáveis (reunião, resumo de comitê). Nunca invente data.

## Pares Bom / Ruim

| Ruim | Bom |
|---|---|
| "Os dados são auditados continuamente." *(sem origem)* | "Trilha de auditoria e detecção de ameaças na conta são responsabilidade da infraestrutura do cliente, fora do escopo do projeto." + chip *Padrão da infra* |
| "Retenção de 7 dias." | "Proposta de prazo: eliminação 7 dias depois do envio de cada arquivo, por regra de ciclo de vida." + chip *Proposta · a confirmar* |
| Linha de tabela com a coluna Origem vazia | Linha com *Desenho de arquitetura* + *Reunião de segurança · data* |
| "Conforme combinado com a equipe do parceiro…" | "Regra da documentação do parceiro." (sem procedência de conversa) |

## Marca no topo e na frase

Item incerto é marcado em dois lugares: no chip da linha (ou callout de aviso na seção) **e** na frase, com "proposta", "a confirmar" ou "a definir". Uma seção inteira que depende de decisão aberta recebe um callout de aviso no início.

## Checklist

- [ ] Legenda de chips na seção 1, com somente as classes usadas
- [ ] Nenhuma célula de Origem vazia
- [ ] Toda proposta indica o que precisa ser validado e por quem
- [ ] Nenhuma data inventada nos chips
- [ ] Lista de propostas devolvida ao leitor (seção 8.4/11)

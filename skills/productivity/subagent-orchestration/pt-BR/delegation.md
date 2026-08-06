# delegation — Partir trabalho e lançar subagentes

## Antes de lançar

1. Definir **critério de pronto** (ex.: "585 arquivos verificados e deletados ou BLOCKED com motivo").
2. Partir em lotes **disjuntos** — sem overlap de `file_id`, path ou recurso exclusivo.
3. Escrever prompt por subagente com:
   - escopo exato (lista, range de linhas, pasta);
   - protocolo passo a passo;
   - paths e ferramentas;
   - o que **não** fazer;
   - formato do retorno (contagens DELETED/BLOCKED/GONE + lista de bloqueios);
   - onde registrar (arquivo de log markdown, se houver).

## Paralelismo

- Lance subagentes **em paralelo** quando os lotes não competem pelo mesmo recurso (mesmo arquivo, mesmo lock de HD, mesma branch git em conflito).
- Se o domínio impõe exclusão (ex.: um compactador no disco fonte), serialize só essa parte; o resto pode paralelizar (upload, verify, delete de pastas diferentes).

## O que o principal faz vs subagente

| Principal | Subagente |
|-----------|-----------|
| Partir lotes, definir protocolo | Executar o lote inteiro até relatório final |
| Monitorar e retomar | Corrigir falhas **dentro** do protocolo |
| Decidir escalação e relançar | Não expandir escopo nem mudar o objetivo |
| Consolidar resumo ao usuário | Append em log compartilhado, se pedido |

## Modelo e harness

- Preferir o modelo que o usuário ou o projeto já usa para subagentes (ex.: composer-2.5), salvo instrução contrária.
- Incluir shell limpo quando PATH quebrado já foi problema na sessão (`env -i` + PATH mínimo).

## Ruim / bom

**Ruim:** um subagente com prompt "limpe o Drive" sem lista, sem protocolo, sem critério de delete.

**Bom:** "Seu lote são linhas 201–400 do TSV X; para cada uma: verificar A+B, se OK deletar, senão BLOCKED com motivo; não criar scripts."

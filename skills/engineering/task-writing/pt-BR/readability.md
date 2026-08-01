# Legibilidade de tasks — profissional e legível, sem perder detalhe técnico

Complementa `lean-writing.md`. **Enxutez** define *o que cortar* (escopo). **Legibilidade**
define *como dispor* o que fica: o texto deve ser profissional e fácil de ler por quem não vai
abrir o código (produto, QA), **sem** descartar o detalhe técnico — apenas isolando-o.

Leia este arquivo **antes de redigir** qualquer task técnica, junto com `lean-writing.md`.

---

## A dor que isto corrige

Dois extremos ruins:
- **Verboso-técnico:** citar nomes de classe, paths e números de linha no meio das frases;
  colar classes/trechos de código inteiros nos critérios de aceite e no DoD. Só quem já
  conhece o código lê com conforto.
- **Raso demais:** remover o detalhe técnico a ponto de quem for implementar não saber o que
  fazer.

O alvo é o **meio-termo**: prosa limpa para humanos + detalhe técnico preservado, porém
**isolado** em seções próprias.

---

## Princípios

1. **Prosa profissional e legível.** Frases completas, entendíveis por produto e QA sem abrir
   o repositório.
2. **Sem código no meio de frases.** Descreva o comportamento em linguagem natural; nomes de
   arquivo, classe e linha não entram na prosa corrida.
3. **Critérios de aceite (BDD) e DoD livres de código.** Só comportamento observável. Nada de
   nomes de método, paths, payloads ou trechos de código.
4. **Detalhe técnico preservado, mas isolado.** Concentre paths, nomes de arquivo/classe e
   decisões de implementação numa seção **"Notas técnicas"** e/ou **"Referências de código"**
   ao fim do card — como lista de referência, não diluído no texto.
5. **Contratos de API em tabela.** Endpoint, método, payload, respostas e erros vão em
   **tabela de campos**, não como classe colada inteira.

---

## Pares Bom / Ruim

### Citação de código na prosa

| Ruim | Bom |
|---|---|
| Tornar `card_id` opcional em `CreateInput` (`app/schemas/input.py:100`), ajustando o `CreateUseCase`. | O identificador do card passa a ser opcional. *(o path vai para "Referências de código")* |

### Critério de aceite

| Ruim | Bom |
|---|---|
| **Then** o endpoint retorna 422 com mensagem mencionando `"campo obrigatório"`. | **Então** o sistema rejeita o pedido quando o campo obrigatório não é informado. |

### Contrato de API

| Ruim | Bom |
|---|---|
| Colar a classe `CreateInput(BaseModel): ...` inteira no corpo. | Tabela com colunas Campo / Tipo / Obrigatório / Observação; a classe real fica como referência em "Notas técnicas". |

---

## Estrutura recomendada de uma task técnica

1. **Contexto** — por que a task existe, em linguagem de negócio (2–4 frases; ver enxutez).
2. **Objetivo / Requisitos** — o que o sistema passa a fazer, em prosa.
3. **Contrato de API** *(se houver)* — em tabela.
4. **Critérios de Aceite (BDD)** — comportamento observável, sem código.
5. **DoD** — evidências desta entrega, sem código.
6. **Notas técnicas** *(opcional)* — decisões de implementação como fatos; paths e nomes de
   arquivo são permitidos aqui, em lista.
7. **Referências de código** *(opcional)* — lista de arquivos/módulos relevantes.

---

## Checklist de legibilidade (aplicar após redigir)

- [ ] Nenhum nome de arquivo, classe ou número de linha no meio de frases da prosa
- [ ] Critérios de aceite e DoD sem código, paths ou payloads
- [ ] Detalhe técnico presente, porém em "Notas técnicas" / "Referências de código"
- [ ] Contratos de API em tabela, não como classe colada
- [ ] Um leitor de produto/QA entende Contexto e Critérios de Aceite sem abrir o repositório

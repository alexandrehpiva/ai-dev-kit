# Revisão antes de entregar

Quatro conferências, nesta ordem. Nenhuma substitui a outra.

## 1. Lint da especificação

```bash
python3 scripts/lint_tickets.py chamados-hml-p2.json
```

Zero erros. Leia cada aviso: aviso de parágrafo longo ou de frase de bastidor quase sempre é verdade. O lint confere: aspas angulares, código de chamado repetido, chamado sem texto, chamado de deploy ou esteira sem a seção "Build e deploy" completa, JSON inválido em bloco, segredo aparente, nome de outro ambiente, frases proibidas, tópico longo, falta de "Preciso de volta" nos casos que devolvem algo, política com ação ou recurso curinga em escrita. É heurístico: não substitui a releitura.

## 2. Revisor SRE cego (subagente)

Um subagente por documento, **sem** o contexto do projeto: recebe só o texto dos chamados (o que o SRE do cliente vai ver) e o papel de especialista em infraestrutura do provedor de nuvem usado.

<sre-reviewer-brief-template>
Você é SRE sênior em <provedor de nuvem> e acabou de receber estes chamados na sua fila. Você não conhece o produto nem o time que pediu. Para cada item de cada chamado, preencha:

| Chamado | Item | O que eu faria (ação entendida) | Veredito (executável / ambíguo / não executável / desnecessário) | Confiança (alta, média, baixa) | Evidência (trecho do texto ou documentação oficial com link) | Pergunta que eu faria ao solicitante | O que não consigo avaliar sem conhecer a empresa |

Depois, liste: o que falta para você executar sem voltar ao solicitante; o que está sobrando (você leria e não faria nada); conflitos entre chamados; o que você devolveria.
Não reescreva os chamados. Não invente padrão da empresa.
</sre-reviewer-brief-template>

**Avalie o retorno com cuidado.** O revisor não conhece a infra do cliente e erra. Para cada achado:

- Confira contra o código, o desenho e a documentação oficial antes de aceitar.
- Achado que contradiz uma resposta já dada pela infra do cliente: a infra ganha.
- Achado que pede mais texto: aplique o critério de [`writing-rules.md`](writing-rules.md) (o executor faria algo diferente?). Revisor cego tende a pedir explicação demais.
- Achado de "não executável" por falta de dado (repositório, entrypoint, ARN de origem): quase sempre procede.
- Relate ao autor o que aceitou, o que recusou e por quê. Se o veredito sozinho não deixa avaliar, melhore o roteiro do revisor e rode de novo.

## 3. Conferência contra o código

Para chamados que configuram a aplicação (deploy, esteira, segredos, identidade, gateway):

- Mapa variável x chamado: cada variável obrigatória no modo de produção está no chamado (ou tem padrão no código); nenhuma variável do chamado deixou de existir.
- Portas, health checks, usuário do processo, tempos de inicialização e encerramento batem com a imagem.
- Permissões da identidade batem com as chamadas reais ao SDK.
- Variáveis do build do front (incorporadas ao pacote) estão todas no chamado da esteira do front; o build falha sem elas.
- Cabeçalhos que o front envia e a aplicação usa (correlação, idempotência, IP do cliente) estão no repasse do CDN e do gateway.

Use uma visão independente (tech lead do projeto ou subagente com acesso ao código). Traga os achados ao autor antes de alterar documento já enviado.

## 4. PDF

Gere com `generate-pdf-report` e leia as páginas:

- [ ] Cada chamado começa em página nova; nenhum título sozinho no pé da página.
- [ ] Blocos de código inteiros, sem corte lateral; ARNs quebrando dentro da caixa.
- [ ] Placeholders `<...>` visíveis.
- [ ] Amarelo só onde há `[A CONFIRMAR]`.
- [ ] Tabela-resumo com todos os chamados, na ordem.
- [ ] Nenhuma aspa angular, nenhum valor de segredo, nenhum nome de outro ambiente.

## 5. Verificação independente

Antes de o documento virar verdade (enviado ao cliente ou gravado como fonte do projeto), rode a skill `hallucination-guard`: cada número, nome e decisão tem origem num arquivo, numa mensagem da infra ou no código.

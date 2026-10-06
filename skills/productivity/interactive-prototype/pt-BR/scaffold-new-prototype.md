# Criar um repositório de protótipo novo (scaffold completo)

Ler antes de criar qualquer protótipo do zero. O repositório nasce **completo e organizado** por script, não montado de memória: `scripts/scaffold.py` copia os `templates/` da skill (shell, estilos em camadas, `build.py`, roteador, stepper, badge/changelog, botão Demo, README, design system, launch.json, `.gitignore`, config de grupo).

## Diagnóstico do modo de falha

Sem um procedimento determinístico, cada protótipo novo sai diferente: falta README ou `.gitignore`, `dist/` é versionado, o badge/changelog é reescrito de memória com variações, o design system nunca é criado, o servidor de dev fica sem porta definida. O agente "reproduz de cabeça" o que viu no último projeto e esquece itens. Template real + script elimina essa variação.

## Passos

1. **Confirmar com o usuário** (uma pergunta curta, junto da direção visual quando possível): nome do produto, pasta de saída, personas/variantes do fluxo (se houver), se quer `docs/user-journeys/` já criado (documentação nova exige confirmação), e se o trabalho será em grupo. Porta: use a padrão `8850` salvo conflito com outro protótipo da máquina.
2. **Rodar o scaffold** (o diretório de saída precisa estar inexistente ou vazio; o script recusa sobrescrever):
   ```bash
   python3 <skill>/scripts/scaffold.py --name "<Nome>" --out <pasta> [--slug kebab] [--port 8850] \
       [--prefix abc] [--personas "PF:Pessoa Física,PJ:Pessoa Jurídica" --journeys] [--group-mode]
   ```
   Use `--dry-run` para listar a árvore antes. `--prefix` é o prefixo das classes de componente (default: 3 letras do slug).
3. **Primeiro build e render:** `cd <pasta> && python3 build.py`, abrir `dist/index.html` (ou subir o hot reload — [`dev-server-hot-reload.md`](dev-server-hot-reload.md)), conferir que a tela inicial renderiza sem erro de console.
4. **Aplicar a direção visual** ([`aesthetic-direction.md`](aesthetic-direction.md)): substituir os valores `PLACEHOLDER` de `styles/tokens.css` e a fonte do `<head>` em `index.html`, e **espelhar os mesmos valores em `docs/design-system.md`** ([`design-system.md`](design-system.md) — o documento e os tokens nascem juntos).
5. **Trocar as telas de exemplo** pelas telas reais seguindo [`app-architecture.md`](app-architecture.md): `FLOWS`, `screens`, `DEMO_FILLERS`, validadores. Remover o que não for usado (a tela de exemplo não deve sobrar no produto final).
6. **Conferir README contra o disco** (`find . -not -path './.git/*' -not -path './dist/*'`): a árvore do README só pode citar o que existe.
7. **Estado inicial de versão:** badge `v0.0.0 · protótipo` e changelog com entrada `Pendente (não commitado)` — já vêm do template ([`versioning-and-changelog.md`](versioning-and-changelog.md)). O primeiro lote aprovado vira `v0.1.0`.
8. **Rodar [`UX-REVIEW.md`](UX-REVIEW.md)** (375/768/1280 px, estados) antes de entregar.
9. **Primeiro commit só com aprovação do usuário.** `git init` já foi feito (branch `main`), sem commit.

## Modo trabalho em grupo

O scaffold nunca grava `groupMode: true`: ele só liga depois que o repositório está pronto e o acesso de push foi conferido. Depois de adicionar o remoto (`git remote add origin <url>`) e fazer o primeiro envio da branch compartilhada, rode:

```bash
python3 <skill>/scripts/group-preflight.py --repo <pasta> --enable
```

Detalhes e o que fazer quando falha: [`group-mode.md`](group-mode.md) → "Pré-requisitos".

## O que NÃO fazer

- Não copiar manualmente a árvore de outro protótipo (arrasta nomes e telas de domínio alheio).
- Não criar `docs/user-journeys/` sem confirmação.
- Não versionar `dist/`.
- Não deixar `PLACEHOLDER` no design system depois de aplicada a direção visual.

#!/usr/bin/env python3
"""Gera a estrutura completa de um protótipo navegável a partir dos templates da skill.

Só stdlib. Determinístico: mesmos argumentos ⇒ mesma árvore. Recusa diretório de saída não vazio.

Exemplo:
  python3 scaffold.py --name "Meu Produto" --out ~/Projects/meu-produto-prototype \
      --personas "PF:Pessoa Física,PJ:Pessoa Jurídica" --journeys
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / 'templates'
# nome no template → caminho no repositório gerado
RENAMES = {
    'dot-gitignore': '.gitignore',
    'dot-claude': '.claude',
    'design-system.md': 'docs/design-system.md',
}
TEXT_SUFFIXES = {'.html', '.css', '.js', '.json', '.md', '.py', ''}


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'prototipo'


def dest_for(rel: Path) -> Path:
    parts = list(rel.parts)
    joined = '/'.join(parts)
    if joined in RENAMES:
        return Path(RENAMES[joined])
    if parts[0] in RENAMES:
        parts[0] = RENAMES[parts[0]]
    return Path(*parts)


def render(text, values):
    for key, val in values.items():
        text = text.replace(f'@@{key}@@', val)
    return text


def parse_personas(raw):
    out = []
    for item in filter(None, (p.strip() for p in raw.split(','))):
        code, _, label = item.partition(':')
        code, label = code.strip().upper(), (label or code).strip()
        # formato lido por journeys-to-pdf.py --groups (lista ordenada)
        out.append({'code': code, 'label': label, 'tag': code, 'folder': code.lower(), 'legend': label})
    return out


def journeys_readme(name, personas, prod, area):
    rows = '\n'.join(f'| {p["label"]} (`{p["code"]}`) | _(nenhuma ainda)_ |' for p in personas) or '| _(definir personas)_ | — |'
    return f"""# Jornadas de usuário — {name}

Documentação das jornadas do protótipo. **Só criar/alterar com confirmação do time** (ver `user-journey-docs.md` da skill `interactive-prototype`).

## Convenção de nome

`<prod>-<area>-<persona>-j<NN>-<tipo>--<descricao-curta>.md`, tudo em minúsculas (ex.: `{prod.lower()}-{area.lower()}-{personas[0]["code"].lower() if personas else "pf"}-j01-fp--cadastro-basico.md`). O H1 do arquivo traz o código `# [{prod}-{area}-<PERSONA>-J01-FP] Título` (é ele que o gerador de PDF lê). Tipos: `FP` fluxo principal, `FA<nn>` alternativo, `FE<nn>` exceção. Personas ficam em `personas.json` (lista ordenada usada por `journeys-to-pdf.py --groups`).

## Jornadas por persona

| Persona | Jornadas |
|---|---|
{rows}

## Arquivadas

_(nenhuma)_

## De-para (id de tela do protótipo → jornada)

| Tela (`screens`) | Jornada |
|---|---|
| _(preencher ao documentar)_ | — |
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True, help='Nome legível do produto/protótipo')
    ap.add_argument('--out', required=True, help='Diretório de saída (inexistente ou vazio)')
    ap.add_argument('--slug', help='kebab-case (default: derivado do nome)')
    ap.add_argument('--port', type=int, default=8850, help='Porta do servidor de desenvolvimento')
    ap.add_argument('--prefix', help='Prefixo das classes de componente (default: 2–4 letras do slug)')
    ap.add_argument('--prod-code', help='Código do produto no H1 das jornadas (default: 4 letras do slug, maiúsculas)')
    ap.add_argument('--area-code', default='ONB', help='Código da área no H1 das jornadas (default: ONB)')
    ap.add_argument('--personas', default='', help='"PF:Pessoa Física,PJ:Pessoa Jurídica" (usado com --journeys)')
    ap.add_argument('--journeys', action='store_true', help='Cria docs/user-journeys/ (só com confirmação do time)')
    ap.add_argument('--group-mode', action='store_true',
                    help='Prepara o modo grupo (grava groupMode:false até o group-preflight.py passar)')
    ap.add_argument('--no-git', action='store_true', help='Não rodar git init')
    ap.add_argument('--dry-run', action='store_true', help='Só listar o que seria criado')
    args = ap.parse_args()

    out = Path(args.out).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f'Erro: {out} não está vazio — recusando sobrescrever.')
    if not TEMPLATES.is_dir():
        sys.exit(f'Erro: templates não encontrados em {TEMPLATES}')

    slug = args.slug or slugify(args.name)
    prefix = args.prefix or re.sub(r'[^a-z]', '', slug)[:3] or 'pt'
    values = {
        'NAME': args.name, 'SLUG': slug, 'PREFIX': prefix, 'PORT': str(args.port),
        'DATE': date.today().isoformat(),
        'GROUP_MODE': 'false',  # nunca nasce true: só o preflight liga
    }

    planned = []
    for src in sorted(TEMPLATES.rglob('*')):
        if src.is_file():
            planned.append((src, dest_for(src.relative_to(TEMPLATES))))
    extras = {}
    if args.journeys:
        personas = parse_personas(args.personas)
        prod = (args.prod_code or re.sub(r'[^a-z]', '', slug)[:4] or 'PROD').upper()
        extras[Path('docs/user-journeys/README.md')] = journeys_readme(args.name, personas, prod, args.area_code.upper())
        extras[Path('docs/user-journeys/personas.json')] = json.dumps(personas, ensure_ascii=False, indent=2) + '\n'

    for _, dst in planned:
        print(('[dry-run] ' if args.dry_run else '') + str(dst))
    for dst in extras:
        print(('[dry-run] ' if args.dry_run else '') + str(dst))
    if args.dry_run:
        return

    for src, dst in planned:
        target = out / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in TEXT_SUFFIXES:
            target.write_text(render(src.read_text(encoding='utf-8'), values), encoding='utf-8')
        else:
            target.write_bytes(src.read_bytes())
    for dst, content in extras.items():
        target = out / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    for empty in ('assets', 'data'):
        (out / empty).mkdir(exist_ok=True)
        (out / empty / '.gitkeep').write_text('', encoding='utf-8')

    if not args.no_git:
        subprocess.run(['git', 'init', '-b', 'main', str(out)], check=True, capture_output=True)

    print(f'\n✓ Protótipo "{args.name}" gerado em {out}')
    print('  Próximo: python3 build.py && abrir dist/index.html; depois aplicar a direção visual (tokens.css + docs/design-system.md).')
    if args.group_mode:
        print('  Modo grupo: configure o remoto e rode group-preflight.py --enable (groupMode segue false até passar).')


if __name__ == '__main__':
    main()

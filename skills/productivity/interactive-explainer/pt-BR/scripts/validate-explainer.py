#!/usr/bin/env python3
"""Valida o JSON de dados de um explicador interativo contra o contrato (EXPLAINER-DATA-FORMAT.md).

  python3 validate-explainer.py <dados.json> [--require-source] [--source-root <pasta>] [--require-quote] [--strict]

Status do envelope:
  VALID      sem erros (avisos podem existir; ok=true)
  INVALID    há erros que impedem o build (ok=false)
  UNREADABLE arquivo ausente ou JSON quebrado (ok=false)
Com --strict, avisos também reprovam (exit 1).
Fontes (a defesa contra desenho inventado):
  --require-source  todo nó E toda aresta de um quadro precisa de `source`, salvo os marcados `"status": "hipotese"`
                    (que aparecem como "a confirmar" na tela e viram perguntas no envelope).
  --source-root     pasta onde os arquivos citados em `source` têm de existir; `quote` (trecho literal) tem de
                    aparecer num deles. Pega fonte inventada e trecho parafraseado.
  --require-quote   todo nó e toda aresta confirmados precisam de `quote` (exige --source-root).
`data.sources` traz a contagem (confirmados, hipóteses, com fonte, com trecho) para o relatório de evidências.
Exit: 0 ok, 1 problemas, 2 uso incorreto.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer_lib as lib  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('data', help='arquivo JSON de dados')
    ap.add_argument('--require-source', action='store_true')
    ap.add_argument('--source-root')
    ap.add_argument('--require-quote', action='store_true')
    ap.add_argument('--strict', action='store_true')
    args = ap.parse_args(argv)
    if args.require_quote and not args.source_root:
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': '--require-quote', 'msg': 'exige --source-root (sem a pasta não há como conferir o trecho)'}]), 2)
    if args.source_root and not Path(args.source_root).is_dir():
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': '--source-root', 'msg': f'pasta inexistente: {args.source_root}'}]), 2)
    try:
        data = lib.load_data(args.data)
    except (FileNotFoundError, ValueError) as err:
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': args.data, 'msg': str(err)}]))
    problems = lib.validate(data, require_source=args.require_source or args.require_quote, source_root=args.source_root, require_quote=args.require_quote, base_dir=Path(args.data).resolve().parent)
    counts = lib.summarize(problems)
    sources, questions = lib.source_summary(data)
    failed = counts['error'] > 0 or (args.strict and counts['warn'] > 0)
    status = 'INVALID' if failed else 'VALID'
    lib.emit(lib.envelope(not failed, status, data={'counts': counts, 'tabs': len(data.get('tabs', [])), 'sources': sources}, problems=problems, questions=questions))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Gera o HTML autossuficiente do explicador a partir do JSON de dados e do template da skill.

  python3 build-explainer.py <dados.json> --out <saida.html> [--require-source] [--source-root <pasta>] [--require-quote] [--force] [--template <arquivo>]

Valida antes de gerar; com erros de validação não grava nada (use --force só para inspecionar um rascunho).
O HTML gerado não depende de rede, biblioteca nem arquivo externo: abre por duplo clique.
Status: BUILT (ok), INVALID (erros de validação, nada gravado), UNREADABLE (dados ilegíveis).
Exit: 0 ok, 1 problemas, 2 uso incorreto.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer_lib as lib  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('data')
    ap.add_argument('--out', required=True)
    ap.add_argument('--require-source', action='store_true')
    ap.add_argument('--source-root')
    ap.add_argument('--require-quote', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--template')
    args = ap.parse_args(argv)
    try:
        data = lib.load_data(args.data)
    except (FileNotFoundError, ValueError) as err:
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': args.data, 'msg': str(err)}]))
    if args.require_quote and not args.source_root:
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': '--require-quote', 'msg': 'exige --source-root'}]), 2)
    problems = lib.validate(data, require_source=args.require_source or args.require_quote, source_root=args.source_root, require_quote=args.require_quote, base_dir=Path(args.data).resolve().parent)
    counts = lib.summarize(problems)
    if counts['error'] and not args.force:
        lib.emit(lib.envelope(False, 'INVALID', data={'counts': counts, 'written': False}, problems=problems))
    try:
        html = lib.build_html(data, args.template, Path(args.data).resolve().parent)
    except (ValueError, OSError, KeyError) as err:
        lib.emit(lib.envelope(False, 'INVALID', problems=problems + [{'level': 'error', 'where': 'build', 'msg': str(err)}]))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    lib.emit(lib.envelope(True, 'BUILT', data={'out': str(out.resolve()), 'bytes': len(html.encode('utf-8')), 'counts': counts, 'written': True}, problems=problems))


if __name__ == '__main__':
    main()

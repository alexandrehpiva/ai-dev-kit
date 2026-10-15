#!/usr/bin/env python3
"""Gera o pacote de afirmações para o verificador INDEPENDENTE (quem não escreveu o explicador).

  python3 source-packet.py <dados.json> [--format md|json] [--include-hypotheses]

Lista, para cada nó e aresta de quadro, a afirmação que o desenho faz, a `source` e o `quote` declarados e as
instruções de conferência. O verificador abre a fonte por conta própria e devolve CONFIRMADO, NÃO CONFIRMADO ou
REPROVADO por item (ver source-verification.md). O pacote NÃO traz o conteúdo das fontes: o verificador tem de lê-las.
Status do envelope (com --format json): PACKET, UNREADABLE. Com --format md imprime o texto direto.
Exit: 0 ok, 1 dados ilegíveis, 2 uso incorreto.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer_lib as lib  # noqa: E402


def claims(data, include_hypotheses=False):
    out = []
    for kind, where, it, label, blk in lib._iter_claims(data):
        if kind in ('bloco', 'etapa', 'item') and not (it.get('source') or it.get('quote')):
            continue  # sem fonte própria: coberto pelo pai ou não afirma fato
        if it.get('status') == 'hipotese' and not include_hypotheses:
            continue
        if kind == 'nó':
            claim = f'Existe a peça "{it.get("title")}" ({it.get("type")}): {it.get("sub", "")}. {it.get("detail", "")}'.strip()
        elif kind == 'aresta':
            claim = f'"{label}" com o verbo "{it.get("label", "")}" (a primeira peça chama, envia ou aciona a segunda, ou a vigia, se for trava)'
        else:
            claim = f'{kind.capitalize()} "{label}": ' + ' '.join(str(it.get(k, '')) for k in ('summary', 'body', 'intro') if it.get(k)).strip()
        out.append({'kind': kind, 'where': where, 'ref': it.get('id') or label, 'claim': claim,
                    'source': it.get('source'), 'quote': it.get('quote'), 'status': it.get('status', 'confirmado')})
    return out


def render_md(items, title):
    lines = [f'# Pacote de verificação independente — {title}', '',
             'Você NÃO escreveu este explicador. Para cada item: abra a `source` por conta própria, leia, e decida se o texto da fonte',
             'sustenta a afirmação. Responda por item: CONFIRMADO (a fonte diz isso), NÃO CONFIRMADO (a fonte é omissa ou não foi achada)',
             'ou REPROVADO (a fonte diz outra coisa). Cite o trecho que usou. Não use conhecimento próprio nem o resto do explicador.', '']
    for i, it in enumerate(items, 1):
        lines += [f'## {i}. {it["kind"]} `{it["ref"]}` — {it["where"]}', f'- **Afirmação:** {it["claim"]}',
                  f'- **Fonte declarada:** {it["source"] or "(nenhuma)"}', f'- **Trecho declarado:** {it["quote"] or "(nenhum)"}',
                  '- **Veredito:** ', '- **Trecho que você usou:** ', '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('data')
    ap.add_argument('--format', choices=['md', 'json'], default='md')
    ap.add_argument('--include-hypotheses', action='store_true')
    args = ap.parse_args(argv)
    try:
        data = lib.load_data(args.data)
    except (FileNotFoundError, ValueError) as err:
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': args.data, 'msg': str(err)}]))
    items = claims(data, args.include_hypotheses)
    if args.format == 'json':
        lib.emit(lib.envelope(True, 'PACKET', data={'count': len(items), 'claims': items}))
    print(render_md(items, str((data.get('meta') or {}).get('title', ''))))


if __name__ == '__main__':
    main()

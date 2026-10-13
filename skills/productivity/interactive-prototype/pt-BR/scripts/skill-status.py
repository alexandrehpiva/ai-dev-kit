#!/usr/bin/env python3
"""Compara a versão da skill instalada com a versão registrada no protótipo. Só stdlib. Somente leitura.

  python3 skill-status.py --repo <pasta>

Status:
  UP_TO_DATE         protótipo na mesma versão da skill
  PROTOTYPE_LEGACY   config sem bloco `skill` (v1, versão implícita 1.0.0) e a skill é mais nova
  PROTOTYPE_OUTDATED skill.version do protótipo menor que a da skill: há migração a aplicar
  SKILL_OUTDATED     protótipo mais novo que a skill instalada: data.mode='consult' (nada deve ser alterado)
  NO_CONFIG          há index.html mas não há prototype.config.json: tratado como legado solo, migrável
  NOT_A_PROTOTYPE    sem index.html
data: skillVersion, prototypeVersion, migrationsPending (saltos em ordem), requiresPromoter (groupMode=true).
Exit: 0 para os status acima, 1 para erro (config ilegível/skill sem version), 2 uso incorreto.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import protolib  # noqa: E402
import configtools  # noqa: E402
import migrate  # noqa: E402


def main(argv=None):
    ap = configtools.JsonArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    args = ap.parse_args(argv)

    repo = configtools.resolve_repo(args.repo)
    if repo is None:
        return configtools.usage_error(f'pasta não encontrada: {args.repo}')

    skill_v = protolib.skill_version()
    if skill_v is None:
        return protolib.emit(False, 'SKILL_VERSION_MISSING', problems=[protolib.problem(
            'SKILL_VERSION_MISSING', 'não foi possível ler `version:` no frontmatter do SKILL.md da skill')])
    if not (repo / 'index.html').is_file():
        return protolib.emit(True, 'NOT_A_PROTOTYPE', {'skillVersion': skill_v, 'prototypeVersion': None,
                             'migrationsPending': [], 'requiresPromoter': False})

    cfg, err = protolib.load_config(repo)
    if err:
        return protolib.emit(False, 'INVALID_CONFIG', problems=[protolib.problem('JSON', err)])
    if cfg is not None and not isinstance(cfg, dict):
        return protolib.emit(False, 'INVALID_CONFIG', problems=[protolib.problem('JSON', 'o config precisa ser um objeto JSON')])

    explicit = isinstance(cfg, dict) and isinstance(cfg.get('skill'), dict) and bool(cfg['skill'].get('version'))
    proto_v = migrate.effective_version(cfg)
    proto_t, skill_t = configtools.parse_semver(proto_v), configtools.parse_semver(skill_v)
    if proto_t is None:
        return protolib.emit(False, 'INVALID_CONFIG', problems=[protolib.problem(
            'SCHEMA', f'skill.version: versão inválida ("{proto_v}"), esperado X.Y.Z')])

    data = {'skillVersion': skill_v, 'prototypeVersion': proto_v, 'migrationsPending': [],
            'requiresPromoter': bool(isinstance(cfg, dict) and cfg.get('groupMode') is True)}
    if cfg is None:
        data['legacy'] = True
        data['migrationsPending'] = migrate.pending_steps(proto_v, skill_v)
        return protolib.emit(True, 'NO_CONFIG', data)
    if proto_t > skill_t:
        data['mode'] = 'consult'
        return protolib.emit(True, 'SKILL_OUTDATED', data)
    if proto_t == skill_t:
        return protolib.emit(True, 'UP_TO_DATE', data)
    data['migrationsPending'] = migrate.pending_steps(proto_v, skill_v)
    return protolib.emit(True, 'PROTOTYPE_OUTDATED' if explicit else 'PROTOTYPE_LEGACY', data)


if __name__ == '__main__':
    sys.exit(main())

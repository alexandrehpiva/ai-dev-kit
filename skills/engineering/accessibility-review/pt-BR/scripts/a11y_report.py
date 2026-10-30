#!/usr/bin/env python3
"""Monta o relatório de acessibilidade a partir da varredura automatizada e das evidências manuais.

Uso:
  python3 a11y_report.py --scan scan.json [--scan outro.json] [--evidence evidencias.json]
                         [--title "Protótipo X"] [--out relatorio.md] [--format md|json]
                         [--criteria caminho/CRITERIA.md]

Regra central (METHOD.md): nenhum critério sai como "Passou" sem evidência escrita. Sem varredura nem
evidência, o estado é "Não verificado". Falha automática vira "Falhou". Evidência que diz "passou"
contra falha automática vira "Conflito" e precisa ser resolvida por quem avalia.

evidencias.json: {"1.4.1": {"status": "passou|falhou|nao-aplica", "evidencia": "texto",
                            "telas": ["Home"], "severidade": "alta|media|baixa", "recomendacao": "texto"}}

Saída: Markdown (padrão) em --out ou stdout; com --format json, o envelope
{"ok","status","data","problems","questions"}. Biblioteca padrão apenas.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
LEVELS = {"A", "AA"}
VERIFICATIONS = {"parcial", "manual"}
EVIDENCE_STATUS = {"passou": "Passou", "falhou": "Falhou", "nao-aplica": "Não se aplica"}
SEVERITY = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
IMPACT_TO_SEVERITY = {"critical": "Alta", "serious": "Alta", "moderate": "Média", "minor": "Baixa"}
MIN_EVIDENCE_CHARS = 10
CODE_RE = re.compile(r"^\d\.\d\.\d{1,2}$")

NOT_COVERED = [
    "Leitor de tela real (VoiceOver, NVDA, TalkBack): a varredura não simula a fala nem a navegação por rotor.",
    "Qualidade de textos alternativos, rótulos e mensagens de erro: o axe detecta presença, não adequação.",
    "Uso real por pessoas com deficiência: a avaliação técnica não substitui teste com usuários.",
]


def code_key(code):
    return tuple(int(p) for p in code.split("."))


def parse_criteria(path):
    """Lê a tabela entre <criterios> e </criterios>. Devolve (linhas, problemas)."""
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r"<criterios>(.*?)</criterios>", text, re.S)
    if not m:
        return [], ["CRITERIA.md sem o bloco <criterios>…</criterios>"]
    rows, problems, seen = [], [], set()
    for line in m.group(1).splitlines():
        if not re.match(r"\|\s*\d", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            problems.append(f"linha com {len(cells)} colunas (esperado 7): {line[:60]}")
            continue
        code, level, name, verif, rules, roteiro, applies = cells
        if not CODE_RE.match(code) or code in seen:
            problems.append(f"código inválido ou repetido: {code}")
            continue
        if level not in LEVELS or verif not in VERIFICATIONS:
            problems.append(f"{code}: nível ou verificação inválidos ({level}/{verif})")
            continue
        seen.add(code)
        axe_rules = [] if rules == "—" else [r.strip().rstrip("*") for r in rules.split(",") if r.strip()]
        rows.append({"code": code, "level": level, "name": name, "verification": verif,
                     "axe_rules": axe_rules, "roteiro": roteiro, "applies": applies})
    rows.sort(key=lambda r: code_key(r["code"]))
    return rows, problems


def load_scans(paths):
    runs, problems, meta = [], [], {"axe": set(), "tags": set(), "viewports": set()}
    for p in paths:
        try:
            doc = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"varredura ilegível ({p}): {exc}")
            continue
        data = doc.get("data") or {}
        if not doc.get("ok") or not data.get("runs"):
            problems.append(f"varredura sem resultados utilizáveis: {p} (status {doc.get('status')})")
            continue
        meta["axe"].add((data.get("tool") or {}).get("axe", "?"))
        meta["tags"].update(data.get("tags") or [])
        for run in data["runs"]:
            meta["viewports"].add(run["viewport"]["name"])
            runs.append(run)
    return runs, problems, meta


def collect_findings(runs):
    """Agrupa por critério as violações e os incompletos; devolve também as regras que passaram."""
    by, passed = {}, set()

    def slot(code):
        return by.setdefault(code, {"violations": {}, "incomplete": {}})

    for run in runs:
        where = f"{run['scan']} @ {run['viewport']['name']}"
        for kind in ("violations", "incomplete"):
            for rule in run["axe"][kind]:
                for code in rule["wcag"] or ["sem-criterio"]:
                    ent = slot(code)[kind].setdefault(rule["id"], {
                        "rule": rule["id"], "impact": rule.get("impact"), "help": rule.get("help"),
                        "helpUrl": rule.get("helpUrl"), "where": [], "nodes": []})
                    ent["where"].append(where)
                    for node in rule["nodes"]:
                        if len(ent["nodes"]) < 5:
                            ent["nodes"].append({"where": where, "target": " ".join(node["target"]), "html": node["html"]})
        passed.update(run["axe"].get("passedRules", []))
    return by, passed


def classify(row, findings, passed, evidence, problems):
    code = row["code"]
    auto = findings.get(code, {"violations": {}, "incomplete": {}})
    ev = evidence.get(code)
    result = {"code": code, "level": row["level"], "name": row["name"], "verification": row["verification"],
              "roteiro": row["roteiro"], "applies": row["applies"], "state": "Não verificado",
              "origin": "—", "note": "", "severity": None, "recommendation": "", "screens": []}
    ran_ok = sorted((set(row["axe_rules"]) & passed) - set(auto["violations"]))
    if ev is not None:
        status = ev.get("status")
        text = str(ev.get("evidencia", "")).strip()
        if status not in EVIDENCE_STATUS:
            problems.append(f"{code}: status de evidência inválido ({status!r}); use {', '.join(EVIDENCE_STATUS)}")
        elif len(text) < MIN_EVIDENCE_CHARS:
            problems.append(f"{code}: evidência vazia ou curta demais — o critério fica como Não verificado")
        else:
            result.update(state=EVIDENCE_STATUS[status], origin="manual", note=text,
                          screens=list(ev.get("telas") or []), recommendation=str(ev.get("recomendacao", "")).strip())
            sev = ev.get("severidade")
            result["severity"] = SEVERITY.get(sev) if sev else None
            if status == "falhou" and not result["severity"]:
                problems.append(f"{code}: falha manual sem severidade (alta|media|baixa)")
            if status == "passou" and auto["violations"]:
                result.update(state="Conflito", origin="manual × automático",
                              note=f"Evidência diz que passou, mas o axe acusa {', '.join(sorted(auto['violations']))}. {text}")
            return finish(result, auto)
    if auto["violations"]:
        worst = sorted(IMPACT_TO_SEVERITY.get(v["impact"], "Média") for v in auto["violations"].values())
        result.update(state="Falhou", origin="automático", severity=("Alta" if "Alta" in worst else worst[0]),
                      note="Regras: " + ", ".join(sorted(auto["violations"])))
    elif auto["incomplete"]:
        result.update(state="Revisar", origin="automático",
                      note="axe não concluiu: " + ", ".join(sorted(auto["incomplete"])) + " — verificar à mão")
    elif ran_ok:
        result["note"] = "Sem achado automático em " + ", ".join(ran_ok) + "; verificação manual pendente."
    return finish(result, auto)


def finish(result, auto):
    result["findings"] = {"violations": sorted(auto["violations"].values(), key=lambda v: v["rule"]),
                          "incomplete": sorted(auto["incomplete"].values(), key=lambda v: v["rule"])}
    return result


def keyboard_notes(runs):
    notes = []
    for run in runs:
        kb = run.get("keyboard")
        if not kb:
            continue
        for flag in kb["flags"]:
            notes.append({"where": f"{run['scan']} @ {run['viewport']['name']}", "kind": flag["kind"],
                          "target": flag.get("target", "")})
    return notes


def layout_notes(runs):
    return [f"{r['scan']} @ {r['viewport']['name']}: rolagem horizontal da página ({r['layout']['scrollWidth']} > {r['layout']['clientWidth']} px)"
            for r in runs if r.get("layout", {}).get("horizontalOverflow") and r["viewport"]["width"] <= 320]


def summarize(results):
    counts = {}
    for r in results:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    return counts


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_md(title, date, meta, results, runs, problems):
    counts = summarize(results)
    order = ["Falhou", "Conflito", "Revisar", "Passou", "Não se aplica", "Não verificado"]
    out = [f"# Avaliação de acessibilidade — {title}", "",
           f"**Data:** {date} · **Padrão:** WCAG 2.2 níveis A e AA ({len(results)} critérios)", ""]
    out += ["## 1. Escopo e método", ""]
    if runs:
        scans = sorted({f"{r['scan']} ({r['url']})" for r in runs})
        out += [f"- Varredura automatizada: axe-core {', '.join(sorted(meta['axe']))}; tags {', '.join(sorted(meta['tags']))}.",
                f"- Viewports: {', '.join(sorted(meta['viewports']))}.", "- Telas e estados varridos:"] + [f"  - {s}" for s in scans]
    else:
        out += ["- Nenhuma varredura automatizada anexada: todos os critérios dependem de evidência manual."]
    out += ["- Verificação manual: somente os critérios com evidência na coluna Evidência/nota (`origem: manual`).", "",
            "**O que este relatório não cobre:**", ""] + [f"- {n}" for n in NOT_COVERED] + [""]
    out += ["## 2. Resumo", "", "| Estado | Critérios |", "|---|---|"]
    out += [f"| {s} | {counts[s]} |" for s in order if s in counts]
    out += ["", "Nenhum critério sem evidência é dado como conforme: \"Não verificado\" não é \"Passou\".", ""]

    out += ["## 3. Matriz por critério", "", "| Código | Nível | Critério | Estado | Origem | Gravidade | Evidência / nota | Telas |", "|---|---|---|---|---|---|---|---|"]
    for r in results:
        out.append(f"| {r['code']} | {r['level']} | {cell(r['name'])} | {r['state']} | {r['origin']} | {r['severity'] or '—'} | {cell(r['note']) or '—'} | {cell(', '.join(r['screens'])) or '—'} |")
    out.append("")

    fails = [r for r in results if r["state"] in ("Falhou", "Conflito")]
    out += ["## 4. Achados", ""]
    if not fails:
        out += ["Nenhuma falha registrada. Isso não equivale a conformidade: ver a seção 2 e a lista de não verificados.", ""]
    for i, r in enumerate(fails, 1):
        out += [f"### {i}. {r['code']} {r['name']} — {r['state']}" + (f" ({r['severity']})" if r["severity"] else ""), "", r["note"] or "", ""]
        for v in r["findings"]["violations"]:
            out += [f"- **{v['rule']}** ({v['impact'] or 's/ impacto'}): {v['help']} — {v['helpUrl']}"]
            out += [f"  - {n['where']}: `{cell(n['target'])}`" for n in v["nodes"][:3]]
        if r["recommendation"]:
            out += ["", f"**Recomendação:** {r['recommendation']}"]
        out += [""]

    kb = keyboard_notes(runs)
    lay = layout_notes(runs)
    if kb or lay:
        out += ["## 5. Indícios de heurística (confirmar à mão)", ""]
        out += [f"- Teclado — {n['where']}: {n['kind']} {('`' + n['target'] + '`') if n['target'] else ''}" for n in kb]
        out += [f"- Realinhar (1.4.10) — {n}" for n in lay] + [""]

    pending = [r for r in results if r["state"] in ("Não verificado", "Revisar")]
    out += ["## 6. Não verificado ou a revisar", "", f"{len(pending)} critérios. Roteiro em `manual-checks.md`.", ""]
    out += [f"- {r['code']} {r['name']} ({r['verification']}, {r['roteiro']}) — aplica quando: {r['applies']}" for r in pending] + [""]
    if problems:
        out += ["## Avisos do gerador", ""] + [f"- {p}" for p in problems] + [""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scan", action="append", default=[])
    ap.add_argument("--evidence")
    ap.add_argument("--title", default="protótipo")
    ap.add_argument("--out")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--criteria", default=str(SKILL_DIR / "CRITERIA.md"))
    ap.add_argument("--date", default=_dt.date.today().isoformat())
    args = ap.parse_args(argv)

    rows, problems = parse_criteria(args.criteria)
    if not rows:
        print(json.dumps({"ok": False, "status": "error", "data": {}, "problems": problems, "questions": []}, ensure_ascii=False))
        return 2
    runs, scan_problems, meta = load_scans(args.scan)
    problems += scan_problems
    evidence = {}
    if args.evidence:
        try:
            evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
            if not isinstance(evidence, dict):
                raise ValueError("a raiz deve ser um objeto {codigo: {...}}")
        except (OSError, ValueError) as exc:
            problems.append(f"evidências ilegíveis: {exc}")
            evidence = {}
    known = {r["code"] for r in rows}
    problems += [f"evidência para critério desconhecido: {c}" for c in evidence if c not in known]

    findings, passed = collect_findings(runs)
    results = [classify(r, findings, passed, evidence, problems) for r in rows]
    if args.format == "json":
        data = {"title": args.title, "summary": summarize(results), "criteria": results, "keyboard": keyboard_notes(runs), "layout": layout_notes(runs)}
        text = json.dumps({"ok": True, "status": "ok" if not problems else "with-warnings", "data": data, "problems": problems, "questions": []}, ensure_ascii=False, indent=2)
    else:
        text = render_md(args.title, args.date, meta, results, runs, problems)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "status": "ok" if not problems else "with-warnings", "data": {"out": args.out, "summary": summarize(results)}, "problems": problems, "questions": []}, ensure_ascii=False))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

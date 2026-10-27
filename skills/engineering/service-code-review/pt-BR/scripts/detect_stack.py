#!/usr/bin/env python3
"""Detecta a stack de um repositório e indica os guias de `stacks/` a usar no review.

Uso:
  python3 detect_stack.py <repositório>        # JSON com linguagens, pacotes, guias e problemas
  python3 detect_stack.py --list               # lista os guias disponíveis (id, kind, detect)

Só lê arquivos; não executa nada do repositório. Biblioteca padrão apenas.
Saída: {"ok", "status", "data", "problems", "questions"}.
  status: "ok" | "missing-guides" (dependência central sem guia) | "stale-guides" (guia velho
  ou versão fora da faixa coberta) | "error".
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
STACKS_DIR = SKILL_DIR / "stacks"
STALE_DAYS = 183
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "vendor", "dist", "build", "target",
             "bin", "obj", ".next", ".nuxt", ".angular", "coverage", "__pycache__", ".tox"}

# Dependências que definem a arquitetura de um serviço. Se aparecerem sem guia, o review avisa.
CORE_PACKAGES = {
    "npm": {"@nestjs/core", "express", "fastify", "hono", "koa", "react", "next", "@angular/core",
            "vue", "nuxt", "svelte", "@sveltejs/kit", "solid-js", "@remix-run/node", "astro",
            "prisma", "@prisma/client", "typeorm", "drizzle-orm", "sequelize", "mongoose",
            "mongodb", "@aws-sdk/client-dynamodb", "ioredis", "redis", "pg", "mysql2"},
    "pypi": {"fastapi", "django", "flask", "starlette", "litestar", "sanic", "aiohttp", "tornado",
             "sqlalchemy", "sqlmodel", "pymongo", "motor", "redis", "boto3", "celery", "peewee",
             "tortoise-orm"},
    "go": {"github.com/gin-gonic/gin", "github.com/labstack/echo", "github.com/go-chi/chi",
           "github.com/gofiber/fiber", "gorm.io/gorm", "github.com/jackc/pgx",
           "go.mongodb.org/mongo-driver", "github.com/redis/go-redis", "entgo.io/ent"},
    "maven": {"org.springframework.boot", "io.quarkus", "io.micronaut", "org.hibernate",
              "org.hibernate.orm", "org.jooq"},
    "nuget": {"Microsoft.AspNetCore", "Microsoft.EntityFrameworkCore", "Dapper"},
}


def _norm_pypi(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower().strip()


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    meta: dict[str, str] = {}
    for line in text[3:end].splitlines():
        line = line.split(" #", 1)[0].rstrip()
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def load_guides(stacks_dir: Path = STACKS_DIR) -> list[dict]:
    guides = []
    for path in sorted(stacks_dir.rglob("*.md")):
        meta = parse_frontmatter(path)
        if not meta.get("id"):
            continue
        meta["path"] = str(path.relative_to(stacks_dir.parent))
        meta["detect_keys"] = [k.strip() for k in meta.get("detect", "").split(",") if k.strip()]
        guides.append(meta)
    return guides


def list_files(repo: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "-C", str(repo), "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, check=True, timeout=60).stdout
        files = [repo / f for f in out.splitlines() if f]
        files = [f for f in files if not (set(f.relative_to(repo).parts) & SKIP_DIRS)]
        if files:
            return files
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    files = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        files.extend(Path(root) / n for n in names)
    return files


def _add(pkgs: dict, eco: str, name: str, version: str, source: Path, repo: Path) -> None:
    key = _norm_pypi(name) if eco == "pypi" else name.strip()
    if not key:
        return
    pkgs.setdefault(eco, {}).setdefault(key, []).append(
        {"version": (version or "").strip(), "file": str(source.relative_to(repo))})


def parse_manifests(repo: Path, files: list[Path]) -> tuple[dict, dict, set[str], list[str]]:
    pkgs: dict[str, dict] = {}
    runtimes: dict[str, str] = {}
    langs: set[str] = set()
    problems: list[str] = []
    names = {f.name for f in files}
    for f in files:
        try:
            if f.name == "package.json":
                data = json.loads(f.read_text(encoding="utf-8"))
                langs.add("javascript")
                for sect in ("dependencies", "devDependencies", "peerDependencies"):
                    for n, v in (data.get(sect) or {}).items():
                        _add(pkgs, "npm", n, str(v), f, repo)
                engines = (data.get("engines") or {}).get("node")
                if engines:
                    runtimes.setdefault("node", engines)
            elif f.name == "tsconfig.json":
                langs.add("typescript")
            elif f.name == "pyproject.toml":
                langs.add("python")
                data = tomllib.loads(f.read_text(encoding="utf-8"))
                proj = data.get("project") or {}
                deps = list(proj.get("dependencies") or [])
                for group in (proj.get("optional-dependencies") or {}).values():
                    deps.extend(group)
                for group in (data.get("dependency-groups") or {}).values():
                    deps.extend(d for d in group if isinstance(d, str))
                for d in deps:
                    m = re.match(r"\s*([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(.*)", d)
                    if m:
                        _add(pkgs, "pypi", m.group(1), m.group(2), f, repo)
                poetry = ((data.get("tool") or {}).get("poetry") or {})
                for sect in ("dependencies", "dev-dependencies"):
                    for n, v in (poetry.get(sect) or {}).items():
                        if n.lower() == "python":
                            runtimes.setdefault("python", str(v))
                        else:
                            _add(pkgs, "pypi", n, v if isinstance(v, str) else json.dumps(v), f, repo)
                for grp in (poetry.get("group") or {}).values():
                    for n, v in (grp.get("dependencies") or {}).items():
                        _add(pkgs, "pypi", n, v if isinstance(v, str) else json.dumps(v), f, repo)
                if proj.get("requires-python"):
                    runtimes.setdefault("python", proj["requires-python"])
            elif re.fullmatch(r"requirements.*\.txt", f.name) or f.name in {"Pipfile", "setup.cfg"}:
                langs.add("python")
                for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.split("#", 1)[0].strip()
                    m = re.match(r"([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*([<>=!~].*)?$", line)
                    if m and not line.startswith("-"):
                        _add(pkgs, "pypi", m.group(1), m.group(2) or "", f, repo)
            elif f.name == "go.mod":
                langs.add("go")
                for line in f.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("go "):
                        runtimes.setdefault("go", line[3:].strip())
                    m = re.match(r"(?:require\s+)?([a-z0-9.\-]+\.[a-z]+/[^\s]+)\s+(v[^\s]+)", line)
                    if m:
                        _add(pkgs, "go", m.group(1), m.group(2), f, repo)
            elif f.name == "pom.xml":
                langs.add("java")
                root = ET.fromstring(f.read_text(encoding="utf-8"))
                for el in root.iter():
                    if el.tag.endswith("}dependency") or el.tag.endswith("}parent") or el.tag in ("dependency", "parent"):
                        vals = {c.tag.split("}")[-1]: (c.text or "") for c in el}
                        if vals.get("groupId"):
                            _add(pkgs, "maven", f'{vals["groupId"]}:{vals.get("artifactId", "")}',
                                 vals.get("version", ""), f, repo)
            elif f.name in {"build.gradle", "build.gradle.kts"}:
                langs.add("java")
                for m in re.finditer(r"""["']([\w.\-]+):([\w.\-]+)(?::([\w.\-]+))?["']""", f.read_text(encoding="utf-8")):
                    _add(pkgs, "maven", f"{m.group(1)}:{m.group(2)}", m.group(3) or "", f, repo)
                for m in re.finditer(r"""id\s*\(?\s*["'](org\.springframework\.boot)["']\s*\)?\s*version\s*["']([^"']+)""",
                                     f.read_text(encoding="utf-8")):
                    _add(pkgs, "maven", f"{m.group(1)}:plugin", m.group(2), f, repo)
            elif f.suffix == ".csproj" or f.name == "Directory.Packages.props":
                langs.add("csharp")
                text = f.read_text(encoding="utf-8")
                sdk = re.search(r'<Project\s+Sdk="([^"]+)"', text)
                if sdk and sdk.group(1) == "Microsoft.NET.Sdk.Web":
                    _add(pkgs, "nuget", "Microsoft.AspNetCore", "(Sdk.Web)", f, repo)
                tf = re.search(r"<TargetFrameworks?>([^<]+)<", text)
                if tf:
                    runtimes.setdefault("dotnet", tf.group(1))
                for m in re.finditer(r'<Package(?:Reference|Version)\s+Include="([^"]+)"(?:\s+Version="([^"]*)")?', text):
                    _add(pkgs, "nuget", m.group(1), m.group(2) or "", f, repo)
        except (OSError, ValueError, ET.ParseError, tomllib.TOMLDecodeError) as exc:
            problems.append(f"Não consegui ler {f.relative_to(repo)}: {exc}")
    if "typescript" in langs or "typescript" in pkgs.get("npm", {}):
        langs.add("typescript")
    for nvm in (".nvmrc", ".node-version", ".python-version", ".tool-versions"):
        if nvm in names:
            p = next(f for f in files if f.name == nvm)
            runtimes.setdefault(nvm, p.read_text(encoding="utf-8", errors="replace").strip()[:80])
    return pkgs, runtimes, langs, problems


def _match_key(key: str, pkgs: dict, langs: set[str], names: set[str]) -> list[dict] | None:
    if key == "always":
        return [{"version": "", "file": ""}]
    eco, _, target = key.partition(":")
    if eco == "lang":
        return [{"version": "", "file": ""}] if target in langs else None
    if eco == "file":
        return [{"version": "", "file": target}] if target in names else None
    found = pkgs.get(eco, {})
    hits: list[dict] = []
    for name, entries in found.items():
        if eco == "npm" and name == target:
            ok = True
        elif eco == "pypi" and name == _norm_pypi(target):
            ok = True
        elif eco == "go":
            ok = name == target or name.startswith(target + "/")
        elif eco == "maven":
            ok = name == target or name.startswith(target + ":") or name.split(":")[0].startswith(target + ".")
        elif eco == "nuget":
            ok = name == target or name.startswith(target + ".")
        else:
            ok = False
        if ok:
            hits.extend({**e, "package": name} for e in entries)
    return hits or None


def _covers(covered: str, versions: list[str]) -> bool | None:
    """Compara major.minor das versões achadas com a faixa "A – B" de versions_covered.

    True: alguma versão dentro; False: todas fora; None: não dá para comparar.
    Limite só com major ("20") vale para qualquer minor daquele major.
    """
    # Só o primeiro trecho (antes de ";") descreve o pacote principal; parênteses são notas.
    first = re.sub(r"\([^)]*\)", "", covered.split(";", 1)[0])
    tokens = re.findall(r"\d+(?:\.\d+)?", first)
    if not tokens:
        return None

    def bound(tok: str, upper: bool) -> tuple[int, int]:
        major, _, minor = tok.partition(".")
        return (int(major), int(minor) if minor else (10**6 if upper else 0))

    lo, hi = bound(tokens[0], False), bound(tokens[-1], True)
    result = None
    for v in versions:
        m = re.search(r"(\d+)(?:\.(\d+))?", v)
        if not m:
            continue
        ver = (int(m.group(1)), int(m.group(2) or 0))
        if lo <= ver <= hi:
            return True
        result = False
    return result


def detect(repo: Path, stacks_dir: Path = STACKS_DIR, today: _dt.date | None = None) -> dict:
    today = today or _dt.date.today()
    if not repo.is_dir():
        return {"ok": False, "status": "error", "data": {}, "problems": [f"{repo} não é diretório"], "questions": []}
    files = list_files(repo)
    names = {f.name for f in files}
    pkgs, runtimes, langs, problems = parse_manifests(repo, files)
    guides_out, covered_pkgs = [], set()
    status = "ok"
    for g in load_guides(stacks_dir):
        matched = {}
        for key in g["detect_keys"]:
            hits = _match_key(key, pkgs, langs, names)
            if hits:
                matched[key] = hits
                covered_pkgs.update((key.partition(":")[0], h.get("package", "")) for h in hits)
        if not matched:
            continue
        versions = sorted({h["version"] for hs in matched.values() for h in hs if h.get("version")})
        stale, reasons = False, []
        try:
            age = (today - _dt.date.fromisoformat(g.get("last_verified", ""))).days
            if age > STALE_DAYS:
                stale, reasons = True, [f"last_verified há {age} dias"]
        except ValueError:
            stale, reasons = True, ["sem last_verified válido"]
        # Guias de banco (language: any) descrevem a versão do servidor, não do pacote cliente:
        # só frameworks e ORMs de uma linguagem comparam a versão do pacote com versions_covered.
        compares_version = g.get("kind") == "framework" or (g.get("kind") == "data" and g.get("language") != "any")
        # versions_covered se refere ao pacote principal: a primeira chave de `detect`.
        primary = g["detect_keys"][0] if g["detect_keys"] else ""
        primary_versions = sorted({h["version"] for h in matched.get(primary, []) if h.get("version")})
        if compares_version and primary_versions:
            cov = _covers(g.get("versions_covered", ""), primary_versions)
            if cov is False:
                stale = True
                reasons.append(f"versão do repositório {primary_versions} fora de versions_covered ({g.get('versions_covered')})")
        if stale:
            status = "stale-guides"
        guides_out.append({"id": g["id"], "path": g["path"], "kind": g.get("kind", ""),
                           "matched_by": sorted(matched), "versions_found": versions,
                           "versions_covered": g.get("versions_covered", ""),
                           "last_verified": g.get("last_verified", ""), "stale": stale,
                           "stale_reasons": reasons})
    missing = []
    for eco, core in CORE_PACKAGES.items():
        for name in pkgs.get(eco, {}):
            base = name.split(":")[0] if eco == "maven" else name
            is_core = any(base == c or base.startswith(c + "/") or base.startswith(c + ".") for c in core) \
                if eco in {"go", "maven", "nuget"} else (_norm_pypi(name) in {_norm_pypi(c) for c in core} if eco == "pypi" else name in core)
            if is_core and (eco, name) not in covered_pkgs:
                missing.append(f"{eco}:{name}")
    if missing:
        status = "missing-guides" if status == "ok" else status
        problems.append("Dependências centrais sem guia de stack: " + ", ".join(sorted(missing)))
    kinds = {g["kind"] for g in guides_out}
    questions = []
    if not ({"framework", "language"} & kinds):
        questions.append("Nenhum guia de linguagem/framework casou: confirme a stack e crie o guia (maintaining-guides.md) ou revise só pelo checklist núcleo.")
    return {"ok": status == "ok", "status": status,
            "data": {"repo": str(repo), "languages": sorted(langs), "runtimes": runtimes,
                     "guides": sorted(guides_out, key=lambda x: (x["kind"], x["id"])),
                     "missing_core": sorted(missing)},
            "problems": problems, "questions": questions}


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--list":
        out = [{k: g.get(k, "") for k in ("id", "kind", "language", "detect", "versions_covered", "last_verified", "path")}
               for g in load_guides()]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    result = detect(Path(argv[1]).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "error" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""session-limit-guard: detecta compactação, lê o limite de uso e agenda a retomada.

Somente stdlib. Subcomandos: status | statusline | check | arm-resume | run-resume | hook.
Saída de dados em JSON no stdout. Nada é agendado sem --apply (exceto `hook`, que agenda
quando o evento é um limite rejeitado e a variável LIMIT_GUARD_DRYRUN não está definida).
"""
import argparse, glob, json, os, pathlib, plistlib, subprocess, sys, time

HOME = pathlib.Path.home()
STATE = pathlib.Path(os.environ.get("LIMIT_GUARD_STATE", HOME / ".claude" / "limit-guard"))
PROJECTS = pathlib.Path(os.environ.get("LIMIT_GUARD_PROJECTS", HOME / ".claude" / "projects"))
AGENTS_DIR = pathlib.Path(os.environ.get("LIMIT_GUARD_LAUNCHAGENTS", HOME / "Library" / "LaunchAgents"))
WARN_PCT = float(os.environ.get("LIMIT_GUARD_WARN_PCT", "85"))
STOP_PCT = float(os.environ.get("LIMIT_GUARD_STOP_PCT", "95"))
MARGIN_S = int(os.environ.get("LIMIT_GUARD_MARGIN_S", "120"))
MAX_TRIES = int(os.environ.get("LIMIT_GUARD_MAX_TRIES", "6"))
SUMMARY_MARK = "continued from a previous conversation"
DEFAULT_PROMPT = (
    "A sessão parou por limite de uso e foi reiniciada automaticamente. Retome do ponto onde parou: "
    "releia o ledger e o checklist em disco (não confie só no sumário), rode a hallucination-guard "
    "(passe completo), liste os subagentes com ListAgents e reenvie com SendMessage os que falharam "
    "por limite, e siga as fases pendentes. Não faça commit nem envie nada a terceiros sem pedido."
)


def find_transcript(session=None, path=None):
    if path:
        return pathlib.Path(path)
    if session:
        hits = sorted(glob.glob(str(PROJECTS / "*" / f"{session}.jsonl")))
        return pathlib.Path(hits[0]) if hits else None
    files = sorted(glob.glob(str(PROJECTS / "*" / "*.jsonl")), key=os.path.getmtime)
    return pathlib.Path(files[-1]) if files else None


def scan(transcript):
    """Lê o transcript uma vez e devolve contexto, compactações e último limite rejeitado."""
    out = {"transcript": str(transcript), "session_id": None, "cwd": None, "context_tokens": None,
           "compactions": 0, "summary_messages": 0, "last_compaction": None, "rejection": None}
    if not transcript or not pathlib.Path(transcript).exists():
        return out
    with open(transcript, errors="ignore") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            out["session_id"] = d.get("sessionId") or out["session_id"]
            out["cwd"] = d.get("cwd") or out["cwd"]
            if d.get("subtype") == "compact_boundary":
                out["compactions"] += 1
                m = d.get("compactMetadata") or {}
                out["last_compaction"] = {"at": d.get("timestamp"), "trigger": m.get("trigger"),
                                          "pre_tokens": m.get("preTokens"), "post_tokens": m.get("postTokens")}
            if d.get("type") == "user" and d.get("isCompactSummary"):
                out["summary_messages"] += 1
            msg = d.get("message") or {}
            usage = msg.get("usage") if isinstance(msg, dict) else None
            if d.get("type") == "assistant" and usage and msg.get("model") != "<synthetic>":
                out["context_tokens"] = (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                                         + usage.get("cache_read_input_tokens", 0))
            q = d.get("quotaLimits")
            info = (d.get("apiErrorParams") or {}).get("rate_limit_info")
            src = q if isinstance(q, dict) and q.get("status") == "rejected" else (
                info if isinstance(info, dict) and info.get("status") == "rejected" else None)
            if src and src.get("resetsAt"):
                out["rejection"] = {"resets_at": int(src["resetsAt"]), "type": src.get("rateLimitType"),
                                    "seen_at": d.get("timestamp")}
    if out["rejection"]:
        out["rejection"]["resets_in_s"] = out["rejection"]["resets_at"] - int(time.time())
    return out


def read_cache(session):
    p = STATE / f"{session}.json" if session else None
    if not p or not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except ValueError:
        return None


def level(cache):
    """ok | warn | stop segundo o maior uso das janelas de 5h e 7d (None sem dado)."""
    if not cache:
        return None, None
    now, worst, which = time.time(), 0.0, None
    for k, w in (cache.get("rate_limits") or {}).items():
        if not isinstance(w, dict) or (w.get("resets_at") or 0) < now:
            continue
        pct = float(w.get("used_percentage") or 0)
        if pct >= worst:
            worst, which = pct, k
    return ("stop" if worst >= STOP_PCT else "warn" if worst >= WARN_PCT else "ok"), {"window": which, "used_pct": worst}


def cmd_status(a):
    t = find_transcript(a.session, a.transcript)
    r = scan(t)
    cache = read_cache(r["session_id"])
    lv, det = level(cache)
    r["statusline_cache"] = {"fresh": bool(cache and time.time() - cache.get("ts", 0) < 600), "level": lv, "detail": det}
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_statusline(a):
    d = json.load(sys.stdin)
    sid = d.get("session_id")
    rl = d.get("rate_limits") or {}
    cw = d.get("context_window") or {}
    if sid:
        STATE.mkdir(parents=True, exist_ok=True)
        (STATE / f"{sid}.json").write_text(json.dumps({"ts": time.time(), "rate_limits": rl, "context_window": cw,
                                                       "transcript_path": d.get("transcript_path")}))
    f5 = (rl.get("five_hour") or {}).get("used_percentage")
    ctx = cw.get("used_percentage")
    print(" · ".join(x for x in (f"5h {f5:.0f}%" if f5 is not None else "", f"ctx {ctx:.0f}%" if ctx is not None else "") if x) or "guard")


def cmd_check(a):
    cache = read_cache(a.session)
    lv, det = level(cache)
    print(json.dumps({"level": lv, "detail": det}))
    sys.exit({"ok": 0, "warn": 10, "stop": 20}.get(lv, 0))


def plist_path(sid):
    return AGENTS_DIR / f"com.ai-dev-kit.limit-guard.{sid[:8]}.plist"


def cmd_arm(a):
    at = int(a.at)
    sid = a.session
    t = find_transcript(sid, None)
    cwd = a.cwd or scan(t)["cwd"]
    if not cwd or not sid:
        sys.exit("faltam --session e cwd (não achei no transcript)")
    when = time.localtime(at + MARGIN_S)
    plan = {"session": sid, "cwd": cwd, "run_at": time.strftime("%Y-%m-%d %H:%M:%S", when),
            "plist": str(plist_path(sid)), "apply": bool(a.apply)}
    if a.apply:
        STATE.mkdir(parents=True, exist_ok=True)
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        args = [sys.executable, os.path.abspath(__file__), "run-resume", "--session", sid, "--at", str(at),
                "--cwd", cwd, "--tries", str(a.tries)]
        if a.prompt:
            args += ["--prompt", a.prompt]
        pl = {"Label": plist_path(sid).stem, "ProgramArguments": args,
              "StartCalendarInterval": {"Month": when.tm_mon, "Day": when.tm_mday, "Hour": when.tm_hour, "Minute": when.tm_min},
              "StandardOutPath": str(STATE / f"{sid}.log"), "StandardErrorPath": str(STATE / f"{sid}.log"),
              "EnvironmentVariables": {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(HOME)}}
        with open(plist_path(sid), "wb") as fh:
            plistlib.dump(pl, fh)
        if not os.environ.get("LIMIT_GUARD_NO_LAUNCHCTL"):
            subprocess.run(["launchctl", "unload", str(plist_path(sid))], capture_output=True)
            plan["launchctl"] = subprocess.run(["launchctl", "load", str(plist_path(sid))], capture_output=True, text=True).returncode
    print(json.dumps(plan, ensure_ascii=False, indent=2))


def cmd_run(a):
    """Executado pelo launchd: espera o reset, retoma a sessão e rearma se ainda estiver limitada."""
    wait = int(a.at) + MARGIN_S - time.time()
    if wait > 0:
        time.sleep(min(wait, 3600))
    cmd = [os.environ.get("CLAUDE_BIN", "claude"), "-p", a.prompt or DEFAULT_PROMPT, "--resume", a.session,
           "--permission-mode", os.environ.get("LIMIT_GUARD_PERMISSION_MODE", "acceptEdits")]
    p = subprocess.run(cmd, cwd=a.cwd, capture_output=True, text=True)
    text = (p.stdout or "") + (p.stderr or "")
    print(time.strftime("%F %T"), "rc=", p.returncode, text[-400:])
    limited = "hit your" in text or "usage_limit" in text
    if limited and a.tries > 1:
        r = scan(find_transcript(a.session))
        nxt = (r["rejection"] or {}).get("resets_at") or int(time.time()) + 1800
        ns = argparse.Namespace(session=a.session, at=max(nxt, int(time.time())), cwd=a.cwd, prompt=a.prompt,
                                tries=a.tries - 1, apply=True)
        cmd_arm(ns)
    else:
        pp = plist_path(a.session)
        if pp.exists():
            if not os.environ.get("LIMIT_GUARD_NO_LAUNCHCTL"):
                subprocess.run(["launchctl", "unload", str(pp)], capture_output=True)
            pp.unlink()


def cmd_watch(a):
    """Vigia o transcript (para sessões iniciadas sem hooks): ao surgir um limite rejeitado novo, arma a retomada."""
    seen = (scan(find_transcript(a.session))["rejection"] or {}).get("seen_at")
    deadline = time.time() + a.hours * 3600
    while time.time() < deadline:
        r = scan(find_transcript(a.session))
        rej = r["rejection"]
        if rej and rej["seen_at"] != seen:
            cmd_arm(argparse.Namespace(session=a.session, at=rej["resets_at"], cwd=r["cwd"], prompt=None,
                                       tries=MAX_TRIES, apply=True))
            return
        time.sleep(a.interval)


def cmd_hook(a):
    d = json.load(sys.stdin)
    ev = d.get("hook_event_name") or d.get("event")
    sid = d.get("session_id")
    ctx = None
    if ev == "StopFailure" and "rate_limit" in str(d.get("error", "")) + str(d.get("error_details", "")):
        r = {}
        for _ in range(4):
            r = scan(find_transcript(sid, d.get("transcript_path")))
            if r["rejection"] and r["rejection"]["resets_in_s"] > -60:
                break
            time.sleep(2)
        at = (r.get("rejection") or {}).get("resets_at") or int(time.time()) + 1800
        ns = argparse.Namespace(session=sid, at=at, cwd=d.get("cwd"), prompt=None, tries=MAX_TRIES,
                                apply=not os.environ.get("LIMIT_GUARD_DRYRUN"))
        cmd_arm(ns)
        return
    if ev == "SessionStart" and d.get("source") in ("compact", "resume", "fork"):
        r = scan(find_transcript(sid, d.get("transcript_path")))
        ctx = (f"[session-limit-guard] Sessão retomada (source={d.get('source')}; compactações no transcript: "
               f"{r['compactions']}). Contexto foi reduzido: acione recall-directives e a hallucination-guard "
               "(passe completo), releia o ledger/checklist em disco e a lista de subagentes antes de agir.")
    elif ev in ("PostToolUse", "UserPromptSubmit"):
        lv, det = level(read_cache(sid))
        flag = STATE / f"{sid}.{lv}.flag"
        if lv in ("warn", "stop") and not (flag.exists() and time.time() - flag.stat().st_mtime < 600):
            STATE.mkdir(parents=True, exist_ok=True)
            flag.touch()
            ctx = (f"[session-limit-guard] Uso da janela {det['window']} em {det['used_pct']:.0f}% "
                   + ("(PARE: não lance subagentes novos, grave o estado de retomada no ledger e aguarde o reset)."
                      if lv == "stop" else "(atenção: priorize o essencial e grave o estado de retomada no ledger)."))
    if ctx:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": ev, "additionalContext": ctx}}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("status"); a.add_argument("--session"); a.add_argument("--transcript"); a.set_defaults(f=cmd_status)
    s.add_parser("statusline").set_defaults(f=cmd_statusline)
    a = s.add_parser("check"); a.add_argument("--session", required=True); a.set_defaults(f=cmd_check)
    a = s.add_parser("arm-resume"); a.add_argument("--session", required=True); a.add_argument("--at", required=True)
    a.add_argument("--cwd"); a.add_argument("--prompt"); a.add_argument("--tries", type=int, default=MAX_TRIES)
    a.add_argument("--apply", action="store_true"); a.set_defaults(f=cmd_arm)
    a = s.add_parser("run-resume"); a.add_argument("--session", required=True); a.add_argument("--at", required=True)
    a.add_argument("--cwd", required=True); a.add_argument("--prompt"); a.add_argument("--tries", type=int, default=MAX_TRIES)
    a.set_defaults(f=cmd_run)
    a = s.add_parser("watch"); a.add_argument("--session", required=True); a.add_argument("--hours", type=float, default=10)
    a.add_argument("--interval", type=int, default=60); a.set_defaults(f=cmd_watch)
    s.add_parser("hook").set_defaults(f=cmd_hook)
    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()

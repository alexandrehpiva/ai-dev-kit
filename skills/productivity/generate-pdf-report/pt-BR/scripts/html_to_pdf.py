#!/usr/bin/env python3
"""Converte um HTML autocontido em PDF via Chrome/Chromium headless (stdlib pura).

Uso:  python3 html_to_pdf.py <entrada.html> <saida.pdf>
      CHROME_PATH=/caminho/do/chrome python3 html_to_pdf.py ...   (override opcional)

Detecta o Chrome em macOS/Linux/Windows, renderiza e valida o resultado (arquivo existe, começa com
%PDF, conta páginas) e sai com código != 0 e mensagem clara se algo falhar.
Um CHROME_PATH que aponta para algo inexistente é erro, não cai em default.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TIMEOUT_S = 90

MAC_APPS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
LINUX_BINS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


def find_chrome():
    override = os.environ.get("CHROME_PATH")
    if override:
        if not Path(override).is_file():
            sys.exit(f"ERRO: CHROME_PATH aponta para algo inexistente: {override}")
        return override
    candidates = []
    if sys.platform == "darwin":
        candidates = MAC_APPS
    elif sys.platform.startswith("win"):
        for var in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData"):
            base = os.environ.get(var)
            if base:
                candidates.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
    for path in candidates:
        if Path(path).is_file():
            return path
    for name in LINUX_BINS:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("ERRO: Chrome/Chromium não encontrado. Defina CHROME_PATH com o executável.")


def count_pages(pdf_bytes):
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    html_path, pdf_path = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if not html_path.is_file():
        sys.exit(f"ERRO: HTML não encontrado: {html_path}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()  # não confundir PDF antigo com sucesso desta execução

    cmd = [find_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={pdf_path}"]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.append("--no-sandbox")  # Chrome como root (contêiner) exige; fora disso, mantém o sandbox
    cmd.append(html_path.as_uri())
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        sys.exit(f"ERRO: Chrome não terminou em {TIMEOUT_S}s (HTML com recurso externo travado?)")

    data = pdf_path.read_bytes() if pdf_path.exists() else b""
    if proc.returncode != 0 or not data.startswith(b"%PDF"):
        tail = "\n".join(l for l in proc.stderr.splitlines() if "task_policy" not in l)[-800:]
        sys.exit(f"ERRO: PDF não foi gerado (exit={proc.returncode}).\n{tail}")
    print(f"OK: {pdf_path} — {count_pages(data)} página(s), {len(data) / 1024:.0f} KB")


if __name__ == "__main__":
    main()

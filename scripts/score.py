#!/usr/bin/env python3
"""Score every transcript in transcripts/<clip>/ against reference/<clip>.txt.

Reports word error rate (WER) and proper-noun accuracy per engine, writes
results/<clip>.md, and refreshes the results table in README.md.

  python3 scripts/score.py            # all clips that have a reference
  python3 scripts/score.py ep40
  python3 scripts/score.py ep40 --diff gemini-3-flash   # show alignment ops

Reference format (reference/<clip>.txt): one speaker turn per line,
  [MM:SS] A: text
Lines starting with '#' are ignored. Hypotheses may be plain text or the same
turn format; markers are stripped before scoring.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMALIZATION_VERSION = "2026-09-07.1"

TURN = re.compile(r"^\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*(?:speaker\s*)?[A-Za-z0-9]{1,2}\s*:\s*", re.I)

# Orthographic variants that are NOT transcription errors. Keep this list
# short and public: every entry moves the numbers.
EQUIVALENTS = [
    ("super-app", "superapp"), ("super app", "superapp"), ("super-up", "superapp"),
    ("pay pay", "paypay"), ("pay-pay", "paypay"),
    ("komu nelen", "komu ne len"),
    ("yigirma foiz", "20 foiz"), ("20%", "20 foiz"),
    ("yuzta", "100 ta"), ("100ta", "100 ta"),
    ("o'ttiz besh mingta", "35 mingta"), ("35000ta", "35 mingta"), ("sakson", "80"),
    ("klikka", "clickka"),
]

def normalize(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        out.append(TURN.sub("", line))
    s = " ".join(out).lower()
    for a in "ʻʼ’‘`´":
        s = s.replace(a, "'")
    for a, b in EQUIVALENTS:
        s = s.replace(a, b)
    s = re.sub(r"[-–—]", " ", s)
    s = re.sub(r"[^\w' ]+", " ", s)
    s = re.sub(r"\b(\w+)'(lardan|lar|ga|ni|dan|da)\b", r"\1\2", s)  # Payme'ni -> paymeni
    return s.split()

def align(ref, hyp):
    n, m = len(ref), len(hyp)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i-1][j] + 1, D[i][j-1] + 1, D[i-1][j-1] + (ref[i-1] != hyp[j-1]))
    i, j, ops = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i-1][j-1] + (ref[i-1] != hyp[j-1]):
            ops.append(("=" if ref[i-1] == hyp[j-1] else "S", ref[i-1], hyp[j-1])); i -= 1; j -= 1
        elif i > 0 and D[i][j] == D[i-1][j] + 1:
            ops.append(("D", ref[i-1], "")); i -= 1
        else:
            ops.append(("I", "", hyp[j-1])); j -= 1
    return ops[::-1]

def terms_for(clip):
    p = ROOT / "reference" / f"{clip}.terms.txt"
    if not p.exists(): return []
    terms = []
    for line in p.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line: terms.append([normalize(v) for v in line.split("|")])
    return terms

def term_accuracy(terms, ref, hyp):
    """Share of reference proper-noun occurrences found in the hypothesis."""
    def count(seq, variants):
        return sum(sum(1 for i in range(len(seq) - len(v) + 1) if seq[i:i+len(v)] == v) for v in variants)
    total = hit = 0
    for variants in terms:
        r = count(ref, variants)
        if not r: continue
        total += r; hit += min(r, count(hyp, variants))
    return (hit, total)

def score_clip(clip, diff=None):
    ref_path = ROOT / "reference" / f"{clip}.txt"
    if not ref_path.exists():
        print(f"{clip}: no reference/{clip}.txt yet (draft only) — skipped"); return None
    ref = normalize(ref_path.read_text())
    terms = terms_for(clip)
    rows = []
    for p in sorted((ROOT / "transcripts" / clip).glob("*.txt")):
        hyp = normalize(p.read_text())
        ops = align(ref, hyp)
        S = sum(o[0] == "S" for o in ops); D = sum(o[0] == "D" for o in ops); I = sum(o[0] == "I" for o in ops)
        hit, total = term_accuracy(terms, ref, hyp)
        rows.append((p.stem, len(hyp), (S + D + I) / len(ref) * 100, S, D, I, hit, total))
        if diff == p.stem:
            for o in ops:
                if o[0] != "=": print(f"  {o[0]} {o[1]:>20s} -> {o[2]}")
    rows.sort(key=lambda r: r[2])
    md = [f"# {clip}", "", f"Reference words: {len(ref)}. Normalization {NORMALIZATION_VERSION}.", "",
          "| Engine | WER | Sub | Del | Ins | Words | Proper nouns |", "|---|---|---|---|---|---|---|"]
    for name, n, wer, S, D, I, hit, total in rows:
        pn = f"{hit}/{total}" if total else "—"
        md.append(f"| {name} | {wer:.1f}% | {S} | {D} | {I} | {n} | {pn} |")
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"{clip}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md)); return "\n".join(md[4:])

def update_readme(tables):
    readme = ROOT / "README.md"
    text = readme.read_text()
    block = "\n\n".join(f"### {clip}\n\n{tbl}" for clip, tbl in tables.items() if tbl) or "_No scored clips yet._"
    new = re.sub(r"(<!-- results:start -->).*?(<!-- results:end -->)", rf"\1\n{block}\n\2", text, flags=re.S)
    readme.write_text(new)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    diff = sys.argv[sys.argv.index("--diff") + 1] if "--diff" in sys.argv else None
    clips = args or [p.name for p in sorted((ROOT / "transcripts").iterdir()) if p.is_dir()]
    tables = {c: score_clip(c, diff) for c in clips}
    update_readme(tables)

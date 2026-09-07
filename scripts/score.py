#!/usr/bin/env python3
"""Score every transcript in transcripts/<clip>/ against reference/<clip>.txt.

Metrics per engine:
  WER            word error rate after normalization
  WER by host    the same, attributed to the reference speaker (A, B, ...)
  proper nouns   share of reference occurrences of reference/<clip>.terms.txt found
  diarization    for engines whose transcript carries [MM:SS] label: turns —
                 word-weighted share of reference turns whose start falls inside a
                 hypothesis turn of the matching speaker (labels mapped 1:1 by best
                 overlap), plus how many speakers and turns the engine produced.

  python3 scripts/score.py                 # all clips with a reference
  python3 scripts/score.py ep40 --diff gemini-3-flash

Reference format (reference/<clip>.txt): one speaker turn per line,
  [MM:SS] A: text
Lines starting with '#' are ignored. Hypotheses may be plain text or the same
turn format.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMALIZATION_VERSION = "2026-09-07.2"

TURN = re.compile(r"^\s*\[?(\d{1,2}):(\d{2})(?::(\d{2}))?\]?\s*(?:speaker[_ ]?)?([A-Za-z0-9]{1,2})\s*:\s*", re.I)

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

def norm_words(s):
    s = s.lower()
    for a in "ʻʼ’‘`´":
        s = s.replace(a, "'")
    for a, b in EQUIVALENTS:
        s = s.replace(a, b)
    s = re.sub(r"\[[^\]]*\]", " ", s)            # [kulgi], [?]
    s = re.sub(r"[-–—]", " ", s)
    s = re.sub(r"[^\w' ]+", " ", s)
    s = re.sub(r"\b(\w+)'(lardan|lar|ga|ni|dan|da)\b", r"\1\2", s)   # Payme'ni -> paymeni
    return s.split()

def parse(text):
    """-> (words, labels-per-word, turns). turns = [(start_sec, label, n_words)] or [] if unlabelled."""
    words, labels, turns = [], [], []
    cur = None
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = TURN.match(line)
        if m:
            h, mnt, sec, lab = m.groups()
            start = int(h) * 60 + int(mnt) + (int(sec) if sec else 0) if sec else int(h) * 60 + int(mnt)
            cur = [start, lab.upper(), 0]; turns.append(cur)
            line = line[m.end():]
        w = norm_words(line)
        words += w; labels += [cur[1] if cur else None] * len(w)
        if cur: cur[2] += len(w)
    return words, labels, [tuple(t) for t in turns]

def align(ref, hyp):
    n, m = len(ref), len(hyp)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i-1][j] + 1, D[i][j-1] + 1, D[i-1][j-1] + (ref[i-1] != hyp[j-1]))
    i, j, ops = n, m, []          # ops: (kind, ref_index or None, ref_word, hyp_word)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i-1][j-1] + (ref[i-1] != hyp[j-1]):
            ops.append(("=" if ref[i-1] == hyp[j-1] else "S", i-1, ref[i-1], hyp[j-1])); i -= 1; j -= 1
        elif i > 0 and D[i][j] == D[i-1][j] + 1:
            ops.append(("D", i-1, ref[i-1], "")); i -= 1
        else:
            ops.append(("I", i-1 if i else 0, "", hyp[j-1])); j -= 1
    return ops[::-1]

def terms_for(clip):
    p = ROOT / "reference" / f"{clip}.terms.txt"
    if not p.exists(): return []
    out = []
    for line in p.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line: out.append([norm_words(v) for v in line.split("|")])
    return out

def term_accuracy(terms, ref, hyp):
    def count(seq, variants):
        return sum(sum(1 for i in range(len(seq) - len(v) + 1) if seq[i:i+len(v)] == v) for v in variants)
    total = hit = 0
    for variants in terms:
        r = count(ref, variants)
        if r: total += r; hit += min(r, count(hyp, variants))
    return hit, total

def diarization(ref_turns, hyp_turns):
    """Map hyp labels to ref labels by word-weighted overlap at turn starts; return accuracy."""
    if not hyp_turns or not ref_turns: return None
    def hyp_label_at(t):
        lab = hyp_turns[0][1]
        for s, l, _ in hyp_turns:
            if s <= t: lab = l
            else: break
        return lab
    conf = {}
    for s, lab, n in ref_turns:
        conf[(lab, hyp_label_at(s))] = conf.get((lab, hyp_label_at(s)), 0) + n
    mapping, used_r, used_h = {}, set(), set()
    for (r, h), n in sorted(conf.items(), key=lambda kv: -kv[1]):
        if r not in used_r and h not in used_h:
            mapping[h] = r; used_r.add(r); used_h.add(h)
    total = sum(n for _, _, n in ref_turns)
    ok = sum(n for (r, h), n in conf.items() if mapping.get(h) == r)
    return ok / total * 100, len({l for _, l, _ in hyp_turns}), len(hyp_turns)

def score_clip(clip, diff=None):
    ref_path = ROOT / "reference" / f"{clip}.txt"
    if not ref_path.exists():
        print(f"{clip}: no reference/{clip}.txt — skipped"); return None
    ref, ref_lab, ref_turns = parse(ref_path.read_text())
    hosts = sorted({l for l in ref_lab if l})
    terms = terms_for(clip)
    rows = []
    for p in sorted((ROOT / "transcripts" / clip).glob("*.txt")):
        hyp, _, hyp_turns = parse(p.read_text())
        ops = align(ref, hyp)
        err = {h: 0 for h in hosts}; S = D = I = 0
        for kind, ri, rw, hw in ops:
            if kind == "=": continue
            S += kind == "S"; D += kind == "D"; I += kind == "I"
            lab = ref_lab[ri] if ri is not None and ri < len(ref_lab) else None
            if lab in err: err[lab] += 1
        per_host = {h: err[h] / max(1, ref_lab.count(h)) * 100 for h in hosts}
        hit, total = term_accuracy(terms, ref, hyp)
        rows.append(dict(name=p.stem, n=len(hyp), wer=(S + D + I) / len(ref) * 100, S=S, D=D, I=I,
                         hosts=per_host, pn=(hit, total), dia=diarization(ref_turns, hyp_turns)))
        if diff == p.stem:
            for kind, ri, rw, hw in ops:
                if kind != "=": print(f"  {kind} {rw:>20s} -> {hw}")
    rows.sort(key=lambda r: r["wer"])
    hdr = ["Engine", "WER"] + [f"WER {h}" for h in hosts] + ["Sub", "Del", "Ins", "Words", "Proper nouns", "Speaker acc", "Spk/turns"]
    md = [f"# {clip}", "", f"Reference: {len(ref)} words, {len(ref_turns)} turns, hosts {', '.join(hosts) or '—'} "
          f"({', '.join(f'{h}={ref_lab.count(h)}' for h in hosts)}). Normalization {NORMALIZATION_VERSION}.", "",
          "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        pn = f"{r['pn'][0]}/{r['pn'][1]}" if r["pn"][1] else "—"
        dia = f"{r['dia'][0]:.0f}%" if r["dia"] else "—"
        spk = f"{r['dia'][1]}/{r['dia'][2]}" if r["dia"] else "—"
        cells = [r["name"], f"{r['wer']:.1f}%"] + [f"{r['hosts'][h]:.1f}%" for h in hosts] + \
                [str(r["S"]), str(r["D"]), str(r["I"]), str(r["n"]), pn, dia, spk]
        md.append("| " + " | ".join(cells) + " |")
    md += ["", "Speaker acc: word-weighted share of reference turns whose start lies in a hypothesis turn of the "
           "matching speaker (hypothesis labels mapped 1:1 to hosts by best overlap). Spk/turns: distinct speakers "
           f"and turns the engine produced; the reference has {len({l for _, l, _ in ref_turns})}/{len(ref_turns)}."]
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"{clip}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md)); return "\n".join(md[4:])

def update_readme(tables):
    readme = ROOT / "README.md"
    text = readme.read_text()
    block = "\n\n".join(f"### {clip}\n\n{tbl}" for clip, tbl in tables.items() if tbl) or "_No scored clips yet._"
    readme.write_text(re.sub(r"(<!-- results:start -->).*?(<!-- results:end -->)", lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}", text, flags=re.S))

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    diff = sys.argv[sys.argv.index("--diff") + 1] if "--diff" in sys.argv else None
    if diff in args: args.remove(diff)
    clips = args or [p.name for p in sorted((ROOT / "transcripts").iterdir()) if p.is_dir()]
    update_readme({c: score_clip(c, diff) for c in clips})

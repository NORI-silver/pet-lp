#!/usr/bin/env python3
"""AI-KIT を別の事業のリポジトリに入れる・入れ直す（Nori 2026-11-22「カタナとかほかのサービスでもこの体制撮れるようにしてくれる」）。

使い方:
  python3 ai-kit/install.py <入れる先のリポジトリ> --name 事業の名前 [--site ドメイン] [--sign 署名の言葉の正規表現] [--sender 送る係] [--owner Nori]
何度動かしても同じ結果になる（入れ直し＝道具と型を最新にする。台帳・ai-kit.json・operating.md は上書きしない）。
入れるもの:
  tools/  draft_check.py reply_check.py proposal_check.py feedback_check.py report_check.cjs（同じ名前の別物があれば止める）
  docs/ai/framework/  README・lessons・toi-questions・proposal-template・org-chart・daily-report
  docs/ai/feedback.json・docs/ai/operating.md（なければ）、ai-kit.json（なければ）
  AGENTS.md の AI-KIT の節（<!-- AI-KIT:START --> 〜 END を入れかえ。なければ先頭の見出しの後ろに足す）
  CLAUDE.md・GEMINI.md（なければ「@AGENTS.md」だけ）、.github/workflows/ai-kit.yml
何も送らない。
"""
import json, os, re, shutil, sys

KIT = os.path.dirname(os.path.abspath(__file__))
TOOLS = ["draft_check.py", "reply_check.py", "proposal_check.py", "feedback_check.py", "report_check.cjs"]
FW = ["README.md", "lessons.md", "toi-questions.md", "proposal-template.md", "org-chart.md", "daily-report.md"]
MARK = "<!-- AI-KIT:"


def opt(a, k, d=None):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d


def fill(text, cfg):
    return text.replace("{{NAME}}", cfg["name"]).replace("{{OWNER}}", cfg["owner"])


def write(path, text, keep=False):
    if keep and os.path.exists(path): return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old == text: return False
    open(path, "w", encoding="utf-8").write(text); return True


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--") or not opt(a, "--name"):
        print(__doc__); return 2
    root = a[0]
    cfgp = os.path.join(root, "ai-kit.json")
    cfg = json.load(open(cfgp, encoding="utf-8")) if os.path.exists(cfgp) else {}
    cfg.setdefault("name", opt(a, "--name")); cfg.setdefault("owner", opt(a, "--owner", "Nori"))
    for k in ("site", "sign", "sender"):
        if opt(a, "--" + k): cfg.setdefault(k, opt(a, "--" + k))
    cfg.setdefault("sign", re.escape(cfg["name"])); cfg.setdefault("ban", [])
    changed = []
    for t in TOOLS:
        dst = os.path.join(root, "tools", t)
        src = open(os.path.join(KIT, "tools", t), encoding="utf-8").read()
        if os.path.exists(dst) and "AI-KIT" not in open(dst, encoding="utf-8").read():
            print(f"止めました：{dst} は別の道具です（名前がぶつかる）"); return 1
        if write(dst, src): changed.append(f"tools/{t}")
    for f in FW:
        if write(os.path.join(root, "docs/ai/framework", f), fill(open(os.path.join(KIT, "framework", f), encoding="utf-8").read(), cfg)): changed.append(f"docs/ai/framework/{f}")
    for src, dst in (("templates/feedback.json", "docs/ai/feedback.json"), ("templates/operating.md", "docs/ai/operating.md")):
        if write(os.path.join(root, dst), fill(open(os.path.join(KIT, src), encoding="utf-8").read(), cfg), keep=True): changed.append(dst)
    if write(cfgp, json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", keep=True): changed.append("ai-kit.json")
    if write(os.path.join(root, ".github/workflows/ai-kit.yml"), open(os.path.join(KIT, "templates/ai-kit.yml"), encoding="utf-8").read()): changed.append(".github/workflows/ai-kit.yml")
    block = fill(open(os.path.join(KIT, "AGENTS.kit.md"), encoding="utf-8").read(), cfg).strip() + "\n"
    ap = os.path.join(root, "AGENTS.md")
    ag = open(ap, encoding="utf-8").read() if os.path.exists(ap) else f"# {cfg['name']}\n"
    if MARK + "START" in ag:
        new = re.sub(r"<!-- AI-KIT:START.*?<!-- AI-KIT:END -->\n?", lambda m: block, ag, flags=re.S)
    else:
        lines = ag.split("\n"); i = next((n for n, l in enumerate(lines) if l.startswith("# ")), -1) + 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"): i += 1
        new = "\n".join(lines[:i] + ["", block] + lines[i:])
    if write(ap, new): changed.append("AGENTS.md")
    for f in ("CLAUDE.md", "GEMINI.md"):
        if write(os.path.join(root, f), "@AGENTS.md\n\n共通の決まりは `AGENTS.md`（AI-KIT の節もふくむ）。ルールを足すときは `AGENTS.md` を直す。\n", keep=True): changed.append(f)
    print("入れました：" if changed else "最新です（変わったところなし）")
    for c in changed: print("  ", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""[G] 言われる前に止める：サイトの決まり（AGENTS.md「品質の決まり」）を、公開の前に機械で確かめる（Nori 2026-11-16
「今僕が指示してることとか、指示しなくてもできるようにしたい」）。

使い方:
  python3 tools/rules_check.py .            → 新しい違反があれば終了コード1（PRごとに seo-check.yml で動く）
  python3 tools/rules_check.py . --all      → 前からの違反（tools/rules_baseline.json）も全部出す（週1回の見回り用）
  python3 tools/rules_check.py . --prune    → 直った違反を rules_baseline.json から消す（gen_areas.py の最後でも動く）

見ること（どれも Nori さんに言われたこと。日付は AGENTS.md）:
  words     使わない言葉（使える会社・公式サイトに書いてあること・当サイトで調べた◯件 など）
  hole      下書きの穴（◯◯・○○・XX・TODO）が画面に出ている
  removed   消した部品がもどってきた（動物病院の「いま具合が悪いとき」の箱 など）
  tally     運営側の集計（しらべた自治体の数・調べた◯件）を見せている
  prefgrid  都道府県のボタン・リンクを20個以上、たたまずに並べている（何画面も使う）
  intro     最初のさがす欄・見出しの前の文が長い（REASONS.intro の字数）
  search    施設の分野の入口・県のページで、さがす欄より前に記事・目次が来ている
  wall      図・表・箇条書き・見出しのない文が長く続く（文字の壁）
前からある違反は tools/rules_baseline.json に入っていて、新しく増えたものだけで止める（直ったものは --prune で消える。
足して逃げない）。新しい決まりを足したら、ここと AGENTS.md の「品質の決まり」の両方に書く。
"""
import json, os, re, sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
PREFS = ["北海道", "青森", "岩手", "宮城", "秋田", "山形", "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川",
         "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "滋賀", "京都", "大阪", "兵庫", "奈良",
         "和歌山", "鳥取", "島根", "岡山", "広島", "山口", "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分",
         "宮崎", "鹿児島", "沖縄"]
PREF_SLUGS = {"hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima", "ibaraki", "tochigi", "gunma", "saitama",
              "chiba", "tokyo", "kanagawa", "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu", "shizuoka", "aichi",
              "mie", "shiga", "kyoto", "osaka", "hyogo", "nara", "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
              "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa",
              }  # 県のページ
HOSP_SUB = {"night", "cat", "exotic", "large-dog", "visit"}  # 動物病院の条件のページ
PREF_RE = re.compile(r"^(%s)(都|道|府|県)?(・[^\d（(]{1,8})?\s*([（(]?\d+\s*(件|軒|か所|院|社|施設|団体|店|頭)?[)）]?|[（(]?(0件|しらべ中|まだ)[)）]?)?$" % "|".join(PREFS))

# 使わない言葉（seo_check.py の BAN・VERIFY_CLAIM のほか）。(正規表現, 理由)
WORDS = [
    (r"(?<![にて])使える会社", "「条件に合う会社」と書く（Nori 11/15）"),
    (r"公式(?:サイト|ページ)に書いて(?:ある|あった)こと", "「公式ページに書いてあること」はやめる（Nori 11/16）"),
    (r"当サイトで(?:調べ|しらべ)", "運営側の作業を見せない（Nori 11/16）"),
    (r"手配料", "「無料」と書く（Nori 10/31）"),
    (r"最大5社", "社数の上限はない（Nori 11/01）"),
    (r"\d+分以内に(?:返|ご連絡|お返事)", "返事の時間を約束しない（Nori 10/31）"),
    (r"先に答え", "「先に答え」の札は使わない（答えの文を見出しに。Nori 11/14）"),
    (r"この子OK|この子オッケー", "札は何が合うかをそのまま書く（Nori 11/15）"),
]
# ○ は表の印にも使うので、穴は「◯◯」（「」の中の例は除く）と TODO などだけ
HOLES = re.compile(r"(?<![「『])◯◯(?![」』一])|TODO|FIXME|XXX|\{\{|\}\}")
# 消した部品（クラス・属性・文）。Nori さんが消すように言ったもの
REMOVED = [
    (re.compile(r'class="hf-sos"|\bdata-sos\b|いま具合が悪いとき'), "動物病院の「いま具合が悪いとき」の箱（Nori 11/16 で消した）"),
    (re.compile(r'写真を見る</button>'), "「写真を見る」のボタン（Nori 11/15「いらない」）"),
]
TALLY = re.compile(r"(?:しらべ|調べ|確かめ|確認し)た(?:自治体|市区町村|施設|病院|会社|件|数)|(?:しらべ|調べ)た数|しらべ済み|調査済みの(?:自治体|市区町村)")
INTRO_MAX = 120      # 施設の分野で、さがす欄・最初の見出しの前に置いてよい文の字数（h1 の下のリード文をふくむ）
INTRO_MAX_GUIDE = 250  # 記事で、最初の見出しの前に置いてよい字数（リード文と、答えの「まとめ」の文まで）
WALL_MAX = 500       # 図・表・箇条書き・見出しなしで続けてよい文の字数
PREFGRID_MAX = 19    # たたまずに並べてよい都道府県のボタン・リンクの数
# 施設の分野（さがす欄が先に来ること）。tools/uikit.py の ALL と同じ。病院は /hospital/ の下の夜間などもふくむ
FAC_CATS = ["hospital", "pet-hotel", "dogrun", "pet-sitter", "trimming", "dog-trainer", "rojin-home", "sougi", "joto",
            "inu-yado", "pet-yado", "inu-cafe", "jichitai", "hinan", "emergency"]
SEARCH_MARK = re.compile(r'class="(?:[^"]*\s)?(?:ux-find|hf|hn-find|bf|ff-box|fit-box|pref-pick|ux-c|emg-item|fr)(?:\s[^"]*)?"|<select\b|<input\b(?![^>]*type="hidden")')
REASONS = {
    "words": "使わない言葉", "hole": "下書きの穴（◯◯など）", "removed": "消した部品がもどった", "tally": "運営側の集計を見せている",
    "prefgrid": f"都道府県のボタンを{PREFGRID_MAX + 1}個以上たたまずに並べている", "intro": f"さがす欄・見出しの前の文が{INTRO_MAX}字を超える",
    "search": "施設の分野で、さがす欄より前に記事・目次がある",
    "card": "タクシー以外の施設のカードが共通のカード（tools/cardskin.py の形）になっていない", "wall": f"図・表・箇条書きのない文が{WALL_MAX}字を超えて続く",
}
BLOCK_BREAK = {"h2", "h3", "h4", "ul", "ol", "table", "figure", "img", "svg", "picture", "details", "dl", "blockquote", "form", "select", "button"}
VOID = {"br", "img", "input", "meta", "link", "hr", "source", "wbr", "area", "col", "embed", "param", "track"}


class Page(HTMLParser):
    """<main> の中だけを見る。script・style・テンプレートは飛ばす。"""

    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.stack, s.in_main, s.skip = [], False, 0
        s.text = []                 # (文, 外側にある details/select/footer/nav があるか)
        s.prefs = []                # たたんでいない都道府県のリンク・ボタン
        s._a = None                 # いま開いている a・button の文
        s.intro, s.intro_done = 0, False
        s.wall, s.walls = 0, []
        s.first_toc = None          # 目次・記事へのリンクの位置
        s.first_search = None
        s.pos = 0

    def folded(s):
        return any(t in ("details", "select", "footer", "header", "noscript", "table") or "catbar" in c or "hub" in c or "crumb" in c
                   for t, c in s.stack)

    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == "main": s.in_main = True
        if not s.in_main: return
        if tag in ("script", "style", "template"): s.skip += 1; return
        if s.skip: return
        cls = a.get("class") or ""
        s.pos += 1
        attrs = " ".join(f'{k}="{v}"' for k, v in a.items() if v is not None)
        if s.first_search is None and (tag in ("select", "input") and a.get("type") != "hidden" or SEARCH_MARK.search(f'class="{cls}"')):
            s.first_search = s.pos
        if s.first_toc is None and (("art-toc" in cls or "toc" in cls.split()) or (tag == "a" and (a.get("href") or "").startswith("/guide/") and not s.folded())):
            s.first_toc = s.pos
        if tag in BLOCK_BREAK or "card" in cls or "tile" in cls or "ux-c" in cls or "emg-item" in cls or "vz-" in cls:
            if s.wall > WALL_MAX: s.walls.append(s.wall)
            s.wall = 0
        if not s.intro_done and (tag in ("h2", "select", "input", "form", "table") or s.first_search is not None):
            s.intro_done = True
        if tag in ("a", "button"): s._a = ""
        if tag not in VOID: s.stack.append((tag, cls))

    def handle_endtag(s, tag):
        if tag == "main":
            s.in_main = False
            if s.wall > WALL_MAX: s.walls.append(s.wall)
            return
        if not s.in_main: return
        if tag in ("script", "style", "template"): s.skip = max(0, s.skip - 1); return
        if s.skip: return
        if tag in ("a", "button") and s._a is not None:
            if PREF_RE.match(s._a.strip()) and not s.folded(): s.prefs.append(s._a.strip())
            s._a = None
        while s.stack:
            t, _ = s.stack.pop()
            if t == tag: break

    def handle_data(s, d):
        if not s.in_main or s.skip: return
        d2 = re.sub(r"\s+", "", d)
        if not d2: return
        if s._a is not None: s._a += d
        s.text.append(d)
        inner = [t for t, _ in s.stack]
        in_p = "p" in inner and not any(t in ("li", "td", "th", "button", "a", "label", "summary") for t in inner[-2:])
        pcls = next((c for t, c in reversed(s.stack) if t == "p"), None)
        # 前置きに数えるのは、ふつうの文（クラスなしの p とリード文）だけ。日付・写真の説明・注意書きは数えない
        if not s.intro_done and pcls is not None and pcls in ("", "lede") and "h1" not in inner and "nav" not in inner and "small" not in inner:
            s.intro += len(d2)
        if in_p and not s.folded(): s.wall += len(d2)


def pages(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".") and d not in ("tools", "node_modules", "tests", "img", "lib", "docs", "sns", "booking", "go", "hub")]
        if "index.html" in fn:
            rel = os.path.relpath(dp, root).replace(os.sep, "/")
            out.append("/" if rel == "." else "/" + rel + "/")
    return sorted(out)


def check_page(root, path):
    raw = open(os.path.join(root, path.strip("/"), "index.html"), encoding="utf-8").read()
    if 'http-equiv="refresh"' in raw[:3000]: return []
    p = Page(); p.feed(raw)
    body = "".join(p.text)
    found = []
    for pat, why in WORDS:
        m = re.search(pat, body)
        if m: found.append(("words", f"「{m.group()}」 {why}"))
    m = next((m for m in HOLES.finditer(body) if body.rfind("「", 0, m.start()) <= body.rfind("」", 0, m.start()) and "◯月" not in body[max(0, m.start() - 40):m.start()]), None)  # 「」の中や、「◯月◯日」のような書き方の例は除く
    if m: found.append(("hole", f"「{body[max(0, m.start() - 12):m.end() + 12].strip()}」"))
    for pat, why in REMOVED:
        if pat.search(raw): found.append(("removed", why))
    m = TALLY.search(body)
    if m: found.append(("tally", f"「{body[max(0, m.start() - 10):m.end() + 10].strip()}」"))
    if len(p.prefs) > PREFGRID_MAX: found.append(("prefgrid", f"{len(p.prefs)}個（<details> でたたむか、選択欄にする）"))
    parts = [x for x in path.split("/") if x]
    info = bool(parts) and (parts[0] in FAC_CATS or parts[0] == "guide")
    # タクシーのページ（トップの写し）はフォームが先にあり、形が決まっているので入口の文は数えない。記事はリード文が少し長くてよい
    listing = len(parts) == 1 or len(parts) == 2 and (parts[1] in PREF_SLUGS or parts[0] == "hospital" and parts[1] in HOSP_SUB)
    if info and p.intro > (INTRO_MAX if parts[0] != "guide" and listing else INTRO_MAX_GUIDE): found.append(("intro", f"{p.intro}字"))
    if parts and parts[0] in FAC_CATS and (len(parts) == 1 or len(parts) == 2 and (parts[1] in PREF_SLUGS or parts[0] == "hospital" and parts[1] in HOSP_SUB)) and p.first_toc is not None and (p.first_search is None or p.first_toc < p.first_search):
        found.append(("search", "さがす欄がない" if p.first_search is None else "目次・記事のリンクがさがす欄より前"))
    # タクシー以外のカードは共通のカード1つ（Nori 2026-11-16「タクシー以外のカードは共通のやつにして」）。
    # 施設1つのページの入口の枠（data-cat つきの emg-co）だけは除く
    if parts and parts[0] in FAC_CATS:
        odd = [m for m in re.finditer(r'<div class="(emg-item[^"]*|yd-card[^"]*)"([^>]*)>', raw)
               if not re.search(r"\b(cs|ux-c|jc-card)\b", m.group(1)) and not ("data-cat=" in m.group(2) and " fc" not in m.group(1))]
        if odd: found.append(("card", f"{len(odd)}枚（{odd[0].group(1)}）"))
    if p.walls and "terms" not in parts: found.append(("wall", f"{max(p.walls)}字"))  # 規約は条文なので除く
    return found


def run(root):
    return {path: v for path in pages(root) if (v := check_page(root, path))}


def key(path, rule):
    return f"{path} {rule}"


def load_base(root):
    f = os.path.join(root, "tools", "rules_baseline.json")
    return set(json.load(open(f, encoding="utf-8"))["known"]) if os.path.exists(f) else set()


def save_base(root, keys):
    f = os.path.join(root, "tools", "rules_baseline.json")
    json.dump({"_note": "2026-11-16 にもうあった違反（tools/rules_check.py）。直ったら --prune（gen_areas.py の最後でも動く）で消える。ここに足して逃げない",
               "known": sorted(keys)}, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    open(f, "a").write("\n")


def prune(root, res=None):
    res = run(root) if res is None else res
    now = {key(p, r) for p, v in res.items() for r, _ in v}
    base = load_base(root)
    keep = base & now
    if keep != base: save_base(root, keep)
    return len(base - keep)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    res = run(root)
    base = load_base(root)
    if "--init" in sys.argv:  # 最初の1回だけ（2026-11-16）。ふだんは使わない
        save_base(root, {key(p, r) for p, v in res.items() for r, _ in v}); print("baseline", len(base)); return
    if "--prune" in sys.argv:
        print("直って消した前からの違反:", prune(root, res)); return
    show_all = "--all" in sys.argv
    new, old = [], []
    for p, v in res.items():
        for r, d in v:
            (old if key(p, r) in base else new).append(f"{p}  [{r}] {REASONS[r]}：{d}")
    for x in new: print("NG:", x)
    if show_all:
        for x in old: print("前から:", x)
    by = {}
    for p, v in res.items():
        for r, _ in v: by[r] = by.get(r, 0) + 1
    print(f"{len(pages(root))}ページを確認。新しい違反 {len(new)}件・前からの違反 {len(old)}件（{', '.join(f'{k} {n}' for k, n in sorted(by.items()))}）")
    if new:
        print("直し方：AGENTS.md の「品質の決まり」を見て、生成のスクリプト（tools/）を直し python3 tools/gen_areas.py . を実行する。")
    sys.exit(1 if new else 0)


if __name__ == "__main__":
    main()

"""Standalone comparison for verified detective listings; no provider action."""
import json
from pathlib import Path
from urllib.parse import urlsplit
import gen_maigo as M
import faccard as F

PATH = "/pet-detective/"
GUIDE = "/jichitai/maigo/"
CSS = """<style>
.pd-hero{padding-bottom:.25rem}.pd-layout{padding-top:0}.pd-layout .wrap{max-width:1040px}
.pd-help{margin:.35rem 0 1rem;font-size:.92rem}.pd-help a{font-weight:700}
.pd-filter{background:white;border:1px solid #ecdccc;border-radius:16px;padding:12px;margin:0 0 14px}
.pd-selects,.pd-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.pd-filter label{font-weight:700;font-size:.88rem;color:#392b22}.pd-selects select{display:block;width:100%;max-width:100%;margin:5px 0 8px;border:1px solid #b89680;border-radius:10px;padding:9px 5px;min-height:44px;background:white;color:#271e18;font:inherit}
.pd-options{display:flex;flex-wrap:wrap;gap:0 15px}.pd-options label{display:flex;align-items:center;gap:5px;min-height:36px}.pd-options input{width:17px;height:17px;accent-color:#a43b0e}
.pd-card{min-width:0;overflow-wrap:anywhere;background:white;border:1px solid #eddccc;border-radius:18px;padding:15px;display:flex;flex-direction:column;gap:8px}.pd-card[hidden]{display:none!important}
.pd-card h2{font-size:1.05rem;margin:0;line-height:1.35}.pd-card dl{margin:0}.pd-card dl div{display:grid;grid-template-columns:5.7em 1fr;gap:6px;padding:4px 0;font-size:.88rem}
.pd-card dt{display:flex;align-items:start;gap:4px;font-weight:700;color:#503421}.pd-card dt svg{width:16px;height:16px;flex:none}.pd-card dd{margin:0;color:#312822}.pd-card details{font-size:.85rem}.pd-card details p,.pd-card details ul{margin:5px 0}.pd-card details summary{cursor:pointer;color:#8b3910;font-weight:700}
.pd-official{margin-top:auto;padding:9px 12px;border-radius:10px;background:#2e231b;color:white!important;text-align:center;text-decoration:none;font-weight:700}
.pd-result{font-size:.87rem;color:#503421;margin:0 0 8px}.pd-empty{padding:.6rem 0}.pd-nojs{font-size:.9rem}.pd-after{padding-top:1rem}
@media(max-width:620px){.pd-grid{grid-template-columns:1fr}.pd-card dl div{padding:3px 0}}
</style>"""

def _covered(d):
    area = d.get("area") or ""
    if not area or area == "記載なし" or "出張範囲は見積もり時に確認" in area:
        return []
    if "全国" in area and ("北海道・沖縄は相談" in area or "離島は個別見積もり" in area):
        # Keep the original exception text on the card; no guaranteed arrival.
        return ["全国"]
    return M._areas(d)

def exists_uri(url):
    return bool(url and urlsplit(url).scheme == "https" and urlsplit(url).hostname)

def page(ctx):
    e, site = ctx["e"], ctx["SITE"]
    rows = []
    for raw, d in zip(M.PRIV.get("detectives", []), M.detectives()):
        if raw.get("kind") != "operator" or not exists_uri(raw.get("url")):
            continue
        comp = d["comparison"] if "eta" in d["flags"].split() else {}
        billed = [p for p in raw.get("plans", []) if p.get("yen")]
        plans = [p for p in billed if not any(k in p["name"] for k in ("成功報酬","延長","出張費","キャンセル"))]
        # On-site search price, not a call-only add-on or an unverified total.
        plan = plans[0] if plans else None
        def line(label, val, ic):
            return f'<div><dt>{F.icon(ic)}{e(label)}</dt><dd>{e(val)}</dd></div>' if val else ""
        flags = [k for k in d["flags"].split() if (k != "p" or plan)]
        attrs = f'data-pd data-area="{e("|".join(_covered(raw)))}" data-pd-flags="{e(" ".join(flags))}"'
        main_price = f'{plan["name"]} {M._yen(plan)}' if plan else ""
        extra = [x.get("text") for x in raw.get("extra_fees", []) if isinstance(x,dict) and x.get("text") and x["text"] != "記載なし"]
        extras_from_plans = [f'{p["name"]} {M._yen(p)}' for p in billed if p not in plans]
        extras_from_plans += [p["extra"] for p in plans if p.get("extra")]
        extra = list(dict.fromkeys(extras_from_plans + extra))
        details = []
        if plans:
            details.append('<ul>' + ''.join(f'<li>{e(p["name"])} {e(M._yen(p))}'+(f'：{e(p["includes"])}' if p.get("includes") else '')+'</li>' for p in plans[:5])+'</ul>')
        if extra: details.append('<p><b>追加費用：</b>'+e("／".join(extra))+'</p>')
        if comp.get("total"): details.append('<p><b>合計の例：</b>'+e(comp["total"])+'</p>')
        if raw.get("near_note"): details.append('<p>'+e(raw["near_note"])+'</p>')
        if d["methods"]: details.append('<p><b>捜索の方法：</b>'+e(d["methods"])+'</p>')
        if comp.get("reception"): details.append('<p>'+e(comp["reception"])+'</p>')
        if comp.get("src") and comp.get("checked") and exists_uri(comp["src"]):
            details.append(f'<p><a href="{e(comp["src"])}">現地入りの出典</a>（{e(comp["checked"])}時点）</p>')
        more = f'<details><summary>詳しく見る</summary>{"".join(details)}</details>' if details else ""
        rows.append(f'<article class="pd-card" {attrs}><h2>{e(d["name"])}</h2><dl>'
                    +line("対応地域",raw.get("area") if raw.get("area") not in (None, "", "記載なし") else "出張範囲は依頼前に相談","pin")
                    +line("対象",d["animals"],"paw")+line("料金の例",main_price,"yen")
                    +line("現地入り",comp.get("arrival"),"clock")
                    + '</dl>'+more+f'<a class="pd-official" href="{e(raw["url"])}" rel="noopener">公式サイトを開く</a></article>')
    opts = ''.join(f'<option value="{e(pref)}">{e(pref)}</option>' for pref in M.PREF47)
    title = "ペット探偵を探す｜対応地域・料金・現地入りを比較｜ペットのくらし窓口"
    desc = "迷子の犬・猫などのペット探偵を都道府県・対象動物で絞り込み。捜索料金と追加費用、現地入りの目安を比較できます。"
    url=site+PATH
    s=f"""<main>
<section class="area-hero pd-hero"><div class="wrap">
<nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットのくらし窓口</a> › ペット探偵</nav>
<h1>ペット探偵を探す</h1>
<p class="pd-help">届け出がまだなら、<a href="{GUIDE}">迷子になったときの初動と地域の届け先</a>へ。</p>
</div></section>
<section class="pd-layout"><div class="wrap">
<form class="pd-filter" id="pd-filter" aria-label="ペット探偵を絞り込む">
<div class="pd-selects"><label>いなくなった都道府県<select id="pd-pref"><option value="">すべて</option>{opts}</select></label>
<label>ペットの種類<select id="pd-animal"><option value="">すべて</option><option value="dg">犬</option><option value="ct">猫</option><option value="ex">鳥・小動物など</option></select></label></div>
<div class="pd-options"><label><input type="checkbox" id="pd-price">料金を公開</label><label><input type="checkbox" id="pd-eta">現地入りの目安あり</label></div>
</form>
<p class="pd-result" id="pd-result" aria-live="polite"></p>
<p class="pd-empty" id="pd-empty" hidden>一致する掲載が見つかりません。条件を減らすか、<a href="{GUIDE}">地域の届け先</a>をご確認ください。</p>
<noscript><p class="pd-nojs">絞り込みを使うにはJavaScriptを有効にしてください。一覧は下で読めます。</p></noscript>
<div class="pd-grid">{''.join(rows)}</div>
</div></section>
<section class="pd-after"><div class="wrap">
<h2>依頼する前に確かめること</h2>
<p>受付時間と、実際に現地へ来られる時刻は別です。開始時刻・捜索時間・出張費・成功報酬・キャンセル料まで含めた総額をお尋ねください。</p>
<p>ペット保険の付帯サービスで無料になる場合があります。有料で依頼する前に、<a href="{GUIDE}#pro-insurance">保険の対象条件</a>も確認してください。掲載順はおすすめ順ではありません。</p>
</div></section></main>
<script src="/pet-detective/filter.js" defer></script>
"""
    return ctx["head"](title,desc,url,"").replace("</head>",CSS+"</head>",1)+F.sprite_for(s)+s+ctx["foot_noband"]()

def write_all(root, ctx):
    p = Path(root) / PATH.strip("/")
    p.mkdir(exist_ok=True)
    (p/"index.html").write_text(page(ctx),encoding="utf-8")
    (p/"filter.js").write_text(Path(__file__).with_name("pet_detective.js").read_text(encoding="utf-8"),encoding="utf-8")

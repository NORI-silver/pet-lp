"""カードの「カード払い」「日曜も」の印を、カードに書いてある文の肯定の根拠だけから決める（純粋な関数）。
書いていない・あいまい・打ち消し・調整中は印を付けない（「分からない」のまま。否定の印にはしない）。
"""
import re

_CARD = re.compile(r"クレジット|カード|VISA|Visa|MasterCard|Master|JCB|Amex|AMEX|アメックス")
_NOT_CREDIT = re.compile(r"ポイントカード|スタンプカード|会員カード|診察カード|カード情報|情報")
_NEG = re.compile(r"現金のみ|現金だけ|不可|できません|できない|いただけません|頂けません|なれません|使えません|使えない|利用できません"
                  r"|対応しておりません|対応していません|対応しません|非対応|導入準備|導入検討|導入予定|調整中|検討中|準備中|予定")
_SPLIT = re.compile(r"[。！!\n／/※\s　]+")


def card_ok(pay_values):
    """支払いの行の文のうち、カード払いができると書いてある（打ち消しのない）文が1つでもあるときだけ True。
    キャッシュレス・電子マネー・QRだけではカード払いにしない。"""
    for v in pay_values:
        for frag in _SPLIT.split(v or ""):
            if not frag or not _CARD.search(frag) or _NOT_CREDIT.search(frag.replace("クレジットカード情報", "情報")) and not re.search(r"クレジット|VISA|Visa|Master|JCB", frag):
                continue
            if "情報" in frag: continue
            if _NEG.search(frag): continue
            return True
    return False


_WD = r"[月火水木金土]"
_SUN_CLOSED = re.compile(r"日曜|日祝|(?<![曜月火水木金土0-9０-９])日(?=[・、,/祝\s]|$)")
_ALWAYS_OPEN = re.compile(r"^(なし|無し)$|年中無休|無休|定休日?[：:\s]*なし|休み[：:\s]*なし|休業日?[：:\s]*なし|定休なし|不定休なし")
_UNSURE = re.compile(r"不定|カレンダー|お問合|お問い合|要確認|応相談|ご確認|他[\s）)」]*$|他に|など|等")
# 営業時間の文に、日曜も営業すると読める書き方
_SUN_OPEN = re.compile(r"(月\s*[〜~\-ー－]\s*日|毎日|土日祝?|土・日|日曜日?・?祝?日?(?:は|も)?\s*(?:各)?[0-9０-９]{1,2}\s*[:：時]|日曜日?は各|日・祝.{0,6}[0-9０-９]{1,2}\s*[:：時])")
_SUN_SHUT = re.compile(r"日[曜日・祝\s]*[\]］】)）]?\s*(?:を)?除く|日曜[日]?.{0,3}以外|平日のみ|日曜[日]?[\s・、]*(?:定休|休み|休業|お休み|休診)|日祝[定休]|日・祝[定休]|(?:定休|休み|休業)[日]?[：:\s]*[^。]*日曜")


def sunday_ok(rows):
    """rows: (ラベル, 値, _)。日曜も営業すると読める根拠があるときだけ True。
    臨時休業の注記は通常の営業日を消さない。通常の営業・休みが読み切れないときは付けない。"""
    hol = [(l, v) for l, v, _ in rows if re.search(r"休", l)]
    hours = [v for l, v, _ in rows if re.search(r"時間|営業|受付", l) and not re.search(r"休", l)]
    inline = []
    for l, v in hol:
        m = re.search(r"(営業時間[^/／]*?)\s*[/／]\s*(?:\[?定休日\]?)", v)
        if m: inline.append(m.group(1))
    hours += inline
    allv = " ".join(hours) + " " + " ".join(v for _, v in hol)
    if _SUN_SHUT.search(allv): return False
    closed = []
    for l, v in hol:
        c = re.sub(r"\(※[^)]*\)|（※[^）]*）|※.*$|＊.*$", "", v)
        c = re.sub(r"[（(][^）)]*[）)]", lambda m: "" if re.search(r"祝|例外|場合|月[0-9１-９]回|臨時|研修|年に", m.group(0)) and not re.search(r"定休", m.group(0)) else m.group(0), c)
        c = re.sub(r"[（）()【】\[\]〇◇＊*]", " ", c)
        if "定休日" in c:
            left, right = c.split("定休日", 1) if c.count("定休日") == 1 else (c.rsplit("定休日", 1)[0], c.rsplit("定休日", 1)[1])
            c = right if re.sub(r"[\s:：.\-●]", "", right) else left
        c = re.sub(r"^[\s:：.\-●]*", "", c).strip()
        closed.append(c)
    # 臨時休業・年末年始の注記は、通常の週の営業を消さない（通常の書き方がはっきりあるときだけ別に判断する）
    reg = [c for c in closed if not re.search(r"臨時", c)]
    if hol and not reg:
        return False
    for c in reg:
        if _ALWAYS_OPEN.search(c) and not re.search(r"不定|カレンダー", c): return True
    if any(_SUN_CLOSED.search(c) for c in reg): return False
    # 営業時間の文に日曜の営業がはっきり書いてあれば、不定休・臨時休業の注記があっても通常の営業は消さない
    if any(_SUN_OPEN.search(h) for h in hours): return True
    # 休みの曜日の一覧と毎日の営業時間だけでは、日曜も営業とは決めない（書いていないことは「分からない」のまま）
    return False

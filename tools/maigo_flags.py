"""迷子探偵の絞り込み印のうち、書いてある事実の判定（元は tools/maigo_private.json の1社ぶん）。

- キャンセル: 実際のキャンセル条件（料金・返金なし・無料の期間など）が書いてあるときだけ。
  「記載なし」「別ページ（未確認）」のような、書いていない・確かめていない印は条件にしない。
- 別途の費用: 本体の料金とは別に払うものが書いてある項目があるときだけ。
  「〜込み」「〜にふくむ」「目安・変動」「営業時間」だけの項目は別途の費用にしない（別途の費用の文言があれば残す）。
"""
import re

NO_INFO = {"記載なし", "別ページ（未確認）"}
_INCLUDED = re.compile(r"込み|にふくむ|ふくむ|含む|変動|営業時間")
_SEPARATE = re.compile(r"別|加算|個別見積|追加|実費")


def has_cancel(d):
    c = d.get("cancel")
    if isinstance(c, list):
        return any(isinstance(x, dict) and (x.get("when") or x.get("yen") is not None) for x in c)
    if isinstance(c, str):
        t = c.strip()
        return bool(t) and t not in NO_INFO and "未確認" not in t
    q = d.get("cancel_quote")
    return isinstance(q, str) and bool(q.strip())


def fee_item_is_separate(x):
    if not isinstance(x, dict):
        return False
    t = (x.get("text") or "") + (x.get("what") or "")
    if not t.strip() and x.get("yen") is None:
        return False
    if _INCLUDED.search(t) and not _SEPARATE.search(t):
        return False
    return True


def has_separate_fee(d):
    ef = d.get("extra_fees")
    return isinstance(ef, list) and any(fee_item_is_separate(x) for x in ef)


METHODS = {
    "mc": ("捜索用カメラ", r"カメラ"),
    "mt": ("捕獲器の設置", r"捕獲[器機]|サークルトラップ"),
    "mf": ("チラシ・ポスター", r"チラシ|ポスター|ポスティング"),
}

def method_keys(d):
    keys = []
    if not (d.get("facts_src") or d.get("src")):
        return keys
    for key, (_, rx) in METHODS.items():
        if any(re.search(rx, row) and not re.search(r"貸し出し|レンタル|使わない|不可|行わない", row)
               for row in (d.get("methods") or []) if isinstance(row, str)):
            keys.append(key)
    return keys

"""施設と市区町村の座標（国土地理院の住所検索で取得した tools/geo.json）。

半径で絞る・距離の目安に使う。施設の住所が分かればその地点（F:ファイル:id）、
分からなければ市区町村の中心（C:県+市区町村）で代用する。座標は目安であり、
施設の正確な位置を保証しない（カードには data-geo="c" の印だけ付け、市区町村中心の
場合は絞り込みを緩めに扱う判断は表示側に任せる）。
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
_GEO = None


def _load():
    global _GEO
    if _GEO is None:
        p = os.path.join(HERE, "geo.json")
        _GEO = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return _GEO


def city_ll(pref, city):
    if not pref or not city:
        return None
    return _load().get(f"C:{pref}{city}")


def facility_ll(fname, rec):
    """施設レコードの座標 [lat, lng] と精度（"f"=住所の地点、"c"=市区町村の中心）。"""
    g = _load()
    rid = rec.get("id")
    if rid:
        ll = g.get(f"F:{fname}:{rid}")
        if ll:
            return ll, "f"
    pref = rec.get("pref") or (rec.get("prefs") or [None])[0]
    return city_ll(pref, rec.get("city")), "c"

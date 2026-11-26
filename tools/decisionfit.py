"""Comparison rows and search keys share the same facility-specific evidence."""
import html
import re

# Key, owner-facing label, accepted facts, positive wording (not menu/FAQ mentions).
RULES = {
    "dog-trainer": [
        ("lesson_owner", "飼い主と一緒に練習", ("しつけの方法", "方法", "料金", "提供内容"), r"飼い主[^。]{0,18}(?:と一緒|も参加|参加型)"),
        ("lesson_trial", "体験レッスンあり", ("初回・体験", "料金", "提供内容"), r"体験レッスン|体験教室"),
    ],
    "pet-sitter": [
        ("home_nursing", "訪問介護を頼める", ("料金", "ほかのサービス", "お世話", "提供内容"), r"訪問介護"),
    ],
    "trimming": [
        ("groom_age_flex", "年齢上限なし（体調は要確認）", ("受け入れ条件", "犬・猫・大きさ", "内容"), r"年齢(?:の)?(?:上限|制限)(?:は)?(?:なし|無し|ありません)|年齢制限を設けていません"),
        ("groom_adapt", "休憩または短時間の施術", ("施術の配慮", "受け入れ条件", "内容"), r"休憩を(?:挟|はさ|取り|入れ)|短時間で(?:施術|シャンプー|カット)|寝たまま(?:施術|洗)"),
    ],
    "rojin-home": [
        ("life_stay", "生涯預かりを相談できる", ("介護", "受け入れ条件", "預かり", "料金", "お世話"), r"(?:終生|生涯|終身)[^。、]{0,12}(?:預か|プラン|一括|契約)|(?:預かり|入所)[^。、]{0,8}(?:終生|生涯|終身)"),
    ],
    "pet-hotel": [
        ("family_room", "同じ家の子と同室", ("料金", "部屋", "受け入れ条件", "内容"), r"(?:家族|頭目|匹|頭|多頭)[^。]{0,10}同室|同室[^。]{0,18}(?:頭目|匹目|多頭)|家族ごとの個室"),
    ],
}
DISPLAY = {
    "rojin-home": ("受け入れ条件", "体制", "介護", "お預かり中の報告", "ふくまれるお世話", "病院", "別料金", "部屋"),
    "dog-trainer": ("しつけの方法", "対象の犬", "初回・体験", "出張費"),
    "pet-sitter": ("訪問介護", "お世話", "初回・契約", "交通費・出張費", "出張費", "追加料金"),
    "trimming": ("受け入れ条件", "犬・猫・大きさ", "施術の配慮", "送迎", "出張費"),
    "pet-hotel": ("受け入れ条件", "部屋", "夜間スタッフ", "お世話", "預かり期間", "別料金"),
}
NEG = re.compile(r"不可|対象外|お断り|非対応|できません|できない|ありません|行っていません|受け(?:付け)?ていません|受けておりません|終了|休止|中止|なし")

def options(cat):
    return [(key, label) for key, label, _, _ in RULES.get(cat, ())]

def evidence(cat, r):
    out = {}
    facts = [(f["k"], f["v"]) for f in r.get("facts", [])
             if f.get("k") and isinstance(f.get("v"), str)
             and f.get("src") and f.get("checked")]
    if r.get("url") and r.get("checked") and r.get("services"):
        field = "提供内容" if cat in ("dog-trainer", "pet-sitter") else "内容"
        facts.append((field, r["services"]))
    for key, label, fields, rx in RULES.get(cat, ()):
        for field, value in facts:
            if field not in fields: continue
            src = [s.strip() for s in re.split(r"[。\n／]", value) if re.search(rx, s)]
            if not src: continue
            if any(NEG.search(re.sub(rx, "", s) if key == "groom_age_flex" else s) for s in src):
                out[key] = (2, label, "")
                break
            if key not in out:
                out[key] = (1, label, "。".join(src[:2]))
    return out

def rows(cat, r):
    found = evidence(cat, r)
    return [(label, value) for status, label, value in found.values() if status == 1]


def attrs(cat, record):
    states = evidence(cat, record)
    return "".join(f' {attr}="{html.escape(" ".join(keys))}"'
                   for attr, status in (("data-decision", 1), ("data-decision-no", 2))
                   if (keys := [key for key, v in states.items() if v[0] == status]))

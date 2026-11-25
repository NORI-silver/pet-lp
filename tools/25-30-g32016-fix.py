import json
P='tools/vet_clinics.json'
d=json.load(open(P,encoding='utf-8'))
for c in d['clinics']:
    if c['id']=='G32016':
        assert c['addr']=='島根県益田市乙吉町イ463-1' and c['name']=='ペットクリニック'
        c['name']='益田ペットクリニック'; c['tel']='0856-22-8911'; c['url']='https://www.iwami.or.jp/pluswan/'; c['src']='https://www.iwami.or.jp/pluswan/'; c['tel_src']='https://www.iwami.or.jp/pluswan/'; c['checked']='2026-11-26'
        # animals は空のまま（要確認）。島根県獣医師会の一覧は「犬、猫」とあるが、日常の診療対象の言い切りにはしない
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('G32016 corrected')

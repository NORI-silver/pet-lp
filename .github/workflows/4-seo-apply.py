import json,sys
P=json.load(open(sys.argv[1],encoding='utf-8'))
REN={('S33db8a','設備'):'設備のくわしく',('S33db8a','月例法要'):'月例法要の日程',('Saf555c','そのほか'):'費用の注意',('S495b9e','立ち会い'):'告別式・供養'}
def load(p): return json.load(open(p,encoding='utf-8'))
def save(p,d): open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=1)+"\n")
R=load('tools/rojin.json'); h={x['id']:x for x in R['homes']}; n=0
for i,fs in P['rojin'].items():
    x=h[i]; cur=x.setdefault('facts',[]); ks={f['k'] for f in cur}
    for f in fs:
        assert f['k'] not in ks,(i,f['k']); cur.append(f); n+=1
save('tools/rojin.json',R); print('rojin facts added',n)
S=load('tools/sougi_facilities.json'); f={x['id']:x for x in S['facilities']}; m=0
for i,ms in P['sougi'].items():
    x=f[i]; cur=x.setdefault('more',[]); ks={a['k'] for a in cur}
    for a in ms:
        a=dict(a)
        if a['k']=='電話': continue  # 電話番号は載せない（データの決まり）
        a['v']=a['v'].replace('。電話 055-280-8322','')
        a['k']=REN.get((i,a['k']),a['k']); assert a['k'] not in ks,(i,a['k']); cur.append(a); m+=1
    x['checked']='2026年11月26日'
save('tools/sougi_facilities.json',S); print('sougi more added',m)
s=open('tools/gen_rojin.py',encoding='utf-8').read()
a='''    total = len(J["homes"])
'''
assert s.count(a)==1
s=s.replace(a,'''    shown = [h for _lab, _prefs in ctx["emg_regions"] for _pf in _prefs for h in rows.get(_pf, [])]
'''+a)
b='''      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\\n</script>"'''
assert s.count(b)==1
nb='''      {"@context": "https://schema.org", "@type": "ItemList", "name": H1, "numberOfItems": len(shown),
       "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": h["name"], "url": h["url"]} for i, h in enumerate(shown[:100])]},
'''+b.replace('ensure_ascii=False, indent=1)','ensure_ascii=False, separators=(",", ":"))')
s=s.replace(b,nb)
open('tools/gen_rojin.py','w',encoding='utf-8').write(s); print('gen_rojin patched')

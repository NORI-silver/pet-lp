# 一時の補助（愛知ドッグトレーナーの写真を入れる）。使い終わったら消す。
import json,io,os,hashlib,sys,urllib.request,urllib.parse
from PIL import Image,ImageStat
from concurrent.futures import ThreadPoolExecutor
D=json.load(open('tools/b2_data.json'))
def shrink(raw):
    im=Image.open(io.BytesIO(raw));im.load()
    if im.width<480 or im.height<300: raise ValueError('small')
    r=im.width/im.height
    if not(0.6<=r<=3.0): raise ValueError('ratio')
    im=im.convert('RGB')
    s=min(1.0,900/max(im.size));im=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
    b=io.BytesIO();im.save(b,'WEBP',quality=70,method=6);return b.getvalue()
def get(u):
    u=urllib.parse.quote(u,safe="%/:?&=#+@;,~!*'()$\\[]")
    for _ in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read()
        except Exception as e: err=e
    raise err
jobs=[(d['id'],k,p) for d in D for k,p in enumerate(d['photos'],1)]
def work(j):
    i,k,p=j
    try: return j,shrink(get(p[0])),''
    except Exception as e: return j,None,str(e)[:80]
with ThreadPoolExecutor(8) as ex: res=list(ex.map(work,jobs))
raw={(j[0],j[1]):b for j,b,e in res if b}
print('images ok',len(raw),'of',len(jobs),[ (j[0],j[1],e) for j,b,e in res if not b])
ph=json.load(open('tools/photos.json'));pp=json.load(open('tools/photo_permits.json'));man=json.load(open('tools/curated_tokyo_small.json'))
have={(x['cat'],x['id']) for x in ph['items']}
os.makedirs('img/fac/trainer',exist_ok=True);os.makedirs('img/fac/sitter',exist_ok=True)
added=0
for d in D:
    cat=d.get('cat','trainer')
    if (cat,d['id']) in have: continue
    files=[];ratios=[];m=[]
    for k,p in enumerate(d['photos'],1):
        b=raw.get((d['id'],k))
        if not b: continue   # 取れなかった写真は入れない（番号を詰める）
        n=len(files)+1;fn=f"img/fac/{cat}/{d['id']}_{n}.webp";open(fn,'wb').write(b)
        im=Image.open(io.BytesIO(b));files.append('/'+fn);ratios.append(round(im.width/im.height,3))
        m.append(dict(id=d['id'],file=fn,src=p[0],page=p[1],sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
    if not files: continue
    man+=m;added+=1
    ph['items'].append(dict(cat=cat,id=d['id'],name=d['name'],url=d['url'],by='permit',src='2026-11-24',checked='2026-11-24',photos=files,credit='写真：'+d['name'],ratio=ratios))
    pp['permits'].append(dict(cat=cat,id=d['id'],name=d['name'],scope='公式サイトの写真（ユーザー指示）',by='ユーザー（塩田）の指示',date='2026-11-24',ref='2026-11-24 ユーザー（塩田）が「許可は全部出てる」と伝達（WhatsApp 1:22）。事業者ごとの許可書ではない',credit='写真：'+d['name']))
print('operators added',added)
json.dump(ph,open('tools/photos.json','w'),ensure_ascii=False,indent=1);json.dump(pp,open('tools/photo_permits.json','w'),ensure_ascii=False,indent=1);json.dump(man,open('tools/curated_tokyo_small.json','w'),ensure_ascii=False,indent=1)

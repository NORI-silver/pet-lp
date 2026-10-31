#!/usr/bin/env python3
"""ガイドの記事・リンク・目次・画像・構造化データの整合を検査する（通信・送信なし）。"""
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from guides import GUIDES

ROOT = Path(sys.argv[1] if len(sys.argv)>1 else '.')
SITE = 'https://pet.shiokonbu.com'

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links=[]; self.ids=set(); self.images=[]; self.metas={}; self.ld=[]
        self.h1=[]; self._h1=False; self.h2=[]; self._h2=None; self._json=False; self._buffer=[]
        self._skip=0; self.visible=[]; self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='img': self.images.append(a)
        if tag=='meta': self.metas[a.get('property') or a.get('name')]=a.get('content')
        if tag=='h1': self._h1=True
        if tag=='h2': self._h2=a.get('id'); self.h2.append(self._h2)
        if tag in ('script','style'): self._skip+=1
        if tag=='script' and a.get('type')=='application/ld+json': self._json=True; self._buffer=[]
    def handle_data(self,text):
        if self._h1: self.h1.append(text)
        if self._json: self._buffer.append(text)
        if not self._skip: self.visible.append(text)
    def handle_endtag(self,tag):
        if tag=='h1': self._h1=False
        if tag=='script' and self._json:
            self.ld.append(json.loads(''.join(self._buffer)));self._json=False
        if tag in ('script','style'): self._skip-=1

def run():
    problems=[]; by={g['slug']:g for g in GUIDES}; incoming={s:set() for s in by}
    sitemap=(ROOT/'sitemap.xml').read_text(); hashes=set()
    import hashlib
    for g in GUIDES:
        slug=g['slug']; path=ROOT/'guide'/slug/'index.html'
        p=Page(path.read_text()); body=''.join(p.visible)
        def check(ok,msg):
            if not ok: problems.append(slug+': '+msg)
        check(''.join(p.h1)==g['title'],'H1と元データが不一致')
        check('すべての会社への予約依頼を停止しています' in body,'依頼停止の表示がない')
        check('ペットタクシーを予約する' not in body,'予約できる表示が残っている')
        check(bool(g['sources']),'出典がない')
        check(len(set(g['related']))==len(g['related']),'関連記事の重複')
        check(all(s in by and s!=slug for s in g['related']),'関連記事の行き先が不正')
        check(SITE+'/guide/'+slug+'/' in sitemap,'サイトマップから欠落')
        for i,_ in enumerate(g['sections'],1):
            check('section-'+str(i) in p.ids,'見出しアンカーがない')
            check('#section-'+str(i) in p.links,'目次から見出しへ移動できない')
        for href in p.links:
            u=urlsplit(href)
            if u.netloc and u.netloc!='pet.shiokonbu.com': continue
            if u.scheme and u.scheme not in ('http','https'): continue
            target=unquote(u.path) or '/guide/'+slug+'/'
            if not target.startswith('/'): continue
            fp=ROOT/target.lstrip('/')
            if target.endswith('/'): fp=fp/'index.html'
            check(fp.exists(),'内部リンク切れ '+href)
            if '/guide/' in target:
                s=target.strip('/').split('/')[-1]
                if s in incoming and s!=slug: incoming[s].add(slug)
                if u.fragment and fp.exists():
                    check(u.fragment in Page(fp.read_text()).ids,'見出しリンク切れ '+href)
        imagepath=ROOT/'img/guide'/g['img']
        check(imagepath.exists(),'JPEGがない')
        check(imagepath.with_suffix('.webp').exists(),'WebPがない')
        if imagepath.exists():
            h=hashlib.sha256(imagepath.read_bytes()).hexdigest()
            check(h not in hashes,'記事写真の使い回し');hashes.add(h)
        check(p.metas.get('og:image')==SITE+'/img/guide/'+g['img'],'共有画像が不一致')
        check(any(i.get('alt')==g['img_alt'] and i.get('width')=='1200' and i.get('height')=='800' for i in p.images),'画像の説明または寸法が不一致')
        articles=[x for x in p.ld if x.get('@type')=='Article']
        check(len(articles)==1,'Article構造化データが不正')
        if articles:
            a=articles[0]
            check(a['headline']==g['title'] and a['description']==g['desc'],'構造化データの本文情報が不一致')
            check(a['author'].get('name')=='ペットタクシー予約窓口','編集者の情報が不明')
            check(date.fromisoformat(a['dateModified'])>=date.fromisoformat(a['datePublished']),'更新日が公開日より前')
            check(set(a['citation'])=={u for _,u in g['sources']},'出典の構造化データが不一致')
        faqs=[x for x in p.ld if x.get('@type')=='FAQPage']
        if faqs:
            for q in faqs[0]['mainEntity']:
                check(q['name'] in body and q['acceptedAnswer']['text'] in body,'FAQ構造化データと表示が不一致')
    for s,ins in incoming.items():
        if not ins:problems.append(s+': 他の記事からリンクがない')
    hub=Page((ROOT/'guide/index.html').read_text())
    for s in by:
        if '/guide/'+s+'/' not in hub.links:problems.append('一覧から欠落: '+s)
    lists=[x for x in hub.ld if x.get('@type')=='ItemList']
    if len(lists)!=1 or lists[0]['numberOfItems']!=len(GUIDES):problems.append('一覧の構造化データ件数が不一致')
    for problem in problems:print('NG:',problem)
    print(f'{len(GUIDES)}記事：内部リンク・目次・固有画像・出典・FAQ・構造化データを確認。NG {len(problems)}件')
    return 1 if problems else 0

if __name__=='__main__':sys.exit(run())

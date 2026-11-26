const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const test = require('node:test');
test('insurance comes before paid search; only sourced arrival notes and grooming accommodations get filter keys', () => {
 const code = `
import sys, html
sys.path.insert(0,'tools')
import gen_maigo as M, gen_grooming as G, decisionfit as D
h=M.maigo({'e':html.escape,'SITE':'https://pet.shiokonbu.com','head':lambda *_:'<html><head></head><body>','foot_noband':lambda:'</body></html>'})
assert h.index('id="pro"') < h.index('id="pro-insurance"') < h.index('id="jcPro"')
insurance=h[h.index('id="pro-insurance"'):h.index('id="jcPro"')]
assert all(x in insurance for x in ('証券番号','先に依頼してからの適用はできません','2027年3月31日','4月1日以降','5日間','3日間の捜索・出張'))
rows=M.detectives()
assert len(rows)==31 and sum('eta' in d['flags'].split() for d in rows)==3
assert 'data-detf="eta"' in h and '89,800円＋交通費' in h and '30日以内' in h and '翌日以降' in h
assert 'eta' not in rows[1]['flags'].split()  # 24h受付は到着目安ではない
for id in ('Gt7a2b758','G-cherisia-tatsuno','G-felice-fukuhama'):
 r=next(x for x in G.J['groomers'] if x['id']==id)
 assert D.evidence('trimming',r)['groom_adapt'][0]==1
print('ok')
`;
 assert.equal(execFileSync(process.env.PYTHON||'python3',['-c',code],{encoding:'utf8'}).trim(),'ok');
});

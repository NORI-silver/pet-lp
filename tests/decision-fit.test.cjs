const test = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
test('new comparison filters and visible card rows come from the same provider record', () => {
  const script = `
import html, re, sys
sys.path.insert(0,'tools')
import decisionfit as D, faccard as F, gen_hotels, gen_sitters, gen_trainers, gen_rojin, gen_grooming, gen_maigo, maigo_flags, uikit

def check(cat, records, rid, render, key, detail):
    r=next(x for x in records if x['id']==rid)
    assert key in D.evidence(cat,r)
    out=F.build_card(render(html.escape,r),F.CATS[cat],{}).split('class="fc-fit"')[0]
    assert detail in out and 'data-decision="' in out, out[:1800]
    tag=out.split('>',1)[0]+'>'
    if cat!='pet-hotel':
        assert key in uikit._keys(tag,cat,r['url'])[0]
check('pet-hotel',gen_hotels.J['hotels'],'PH035',gen_hotels._card,'family_room','2匹同室利用時＋1,000円')
check('pet-sitter',gen_sitters.J['sitters'],'S175',gen_sitters._card,'home_nursing','訪問介護60分4,800円')
check('pet-sitter',gen_sitters.J['sitters'],'Snk019',gen_sitters._card,'home_nursing','おむつ交換や体位を変えるお手伝い')
check('dog-trainer',gen_trainers.J['trainers'],'T164',gen_trainers._card,'lesson_owner','飼い主さんと一緒に行う')
check('rojin-home',gen_rojin.J['homes'],'R055',gen_rojin._card,'life_stay','寝たきり・障害のある犬を生涯預かり')
check('trimming',gen_grooming.J['groomers'],'Gnk001',gen_grooming._card,'groom_age_flex','シニアも体調に合わせて')
assert not D.evidence('trimming',{'facts':[{'k':'駐車場','v':'短時間で施術','src':'https://example.com/','checked':'2026-11-26'}]})
assert not D.evidence('pet-sitter',{'facts':[{'k':'料金','v':'訪問介護'}]})
assert D.evidence('pet-sitter',{'facts':[{'k':'料金','v':'訪問介護は対象外','src':'https://example.com/','checked':'2026-11-26'}]})['home_nursing'][0]==2
assert not D.evidence('pet-hotel',{'facts':[{'k':'お世話','v':'夜間もオーナーと同室','src':'https://example.com/','checked':'2026-11-26'}]})
assert maigo_flags.method_keys({'src':'https://example.com','methods':['捕獲機・トレイルカメラの貸し出し'],'area_quote':'24時間全国対応'})==[]
assert any('mt' in d['flags'].split() and '捕獲器' in d['methods'] for d in gen_maigo.detectives())
print('ok')
`;
  assert.equal(execFileSync(process.env.PYTHON||'python3',['-c',script],{encoding:'utf8'}).trim(),'ok');
});

// 料金が「例だけ」（budget_example_only）の施設を、全国の真ん中・県ごとの幅に入れないことを確かめる。
// 区分・税・含まれるものが施設ごとにちがう「例」を並べて、比べられる相場に見せないため。
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('fs');
const {execFileSync}=require('node:child_process');
test('budget_example_only facilities stay out of national medians and prefecture ranges',()=>{
 const script=`import sys, json
sys.path.insert(0, 'tools')
import guides_sougi as gs, gen_prefcats as pc
F = gs._FAC
flag = [f for f in F if f.get('budget_example_only') and f.get('price')]
assert len(flag) >= 19, len(flag)
cmp_ = [f for f in F if not f.get('budget_example_only')]
assert gs._P == [gs._prices(f.get('price')) for f in cmp_]
assert gs.N_MED == sum(1 for f in cmp_ if f.get('price')) and gs.N_MED + len(flag) == gs.N_PRICED
# 例だけの施設を全部足すと、真ん中が動く（除外が効いている）
allp = [gs._prices(f.get('price')) for f in F]
import statistics as st
for t, S in (('kobetsu', gs.SK), ('tachiai', gs.ST), ('goudou', gs.SG)):
    v_all = sorted(g[t] for g in allp if t in g); v_cmp = sorted(g[t] for g in gs._P if t in g)
    assert S['n'] == len(v_cmp) < len(v_all), (t, S['n'], len(v_cmp), len(v_all))
    assert S['med'] == f"{int(st.median(v_cmp)):,}円"
# 県の幅も同じ
chiba = [f for f in F if f['pref'] == '千葉県']
for lab, n, rng, med in pc._price_lines(chiba):
    k = {'個別火葬（おまかせ）': 'kobetsu', '立ち会い火葬': 'tachiai', '合同火葬': 'goudou'}[lab]
    v = sorted(g[k] for g in (gs._prices(f.get('price')) for f in chiba if not f.get('budget_example_only')) if k in g)
    assert n == len(v) and rng == f"{v[0]:,}円〜{v[-1]:,}円", (lab, n, rng)
print('ok')
`;
 const out=execFileSync('python3.12',['-c',script],{encoding:'utf8'});
 assert.match(out,/ok/);
 // カードの料金の例そのものは消さない
 const d=JSON.parse(fs.readFileSync('tools/sougi_facilities.json','utf8')).facilities;
 for(const id of ['Sb22bec','S4ba28d','Sbd4890']){const f=d.find(x=>x.id===id);assert.ok(f.price&&f.budget_example_only,id);}
 // 生成されたページの「N施設」は、真ん中に入れた施設の数（料金の例だけの施設を除く）
 const g=fs.readFileSync('guide/pet-cremation-types/index.html','utf8');
 const nmed=JSON.parse(execFileSync('python3.12',['-c',"import sys,json;sys.path.insert(0,'tools');import guides_sougi as g;print(json.dumps(g.N_MED))"],{encoding:'utf8'}));
 assert.ok(g.includes('全国'+nmed+'施設の公式サイトの料金'),'guide states the median basis count');
});

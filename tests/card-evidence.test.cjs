const test=require('node:test'), assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
test('confirmed card data does not turn limitations, FAQs or surcharges into matches',()=>{
const py=`
import sys,re,html
sys.path.insert(0,'tools')
import gen_hotels,ownerfit,faccard,uikit,gen_sitters,gen_sougi,facility_cards
h=next(h for h in gen_hotels.J['hotels'] if h['id']=='PHt475672a')
yes,no=ownerfit.keys('pet-hotel',h['url'])
assert 'big' in yes and not {'sen','med','pup','staff24'}.intersection(yes)
assert {'staff24','night_staff'} <= set(no)
out=faccard.build_card(gen_hotels._card(html.escape,h),faccard.CATS['pet-hotel'],{}).split('class="fc-fit"')[0]
assert all(x in out for x in ('9,900円','11,000円','8歳未満','スタッフ不在','動物取扱業'))
assert ownerfit._find('大型駐車場完備','big')==0
assert 'big' not in uikit._keys(" data-fit='{\\\"s\\\":[\\\"l\\\"]}'>",'dog-trainer','https://kitanodog.com/')[0]
sf=next(s for s in gen_sougi.F['facilities'] if s['id']=='S105757')
yes,no=ownerfit.keys('sougi',sf['u'])
assert 'call24' in no and '深夜・早朝も受付' not in facility_cards.sougi_tags(sf)
assert '電話受付9:00〜17:00' in gen_sougi._fcard(html.escape,sf)
sit=next(s for s in gen_sitters.J['sitters'] if s['id']=='S175')
assert faccard._yen_of(sit)==4700 and '訪問介護60分4,800円' in gen_sitters._card(html.escape,sit)
assert 'big' in ownerfit.keys('trimming','https://www.dogsalon-purumo.com/')[1]
print('ok')`;
const text=execFileSync(process.env.PYTHON || 'python3',['-c',py],{encoding:'utf8'});
assert.equal(text.trim(),'ok');
});

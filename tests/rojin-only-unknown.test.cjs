// 老犬ホームの「その動物だけ」判定（data-fit の o → data-no＝断っている印）。
// 「要確認」（分からない）や「など」（例）は断った印にしてはいけない。名前で言い切っているものは今まで通り。
const {test}=require('node:test'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
test('rojin only-flag: explicit-only stays, broad example and unknown do not', ()=>{
  const py=`
import sys
sys.path.insert(0,'tools')
import faccard
def f(t): return faccard.rojin_only(faccard._kinds_in(t), t)
assert f('犬のみ（大型犬30kgまで）') is True
assert f('猫だけ') is True
assert f('犬') is True
assert f('犬・猫') is True
assert f('犬・猫・小動物（うさぎ・鳥など）') is False
assert f('犬（ほかの動物は要確認）') is False
assert f('猫（ほかの動物は要確認）') is False
assert f('公式サイトに記載なし（老犬介護が中心）') is False
print('ok')`;
  assert.equal(execFileSync('python3',['-c',py],{encoding:'utf8'}).trim(),'ok');
});

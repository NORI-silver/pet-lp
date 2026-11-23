// [A] Avoid replacing the municipality's actual decisions with generic pet advice.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
const finder = JSON.parse(read('hinan/munis.json'));
const cms = [
  ['愛知県','半田市','ケージの持参が必要','開設先の状況','別の場所'],
  ['愛知県','犬山市','3施設','原則ケージ','楽田ふれあいセンター'],
  ['愛知県','愛西市','受け入れ','確認','確約されていません'],
  ['埼玉県','志木市','小・中学校','避難所として開いた','屋外'],
  ['千葉県','佐倉市','指定場所','リードでつなぎます','指定の場所'],
  ['宮崎県','延岡市','必ずケージに入れます','事前に避難先','リードだけでは'],
  ['香川県','丸亀市','屋外でつなげるか','避難所の状況','学校が避難所として開いた'],
  ['新潟県','関川村','必ずケージに入れます','開設先に確認','原則屋外'],
  ['新潟県','胎内市','ケージ持参','広さの確認','避難所ごと'],
  ['長野県','豊丘村','3校','係留場所に限り','豊丘北小'],
  ['新潟県','妙高市','県の条例','対象外','人とは別'],
  ['北海道','豊富町','受け入れ','事前の調整','事前の調整'],
  ['三重県','亀山市','安全・衛生','ケージなど','雨風をしのげる屋外'],
];
for (const [pref, name, answer, condition, place] of cms) {
  const row = finder[pref].find((m) => m[0] === name);
  assert.ok(row, name);
  assert.ok(['card', 'page'].includes(row[1]), name + ': destination');
  const items = row[7];
  assert.ok(items[4].includes(answer) && items[4].includes(condition), name + ': finder answer');
  assert.ok(items[2].includes(place), name + ': finder place');
  const file = row[2].split('#')[0].replace(/^\//, '') + 'index.html';
  const html = read(file);
  if (row[1] === 'page') {
    const top = html.split('id="uchinoko"')[1].split('id="detail"')[0];
    assert.ok(top.includes(answer) && top.includes(condition) && top.includes(place), name + ': top answers must agree with finder');
    if (['延岡市','関川村'].includes(name)) {
      assert.ok(!top.includes('リードでつないで過ごすのがふつう'), name + ': no tethering generalization');
      assert.ok(!top.includes('屋外につなぐことが多い'), name + ': no tethering preparation');
      assert.ok(top.includes('犬が入れるケージを準備する'), name + ': actionable cage prep');
      assert.ok(items[1].includes('必ずケージに入れます'), name + ': cage detail');
    }
    if (name === '愛西市') {
      assert.ok(!top.includes('ペットは人とは別の、屋外の場所'), name + ': not a guaranteed outdoor place');
      assert.ok(top.includes('受け入れ・場所は要確認'), name + ': no green acceptance');
    }
  } else {
    assert.ok(html.includes('id="' + name + '"'), name + ': prefecture card anchor');
    const card = html.split('id="' + name + '"')[1].split('</section>')[0];
    assert.ok(card.includes(name + 'の回答'), name + ': prefecture card keeps provenance');
  }
  if (['延岡市','関川村','半田市','胎内市','妙高市'].includes(name)) {
    assert.equal(row[5].charAt(6), '0', name + ': finder specific cage wording supersedes generic label');
  }
}
const izumo = read('joto/shimane/izumo-shi/index.html');
assert.ok(izumo.includes('譲渡前適正講習会') && izumo.includes('65歳未満') && izumo.includes('出雲保健所の回答'));
assert.ok(izumo.includes('出雲の募集状況と講習会'));
console.log(cms.length + ' municipality finder/page decisions and Izumo adoption: OK');

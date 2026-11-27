const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const test = require('node:test');

test('lost pet users can see what to do before leaving and local facts use matching sources', () => {
 const code = `
import sys, html
sys.path.insert(0,'tools')
import gen_maigo as M
h=M.maigo({'e':html.escape,'SITE':'https://pet.shiokonbu.com','head':lambda *_:'<html><head></head><body>','foot_noband':lambda:'</body></html>'})
report=h[h.index('id="report"'):h.index('id="jcR"')]
assert all(x in report for x in ('id="jcLocal"', 'id="jcReportText"', 'id="jcReportCopy"', 'id="jcReportStatus"', 'このサイトから提出はされません', 'href="#jcFly"', 'href="#pro"'))
assert 'href="https://' not in report
d=M.data('.',{'千葉県':'chiba','東京都':'tokyo','大阪府':'osaka'})
s=d['l']['千葉県佐倉市']
assert s['center'][0]=='千葉県動物愛護センター本所'
assert s['city'][0]=='佐倉市 生活環境課'
assert s['police'][0].startswith('佐倉警察署')
assert s['center'][2].endswith('/pets/animal-info.html')
assert '3,890円' in s['return'] and '600円' in s['return']
assert not any('電話0' in str(v) for v in s.values())
assert 'data-go-detective href="/pet-detective/"' in h
assert 'id="jcPro"' not in h and 'data-det-site' not in h
print('ok')
`;
 assert.equal(execFileSync(process.env.PYTHON||'python3',['-c',code],{encoding:'utf8'}).trim(),'ok');
});

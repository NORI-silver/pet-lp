#!/usr/bin/env node
// マッチング検査（Nori 2026-10-31「全事業者であらゆる組み合わせの入力があった時に絞り込めないポイントを事業者ごとにまとめて」）
//
// 予約フォームで入れられる組み合わせを全部つくり、全国の事業者に当てて、
//   ・正しく外せる（ng）／会社が引き受けるときに確かめる（ask）
//   ・分からないのに「軽バン」とみなして黙って外している（drop）
//   ・しくみが見ていないので、本当は受けられないのに候補に出てしまう（miss）
// を事業者ごと・観点ごとに数える。しぼりこみは booking/Code.gs の関数（fitsCar_・fitsCage_・checks_）をそのまま動かす。
// 事業者の情報はダッシュボードの companies.json（公式サイトに書いてあることだけ。公開リポジトリには置かない）から読む。
//
// 使い方：
//   node tools/match_audit.cjs --companies <companies.json> [--sheet <提携先タブの写し.json>] [--out <出力フォルダ>]
// 出力：audit.json（全部の結果）、audit.md（事業者ごとの一覧）、audit.html（表）、questions.json（問い合わせで聞く項目の候補）
// 事業者やお客さまには何も送らない（読むだけ・書き出すだけ）。
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : ''; };
const ROOT = path.join(__dirname, '..');
const COMPANIES = arg('companies') || '/mnt/project-files/dashboard/companies.json';
const SHEET = arg('sheet');
const OUT = arg('out') || '.';
const LIMIT = Number(arg('limit')) || 0; // 試しに数社だけ動かすとき

/* ───────── Code.gs を読み込む（テストと同じやり方） ───────── */
let sheetValues = [['ID']];
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite,
  SpreadsheetApp: { getActive: () => ({ getSheetByName: () => ({ getDataRange: () => ({ getValues: () => sheetValues }) }) }) } });
vm.runInContext(fs.readFileSync(path.join(ROOT, 'booking/Code.gs'), 'utf8'), ctx);
const fares = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/fares.json'), 'utf8')).companies;

/* ───────── サイトに出すかどうか（Nori 2026-10-31） ─────────
   除外：閉鎖・運営していない／公式サイトなし／会員制／ホテル・サロンの送迎だけ／重複の行
   輸送のときだけ：赤帽などペットの輸送をする会社（引っ越し・長距離など目的が輸送のときだけ出す）
   緊急タブだけ：救急搬送・往診（予約の候補には出さない） */
const BOOK_PREFS = ['東京都', '神奈川県', '埼玉県', '千葉県'];
function listing(c) {
  const t = [c.name, c.inactive, c.hotel, c.lic, c.note, c.op].join(' ');
  if (/閉鎖|停止|終了/.test(c.inactive)) return ['除外', '閉鎖・受付停止'];
  if (/公式サイトなし/.test(c.inactive)) return ['除外', '公式サイトなし（運営が確かめられない）'];
  if (/連絡先/.test(c.inactive)) return ['除外', '連絡先の記載なし'];
  if (/会員制/.test(c.inactive)) return ['除外', '会員制（一般の依頼は不可）'];
  if (/自社施設|ホテル送迎が中心/.test(c.inactive + c.hotel) || /^はい/.test(c.hotel)) return ['除外', 'ホテル・サロンの送迎だけ'];
  if (/チェーン全体|行を参照/.test(c.name)) return ['除外', '重複の行（店ごとの行で見る）'];
  if (/救急|往診|ドクターカー/.test(c.name) || /^いいえ（救急/.test(c.hotel)) return ['緊急タブだけ', '救急搬送・往診'];
  if (/赤帽|運送店|運送（|輸送/.test(c.name) || /赤帽/.test(c.lic)) return ['輸送のときだけ', 'ペットの輸送（赤帽など）'];
  if (/不明/.test(c.area) && /不明/.test(c.ch_group)) return ['除外', '対応エリアも窓口も分からない（運営が確かめられない）'];
  return ['候補', ''];
}

/* ───────── サイトの文章から、しぼりこみの値をつくる ───────── */
const unk = v => !v || /^(不明|サイトに記載あり|—|-|記載なし|未問い合わせ)/.test(String(v).trim());
const maxNum = (s, re) => { let m, best = null; const g = new RegExp(re.source, 'g'); while ((m = g.exec(s))) { const n = Number(m[m.length - 1]); if (best === null || n > best) best = n; } return best; };
function derive(c) {
  const f = {}, gaps = [];
  // 送迎できる時間（受付の時間しか書いていない会社は、送迎の時間は分からない）
  const h = String(c.hours || '');
  f.hoursText = unk(h) ? '' : h;
  f.rideHours = ''; f.hours = '';
  if (f.hoursText) {
    const r = ctx.toHalf_(h).match(/(\d{1,2})(?::\d{2})?\s*[-~〜～]\s*翌?\s*(\d{1,2})/);
    if (/受付\s*24/.test(h)) { f.hours = '0-24'; gaps.push(['時間', '受付は24時間と書いてあるが、送迎できる時間は分からない']); }
    else if (/24時間/.test(h)) f.rideHours = '0-24';
    else if (r && Number(r[2]) <= Number(r[1])) { gaps.push(['時間', '日をまたぐ営業時間（' + r[1] + '〜' + r[2] + '時）は、しくみの「8-18」形式で書けない（入れると昼が外れ、夜が通る）']); f.overnight = [Number(r[1]), Number(r[2])]; }
    else if (r) f.rideHours = r[1] + '-' + r[2];
    if (/時間外は相談|相談/.test(h)) gaps.push(['時間', '「時間外は相談」と書いてある（時間外の依頼は外れる）']);
  }
  // 人数・頭数
  const capT = [c.cap, c.ride, c.large_dog].filter(v => !unk(v)).join('／');
  f.riders = maxNum(capT, /(?:付添|付き添い|飼い主|同乗|定員)[^\d。／]{0,6}(?:\d〜)?(\d)\s*(?:名|人)/);
  if (f.riders === null) f.riders = maxNum(capT, /(\d)\s*(?:名|人)まで/);
  f.pets = maxNum(capT, /(?:犬|ペット|猫)\s*(?:\d〜)?(\d)\s*(?:頭|匹)/);
  if (f.pets === null) { const m = capT.match(/小型(\d)/); if (m) f.pets = Number(m[1]); }
  if (/大型犬は(\d)人/.test(capT)) gaps.push(['頭数×人数', '大型犬のときだけ人数が減る（' + capT.match(/大型犬は\d人/)[0] + '）。しくみは「大型犬の頭数と人数」の組み合わせを書く欄がない']);
  if (/小型\d・中型\d・大型\d/.test(capT)) gaps.push(['頭数', '犬の大きさで乗れる頭数が変わる（' + capT.match(/小型\d・中型\d・大型\d頭?/)[0] + '）。しくみは頭数を1つしか持てない']);
  // 大型犬
  const big = [c.large_dog, c.animals, c.cap, c.cars].join(' ');
  f.big = /大型犬(は)?(不可|お断り|NG)|小型犬のみ|小型・中型のみ/.test(big) ? false : /大型|小〜大/.test(big) ? true : null;
  f.maxKg = (() => { const m = big.match(/(\d{2,3})\s*kg\s*(まで|以下)/); return m ? Number(m[1]) : null; })();
  f.maxBig = (() => { const m = big.match(/大型(?:犬)?\s*(\d)\s*頭/); return m ? Number(m[1]) : null; })();
  // ペットだけ
  const po = [c.pet_only, c.ride].join(' ');
  f.petOnly = /^可|ペットだけ(も)?可|ペットだけもOK/.test(po) || /^可/.test(c.pet_only) ? true : /^不可|ペットだけは不可|必須/.test(po) ? false : null;
  // ケージ
  const cg = unk(c.cage) && !/^不明（/.test(c.cage) ? '' : String(c.cage);
  f.cageText = cg;
  f.cageMust = /^不要|ケージなしで乗れる/.test(cg) ? '×' : /ケージ内|必須|必ず/.test(cg) ? '○' : '';
  if (cg && !f.cageMust) gaps.push(['ケージ必須', '「' + cg.slice(0, 40) + '」は○×に直せない（その時々で決まる）']);
  f.cageLend = /貸し出し(なし|はしていない|不可)/.test(cg) ? false : /貸し出し|貸出|レンタル|無料で(使|用意)/.test(cg) ? true : null;
  f.lendKg = null;
  // 介護
  f.care = /^○/.test(c.care) ? true : /介護(は)?(不可|できない)|^×/.test(c.care) ? false : null;
  // ワクチン・動物の種類
  const an = String(c.animals || '');
  f.vacMust = /ワクチン/.test(an) ? true : null;
  if (c.dog_only === 'はい' || /犬（ほかは不明）|^犬$|犬のみ/.test(an)) f.species = ['犬'];
  else if (unk(an)) f.species = null;
  else if (/禁止されていない|認められた|ペット全般|^ペット$/.test(an)) f.species = ['犬', '猫', 'その他'];
  else { f.species = []; if (/犬/.test(an)) f.species.push('犬'); if (/猫/.test(an)) f.species.push('猫'); if (/ほか|など|小動物|鳥|うさぎ|禁止されていない/.test(an)) f.species.push('その他'); if (!f.species.length) f.species = null; }
  // 車
  f.cars = unk(c.cars) ? '' : c.cars;
  f.carClass = /軽|エブリイ|クリッパー|N-VAN|ハイゼット|アトレー/.test(f.cars) ? '軽' : /ミニバン|ハイエース|アルファード|ノア|セレナ|キャラバン|普通車/.test(f.cars) ? '大きい車' : '';
  // 締切
  const ld = String(c.lead || '');
  f.lead = (() => { const m = ld.match(/(\d+)\s*時間前/); return m ? Number(m[1]) : null; })();
  if (/前日/.test(ld)) gaps.push(['締切', '「前日◯時まで」の締切は「何時間前まで」の数字では書けない（数字だけ拾うと時刻が時間数として読まれる）']);
  return { f, gaps };
}

// 予約シートの1行と同じ形にして、Code.gs の partners_() に読ませる
function asSheetRow(id, c, f) {
  const H = ['ID', '事業者名', '担当者名', '対応エリア', 'メール', '電話番号', 'LINE公式ID（先方）', '受付中', '大型犬OK', '介助OK', 'LINE登録コード', 'LINE userId', '引き受け件数', 'メモ', '車のタイプ', '同乗できる人数', '乗せられるペット数', '荷物多めOK', 'ケージ必須', 'ケージ貸し出し', '支払い方法', '支払いのタイミング', '営業時間', '何時間前まで', '送迎できる時間', '大型犬の最大kg', '大型犬の最大頭数', '貸し出しケージの最大kg', 'ペットだけOK', 'ワクチン必須'];
  const tri = v => v === true ? '○' : v === false ? '×' : '';
  const o = { 'ID': id, '事業者名': c.name, '対応エリア': c.pref.replace(/[都府県]$/, ''), 'メール': 'あり', '受付中': '○', '大型犬OK': tri(f.big), '介助OK': tri(f.care),
    '車のタイプ': f.cars, '同乗できる人数': f.riders ?? '', '乗せられるペット数': f.pets ?? '', 'ケージ必須': f.cageMust, 'ケージ貸し出し': tri(f.cageLend),
    '営業時間': f.hours, '何時間前まで': f.lead ?? '', '送迎できる時間': f.rideHours, '大型犬の最大kg': f.maxKg ?? '', '大型犬の最大頭数': f.maxBig ?? '',
    'ペットだけOK': tri(f.petOnly), 'ワクチン必須': tri(f.vacMust) };
  return { H, row: H.map(k => o[k] ?? '') };
}

/* ───────── 入力の組み合わせ ───────── */
// フォームで選べる値をそのまま使う（人数・荷物・ケージ・介護の選択肢は index.html と同じ）。時刻は割増・営業時間の境目の前後
const TIMES = ['02:00', '06:30', '07:50', '10:00', '17:50', '19:50', '21:30', '23:30'];
const ANIMALS = [['犬', 5], ['犬', 15], ['犬', 25], ['犬', 38], ['犬', 50], ['猫', 5], ['その他', 2]];
const COUNTS = [1, 2, 3, 5];
const RIDERS = ['0人（ペットだけ）', '1人', '2人', '3人'];
const LUGGAGE = ['手荷物くらい', '多め（スーツケース・大きなケージ・カートなど）'];
const CAGES = ['持ち込む', 'なし', '借りたい', 'どれでも'];
const CARES = [['不要', []], ['必要', ['歩けない（抱っこで運ぶ）']], ['必要', ['寝たきり（担架やマットで運ぶ）', '階段で運び出す（エレベーターなし）', '酸素や点滴などの医療機器がある']]];
const VACS = ['済', ''];
const TRIPS = ['片道', '往復'];
const jst = (hm, addDay) => { const [h, m] = hm.split(':').map(Number); return new Date(Date.UTC(2026, 11, 1 + (addDay || 0), h - 9, m)); };
function* combos() {
  for (const t of TIMES) for (const [sp, kg] of ANIMALS) for (const n of COUNTS) for (const riders of RIDERS) for (const lug of LUGGAGE)
    for (const cage of CAGES) for (const [care, need] of CARES) for (const vac of VACS) for (const trip of TRIPS) {
      const pets = [];
      for (let i = 0; i < n; i++) pets.push({ species: sp, weight: String(i === 0 ? kg : kg >= 20 && i === 1 ? kg - 8 : sp === '犬' ? 5 : kg), cage, care: i === 0 ? care : '不要', care_need: i === 0 ? need : [], vaccine: vac });
      const at = jst(t), ret = trip === '往復' ? new Date(at.getTime() + 3 * 3600000) : '';
      yield { t, sp, kg, n, riders, lug, cage, care, need, vac, trip, pets,
        r: { '希望日時': at, '帰りの日時': ret, '片道・往復': trip, '体重kg': Math.max(...pets.map(p => Number(p.weight))), '同乗人数': riders, 'ペット数': n,
          'キャリー': cage, '介助': care, '荷物': lug, 'ペットJSON': JSON.stringify(pets) } };
    }
}

/* ───────── 観点 ───────── */
const DIMS = ['エリア', '時間', '大型犬', '大型犬のkg', '頭数', '大型犬の頭数', '人数', '頭数×人数', '荷物', 'ケージ必須', '貸しケージの大きさ', '持参ケージと車', 'ペットだけ', 'ワクチン', '動物の種類', '介護の中身', '割増のまたぎ', '料金', '支払い', '締切', 'キャンセル', '返事の速さ'];
function dimOf(s) {
  if (/割増/.test(s)) return '割増のまたぎ';
  if (/お迎え/.test(s)) return '時間';
  if (/大型犬\d+頭と大人/.test(s)) return '頭数×人数';
  if (/ケージ.*貸し出|貸し出.*ケージ|入るケージ/.test(s)) return '貸しケージの大きさ';
  if (/ケージ/.test(s)) return 'ケージ必須';
  if (/kgの子/.test(s)) return '大型犬のkg';
  if (/大型犬\d+頭/.test(s)) return '大型犬の頭数';
  if (s === '大型犬') return '大型犬';
  if (/大人/.test(s)) return '人数';
  if (/匹/.test(s)) return '頭数';
  if (/荷物/.test(s)) return '荷物';
  if (/介護/.test(s)) return '介護の中身';
  if (/ペットだけ/.test(s)) return 'ペットだけ';
  if (/ワクチン/.test(s)) return 'ワクチン';
  return 'その他';
}

function auditCompany(pt, f) {
  const d = {}; DIMS.forEach(k => d[k] = { ng: 0, ask: 0, drop: 0, miss: 0 });
  const tot = { all: 0, clean: 0, ask: 0, ng: 0, drop: 0, miss: 0 };
  const typ = { all: 0, clean: 0, ask: 0, ng: 0, drop: 0, miss: 0 }; // よくある依頼（犬・猫／2匹まで／大人1〜2人／荷物少なめ／朝8時前〜夜21時半）
  const ex = {}; // 観点ごとの例（最初の1件）
  const note = (k, kind, c, why) => { const key = k + ':' + kind; if (!ex[key]) ex[key] = { dim: k, kind, why, input: label(c) }; };
  const def = ctx.CONFIG.DEFAULT_CAR;
  for (const c of combos()) {
    tot.all++;
    const ck = ctx.checks_(pt, c.r), car = ctx.fitsCar_(pt, c.r), cage = ctx.fitsCage_(pt, c.r);
    const n = ctx.needs_(c.r);
    let kind;
    const rentDrop = ck.ng.length === 1 && ck.ng[0] === 'ケージの条件' && /借り/.test(c.cage) && pt.cageLend === null;
    if (rentDrop) { kind = 'drop'; d['貸しケージの大きさ'].drop++; note('貸しケージの大きさ', 'drop', c, 'ケージの貸し出しが分からないので「用意なし」とみなして外れる'); }
    else if (ck.ng.length) { kind = 'ng'; ck.ng.forEach(s => d[dimOf(s)] && d[dimOf(s)].ng++); }
    else if (!car || !cage) {
      // checks_ は「分からない→確かめる」と言っているのに、fitsCar_ が軽バンの決まり（人2・ペット2・荷物少なめ）で外している
      kind = 'drop';
      if (pt.riders === null && n.riders > def.riders) { d['人数'].drop++; note('人数', 'drop', c, '人数が分からないので軽バン（大人' + def.riders + '人）とみなして外れる'); }
      if (pt.pets === null && n.pets > def.pets) { d['頭数'].drop++; note('頭数', 'drop', c, '頭数が分からないので軽バン（' + def.pets + '匹）とみなして外れる'); }
      if (pt.luggage === null && n.luggage && !def.luggage) { d['荷物'].drop++; note('荷物', 'drop', c, '荷物が分からないので軽バン（荷物少なめ）とみなして外れる'); }
    } else {
      // しくみが見ていない条件：候補に出てしまう
      const miss = [];
      if (f.species && !f.species.includes(c.sp)) miss.push(['動物の種類', (c.sp === 'その他' ? 'うさぎ・鳥など' : c.sp) + 'は乗せていない（サイトでは ' + f.species.join('・') + '）。しくみは種類を見ない']);
      else if (!f.species && c.sp === 'その他') miss.push(['動物の種類', '乗せられる動物がサイトにない。しくみは種類を見ないので、うさぎ・鳥でも聞かずに候補に出る']);
      if (f.overnight) { const hr = Number(c.t.slice(0, 2)) + Number(c.t.slice(3)) / 60, [a, b] = f.overnight; if (!(hr >= a || hr < b)) miss.push(['時間', '送迎は' + a + '〜' + b + '時だけ。しくみに書けないので昼の依頼も候補に出る']); }
      if (c.cage === '持ち込む' && c.kg >= 25 && f.carClass !== '大きい車') miss.push(['持参ケージと車', c.kg + 'kgの子のケージが車（' + (f.carClass || '車種不明') + '）に入るかを、しくみは聞かない']);
      if (f.vacMust && !c.vac && !ck.ask.some(x => /ワクチン/.test(x))) miss.push(['ワクチン', 'サイトではワクチン接種済みが条件。しくみ（予約シート）にワクチン必須が入っていないので、未接種でも聞かずに候補に出る']);
      if (miss.length) { kind = 'miss'; miss.forEach(([k, why]) => { d[k].miss++; note(k, 'miss', c, why); }); }
      else if (ck.ask.length) kind = 'ask';
      else kind = 'clean';
      if (ck.ask.length) ck.ask.forEach(s => { const k = dimOf(s); if (d[k]) { d[k].ask++; note(k, 'ask', c, '会社が引き受けるときに確かめる：' + s); } });
    }
    if (kind === 'ng') ck.ng.forEach(s => { const k = dimOf(s); if (d[k]) note(k, 'ng', c, '外す：' + s); });
    tot[kind]++;
    if (c.sp !== 'その他' && c.n <= 2 && /^[12]人/.test(c.riders) && c.lug === LUGGAGE[0] && ['07:50', '10:00', '17:50', '19:50', '21:30'].includes(c.t)) { typ.all++; typ[kind]++; }
  }
  return { d, tot, typ, ex: Object.values(ex) };
}
function label(c) {
  return [c.t + 'お迎え', c.trip, (c.sp === 'その他' ? 'うさぎ等' : c.sp) + c.kg + 'kg' + (c.n > 1 ? 'ほか計' + c.n + '匹' : ''), '人' + c.riders.replace(/（.*/, ''), c.lug.slice(0, 2) === '多め' ? '荷物多め' : '', 'ケージ' + c.cage,
    c.care === '必要' ? '介護（' + c.need.map(x => x.replace(/（.*/, '')).join('・') + '）' : '', c.vac ? '' : 'ワクチン未記入'].filter(String).join('／');
}

/* ───────── 会社ごとの項目（組み合わせに関係しないもの） ───────── */
function companyLevel(c, f, sheetPt, fareKey) {
  const out = [];
  const add = (dim, level, text) => out.push({ dim, level, text });
  // エリア：しくみは都府県でしか見ない
  const area = String(c.area || '');
  if (unk(area)) add('エリア', 'gap', '対応エリアがサイトにない。都府県全体で候補に出てしまう');
  else if (!/全国|全域/.test(area)) add('エリア', 'gap', '対応エリアは「' + area.slice(0, 60) + '」。しくみは都府県単位なので、同じ都県の遠い場所（例：東京の多摩と江戸川）でも候補に出る。お店の位置と「何kmまで」で判定する欄が必要');
  if (/(東京|神奈川|埼玉|千葉|茨城|栃木|群馬|山梨|静岡)/.test(area)) {
    const others = (area.match(/東京|神奈川|埼玉|千葉|茨城|栃木|群馬|山梨|静岡/g) || []).filter(p => !c.pref.startsWith(p));
    if (others.length) add('エリア', 'info', 'サイトでは他県（' + [...new Set(others)].join('・') + '）も対応。予約シートの「対応エリア」に入れないと、その県のお迎えで候補に出ない');
  }
  if (sheetPt) {
    const prefs = sheetPt.areas;
    const siteHas = p => new RegExp(p).test(area + c.pref);
    prefs.forEach(p => { if (!siteHas(p)) add('エリア', 'miss', '予約シートでは「' + p + '」も対応になっているが、サイトのエリア（' + area.slice(0, 30) + '）には書いていない'); });
  }
  // 料金
  const fare = [];
  if (unk(c.km5) && unk(c.perkm)) fare.push('基本料金・km単価がない（概算が出せない）');
  if (unk(c.pick)) fare.push('お迎え料金（迎車・回送）が分からない');
  else if (/km/.test(c.pick)) fare.push('お迎え料金は距離制（' + c.pick + '）。お店の位置（shop）がないと計算できない');
  const nt = String(c.night || '');
  if (unk(nt)) fare.push('夜間・早朝の割増が分からない');
  else {
    if (/[\d,]{3,}円/.test(nt) && !/割増|倍/.test(nt)) fare.push('割増は固定額（' + nt.match(/[+＋]?\s*[\d,]{3,}円/)[0] + '）。しくみの割増は倍率だけなので、そのままでは入らない');
    if ((nt.match(/\d+\s*[〜~]\s*\d+時/g) || []).length >= 2) fare.push('割増の時間帯が2つある（' + nt.slice(0, 30) + '）。しくみは1つだけ');
    if (/食い違/.test(nt)) fare.push('サイトの中で割増の時間か額が食い違っている');
  }
  fare.push('割増の時間をまたぐとき（乗った時刻／降りた時刻／走った分）の決まりが' + (unk(c.night_span) ? '分からない。しくみは乗る時刻だけで決めている' : 'サイトにある：' + c.night_span));
  if (unk(c.wait)) fare.push('待ち時間の料金が分からない（往復で待ってもらうときにずれる）');
  if (unk(c.toll)) fare.push('高速代・駐車場の扱いが分からない');
  if (unk(c.rt_fare)) fare.push('往復の料金（待つ／あとで迎え）が分からない');
  if (unk(c.extra_fees) || /未転記/.test(c.extra_fees)) fare.push('大型犬・多頭・介助・ケージの貸し出し・予約料などの追加料金が' + (/未転記/.test(c.extra_fees) ? 'サイトにあるが、まだ写していない' : '分からない'));
  if (!fareKey) fare.push('料金表（tools/fares.json）に入っていない。候補カードは「料金はお見積もり」になる');
  fare.forEach(t => add('料金', /固定額|2つ|食い違|入っていない|出せない/.test(t) ? 'gap' : 'unknown', t));
  if (fareKey) fareCompare(c, fares[fareKey]).forEach(t => add('料金', 'miss', t));
  // 支払い
  if (unk(c.pay)) add('支払い', 'unknown', '支払い方法（現金・カード・コード払い）が分からない');
  if (unk(c.pay_timing)) add('支払い', 'unknown', '支払いの時期（前払い／降りるとき）が分からない');
  else if (/前払/.test(c.pay_timing)) add('支払い', 'gap', '前払い。しくみは「降りるときに直接」として案内している');
  if (unk(c.rt_pay)) add('支払い', 'unknown', '往復の支払い（行き帰りで別々／まとめて）が分からない');
  // 締切・キャンセル・返事
  if (unk(c.lead)) add('締切', 'unknown', '何時間前まで申し込めるか分からない（しくみは3時間前とみなす）');
  if (unk(c.cancel)) add('キャンセル', 'unknown', 'キャンセルの決まり（無料の期限・割合）が分からない');
  add('キャンセル', 'gap', 'キャンセルの決まりは候補カードに出ていない（会社ごとに違う：' + (unk(c.cancel) ? '不明' : c.cancel.slice(0, 30)) + '）');
  if (unk(c.rt_cancel)) add('キャンセル', 'unknown', '往復の帰りだけ取り消せるか分からない');
  add('返事の速さ', 'unknown', '返事の速さはまだ測っていない（問い合わせの返事で記録する）');
  if (!f.hoursText) add('時間', 'unknown', '営業時間・送迎できる時間がサイトにない（しくみは8〜18時とみなす）');
  if (!f.species) add('動物の種類', 'unknown', '乗せられる動物（猫・うさぎ・鳥など）がサイトにない');
  if (!f.cars) add('持参ケージと車', 'unknown', '車種・車の大きさが分からない（大型犬のケージ・人数・荷物が乗るか判断できない）');
  return out;
}

// 料金表（fares.json）とダッシュボードの値が合っているか
function fareCompare(c, fc) {
  const out = [], n = s => Number(String(s).replace(/[^\d]/g, '')) || null;
  const site5 = c.km5_yen || n(c.km5);
  if (site5) {
    let amount = fc.base, start = fc.base_km;
    fc.tiers.forEach(t => { const end = t[0] == null ? Infinity : t[0]; if (5 > start) amount += t[1] * (Math.min(5, end) - start); start = end; });
    if (amount !== site5) out.push('5kmの乗車料金：料金表では' + amount + '円、サイトでは' + site5 + '円');
  }
  const sitePer = n(String(c.perkm).match(/\d[\d,]*円/)?.[0] || '');
  if (sitePer && fc.tiers[0][1] !== sitePer) out.push('1kmごとの料金：料金表では' + fc.tiers[0][1] + '円、サイトでは' + sitePer + '円');
  const sn = String(c.night || '');
  const ratio = sn.match(/(\d)割増/);
  if (ratio && Math.abs(fc.night - (1 + Number(ratio[1]) / 10)) > 0.001) out.push('割増：料金表では' + fc.night + '倍、サイトでは' + ratio[0]);
  if (!ratio && fc.night > 1 && /記載なし|なし/.test(sn)) out.push('割増：料金表では' + fc.night + '倍、サイトでは割増なし');
  return out;
}

/* ───────── 実行 ───────── */
if (require.main === module) main();
function main() {
const companies = JSON.parse(fs.readFileSync(COMPANIES, 'utf8')).filter(c => c.pref);
let sheet = null;
if (SHEET) sheet = JSON.parse(fs.readFileSync(SHEET, 'utf8')).values;
// 名前の照合：かっこ書き・「ペットタクシー」などの共通語を外して、同じ名前のときだけ同じ会社とみなす（「東京」と「西東京店」を取り違えない）
const norm = s => String(s).normalize('NFKC').replace(/[（(][^）)]*[）)]/g, '').replace(/[\s・]/g, '').replace(/ペットタクシー|ペット送迎サービス|ペット専用タクシー/g, '').replace(/cocoタク/gi, 'COCOタク').replace(/COCOタク埼玉/, 'COCOタク').toLowerCase();
function sheetPartnerFor(c) {
  if (!sheet) return null;
  sheetValues = sheet;
  const all = ctx.partners_();
  const nc = norm(c.name);
  return all.find(p => p.name && norm(p.name) === nc) || null;
}
const fareKeyFor = (c, sp) => Object.keys(fares).find(k => (sp && fares[k].partner_id === sp.id) || norm(c.name) === norm(fares[k]['名前']));

const results = [];
const list = LIMIT ? companies.slice(0, LIMIT) : companies;
list.forEach((c, i) => {
  const [status, why] = listing(c);
  const { f, gaps } = derive(c);
  const sp = sheetPartnerFor(c);
  const fk = fareKeyFor(c, sp);
  const res = { id: c.id, pref: c.pref, name: c.name, url: c.url, status, why, book: BOOK_PREFS.includes(c.pref) || /全国/.test(c.pref), sheet: sp ? { id: sp.id, active: sp.active } : null,
    derived: f, gaps: gaps.map(([dim, text]) => ({ dim, level: 'gap', text })), company: [], combos: null, sheetCombos: null };
  if (status !== '除外') {
    const { H, row } = asSheetRow('X' + i, c, f);
    sheetValues = [H, row];
    const pt = ctx.partners_()[0];
    if (fk) pt.id = fares[fk].partner_id; // 割増の境目のチェックは料金表の会社だけ動く
    res.combos = auditCompany(pt, f);
    if (sp) { const spc = Object.assign({}, sp); res.sheetCombos = auditCompany(spc, f); }
    res.company = companyLevel(c, f, sp, fk);
  }
  results.push(res);
  process.stderr.write('\r' + (i + 1) + '/' + list.length + ' ' + c.name.slice(0, 20) + '                ');
});
process.stderr.write('\n');

/* ───────── 問い合わせで聞く項目の候補 ───────── */
const ASK_KEY = { '人数': 'cap', '頭数': 'cap', '頭数×人数': 'large_dog', '大型犬': 'large_dog', '大型犬のkg': 'large_dog', '大型犬の頭数': 'large_dog', '荷物': 'cap', 'ケージ必須': 'cage', '貸しケージの大きさ': 'cage', '持参ケージと車': 'cars', 'ペットだけ': 'pet_only', 'ワクチン': 'animals', '動物の種類': 'animals', '介護の中身': 'care', '時間': 'hours', '割増のまたぎ': 'night_span', 'エリア': 'area', '締切': 'lead', 'キャンセル': 'cancel', '支払い': 'pay', '料金': 'extra_fees', '返事の速さ': 'reply' };
// 問い合わせの下書き（inquiry-drafts/gen_drafts.py の Q・Q2）がすでに聞いている項目
const DRAFT_KEYS = ['area', 'pick', 'night', 'night_span', 'large_dog', 'cap', 'cage', 'pet_only', 'extra_fees', 'rt_fare', 'rt_pay', 'rt_cancel', 'toll', 'pay', 'pay_timing', 'lead', 'cancel', 'care'];
// 下書きにまだない項目の文案（お客さまとして聞く形）
const NEW_Q = {
  hours: '送迎していただける時間帯（受付の時間とちがう場合は、何時から何時までお迎えに来ていただけるか）',
  animals: '猫やうさぎ・鳥なども乗せていただけるか、犬と猫を一緒に乗せられるか、ワクチンの接種が必要か',
  cars: '車の種類と大きさ（大型犬用の大きなケージ〔例：幅90cmほど〕が載るか、そのとき人は何人乗れるか）',
  wait: '病院などで待っていただくときの料金（何分まで無料か、そのあとの金額）',
  reply: null
};
const questions = {};
results.filter(r => r.combos).forEach(r => {
  const need = new Set();
  Object.entries(r.combos.d).forEach(([k, v]) => { if ((v.ask || v.drop || v.miss) && ASK_KEY[k]) need.add(ASK_KEY[k]); });
  r.company.filter(x => x.level !== 'info').forEach(x => ASK_KEY[x.dim] && need.add(ASK_KEY[x.dim]));
  r.gaps.forEach(x => ASK_KEY[x.dim] && need.add(ASK_KEY[x.dim]));
  if (r.company.some(x => /待ち時間/.test(x.text))) need.add('wait');
  questions[r.id] = { name: r.name, status: r.status, keys: [...need].sort(), add: [...need].filter(k => NEW_Q[k]).map(k => NEW_Q[k]) };
});

/* ───────── 書き出し ───────── */
fs.mkdirSync(OUT, { recursive: true });
const meta = { generated: new Date().toISOString(), companies: COMPANIES, sheet: SHEET || null, combosPerCompany: results.find(r => r.combos)?.combos.tot.all || 0, dims: DIMS };
fs.writeFileSync(path.join(OUT, 'audit.json'), JSON.stringify({ meta, results }, null, 1));
fs.writeFileSync(path.join(OUT, 'questions.json'), JSON.stringify(questions, null, 1));
fs.writeFileSync(path.join(OUT, 'audit.md'), markdown(meta, results));
fs.writeFileSync(path.join(OUT, 'audit.html'), require('./match_audit_html.cjs')(meta, results, questions, NEW_Q));
console.log('companies', results.length, 'combos/company', meta.combosPerCompany, '→', OUT);
}

function cell(r, k) {
  const v = r.combos && r.combos.d[k], lv = new Set(r.company.filter(x => x.dim === k).map(x => x.level).concat(r.gaps.filter(x => x.dim === k).map(() => 'gap')));
  if (v && v.miss || lv.has('miss')) return '見落とし';
  if (v && v.drop) return '黙って除外';
  if (lv.has('gap')) return 'しくみ外';
  if (v && v.ask || lv.has('unknown')) return '要確認';
  return 'OK';
}
function markdown(meta, rs) {
  const L = ['# マッチング検査の結果', '', '作成 ' + meta.generated + '。1社あたり ' + meta.combosPerCompany + ' 通りの入力を当てた。', '',
    '- 見落とし：本当は受けられないのに候補に出る／料金表とサイトが合わない', '- 黙って除外：分からないのに軽バンとみなして候補から外している', '- しくみ外：サイトに書いてあるが、しくみに入れる欄・計算がない', '- 要確認：分からないので、会社が引き受けるときに確かめる（問い合わせで埋める）', ''];
  for (const st of ['候補', '輸送のときだけ', '緊急タブだけ', '除外']) {
    const g = rs.filter(r => r.status === st);
    L.push('## ' + st + '（' + g.length + '社）', '');
    if (st === '除外') { g.forEach(r => L.push('- ' + r.pref + ' ' + r.name + '：' + r.why)); L.push(''); continue; }
    g.forEach(r => {
      const t = r.combos.typ, pc = x => (100 * x / t.all).toFixed(1) + '%';
      L.push('### ' + r.pref + ' ' + r.name + (r.sheet ? '（予約シート ' + r.sheet.id + (r.sheet.active ? '・受付中' : '') + '）' : ''), '',
        '- よくある依頼 ' + t.all + '通りのうち：そのまま出せる ' + pc(t.clean) + '／会社が確認 ' + pc(t.ask) + '／正しく除外 ' + pc(t.ng) + '／黙って除外 ' + pc(t.drop) + '／見落とし ' + pc(t.miss));
      const bad = DIMS.map(k => [k, cell(r, k)]).filter(x => x[1] !== 'OK');
      L.push('- ' + bad.map(x => x[0] + '：' + x[1]).join('、'));
      r.gaps.concat(r.company.filter(x => x.level !== 'unknown')).forEach(x => L.push('  - [' + x.dim + '] ' + x.text));
      r.combos.ex.filter(x => x.kind === 'miss' || x.kind === 'drop').slice(0, 6).forEach(x => L.push('  - 例（' + (x.kind === 'miss' ? '見落とし' : '黙って除外') + '）' + x.input + ' → ' + x.why));
      L.push('');
    });
  }
  return L.join('\n');
}
module.exports = { listing, derive, auditCompany, companyLevel, ctx };

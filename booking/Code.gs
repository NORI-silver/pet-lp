/**
 * ペットタクシー予約窓口 自動手配システム（Google Apps Script）
 *
 * 流れ
 *   1. LPのフォーム → doPost で「予約」シートに1行追加
 *   2. そのエリアの提携先へ一斉にお知らせ。お名前・電話は伏せる
 *        メールの会社      → 自動で送信
 *        こちらのLINEに登録済み → 自動で送信
 *        先方のLINE公式だけ   → 運営者が「手配ページ」のボタンを押して送信（文面は入力済み）
 *        電話だけ        → 対象外
 *   3. 提携先がリンクを開き「お迎え時刻・確定料金（一般道／高速利用時）」を入れて引き受け（先着1社）
 *      返信で答えてきた場合は、運営者が手配ページで決定を入力
 *   4. お客さまへ「決まりました」を自動送信。引き受けた提携先にだけお客さまの連絡先を送る
 *   5. 決まらないとき：一定時間で近くのエリア・全国対応の提携先にも送る → それでもだめならお詫びを自動送信
 *
 * 設定は下の CONFIG だけ触ればOKです。
 */

var CONFIG = {
  SERVICE_NAME: 'ペットタクシー予約窓口',
  SITE_URL: 'https://pet.shiokonbu.com/',
  // メールのリンク（引き受け・取り消し・手配ページ）を開くページ。LPの中に表示して、Googleの注意書きを出さない
  // 空にすると、今までどおり script.google.com のページを直接開く
  PAGE_URL: 'https://pet.shiokonbu.com/go/',

  // ウェブアプリとして公開したあとのURL（https://script.google.com/macros/s/〇〇/exec）
  WEB_APP_URL: 'https://script.google.com/macros/s/AKfycbyy-cTvD-t8DFGhEyA2IbFiXWoB50kl_2_97WiVdMlXec8sIbI2NVUkkyn-45VkIMc_5g/exec',

  // 運営者（Noriさん）のメール。空なら、このスクリプトを動かしているGoogleアカウント
  ADMIN_EMAIL: 'pettaxi.yoyaku@gmail.com',
  // お客さま・会社へのメールの差出人。Gmailの「他のメールアドレスを追加」で登録すると使われる（未登録なら今のアドレスから送る）
  FROM_EMAIL: 'pettaxi.yoyaku@gmail.com',
  // 返信先。空なら FROM_EMAIL
  REPLY_TO: '',
  // 新しい受付・決定・見つからずのたびに運営者へメールする
  ADMIN_NOTIFY: true,
  // テスト：true にすると、すべての依頼で会社あての連絡を運営者のメールに送る（会社には届かない）
  // false のままでも、お名前が「テスト」で始まる依頼／メールが運営者と同じ依頼はテスト扱いになる
  TEST_MODE: false,

  // 候補カードに、提携先シートの会社に加えて「掲載候補」の会社（tools/display_companies.json）も表示だけで出す（Nori 2026-10-31）
  // true のあいだは、提携先シートの会社（P002・P003）も含めて全社「準備中」：予約の依頼は誰にも送れない（ボタンは押せず、サーバーでも断る。Nori「その2社もまだ準備中。送信はできないように」）
  // false にすると今までの状態（提携先の2社だけ・依頼できる）に戻る
  SHOW_ALL_CANDIDATES: true,
  // 表示だけの会社は、お店からお迎えの場所までが直線でこのkmを超えると出さない（都道府県が合っていても遠すぎる会社を外す）
  DISPLAY_MAX_KM: 80,

  // 決まらないときの待ち時間（分）。会社が動いている時間（OPEN_HOURS）だけ数える。夜の依頼は朝から数え始める
  OPEN_HOURS: '8-20',
  WAVE2_MIN: 20,   // これを過ぎたら、近くのエリア・全国対応の提携先にも送る
  GIVE_UP_MIN: 60, // これを過ぎたら、お客さまにお詫びを送って終了
  MIN_LEAD_HOURS: 3, // お迎えは受付から3時間より先だけ（LPと同じ。入力にかかる時間を見て15分は大目に見る）
  URGENT_HOURS: 3, // 希望時刻まで3時間を切っている依頼は、待ち時間を半分にする

  // 提携先シートの「営業時間」「何時間前まで」が空欄のとき。メールは営業時間に読まれる前提で、読める時刻からお迎えまでこれだけ必要
  DEFAULT_PARTNER_HOURS: '8-18',
  DEFAULT_LEAD_HOURS: 3,

  LARGE_DOG_KG: 20, // この体重以上は「大型犬OK」の提携先にだけ送る
  ASK_KG: 30, // この体重以上の子は、上限が分からない会社に乗れるかを引き受けるときに確かめる（Nori 2026-10-31「30kg以上は予約時に要確認」）
  VAN_BIG_DOGS: 2, // 軽バン（エブリイ・N-VAN など）は大型犬2頭まで乗れる（Nori 2026-10-31）
  // 提携先シートの車の情報が空欄のときは、いちばん小さい車（軽バン）とみなす
  DEFAULT_CAR: { riders: 2, pets: 2, big: true, luggage: false }, // 使っていない（空欄は外さず、引き受けるときに会社が確かめる。2026-10-31）

  // LINE公式アカウント（作ったら入れる。空ならメールだけで動きます）
  LINE_CHANNEL_ACCESS_TOKEN: '',
  LINE_ADD_URL: '', // 友だち追加URL（https://lin.ee/〇〇）

  // 会社カードの口コミの点数（地図サービスから正式に取り寄せる。規約で書き写し・保存はできない）
  // キーはここに書かず、スクリプトのプロパティ PLACES_API_KEY に入れる。空なら点数は出さず「口コミを見る」リンクだけ
  REVIEW_MONTHLY_LIMIT: 900, // 1か月に取り寄せる回数の上限（無料の範囲 1,000回に収める。超えたら月末までリンクだけ）
  REVIEW_EMG_MONTHLY_LIMIT: 500, // そのうち緊急タブの搬送の会社・病院に使ってよい回数（予約の候補カードのぶんを残すため）
  REVIEW_DASH_MONTHLY_LIMIT: 200 // そのうち社内用の事業者一覧（a=dash）で使ってよい回数
};

var TZ = 'Asia/Tokyo';
// 2026-10-27 最初は首都圏4都県だけで受け付ける（大阪・兵庫・福岡は休止。戻すときはここに足す）
var PREFS = ['東京', '神奈川', '千葉', '埼玉'];
var PREF_FULL = { '東京': '東京都', '神奈川': '神奈川県', '千葉': '千葉県', '埼玉': '埼玉県', '大阪': '大阪府', '兵庫': '兵庫県', '福岡': '福岡県' };
// 最初の提携先で決まらなかったとき、次に声をかけるエリア
var NEIGHBORS = {
  '東京': ['神奈川', '埼玉', '千葉'], '神奈川': ['東京'], '千葉': ['東京', '埼玉'], '埼玉': ['東京', '千葉'],
  '大阪': ['兵庫'], '兵庫': ['大阪'], '福岡': []
};

var SHEET_REQ = '予約';
var SHEET_PARTNER = '提携先';
var SHEET_LOG = 'ログ';

var REQ_HEADERS = [
  '受付番号', '受付日時', '状態', '都府県', 'お迎えの場所', '行き先', '希望日時', '片道・往復',
  '種類', '犬種・猫種', '体重kg', '年齢', '性別', 'キャリー', '介助', '同乗人数',
  'お名前', '電話番号', 'メール', '連絡方法', 'メモ',
  '通知段階', '通知した提携先', '決定した提携先ID', '決定した提携先', 'お迎え予定', '料金の目安', '提携先から一言', '決定日時',
  'お客さまLINE', '終了日時', 'ペット数', 'ペット詳細', '日付のみ', '経由地', 'ペットJSON', '概算km', '概算料金', '荷物', '高速利用時の料金', '帰りの日時', '帰りのお迎え', '帰りの行き先', '待ち時間（分）', '概算料金の表示', '帰りのやり方', '指定した提携先ID', '指定した提携先', '区間', 'ペアの受付番号',
  // 2026-10-31 Nori「複数社に予約・見積もりを依頼できるように。どちらかはお客さまが選ぶ」。依頼の種類＝予約／見積もり、見積もりJSON＝届いた見積もり
  '依頼の種類', '見積もりJSON'
];
var PARTNER_HEADERS = [
  'ID', '事業者名', '担当者名', '対応エリア', 'メール', '電話番号', 'LINE公式ID（先方）', '受付中', '大型犬OK', '介助OK',
  'LINE登録コード', 'LINE userId', '引き受け件数', 'メモ',
  '車のタイプ', '同乗できる人数', '乗せられるペット数', '荷物多めOK',
  'ケージ必須', 'ケージ貸し出し', '支払い方法', '支払いのタイミング', '営業時間', '何時間前まで',
  // 2026-10-31 追加（空欄＝まだ分からない。分からない条件は候補に出し、引き受けるときに会社がチェックして確かめる）
  '送迎できる時間', '大型犬の最大kg', '大型犬の最大頭数', '貸し出しケージの最大kg', 'ペットだけOK', 'ワクチン必須'
];

var ST = { OPEN: '手配中', DONE: '決定', NONE: '見つからず', CANCEL: '取り消し' };
var MAX_PICKS = 5; // 1回に依頼できる会社の数

// お客さまが選んだ会社（カンマ区切り）。1社のときも同じ形
function pickedIds_(r) { return String(r['指定した提携先ID'] || '').split(',').filter(String); }
function isQuoteReq_(r) { return r['依頼の種類'] === '見積もり'; }
// お客さまがあとで1社を選ぶ依頼：見積もり依頼と、複数社への予約依頼（Nori 2026-10-31「お客さまがあとで1社選ぶ」）。1社だけの予約依頼は、引き受けた時点で決まる
function needsChoice_(r) { return isQuoteReq_(r) || pickedIds_(r).length > 1; }
function quotesOf_(r) { try { return JSON.parse(r['見積もりJSON'] || '[]') || []; } catch (e) { return []; } }
// 複数社を選んだとき：picks＝[{id, token, expires}]（LPのカードの見積もりの署名）。1社のときは partner_id などをそのまま使う
function picksOf_(p) {
  var list = [];
  try { list = JSON.parse(p.picks || '[]') || []; } catch (e) { list = []; }
  if (!Array.isArray(list)) list = [];
  if (!list.length && p.partner_id) list = [{id:p.partner_id, token:p.quote_token, expires:p.quote_expires}];
  return list.filter(function (x, i, a) { return x && x.id && a.map(function (y) { return y && y.id; }).indexOf(x.id) === i; });
}

/* ───────── 初回だけ実行 ───────── */

function setup() {
  var ss = SpreadsheetApp.getActive();
  ss.setSpreadsheetTimeZone(TZ);
  ensureSheet_(ss, SHEET_REQ, REQ_HEADERS);
  var p = ensureSheet_(ss, SHEET_PARTNER, PARTNER_HEADERS);
  ensureSheet_(ss, SHEET_LOG, ['日時', '内容']);
  if (p.getLastRow() === 1) {
    // 動作確認用のサンプル（自分のメールに変えてテストし、本番前に消してください）
    p.appendRow(['P001', 'テスト用ペットタクシー', 'テスト', '東京', adminEmail_(), '', '', '○', '○', '○', makeCode_(), '', 0, '本番前に消す']);
  }
  var props = PropertiesService.getScriptProperties();
  if (!props.getProperty('SECRET')) props.setProperty('SECRET', Utilities.getUuid() + Utilities.getUuid());

  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'checkPending') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('checkPending').timeBased().everyMinutes(5).create();
  log_('setup 完了');
}

// 貼り直したあと1回だけ実行：Gmailの権限を許可して、差出人の登録を確かめる
function checkSender() {
  var ok = fromOk_();
  Logger.log(ok ? '差出人 ' + CONFIG.FROM_EMAIL + ' から送れます' : '差出人 ' + CONFIG.FROM_EMAIL + ' はまだGmailに登録されていません（今のアドレスから送ります）');
  log_('差出人の確認: ' + (ok ? 'OK' : '未登録'));
}

function ensureSheet_(ss, name, headers) {
  var sh = ss.getSheetByName(name) || ss.insertSheet(name);
  if (sh.getLastRow() === 0) {
    sh.appendRow(headers);
    sh.getRange(1, 1, 1, headers.length).setFontWeight('bold').setBackground('#fff1e6');
    sh.setFrozenRows(1);
  }
  return sh;
}

/* ───────── 受付（LPフォーム / LINE） ───────── */

function doPost(e) {
  var body = e && e.postData && e.postData.contents;
  if (body && body.charAt(0) === '{') {
    try { handleLine_(JSON.parse(body)); } catch (err) { log_('LINEエラー: ' + err); }
    return json_({ ok: true });
  }
  if ((e.parameter || {}).kind === 'quotes') {
    try { return json_(selectionQuotes_(e.parameter)); } catch (err) { return json_({ok:false,error:'quotes_unavailable'}); }
  }
  if ((e.parameter || {}).kind === 'emg_scores') {
    try { return json_(emgScores_(String(e.parameter.ids || ''))); } catch (err) { return json_({ok:false,error:'reviews_unavailable'}); }
  }
  if ((e.parameter || {}).kind === 'scores') {
    try { return json_(selectionScores_(String(e.parameter.ids || ''))); } catch (err) { return json_({ok:false,error:'reviews_unavailable'}); }
  }
  if ((e.parameter || {}).kind === 'reviews') {
    try { return json_(selectionReviews_(String(e.parameter.partner_id || ''))); } catch (err) { return json_({ok:false,error:'reviews_unavailable'}); }
  }
  try {
    if ((e.parameter || {}).kind === 'contact') return json_(contact_(e.parameter));
    return json_(receive_(e.parameter || {}));
  } catch (err) {
    log_('受付エラー: ' + err + ' / ' + JSON.stringify(e.parameter));
    notifyAdmin_('【要確認】受付でエラー', '受付の途中でエラーが出ました。\n' + err + '\n\n入力内容:\n' + JSON.stringify(e.parameter, null, 1));
    return json_({ ok: false });
  }
}

/* ───────── お問い合わせ（LPの /contact/） ───────── */

var CONTACT_TOPICS = ['ご予約について', 'キャンセル・変更について', '料金について', 'ペットタクシー会社の方（提携のご相談）', 'その他'];

function contact_(p) {
  if (p.website) return { ok: true }; // 迷惑投稿よけ
  var name = clip_(p.name, 100), email = clip_(p.email, 200).trim(), msg = clip_(p.message, 2000);
  var topic = clip_(p.topic, 80).trim() || 'その他'; // 提携の申し込み（/partner/）は「提携のお申し込み（会社名）」で来る
  if (!name || !msg || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return { ok: false, error: 'missing' };
  var reqId = clip_(p.req_id, 20);
  var sh = ensureSheet_(SpreadsheetApp.getActive(), '問い合わせ', ['受付日時', '種類', 'お名前', 'メール', '受付番号', '内容', '対応']);
  sh.appendRow([new Date(), topic, name, email, reqId ? "'" + reqId : '', msg, '']);
  try {
    MailApp.sendEmail({ to: adminEmail_(), replyTo: email, name: CONFIG.SERVICE_NAME,
      subject: '[お問い合わせ] ' + topic + '：' + name + ' 様',
      body: '■ 種類：' + topic + '\n■ お名前：' + name + ' 様\n■ メール：' + email + (reqId ? '\n■ 受付番号：' + reqId : '') +
        '\n\n' + msg + '\n\n――――――――――\nこのメールに返信すると、お客さま（' + email + '）に届きます。\n予約シート「問い合わせ」タブにも残しています：' + SpreadsheetApp.getActive().getUrl() });
  } catch (err) { log_('問い合わせメールの送信エラー: ' + err); }
  return { ok: true };
}

function receive_(p) {
  if (p.website) return { ok: true }; // 迷惑投稿よけ（人には見えない欄）
  var need = ['pref', 'pickup', 'dropoff', 'datetime', 'trip', 'species', 'weight', 'cage', 'care', 'riders', 'name', 'tel', 'email', 'contact'];
  for (var i = 0; i < need.length; i++) {
    if (!String(p[need[i]] || '').trim()) return { ok: false, error: 'missing ' + need[i] };
  }
  var pref = shortPref_(p.pref);
  if (PREFS.indexOf(pref) < 0) return { ok: false, error: 'area' };
  // 日付だけ（YYYY-MM-DD）のときは、その日の終わりを期限にする
  var when = /^\d{4}-\d{1,2}-\d{1,2}$/.test(String(p.date || '')) ? parseJst_(p.date + 'T23:59') : parseJst_(p.datetime);
  if (!when) return { ok: false, error: 'datetime' };
  if (!p.date && when.getTime() - Date.now() < (CONFIG.MIN_LEAD_HOURS * 60 - 15) * 60000) return { ok: false, error: 'datetime' };

  // 往復を行きと帰りで別の会社に頼むとき（split=1）は、片道の依頼を2件つくる。それぞれ選んだ会社にだけ送る
  var split = p.split === '1' && p.trip === '往復';
  var legs = split ? [
    { p: legParams_(p, 'go'), label: '行き（往復の1/2）' },
    { p: withPick_(legParams_(p, 'back'), p.back_partner_id, p.back_quote_token, p.back_quote_expires), label: '帰り（往復の2/2）' }
  ] : [{ p: p, label: '' }];
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var rows = [];
  // 二重送信よけ：LPは入力が同じなら同じ req_key を送る。6時間以内の同じ key には同じ受付番号を返す
  var key = String(p.req_key || '').slice(0, 200), cache = key ? CacheService.getScriptCache() : null;
  try {
    if (cache) {
      var dup = cache.get('req_' + key);
      if (dup) { var ids = dup.split(','); return ids.length > 1 ? { ok: true, id: ids[0], back_id: ids[1] } : { ok: true, id: dup }; }
    }
    var mode = !split && p.mode === 'quote' ? '見積もり' : '予約';
    var picks = split ? [] : picksOf_(p);
    if (!split && (!picks.length || picks.length > MAX_PICKS)) return { ok: false, error: 'selection_unavailable' };
    // 1社ずつ、表示した見積もりの署名を確かめる（複数社でも同じ）
    var sels = split ? legs.map(function (l) { return validateSelection_(l.p); }) : [(function () {
      var got = picks.map(function (x) { var q = {}; Object.keys(p).forEach(function (k) { q[k] = p[k]; }); return validateSelection_(withPick_(q, x.id, x.token, x.expires)); });
      var bad = got.filter(function (g) { return !g.ok; })[0];
      if (bad) return bad;
      if (got.length === 1) return got[0];
      var low = Math.min.apply(null, got.map(function (g) { return g.price.amount || Infinity; }));
      return { ok: true, partner: { id: got.map(function (g) { return g.partner.id; }).join(','), name: got.map(function (g) { return g.partner.name; }).join('、') },
        price: { amount: isFinite(low) ? low : '', text: got.map(function (g) { return g.partner.name + ' ' + g.price.text; }).join('／') } };
    })()];
    for (var k = 0; k < sels.length; k++) {
      if (!sels[k].ok) return split ? { ok: false, error: sels[k].error, leg: k ? 'back' : 'go' } : sels[k];
    }
    var sh = sheet_(SHEET_REQ);
    var head = ensureReqHeaders_(sh);
    var ids = legs.map(function () { return newId_(sh); });
    for (var t = 0; ids[1] && ids[1] === ids[0] && t < 20; t++) ids[1] = newId_(sh); // 2件が同じ番号にならないように
    legs.forEach(function (l, n) {
      var q = l.p, selection = sels[n], at = n ? parseJst_(q.datetime) : when;
      var r = {
        '受付番号': ids[n], 'ペアの受付番号': split ? ids[1 - n] : '', '受付日時': new Date(), '状態': ST.OPEN, '都府県': pref,
        'お迎えの場所': clip_(q.pickup), '行き先': clip_(q.dropoff), '希望日時': at, '片道・往復': clip_(q.trip),
        '種類': clip_(p.species), '犬種・猫種': clip_(p.breed), '体重kg': Number(p.weight) || '', '年齢': clip_(p.age),
        '性別': clip_(p.sex), 'キャリー': clip_(p.cage), '介助': clip_(p.care), '同乗人数': clip_(p.riders),
        'お名前': clip_(p.name), '電話番号': "'" + clip_(p.tel), 'メール': clip_(p.email).trim(), '連絡方法': clip_(p.contact),
        'メモ': clip_(p.notes, 1000), '通知段階': 0, '通知した提携先': '',
        'ペット数': Number(p.pet_count) || 1, 'ペット詳細': clip_(p.pets, 1000), '日付のみ': p.date && !split ? '○' : '',
        '経由地': clip_(q.via), 'ペットJSON': clip_(p.pets_json, 5000),
        '概算km': split ? '' : Number(p.est_km) || '', '概算料金': selection.price.amount || '', '荷物': clip_(p.luggage),
        '帰りの日時': parseJst_(q.return_datetime) || '', '帰りのお迎え': clip_(q.return_pickup), '帰りの行き先': clip_(q.return_dropoff),
        '待ち時間（分）': clip_(p.wait_time, 20),
        '概算料金の表示': selection.price.text, '指定した提携先ID': selection.partner.id, '指定した提携先': selection.partner.name,
        '区間': l.label, '依頼の種類': mode
      };
      sh.appendRow(head.map(function (h) { return r[h] === undefined ? '' : r[h]; }));
      // 数字の列が「日付」の書式になっていると、読み出したときに日付になってしまうので、書式を数字に固定する
      var last = sh.getLastRow();
      [['体重kg', '0.#'], ['ペット数', '0'], ['概算km', '0.0'], ['概算料金', '#,##0'], ['待ち時間（分）', '@'], ['概算料金の表示', '@']].forEach(function (f) {
        var c = head.indexOf(f[0]);
        if (c >= 0) sh.getRange(last, c + 1).setNumberFormat(f[1]);
      });
      SpreadsheetApp.flush();
      rows.push(r);
    });
    if (cache) cache.put('req_' + key, rows.map(function (r) { return r['受付番号']; }).join(','), 21600);
  } finally {
    lock.releaseLock();
  }
  rows.forEach(function (r) {
    r['電話番号'] = String(r['電話番号']).replace(/^'/, '');
    sendReceipt_(r);
    var sent = sendWave_(r['受付番号'], 1);
    notifyAdmin_((isTest_(r) ? '【テスト】' : '') + '新しいご依頼 ' + r['受付番号'] + (r['区間'] ? '・' + r['区間'] : '') + '（' + pref + '・' + whenText_(r) + '）',
      rideText_(r) + '\n\nお名前：' + r['お名前'] + '\n電話：' + r['電話番号'] + '\nメール：' + r['メール'] + '\n連絡方法：' + r['連絡方法'] +
      '\n\nお知らせした提携先：' + (sent || 'なし（このエリアの提携先がいません）') + '\n\n▼ 手配ページ（LINEで送る・決定の入力）\n' + adminUrl_(r['受付番号']));
  });
  return split ? { ok: true, id: rows[0]['受付番号'], back_id: rows[1]['受付番号'] } : { ok: true, id: rows[0]['受付番号'] };
}

// 往復を2社に分けた依頼の件名につける印（「・行き」「・帰り」）
function legTag_(r) { return r && r['区間'] ? '・' + String(r['区間']).replace(/（.*$/, '') : ''; }

// 帰りの選択（back_*）を、片道の依頼として確かめる形（partner_id など）に入れ替える
function withPick_(q, id, token, expires) {
  q.partner_id = id; q.quote_token = token; q.quote_expires = expires;
  return q;
}

/* ───────── 提携先へのお知らせ ───────── */

// stage 1: そのエリアの提携先 / stage 2: 近くのエリア＋全国対応
// 戻り値：お知らせした提携先名（カンマ区切り）
function sendWave_(id, stage) {
  var row = findReq_(id);
  if (!row || row.data['状態'] !== ST.OPEN) return '';
  var r = row.data;
  var already = String(r['通知した提携先'] || '').split(',').filter(String);
  var selected = pickedIds_(r);
  if (selected.length && stage !== 1) return '';
  var pool = selected.length ? selectionCandidates_(r).filter(function(pt) { return selected.indexOf(pt.id) >= 0; }) : pickPartners_(r, stage);
  var targets = pool.filter(function (pt) { return already.indexOf(pt.id) < 0; });
  // 第1段で誰もいなければ、すぐ第2段の相手にも送る
  if (!selected.length && stage === 1 && targets.length === 0) {
    stage = 2;
    targets = pickPartners_(r, 2).filter(function (pt) { return already.indexOf(pt.id) < 0; });
  }
  var manual = [];
  targets = targets.filter(function (pt) {
    var how = deliver_(pt, (isQuoteReq_(r) ? '【お見積もりのご依頼】' : '【新しいご依頼】') + r['都府県'] + '・' + whenText_(r), requestText_(r, pt), r);
    if (how === 'manual') manual.push(pt.name);
    return !!how;
  });
  already = already.concat(targets.map(function (pt) { return pt.id; }));
  setReq_(row.rowIndex, { '通知段階': stage, '通知した提携先': already.join(',') });
  log_(id + ' 第' + stage + '段 お知らせ: ' + (targets.map(function (pt) { return pt.id; }).join(',') || 'なし'));
  if (manual.length) {
    notifyAdmin_('LINEで送ってください ' + id + '（' + manual.length + '社）', 'LINE公式アカウントだけで受け付けている会社があります。\n下の手配ページで、会社ごとの「LINEで依頼を送る」を押してください。文面は入力済みなので、LINEが開いたら送信を押すだけです。\n\n' +
      manual.join('、') + '\n\n▼ 手配ページ\n' + adminUrl_(id));
  }
  return targets.map(function (pt) { return pt.name; }).join('、');
}

/* ───────── 提携先への文面 ───────── */

function requestText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\n' +
    'ペットタクシーの手配サービス「' + CONFIG.SERVICE_NAME + '」です。お客さまに代わって、送迎のご相談です。\n' +
    '★お客さまのお名前・ご連絡先は、引き受けが決まった時点でお知らせします（リンクから引き受けた場合はその場で表示されます）。\n\n' +
    rideText_(r) + retAsk_(r) + estText_(r) + '\n■ お支払い：' + payForPartner_(pt) + askText_(pt, r) + '\n\n' +
    (isQuoteReq_(r) ? 'お見積もりのご依頼です。お客さまは、ほかの会社のお見積もりとくらべて1社を選びます。\nお受けいただける場合は、下のリンクからお迎え時刻と確定料金（税込）をご入力ください（数字を入れるだけです）。お客さまが貴社を選んだら、お名前・ご連絡先をお知らせします。\n'
      : needsChoice_(r) ? 'お客さまが選んだ' + pickedIds_(r).length + '社にお声がけしています。お受けいただける場合は、下のリンクからお迎え時刻と確定料金（税込）をご入力ください（数字を入れるだけです）。お客さまが引き受けた会社の中から1社を選んだ時点で決まり、お名前・ご連絡先をお知らせします。\n'
      : 'お受けいただける場合は、下のリンクからお迎え時刻と確定料金（税込）をご入力ください（数字を入れるだけです。先着1社）。\n') + acceptUrl_(r['受付番号'], pt.id) +
    '\n\nご返信でお答えいただく場合は、次のどちらかでお願いします。\n' +
    '・受けられる：お迎え時刻〇時〇分・一般道〇円・高速を使う場合〇円（高速代込み。使わないなら「なし」）' + (isRound_(r) ? '・帰りは「待つ」か「あとで迎え」か' : '') + '\n' +
    '・難しい\n\n' +
    '※ご質問（ペットの様子・建物の入り方など）は、決まったあとにお客さまへ直接お聞きください。\n' +
    '※ご都合が合わない場合、お返事は不要です。';
}

// 引き受ける前に確かめてほしいこと（会社の答えがまだ分からない条件）
function askText_(pt, r) {
  var a = checks_(pt, r).ask;
  return a.length ? '\n\n■ 引き受ける前にご確認ください（できない場合はお受けにならないでください）\n' + a.map(function (x) { return '・' + x; }).join('\n') : '';
}

// お客さまに表示した料金の目安（LPの概算）。無いときは何も足さない
function estText_(r) {
  var fare = num_(r['概算料金']), km = num_(r['概算km']);
  if (!fare) return '';
  return '\n■ お客さまに表示した料金の目安：' + estShown_(r) + (km && !/km/.test(estShown_(r)) ? '（約' + (Math.round(km * 10) / 10) + 'km）' : '') + '\n　※実際の料金は貴社の料金でご提示ください';
}

// LPのフォームに出したとおりの表示（例「11,300〜13,900円」）。無ければ数字から
function estShown_(r) { return String(r['概算料金の表示'] || '').trim() || yen_(num_(r['概算料金'])) + '〜'; }

function isRound_(r) { return /往復/.test(String(r['片道・往復'] || '')); }
var RET_WAYS = ['待つ（病院などで終わるまで待機）', 'あとで迎え（一度戻って、帰りの時刻に迎えに行く）'];
// 往復のときだけ：待つか一度戻るかは、お客さまの料金が安くなるほうを会社に選んでもらう
function retAsk_(r) {
  return isRound_(r) && !r['帰りのやり方'] ? '\n■ 帰りのやり方：病院などで待つか、一度戻ってあとで迎えに行くかは、お客さまの料金が安くなるほうを貴社で選んでください（確定料金は選んだやり方の往復の合計で）' : '';
}
function retWayOf_(v) { return RET_WAYS.filter(function (w) { return w === v; })[0] || ''; }
function retSelect_() {
  return '<label>帰りのやり方（お客さまの料金が安くなるほう）<select name="ret_way" required><option value="">選んでください</option>' +
    RET_WAYS.map(function (w) { return '<option>' + esc_(w) + '</option>'; }).join('') + '</select></label>';
}

function decidedText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\nありがとうございます。こちらのご依頼をお願いすることになりました。\nお客さまへ直接ご連絡をお願いします。\n\n' + customerForPartner_(r);
}

function closedText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\n' + CONFIG.SERVICE_NAME + 'です。先日ご相談した ' + whenText_(r) + ' のご依頼（受付番号 ' + r['受付番号'] + '）は、締め切りとなりました。\nご確認いただき、ありがとうございました。またよろしくお願いします。';
}

function cancelText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\nお客さまがご依頼を取り消されました。お迎えは不要です。\n\n受付番号：' + r['受付番号'] + '\nお迎え予定：' + fmt_(r['お迎え予定']) + '\nお客さま：' + r['お名前'] + ' 様\n\nご対応いただきありがとうございました。';
}

function pickPartners_(r, stage) {
  var pref = r['都府県'];
  var areas = stage === 1 ? [pref] : (NEIGHBORS[pref] || []).concat(['全国']);
  var care = r['介助'] === '必要';
  return partners_().filter(function (pt) {
    if (!pt.active) return false;
    if (CONFIG.SHOW_ALL_CANDIDATES || isDisplayOnly_(pt.id)) return false; // 全社準備中のあいだ・表示だけの会社には送らない
    if (!fitsCar_(pt, r)) return false;
    if (!fitsCage_(pt, r)) return false;
    if (!inTime_(pt, r)) return false;
    if (care && !pt.careOk) return false;
    if (checks_(pt, r).ng.length) return false;
    if (!reachable_(pt)) return false; // 自動で届けられない提携先は対象外
    if (stage === 2 && pt.areas.indexOf(pref) >= 0) return false; // 第1段の相手
    return pt.areas.some(function (a) { return areas.indexOf(a) >= 0; });
  });
}

function partners_() {
  var sh = sheet_(SHEET_PARTNER);
  var vals = sh.getDataRange().getValues();
  var h = vals[0];
  var col = function (name) { return h.indexOf(name); };
  var no = function (v) { return /^(×|x|✕|いいえ|no|false|0|停止|休み)$/i.test(String(v).trim()); };
  // ○ = true / × = false / 空欄 = null（わからない）
  var cell = function (name) { var x = col(name) < 0 ? '' : v[col(name)]; return x == null ? '' : String(x).trim(); };
  var tri = function (name) {
    var t = cell(name);
    return t === '' ? null : !no(t);
  };
  // 数字だけ取り出す。空欄は null
  var num = function (name) {
    var m = cell(name).match(/\d+/);
    return m ? Number(m[0]) : null;
  };
  var out = [];
  for (var i = 1; i < vals.length; i++) {
    var v = vals[i];
    var id = String(v[col('ID')]).trim();
    if (!id) continue;
    out.push({
      row: i + 1, id: id, name: String(v[col('事業者名')]).trim(), person: String(v[col('担当者名')]).trim(),
      areas: String(v[col('対応エリア')]).split(/[,、，\s・\/]+/).map(shortPref_).filter(String),
      email: String(v[col('メール')]).trim(), tel: String(v[col('電話番号')]).trim(),
      oaId: normOaId_(col('LINE公式ID（先方）') >= 0 ? v[col('LINE公式ID（先方）')] : ''),
      lineUrl: lineUrlOf_(col('LINE公式ID（先方）') >= 0 ? v[col('LINE公式ID（先方）')] : ''),
      active: !no(v[col('受付中')]), careOk: !no(v[col('介助OK')]),
      lineCode: String(v[col('LINE登録コード')]).trim(), lineId: String(v[col('LINE userId')]).trim(),
      big: tri('大型犬OK'), luggage: tri('荷物多めOK'), riders: num('同乗できる人数'), pets: num('乗せられるペット数'),
      car: cell('車のタイプ'),
      cageMust: cell('ケージ必須'), cageLend: tri('ケージ貸し出し'),
      payMethod: cell('支払い方法'), payWhen: cell('支払いのタイミング'),
      hours: cell('営業時間'), lead: num('何時間前まで'),
      careTri: tri('介助OK'), rideHours: cell('送迎できる時間'), maxKg: num('大型犬の最大kg'), maxBig: num('大型犬の最大頭数'),
      lendKg: num('貸し出しケージの最大kg'), petOnly: tri('ペットだけOK'), vacMust: tri('ワクチン必須')
    });
  }
  return out;
}

// 届けられる窓口があるか（電話だけの会社は対象外）
function reachable_(pt) {
  return !!(pt.email || (pt.lineId && CONFIG.LINE_CHANNEL_ACCESS_TOKEN) || pt.oaId || pt.lineUrl);
}

// 依頼の中身（人数・ペット数・大型犬・荷物）
function needs_(r) {
  var m = String(r['同乗人数'] || '').match(/\d+/);
  return {
    riders: m ? Number(m[0]) : 1,
    pets: Number(r['ペット数']) || 1,
    big: Number(r['体重kg']) >= CONFIG.LARGE_DOG_KG,
    luggage: /多/.test(String(r['荷物'] || ''))
  };
}

// ケージの希望に合うか（お客さまの「キャリー」欄：持ち込む／なし／借りたい、「・」区切りで複数あり）
// ・借りたい → 「ケージ貸し出し」が×の会社は対象外（空欄は外さず、checks_ で会社が確かめる）
// ・なし     → 「ケージ必須」が○の会社は対象外。「ペットだけ」の会社は、飼い主さんが乗らないときだけ対象外
// ・どれでも → 会社のやり方に合わせられるので、しぼりこまない
function fitsCage_(pt, r) {
  var c = String(r['キャリー'] || '');
  var rent = /借り|持っていない/.test(c), none = /なし/.test(c);
  if (rent && pt.cageLend === false) return false;
  if (none) {
    var must = pt.cageMust;
    if (must !== '' && !/^(×|✕|x|X|いいえ|不要|NG)$/.test(must)) {
      if (!/ペットだけ/.test(must)) return false;
      if (needs_(r).riders === 0) return false;
    }
  }
  return true;
}

// 間に合うか：メールを読めるのは営業時間だけ。読める時刻からお迎えまで「何時間前まで」以上あること
function inTime_(pt, r, now) {
  var lead = pt.lead === null || pt.lead === undefined ? CONFIG.DEFAULT_LEAD_HOURS : pt.lead;
  var at = parseJst_(defaultAt_(r));
  if (!at) return true;
  var seen = nextOpen_(now ? new Date(now) : new Date(), pt.hours || CONFIG.DEFAULT_PARTNER_HOURS);
  return at.getTime() - seen.getTime() >= lead * 3600000;
}

// 「8-18」「8:00〜18:00」→ [8, 18]。日をまたぐ「20-5」「20時〜翌5時」→ [20, 5]
function hoursOf_(v) {
  var m = toHalf_(v).match(/(\d{1,2})(?::\d{2})?\s*時?\s*[-~〜～]\s*翌?\s*(\d{1,2})/);
  return m ? [Number(m[1]), Number(m[2])] : [0, 24];
}
// hr（0〜24の時刻）が時間帯 h に入っているか（日をまたぐ時間帯も）
function inHours_(hr, h) {
  return h[0] <= h[1] ? hr >= h[0] && hr < h[1] : hr >= h[0] || hr < h[1];
}

// その時刻が営業時間ならそのまま、外なら次に開く時刻（日本時間）
function nextOpen_(d, hours) {
  var h = hoursOf_(hours), j = new Date(d.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
  if (inHours_(hr, h)) return d;
  var day = Date.UTC(j.getUTCFullYear(), j.getUTCMonth(), j.getUTCDate()) + (h[0] <= h[1] && hr >= h[1] ? 86400000 : 0);
  return new Date(day + (h[0] - 9) * 3600000);
}

// from〜to のうち、営業時間に入っている分数
function openMinutes_(from, to, hours) {
  var t = new Date(from).getTime(), end = new Date(to).getTime(), min = 0;
  for (var guard = 0; t < end && guard < 30; guard++) {
    var o = nextOpen_(new Date(t), hours).getTime();
    if (o >= end) break;
    var j = new Date(o + 9 * 3600000), close = Date.UTC(j.getUTCFullYear(), j.getUTCMonth(), j.getUTCDate()) + (hoursOf_(hours)[1] - 9) * 3600000;
    var stop = Math.min(close, end);
    min += Math.max(0, stop - o) / 60000;
    t = stop + 1;
  }
  return min;
}

// 車に乗るか。分かっている値だけで外す（空欄は外さず、checks_ の「確かめること」で会社が引き受けるときに確かめる。
// 前は空欄を軽バンとみなして黙って外していたので、3匹以上・荷物多めで受けられる会社も出なかった。2026-10-31）
function fitsCar_(pt, r) {
  var n = needs_(r);
  if (pt.riders !== null && n.riders > pt.riders) return false;
  if (pt.pets !== null && n.pets > pt.pets) return false;
  if (n.big && pt.big === false) return false;
  if (n.luggage && pt.luggage === false) return false;
  return true;
}

// 依頼の条件を会社ごとに1つずつ確かめる。ng＝受けられないと分かっている（候補に出さない）、
// ask＝会社の答えがまだ分からない、または組み合わせ次第の条件（候補には出し、引き受けるときに会社がチェックして確かめる。Nori 2026-10-31）
function petsOf_(r) {
  var a;
  try { a = JSON.parse(r['ペットJSON'] || '[]'); } catch (e) { a = []; }
  if (!Array.isArray(a) || !a.length) a = [{ weight: r['体重kg'], care: r['介助'] }];
  if (a.length === 1 && !a[0].species) a[0].species = r['種類'];
  return a.map(function (p) { return { kg: Number(p.weight) || 0, care: p.care || '', vac: p.vaccine === '済', sp: String(p.species || ''), breed: String(p.breed || ''), need: (p.care_need || []).concat(p.care_note ? [p.care_note] : []) }; });
}
// 犬・猫のほかの子の種類（small＝うさぎ・フェレット・ハムスターなどの小動物、bird＝鳥、reptile＝爬虫類・両生類、fish＝魚、other＝そのほか）。犬・猫なら ''
// フォームの「その他」で選んだ種類（種類の欄に入る）と、くわしい種類の欄から読む（Nori 2026-10-31「犬、猫以外の動物の利用もできる事業者さん」）
function animalKind_(p) {
  var sp = String(p.sp || ''), t = sp + ' ' + String(p.breed || '');
  if (!sp || /^(犬|猫)$/.test(sp)) return '';
  if (/鳥|インコ|オウム|文鳥|カナリア/.test(t)) return 'bird';
  if (/爬虫|両生|カメ|亀|トカゲ|ヘビ|蛇|カエル|イモリ/.test(t)) return 'reptile';
  if (/魚|金魚|メダカ|鯉/.test(t)) return 'fish';
  if (/うさぎ|ウサギ|フェレット|ハムスター|モルモット|チンチラ|リス|りす|ハリネズミ|デグー|小動物/.test(t)) return 'small';
  return 'other';
}
var ANIMAL_LABEL = {small:'小動物', bird:'鳥', reptile:'爬虫類', fish:'魚', other:'犬・猫のほかの子'};
// 表示だけの会社が、犬・猫のほかの子を乗せられるか。true＝サイトに書いてある、false＝断る・犬猫のみと書いてある、null＝分からない
function displayAnimalOk_(c, kind) {
  var a = c.animals || {};
  if ((a.no || []).indexOf(kind) >= 0 || a.only) return false;
  if (a.all || (a.ok || []).indexOf(kind) >= 0) return true;
  return null;
}

// 軽バン（スズキ エブリイ・ホンダ N-VAN・ダイハツ ハイゼット/アトレー など）か。予約シート「車のタイプ」から読む
function isVan_(pt) { return /軽バン|エブリ|N-?VAN|ハイゼット|アトレー|クリッパー/i.test(String(pt.car || '')); }
function checks_(pt, r) {
  var ng = [], ask = [], n = needs_(r), pets = petsOf_(r);
  var bigs = pets.filter(function (p) { return p.kg >= CONFIG.LARGE_DOG_KG; }), maxKg = Math.max.apply(null, pets.map(function (p) { return p.kg; }));
  // 時間：お迎え（往復なら帰りも）が送迎できる時間に入っているか
  [r['希望日時'], r['帰りの日時']].forEach(function (t, i) {
    var at = t ? new Date(t) : null;
    if (!at || !isFinite(at.getTime()) || (i === 0 && r['日付のみ'])) return;
    var j = new Date(at.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
    var label = (i ? '帰りの' : '') + 'お迎え ' + j.getUTCHours() + ':' + ('0' + j.getUTCMinutes()).slice(-2);
    if (pt.rideHours) { if (!inHours_(hr, hoursOf_(pt.rideHours))) ng.push(label + '（送迎できる時間の外）'); }
    else if (!inHours_(hr, hoursOf_(pt.hours || CONFIG.DEFAULT_PARTNER_HOURS))) ask.push(label + 'に送迎できる');
  });
  // 人数・頭数・荷物
  if (pt.riders !== null && n.riders > pt.riders) ng.push('大人' + n.riders + '人');
  else if (pt.riders === null && n.riders >= 2) ask.push('大人' + n.riders + '人が一緒に乗れる'); // 定員が分からない会社は2人から確かめる
  if (pt.pets !== null && n.pets > pt.pets) ng.push(n.pets + '匹');
  else if (pt.pets === null && n.pets >= 2) ask.push(n.pets + '匹が一緒に乗れる');
  if (n.luggage && pt.luggage === false) ng.push('荷物が多い');
  else if (n.luggage && pt.luggage === null) ask.push('多めの荷物（スーツケース・大きなケージなど）が載る');
  // 種類：犬・猫のほかの子は、乗せられるかを会社ごとに確かめる
  pets.filter(function (p) { return animalKind_(p); }).forEach(function (p) {
    ask.push('犬・猫のほかの子（' + (p.breed || p.sp) + '）を乗せられる');
  });
  // 大きさ
  if (bigs.length) {
    if (pt.big === false) ng.push('大型犬');
    else if (pt.maxKg !== null && maxKg > pt.maxKg) ng.push(maxKg + 'kgの子（' + pt.maxKg + 'kgまで）');
    else if (pt.maxKg === null && maxKg >= CONFIG.ASK_KG) ask.push(maxKg + 'kgの子が乗れる'); // 20〜29kgは軽バンでも乗れるので聞かない
    var maxBig = pt.maxBig !== null ? pt.maxBig : isVan_(pt) ? CONFIG.VAN_BIG_DOGS : null;
    if (maxBig !== null && bigs.length > maxBig) ng.push('大型犬' + bigs.length + '頭' + (pt.maxBig === null ? '（軽バンは' + maxBig + '頭まで）' : ''));
    else if (maxBig === null && bigs.length >= 2) ask.push('大型犬' + bigs.length + '頭が一緒に乗れる');
    if (n.riders + bigs.length >= 3) ask.push('大型犬' + bigs.length + '頭と大人' + n.riders + '人が一緒に乗れる');
  }
  // ケージ
  if (!fitsCage_(pt, r)) ng.push('ケージの条件');
  else {
    var c = String(r['キャリー'] || '');
    if (/借り|持っていない/.test(c)) {
      if (pt.cageLend === null) ask.push('ケージを貸し出せる' + (maxKg ? '（' + maxKg + 'kgの子が入るもの）' : '')); // 貸し出しがあるか分からない会社
      else if (pt.lendKg !== null && maxKg > pt.lendKg) ng.push(maxKg + 'kgの子が入るケージの貸し出し');
      else if (pt.lendKg === null && maxKg >= 10) ask.push(maxKg + 'kgの子が入るケージを貸し出せる'); // 小さい子のケージはどこでも用意できる
    }
    if (/なし/.test(c) && pt.cageMust === '') ask.push('ケージなしで乗れる');
    // 「どちらでもいい」でも、会社がケージを使うなら大型犬が入る大きさを持っているか確かめる（Nori 2026-10-31）
    if (/どれでも/.test(c) && bigs.length && pt.cageLend !== false && pt.lendKg === null) ask.push('ケージを使う場合、' + maxKg + 'kgの子が入る大きさのケージを用意できる');
  }
  // 介護
  var careNeed = r['介助'] === '必要' || pets.some(function (p) { return p.care === '必要'; });
  if (careNeed) {
    if (pt.careTri === false) ng.push('介護が必要な子');
    var what = [].concat.apply([], pets.map(function (p) { return p.need; }));
    ask.push('介護が必要な子の送迎' + (what.length ? '（' + what.join('／') + '）' : '') + 'ができる');
  }
  // ペットだけ
  if (n.riders === 0) {
    if (pt.petOnly === false) ng.push('ペットだけの送迎');
    else if (pt.petOnly === null) ask.push('飼い主さんが乗らない、ペットだけの送迎ができる');
  }
  // 夜間・早朝の割増の境目の近く（1時間以内）に乗るときは、またいだ分の料金の決まりが会社ごとに違うので確かめてもらう
  var fk = typeof SELECTION_FARES !== 'undefined' && SELECTION_FARES ? Object.keys(SELECTION_FARES).filter(function (k) { return SELECTION_FARES[k].partner_id === pt.id; })[0] : null;
  var nh = fk && SELECTION_FARES[fk].night > 1 && SELECTION_FARES[fk].night_hours;
  if (nh && [r['希望日時'], r['帰りの日時']].some(function (t) {
    var at = t ? new Date(t) : null; if (!at || !isFinite(at.getTime())) return false;
    var j = new Date(at.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
    return nh.some(function (b) { var dlt = b - hr; return dlt > 0 && dlt <= 1; });
  })) ask.push('割増の時間（' + nh[0] + '時〜' + nh[1] + '時）をまたぐ分も、確定料金に入れる');
  // ワクチン
  if (pt.vacMust === true && pets.some(function (p) { return !p.vac; })) ask.push('混合ワクチンの接種が記入されていない子がいるが、乗れる');
  return { ng: ng, ask: ask };
}

// 「@ID」ではなく line.me のURL（個人アカウントなど）が書かれている場合。文面の入力済みでは開けないので、コピーして貼る
function lineUrlOf_(v) {
  var s = String(v || '').trim();
  return /^https:\/\/(line\.me|lin\.ee)\//.test(s) && !/\/@[\w.\-]+/.test(s) ? s : '';
}

// 先方LINE公式のID（@abc123）。@がなければ付ける。lin.ee のURLなどIDでないものは使えない
function normOaId_(v) {
  var s = toHalf_(v).replace(/\s/g, '');
  var m = s.match(/\/(@[\w.\-]+)/); // https://line.me/R/ti/p/@abc123 の形でもOK
  if (m) return m[1];
  if (!s || /[\/:]/.test(s)) return '';
  return s.charAt(0) === '@' ? s : '@' + s;
}

// 運営者のLINEで、先方の公式アカウントあての文面を入力済みで開くリンク
function oaLink_(pt, text) {
  return 'https://line.me/R/oaMessage/' + pt.oaId + '/?' + encodeURIComponent(text);
}

function partnerById_(id) {
  return partners_().filter(function (pt) { return pt.id === id; })[0] || null;
}

/* ───────── 引き受け・取り消しページ ───────── */

var JSON_PAGE = false; // LPの /go/ ページから fmt=json で呼ばれたとき true（ページをJSONで返す）

function doGet(e) {
  var q = (e && e.parameter) || {};
  JSON_PAGE = q.fmt === 'json';
  try {
    if (q.a === 'accept') return acceptPage_(q);
    if (q.a === 'cancel') return cancelPage_(q);
    if (q.a === 'choose') return choosePage_(q);
    if (q.a === 'admin') return adminPage_(q);
    if (q.a === 'prefill') return prefill_(q);
    if (q.a === 'dash') return dashPage_(q);
  } catch (err) {
    log_('ページエラー: ' + err);
    return page_('エラー', '<p>うまく表示できませんでした。時間をおいてもう一度お試しください。</p>');
  }
  return page_(CONFIG.SERVICE_NAME, '<p><a href="' + esc_(CONFIG.SITE_URL) + '" target="_top">トップページへ</a></p>');
}

function acceptPage_(q) {
  if (!q.id || !q.p || q.k !== sign_(q.id + ':' + q.p)) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメール（LINE）のリンクからもう一度開いてください。</p>');
  var pt = partnerById_(q.p);
  var row = findReq_(q.id);
  if (!pt || !row) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  var r = row.data;

  if (q.go === '1') {
    var fare = Number(String(q.fare || '').replace(/[^\d]/g, ''));
    var at = parseJst_(q.at);
    var way = retWayOf_(q.ret_way);
    var asks = checks_(pt, r).ask;
    if (asks.some(function (x, i) { return q['ok' + i] !== '1'; })) return page_('確認が終わっていません', '<p>「引き受ける前にご確認ください」の項目に、すべてチェックを入れてください。できない項目があるときは、お受けにならないでください。</p><p><a href="javascript:history.back()">戻る</a></p>');
    if (!fare || !at || (isRound_(r) && !way)) return page_('入力が足りません', '<p>お迎え時刻・確定料金（円）' + (isRound_(r) ? '・帰りのやり方' : '') + 'を入れてください。</p><p><a href="javascript:history.back()">戻る</a></p>');
    if (needsChoice_(r)) {
      var qr = quote_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way);
      if (!qr.ok) return page_('締め切りました', '<p>' + esc_(qr.msg) + '</p>');
      return page_(isQuoteReq_(r) ? 'お見積もりを送りました' : '引き受けのお返事を送りました', '<p>お客さまに' + (isQuoteReq_(r) ? 'お見積もり' : '引き受けのお返事と確定料金') + 'をお届けしました。<b>お客さまが貴社を選んだら、お名前・ご連絡先をメールでお知らせします。</b>選ばれなかったときは「締め切り」のお知らせをお送りします。</p>');
    }
    var res = accept_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way);
    if (!res.ok) return page_('締め切りました', '<p>' + esc_(res.msg) + '</p>');
    var c = res.r;
    return page_('ありがとうございます！決まりました', '<p>お客さまに「決まりました」とお知らせしました。<b>お客さまへ直接ご連絡をお願いします。</b>この画面の内容を控えておいてください。</p>' +
      '<div class="box">' + nl2br_(esc_(customerForPartner_(c))) + '</div>');
  }

  if (r['状態'] === ST.DONE && r['決定した提携先ID'] === pt.id) {
    return page_('あなたに決まっています', '<p>お客さまへ直接ご連絡をお願いします。</p><div class="box">' + nl2br_(esc_(customerForPartner_(r))) + '</div>');
  }
  if (r['状態'] !== ST.OPEN) return page_('締め切りました', '<p>このご依頼は締め切りました。ご確認ありがとうございました。</p>');
  var quoted = needsChoice_(r) && quotesOf_(r).filter(function (x) { return x.pid === pt.id; })[0];
  if (quoted) return page_(isQuoteReq_(r) ? 'お見積もりをお送り済みです' : 'お返事をお送り済みです', '<p>確定料金 ' + esc_(fareText_(quoted.fare, quoted.fareHw)) + '・お迎え予定 ' + esc_(fmt_(new Date(quoted.at))) + ' でお客さまにお届けしています。お客さまが選んだらお知らせします。</p>');
  var def = defaultAt_(r);
  var html = '<p>' + esc_(pt.name) + ' 様</p>' +
    (isQuoteReq_(r) ? '<div class="box"><b>お見積もりのご依頼です。</b>入れた確定料金をお客さまにお届けし、お客さまがほかの会社とくらべて1社を選びます。選ばれたら、お名前・ご連絡先をお知らせします。</div>'
      : needsChoice_(r) ? '<div class="box"><b>お客さまが' + pickedIds_(r).length + '社にお声がけしています。</b>引き受ける場合は確定料金を入れてください。お客さまが引き受けた会社の中から1社を選んだ時点で決まり、お名前・ご連絡先をお知らせします。</div>'
      : '<div class="box"><b>お客さまのお名前・電話番号・メールは、下の「引き受ける」を押すとすぐにこの画面に表示されます。</b>同じ内容をメールでもお送りします。先着1社です。</div>') +
    '<div class="box">' + nl2br_(esc_(rideText_(r) + retAsk_(r) + '\n■ お支払い：' + payForPartner_(pt))) + '</div>' +
    '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' +
    hidden_('a', 'accept') + hidden_('id', q.id) + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') +
    askBoxes_(pt, r) +
    '<label>お迎え予定の時刻<input type="datetime-local" name="at" value="' + def + '" required></label>' +
    (isRound_(r) ? retSelect_() : '') +
    '<label>確定料金・一般道で行く場合（円・税込' + (isRound_(r) ? '、往復の合計' : '') + '）<input type="number" name="fare" inputmode="numeric" min="0" step="10" placeholder="例：4800" required></label>' +
    '<label>確定料金・高速道路を使う場合（円・税込、高速代込み）<input type="number" name="fare_hw" inputmode="numeric" min="0" step="10" placeholder="高速を使わないなら空欄"></label>' +
    '<p class="note">入れた金額を、お客さまに確定の料金としてお伝えします。</p>' +
    '<label>お客さまへ一言（なくてもOK）<textarea name="msg" maxlength="300" placeholder="例：前日にお電話します"></textarea></label>' +
    '<button type="submit">' + (isQuoteReq_(r) ? 'この内容でお見積もりを送る' : 'この内容で引き受ける') + '</button></form>' +
    '';
  return page_(isQuoteReq_(r) ? 'お見積もりを出しますか？' : 'ご依頼を引き受けますか？', html);
}

// 引き受け画面のチェック欄（すべてにチェックしないと引き受けられない）
function askBoxes_(pt, r) {
  var a = checks_(pt, r).ask;
  if (!a.length) return '';
  return '<div class="box"><b>引き受ける前にご確認ください</b>（できない項目があるときは、お受けにならないでください）' +
    a.map(function (x, i) { return '<label style="display:flex;gap:8px;align-items:flex-start;font-weight:400"><input type="checkbox" name="ok' + i + '" value="1" required style="width:auto;margin-top:4px"> ' + esc_(x) + '</label>'; }).join('') + '</div>';
}

function accept_(id, pt, at, fare, msg, fareHw, retWay) {
  fareHw = fareHw || '';
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var row;
  try {
    row = findReq_(id);
    if (!row || row.data['状態'] !== ST.OPEN) {
      var mine = row && row.data['状態'] === ST.DONE && row.data['決定した提携先ID'] === pt.id;
      return { ok: false, msg: mine ? 'このご依頼はすでにこの会社に決まっています。' : '申し訳ありません、ほかの方が先に引き受けたか、受付が終わりました。' };
    }
    if (pickedIds_(row.data).length && pickedIds_(row.data).indexOf(pt.id) < 0) return {ok:false,msg:'お客さまが選んだ会社と異なるため引き受けできません。'};
    setReq_(row.rowIndex, {
      '状態': ST.DONE, '決定した提携先ID': pt.id, '決定した提携先': pt.name, 'お迎え予定': at,
      '料金の目安': fare, '高速利用時の料金': fareHw, '帰りのやり方': retWay || '', '提携先から一言': msg, '決定日時': new Date()
    });
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
  var r = findReq_(id).data;
  bumpCount_(pt);
  log_(id + ' 決定: ' + pt.id);

  var cancelUrl = cancelUrl_(id);
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】お迎えが決まりました（受付番号 ' + id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\nペットタクシーが決まりました！\n\n' +
    '■ ペットタクシー：' + pt.name + '\n' +
    '■ お迎え予定：' + fmt_(at) + '\n' +
    '■ 料金（確定・税込）：' + fareText_(fare, fareHw) + '\n' +
    (retWay ? '■ 帰りのやり方：' + retWay + '（料金が安くなるほうをペットタクシーに選んでもらいました）\n' : '') +
    '■ お支払い：' + payForCustomer_(pt) + '\n' +
    (msg ? '■ ペットタクシーから：' + msg + '\n' : '') +
    '\nこのあと「' + pt.name + '」から、ご連絡先あてに直接ご連絡があります。ペットの様子などのご質問も、ペットタクシーと直接やりとりしてください。\n\n' +
    '▼ 取り消す場合はこちら（当サイトのキャンセル料はありません。ペットタクシーのキャンセル規定は、この会社の案内をご確認ください）\n' + cancelUrl);
  var how = deliver_(pt, '【決定】' + id + ' お客さまのご連絡先', decidedText_(r, pt), r);
  closeOthers_(r, pt.id);
  notifyAdmin_((how === 'manual' ? '【LINEで決定を伝えてください】' : '') + '決定 ' + id + '：' + pt.name,
    (how === 'manual' ? pt.name + 'はLINE公式アカウントだけの会社です。手配ページの「決定をLINEで伝える」を押してください（お客さまの連絡先が入った文面です）。\n\n' : '') +
    '■ ' + pt.name + '\n■ お迎え予定：' + fmt_(at) + '\n■ 確定料金：' + fareText_(fare, fareHw) + '\n\n' + rideText_(r) + '\n\n▼ 手配ページ\n' + adminUrl_(id));
  return { ok: true, r: r };
}

/* ───────── 見積もり依頼（2026-10-31 Nori「見積もり依頼か予約依頼かはユーザに選択できるように」） ───────── */

// 会社のお見積もりを受け取り、お客さまに「この会社に決める」リンクつきでお届けする。お客さまの連絡先はまだ渡さない
function quote_(id, pt, at, fare, msg, fareHw, retWay) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var r;
  try {
    var row = findReq_(id);
    if (!row || row.data['状態'] !== ST.OPEN) return { ok: false, msg: 'このご依頼は締め切りました。ご確認ありがとうございました。' };
    if (pickedIds_(row.data).indexOf(pt.id) < 0) return { ok: false, msg: 'お客さまが選んだ会社と異なるため、お見積もりを出せません。' };
    var list = quotesOf_(row.data).filter(function (x) { return x.pid !== pt.id; });
    list.push({ pid: pt.id, at: at.getTime(), fare: fare, fareHw: fareHw || '', way: retWay || '', msg: msg || '', time: Date.now() });
    setReq_(row.rowIndex, { '見積もりJSON': JSON.stringify(list) });
    SpreadsheetApp.flush();
    r = findReq_(id).data;
  } finally {
    lock.releaseLock();
  }
  log_(id + ' 見積もり: ' + pt.id + ' ' + fare);
  var word = isQuoteReq_(r) ? 'お見積もり' : '引き受けのお返事';
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】' + word + 'が届きました：' + pt.name + '（受付番号 ' + id + '）',
    r['お名前'] + ' 様\n\n「' + pt.name + '」から' + word + 'が届きました。まだ予約は決まっていません。\n\n' +
    '■ ペットタクシー：' + pt.name + '\n■ お迎え予定：' + fmt_(at) + '\n■ 料金（確定・税込）：' + fareText_(fare, fareHw) + '\n' +
    (retWay ? '■ 帰りのやり方：' + retWay + '\n' : '') + '■ お支払い：' + payForCustomer_(pt) + '\n' + (msg ? '■ ペットタクシーから：' + msg + '\n' : '') +
    '\n▼ この会社に決める（押すと予約が決まり、この会社からご連絡があります）\n' + chooseUrl_(id, pt.id) +
    '\n\nほかの会社の' + word + 'も、届きしだいお送りします。くらべてから決めてかまいません。どの会社にも決めない場合は、何もしなくて大丈夫です（下のリンクで取り消すこともできます）。\n' + cancelUrl_(id));
  notifyAdmin_(word + ' ' + id + '：' + pt.name, '■ ' + pt.name + '\n■ お迎え予定：' + fmt_(at) + '\n■ 確定料金：' + fareText_(fare, fareHw) + '\n\n' + rideText_(r));
  return { ok: true };
}

function chooseUrl_(id, pid) { return linkBase_() + '?a=choose&id=' + encodeURIComponent(id) + '&p=' + encodeURIComponent(pid) + '&k=' + sign_(id + ':' + pid + ':choose'); }

// お客さまが見積もりの中から1社に決めるページ
function choosePage_(q) {
  if (!q.id || !q.p || q.k !== sign_(q.id + ':' + q.p + ':choose')) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var row = findReq_(q.id), pt = partnerById_(q.p);
  if (!row || !pt) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  var r = row.data, qt = quotesOf_(r).filter(function (x) { return x.pid === pt.id; })[0];
  if (r['状態'] === ST.DONE) return page_(r['決定した提携先ID'] === pt.id ? 'この会社に決まっています' : 'ほかの会社に決まっています', '<p>' + esc_(r['決定した提携先'] || '') + 'に決まっています。決定のメールをご確認ください。</p>');
  if (r['状態'] !== ST.OPEN || !qt) return page_('締め切りました', '<p>このご依頼は締め切りました。</p>');
  if (q.go === '1') {
    var res = accept_(q.id, pt, new Date(qt.at), qt.fare, qt.msg, qt.fareHw, qt.way);
    if (!res.ok) return page_('決められませんでした', '<p>' + esc_(res.msg) + '</p>');
    return page_('決まりました', '<p>「' + esc_(pt.name) + '」に決まりました。決定のメールをお送りしました。このあと、' + esc_(pt.name) + 'からご連絡があります。</p>');
  }
  return page_('この会社に決めますか？', '<div class="box">■ ペットタクシー：' + esc_(pt.name) + '<br>■ お迎え予定：' + esc_(fmt_(new Date(qt.at))) + '<br>■ 料金（確定・税込）：' + esc_(fareText_(qt.fare, qt.fareHw)) +
    (qt.way ? '<br>■ 帰りのやり方：' + esc_(qt.way) : '') + '<br>■ お支払い：' + esc_(payForCustomer_(pt)) + '</div>' +
    '<p>決めると、ほかの会社へのご依頼は締め切ります。</p>' +
    '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'choose') + hidden_('id', q.id) + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') +
    '<button type="submit">この会社に決める</button></form>');
}

/* ───────── 運営者の手配ページ（LINEで送る・決定の入力） ───────── */

function adminPage_(q) {
  if (!q.id || q.k !== sign_(q.id + ':admin')) return page_('リンクが正しくありません', '<p>運営者あてのメールのリンクから開いてください。</p>');
  var row = findReq_(q.id);
  if (!row) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  var notice = '';

  if (q.go === '1') { // 返信で答えてきた会社に決める
    var pt = partnerById_(q.p);
    var fare = Number(String(q.fare || '').replace(/[^\d]/g, ''));
    var at = parseJst_(q.at);
    var way = retWayOf_(q.ret_way);
    if (!pt || !fare || !at || (isRound_(row.data) && !way)) {
      notice = '<p class="note"><b>会社・お迎え時刻・確定料金' + (isRound_(row.data) ? '・帰りのやり方' : '') + 'を入れてください。</b></p>';
    } else {
      var res = accept_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way);
      notice = '<p class="note"><b>' + esc_(res.ok ? '決定しました。お客さまへお知らせを送りました。' : res.msg) + '</b></p>';
    }
    row = findReq_(q.id);
  } else if (q.wave === '2') {
    var sent = sendWave_(q.id, 2);
    notice = '<p class="note"><b>近くのエリア・全国対応の会社にも送りました：' + esc_(sent || 'なし') + '</b></p>';
    row = findReq_(q.id);
  }

  var r = row.data;
  var st = r['状態'];
  var asked = String(r['通知した提携先'] || '').split(',').filter(String).map(partnerById_).filter(Boolean);
  var winner = st === ST.DONE || (st === ST.CANCEL && r['決定した提携先ID']) ? partnerById_(r['決定した提携先ID']) : null;
  var auto = function (pt) { return pt.email || (pt.lineId && CONFIG.LINE_CHANNEL_ACCESS_TOKEN); };
  var html = notice + '<p>状態：<b>' + esc_(st) + '</b>' + (winner ? '（' + esc_(winner.name) + '）' : '') + '</p>' +
    '<div class="box">' + nl2br_(esc_('受付番号：' + r['受付番号'] + '\n' + rideText_(r) + '\n\nお名前：' + r['お名前'] + '\n電話：' + String(r['電話番号']).replace(/^'/, '') + '\nメール：' + r['メール'])) + '</div>';

  if (st === ST.OPEN) {
    html += '<h2>声をかけた会社</h2>';
    asked.forEach(function (pt) {
      html += '<div class="pt"><b>' + esc_(pt.name) + '</b><br><span class="note">' + (auto(pt) ? '自動で送信済み' : 'LINE公式だけの会社です。下のボタンで送ってください') + '</span>' +
        lineAction_(pt, 'LINEで依頼を送る' + (auto(pt) ? '（任意）' : ''), requestText_(r, pt)) + '</div>';
    });
    if (!asked.length) html += '<p class="note">まだどこにも送れていません。</p>';
    if (!pickedIds_(r).length && Number(r['通知段階']) < 2) {
      html += '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'admin') + hidden_('id', q.id) + hidden_('k', q.k) + hidden_('wave', '2') +
        '<button type="submit" class="gray">近くのエリア・全国対応の会社にも今すぐ送る</button></form>';
    }
    if (asked.length) {
      var def = defaultAt_(r);
      html += '<h2>返信で答えてきた会社に決める</h2><p class="note">リンクから入力してもらえた場合は自動で決まるので、ここは不要です。</p>' +
        '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'admin') + hidden_('id', q.id) + hidden_('k', q.k) + hidden_('go', '1') +
        '<label>会社<select name="p" required>' + asked.map(function (pt) { return '<option value="' + esc_(pt.id) + '">' + esc_(pt.name) + '</option>'; }).join('') + '</select></label>' +
        '<label>お迎え予定の時刻<input type="datetime-local" name="at" value="' + def + '" required></label>' +
        (isRound_(r) ? retSelect_() : '') +
        '<label>確定料金・一般道（円・税込）<input type="number" name="fare" inputmode="numeric" min="0" step="10" required></label>' +
        '<label>確定料金・高速を使う場合（円・税込、なければ空欄）<input type="number" name="fare_hw" inputmode="numeric" min="0" step="10"></label>' +
        '<label>会社からの一言（なくてもOK）<textarea name="msg" maxlength="300"></textarea></label>' +
        '<button type="submit">この会社に決めて、お客さまに知らせる</button></form>';
    }
  } else {
    var btns = '';
    if (winner && (winner.oaId || winner.lineUrl) && !auto(winner)) {
      btns += st === ST.CANCEL ? lineBtn_(winner, '取り消しをLINEで伝える', cancelText_(r, winner)) : lineBtn_(winner, '決定をLINEで伝える', decidedText_(r, winner));
    }
    asked.forEach(function (pt) {
      if ((pt.oaId || pt.lineUrl) && !auto(pt) && (!winner || pt.id !== winner.id)) btns += lineBtn_(pt, '締め切りをLINEで伝える', closedText_(r, pt));
    });
    html += btns ? '<h2>LINEで伝えること</h2>' + btns : '<p class="note">LINEで伝えることはありません。連絡はすべて自動で送りました。</p>';
  }
  return page_('手配ページ ' + r['受付番号'], html);
}

function lineBtn_(pt, label, text) {
  return '<div class="pt"><b>' + esc_(pt.name) + '</b>' + lineAction_(pt, label, text) + '</div>';
}

// @IDなら文面入りでトークを開く。URLだけの相手は、文面をコピーしてからトークを開く
function lineAction_(pt, label, text) {
  if (pt.oaId) return '<a class="line" href="' + esc_(oaLink_(pt, text)) + '">' + esc_(label) + '</a>';
  if (!pt.lineUrl) return '';
  return '<textarea readonly onclick="this.select()" style="min-height:120px">' + esc_(text) + '</textarea>' +
    '<button type="button" class="gray" onclick="var t=this.previousElementSibling;t.select();document.execCommand(\'copy\');this.textContent=\'コピーしました\'">1. 文面をコピー</button>' +
    '<a class="line" href="' + esc_(pt.lineUrl) + '">2. LINEを開いて貼り付け（' + esc_(label) + '）</a>';
}

function cancelPage_(q) {
  if (!q.id || q.k !== sign_(q.id + ':cancel')) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var row = findReq_(q.id);
  if (!row) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  var r = row.data;
  if (r['状態'] === ST.CANCEL) return page_('取り消し済みです', '<p>このご依頼はすでに取り消されています。</p>');
  if (r['状態'] === ST.NONE) return page_('受付は終了しています', '<p>このご依頼は受付が終わっています。取り消しの手続きは不要です。</p>');

  if (q.go === '1') {
    var res = cancel_(q.id);
    return page_('取り消しました', '<p>' + esc_(res.msg) + '</p><p>またいつでもご利用ください。</p>');
  }
  var warn = '';
  if (r['状態'] === ST.DONE) {
    var left = (r['お迎え予定'].getTime() - Date.now()) / 3600000;
    warn = '<p class="note">ペットタクシー「' + esc_(r['決定した提携先']) + '」に決まっています。取り消すと、こちらからペットタクシーへお伝えします。' +
      (left < 2 ? '<br><b>お迎えまで2時間を切っているため、ペットタクシー側のキャンセル料がかかる場合があります。</b>' : '') + '</p>';
  }
  var html = '<div class="box">' + nl2br_(esc_('受付番号：' + q.id + '\n希望日時：' + whenText_(r) + '\nお迎え：' + r['お迎えの場所'] + '\n行き先：' + r['行き先'])) + '</div>' + warn +
    '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'cancel') + hidden_('id', q.id) + hidden_('k', q.k) + hidden_('go', '1') +
    '<button type="submit" class="gray">このご依頼を取り消す</button></form>';
  return page_('ご依頼を取り消しますか？', html);
}

function cancel_(id) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var before;
  try {
    var row = findReq_(id);
    before = row.data['状態'];
    if (before !== ST.OPEN && before !== ST.DONE) return { msg: 'このご依頼はすでに受付が終わっています。' };
    setReq_(row.rowIndex, { '状態': ST.CANCEL, '終了日時': new Date() });
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
  var r = findReq_(id).data;
  log_(id + ' 取り消し（' + before + 'から）');
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】ご依頼を取り消しました（受付番号 ' + id + '）',
    r['お名前'] + ' 様\n\nご依頼を取り消しました。\n希望日時：' + whenText_(r) + '\n\nまたいつでもご利用ください。\n' + CONFIG.SITE_URL);
  if (before === ST.DONE) {
    var pt = partnerById_(r['決定した提携先ID']);
    var how = pt && deliver_(pt, '【取り消し】' + id + ' ' + fmt_(r['お迎え予定']) + ' のご依頼', cancelText_(r, pt), r);
    if (how === 'manual') {
      notifyAdmin_('【LINEで取り消しを伝えてください】' + id, pt.name + 'へ、手配ページの「取り消しをLINEで伝える」を押してください。\n\n▼ 手配ページ\n' + adminUrl_(id));
    }
  } else {
    closeOthers_(r, '');
  }
  notifyAdmin_('取り消し ' + id, '状態「' + before + '」から取り消されました。\n\n' + rideText_(r));
  return { msg: before === ST.DONE ? 'ご依頼を取り消し、ペットタクシーにもお伝えしました。' : 'ご依頼を取り消しました。' };
}

/* ───────── 日時だけ変えて再依頼（LPがフォームに入れ直すためのデータ） ───────── */

function prefill_(q) {
  var row = q.id && q.k === sign_(q.id + ':prefill') ? findReq_(q.id) : null;
  if (!row) return json_({ ok: false });
  var r = row.data;
  return json_({
    ok: true, pref: PREF_FULL[r['都府県']] || r['都府県'], pickup: r['お迎えの場所'], via: r['経由地'] || '', dropoff: r['行き先'],
    trip: r['片道・往復'], riders: r['同乗人数'], name: r['お名前'], tel: String(r['電話番号']).replace(/^'/, ''), email: r['メール'],
    notes: r['メモ'], pet_count: Number(r['ペット数']) || 1, pets_json: r['ペットJSON'] || '', luggage: r['荷物'] || '',
    return_pickup: r['帰りのお迎え'] || '', return_dropoff: r['帰りの行き先'] || '', wait_time: String(r['待ち時間（分）'] || '')
  });
}

function retryUrl_(id) { return CONFIG.SITE_URL + '?r=' + encodeURIComponent(id) + '&k=' + sign_(id + ':prefill') + '#form'; }

/* ───────── 決まらないときの自動対応（5分ごとに実行） ───────── */

function checkPending() {
  var sh = sheet_(SHEET_REQ);
  var vals = sh.getDataRange().getValues();
  var h = vals[0];
  var now = Date.now();
  for (var i = 1; i < vals.length; i++) {
    var r = toObj_(h, vals[i]);
    if (r['状態'] !== ST.OPEN) continue;
    var age = openMinutes_(r['受付日時'], now, CONFIG.OPEN_HOURS); // 会社が動いている時間だけ数える
    var until = (new Date(r['希望日時']).getTime() - now) / 3600000;
    var today = Utilities.formatDate(new Date(), TZ, 'yyyyMMdd') === Utilities.formatDate(new Date(r['希望日時']), TZ, 'yyyyMMdd');
    var k = (r['日付のみ'] ? today : until < CONFIG.URGENT_HOURS) ? 0.5 : 1;
    // 見積もりが届いているあいだは、お客さまが選ぶのを待つ（お迎えの時刻を過ぎたら終わり）
    if (until < 0 || (age >= CONFIG.GIVE_UP_MIN * k && !(needsChoice_(r) && quotesOf_(r).length))) {
      giveUp_(r['受付番号']);
    } else if (!pickedIds_(r).length && age >= CONFIG.WAVE2_MIN * k && Number(r['通知段階']) < 2) {
      var sent = sendWave_(r['受付番号'], 2);
      notifyAdmin_('まだ決まっていません ' + r['受付番号'], Math.round(age) + '分たっても決まっていません。近くのエリア・全国対応の提携先にも送りました：' + (sent || 'なし') +
        '\nこのまま決まらなければ、' + Math.round(CONFIG.GIVE_UP_MIN * k) + '分でお客さまにお詫びを自動で送ります。\n\n' + rideText_(r));
    }
  }
}

function giveUp_(id) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var row = findReq_(id);
    if (!row || row.data['状態'] !== ST.OPEN) return;
    setReq_(row.rowIndex, { '状態': ST.NONE, '終了日時': new Date() });
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
  var r = findReq_(id).data;
  log_(id + ' 見つからず');
  closeOthers_(r, '');
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】申し訳ありません、空いている車が見つかりませんでした（受付番号 ' + id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\nご依頼ありがとうございました。\n' + whenText_(r) + ' のお迎えについて、' + (r['指定した提携先'] ? r['指定した提携先'] + 'に確認しましたが、あいにくお引き受けできませんでした。' : 'エリアのペットタクシーにお声がけしましたが、あいにく空いている車が見つかりませんでした。') + '\nお力になれず、申し訳ありません。\n\n' +
    (r['ペアの受付番号'] ? 'これは往復の' + legTag_(r).slice(1) + 'のご依頼です。もう片方（受付番号 ' + r['ペアの受付番号'] + '）は、そのまま手配を続けています。取り消す場合は、そちらのメールのリンクからどうぞ。\n\n' : '') +
    '時間を少しずらすと見つかることがあります。下のリンクから開くと、前回の内容が入った状態になるので、日時だけ変えてもう一度お送りいただけます。\n' + retryUrl_(id));
  notifyAdmin_('見つからず ' + id, 'お客さまにお詫びを送りました。\n\n' + rideText_(r) + '\n\nお名前：' + r['お名前'] + '\n電話：' + r['電話番号']);
}

/* ───────── お客さまへのメール ───────── */

function sendReceipt_(r) {
  var lineNote = '';
  if (CONFIG.LINE_CHANNEL_ACCESS_TOKEN && CONFIG.LINE_ADD_URL) {
    lineNote = '\n\n▼ LINEでもお知らせを受け取れます\n友だち追加して、受付番号「' + r['受付番号'] + '」を送ってください。\n' + CONFIG.LINE_ADD_URL;
  }
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】受け付けました（受付番号 ' + r['受付番号'] + '）' + legTag_(r),
    r['お名前'] + ' 様\n\nご依頼ありがとうございます。受け付けました。\n' + (isQuoteReq_(r) ? '選んだ会社「' + r['指定した提携先'] + '」にお見積もりを依頼しています。ほかの会社には依頼しません。お見積もりが届くたびにメールでお送りするので、料金をくらべて、決める会社のリンクを押してください。押すまで予約は決まりません。\n\n'
      : needsChoice_(r) ? '選んだ会社「' + r['指定した提携先'] + '」に空き状況を確認しています。ほかの会社には依頼しません。引き受けた会社から、お迎えの時間と確定料金が届くたびにメールでお送りするので、決める会社のリンクを押してください。押した時点で予約が決まり、ほかの会社への依頼は取り消します。\n\n'
      : (r['指定した提携先'] ? '選んだ会社「' + r['指定した提携先'] + '」に空き状況を確認しています。ほかの会社には依頼しません。' : 'いま、空いているペットタクシーを探しています。') + '引き受けが決まりしだい、お迎えの時間と確定料金をお送りします。\n\n') +
    '受付番号：' + r['受付番号'] + '\n' + rideText_(r) +
    (num_(r['概算料金']) ? '\n■ 料金の目安（概算）：' + estShown_(r) + '\n　※実際の料金は、決まったペットタクシーからお知らせします' : '') + lineNote +
    '\n\n▼ 取り消す場合はこちら（決まる前ならいつでも無料です）\n' + cancelUrl_(r['受付番号']) +
    '\n\n※このメールは自動でお送りしています。');
}

function toCustomer_(r, subject, text) {
  if (r['メール']) mail_(r['メール'], subject, text + footer_());
  if (r['お客さまLINE']) linePush_(r['お客さまLINE'], text);
}

/* ───────── LINE（公式アカウントを作ったら使えます） ───────── */

// 提携先：LINEで「登録コード」を送ると、その提携先へのお知らせがLINEになります
// お客さま：LINEで「受付番号」を送ると、決まったときのお知らせがLINEにも届きます
function handleLine_(body) {
  (body.events || []).forEach(function (ev) {
    var uid = ev.source && ev.source.userId;
    if (!uid || !ev.replyToken) return;
    if (ev.type === 'follow') {
      return lineReply_(ev.replyToken, '友だち追加ありがとうございます！\nご依頼のお知らせを受け取るには、メールに書いてある「受付番号」（例：1026-4821）を送ってください。');
    }
    if (ev.type !== 'message' || !ev.message || ev.message.type !== 'text') return;
    var t = toHalf_(ev.message.text).replace(/\s/g, '').toUpperCase();

    var pt = partners_().filter(function (x) { return x.lineCode && x.lineCode.toUpperCase() === t; })[0];
    if (pt) {
      sheet_(SHEET_PARTNER).getRange(pt.row, partnerCol_('LINE userId')).setValue(uid);
      log_('提携先LINE登録: ' + pt.id);
      return lineReply_(ev.replyToken, pt.name + ' 様\n登録できました。これからご依頼のお知らせをLINEでお送りします。');
    }
    var m = t.match(/(\d{4})-?(\d{4})/);
    var row = m && findReq_(m[1] + '-' + m[2]);
    if (row) {
      setReq_(row.rowIndex, { 'お客さまLINE': uid });
      var s = row.data['状態'];
      var msg = s === ST.DONE ? 'ペットタクシー「' + row.data['決定した提携先'] + '」に決まっています。\nお迎え予定：' + fmt_(row.data['お迎え予定']) + '\n料金（確定・税込）：' + fareText_(row.data['料金の目安'], row.data['高速利用時の料金'])
        : s === ST.OPEN ? 'いま、空いているペットタクシーを探しています。決まったらLINEでもお知らせしますね。'
        : 'このご依頼の受付は終わっています（' + s + '）。';
      return lineReply_(ev.replyToken, '受付番号 ' + row.data['受付番号'] + ' を確認しました。\n' + msg);
    }
    lineReply_(ev.replyToken, 'メッセージありがとうございます。\nご依頼のお知らせを受け取るには「受付番号」（例：1026-4821）を送ってください。\nご依頼はこちらから：' + CONFIG.SITE_URL);
  });
}

function lineReply_(token, text) {
  lineApi_('reply', { replyToken: token, messages: [{ type: 'text', text: text.slice(0, 4900) }] });
}

function linePush_(to, text) {
  return lineApi_('push', { to: to, messages: [{ type: 'text', text: text.slice(0, 4900) }] });
}

function lineApi_(kind, payload) {
  if (!CONFIG.LINE_CHANNEL_ACCESS_TOKEN) return false;
  var res = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/' + kind, {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + CONFIG.LINE_CHANNEL_ACCESS_TOKEN },
    payload: JSON.stringify(payload)
  });
  if (res.getResponseCode() === 200) return true;
  log_('LINE送信エラー ' + res.getResponseCode() + ': ' + res.getContentText());
  return false;
}

/* ───────── 送信まわり ───────── */

// 提携先へ：こちらのLINEに登録済みならLINE → メール → 先方LINE公式（運営者がボタンで送信）
// 戻り値：'auto'（自動で送った）/ 'manual'（手配ページから運営者が送る）/ false（届けられない）
function deliver_(pt, subject, text, r) {
  if (r && isTest_(r)) {
    if (!pt.email && !pt.lineId && !pt.oaId && !pt.lineUrl) return false;
    var to = pt.email || (pt.lineId ? 'こちらのLINE' : 'LINE公式 ' + (pt.oaId || pt.lineUrl));
    return mail_(adminEmail_(), '【テスト｜本来は ' + pt.name + '（' + to + '）へ】' + subject, text + footer_()) ? 'auto' : false;
  }
  if (pt.lineId && CONFIG.LINE_CHANNEL_ACCESS_TOKEN && linePush_(pt.lineId, text)) return 'auto';
  if (pt.email && mail_(pt.email, '【' + CONFIG.SERVICE_NAME + '】' + subject, text + footer_())) return 'auto';
  if (pt.oaId || pt.lineUrl) return 'manual';
  log_('届けられませんでした: ' + pt.id + ' ' + subject);
  return false;
}

// 声をかけたほかの会社へ「締め切りました」（自動で送れる相手だけ。LINE公式の相手は手配ページにボタン）
function closeOthers_(r, winnerId) {
  String(r['通知した提携先'] || '').split(',').filter(String).forEach(function (pid) {
    if (pid === winnerId) return;
    var pt = partnerById_(pid);
    if (pt && (pt.email || (pt.lineId && CONFIG.LINE_CHANNEL_ACCESS_TOKEN))) deliver_(pt, '【締め切り】' + r['受付番号'] + ' のご依頼', closedText_(r, pt), r);
  });
}

function notifyAdmin_(subject, text) {
  if (!CONFIG.ADMIN_NOTIFY) return;
  mail_(adminEmail_(), '[運営] ' + subject, text + '\n\n予約シート：' + SpreadsheetApp.getActive().getUrl());
}

function mail_(to, subject, body) {
  try {
    var replyTo = CONFIG.REPLY_TO || CONFIG.FROM_EMAIL || adminEmail_();
    if (fromOk_()) {
      GmailApp.sendEmail(to, subject, body, { from: CONFIG.FROM_EMAIL, name: CONFIG.SERVICE_NAME, replyTo: replyTo });
    } else {
      MailApp.sendEmail({ to: to, subject: subject, body: body, name: CONFIG.SERVICE_NAME, replyTo: replyTo });
    }
    return true;
  } catch (err) {
    log_('メール送信エラー（' + to + '）: ' + err);
    return false;
  }
}

// FROM_EMAIL がGmailの送信元に登録済みか（1回の実行の中では覚えておく）
var FROM_OK_ = null;
function fromOk_() {
  if (FROM_OK_ !== null) return FROM_OK_;
  try {
    var f = String(CONFIG.FROM_EMAIL || '').toLowerCase();
    FROM_OK_ = !!f && GmailApp.getAliases().some(function (a) { return String(a).toLowerCase() === f; });
  } catch (err) { FROM_OK_ = false; }
  return FROM_OK_;
}

function footer_() {
  return '\n\n――――――――――\n' + CONFIG.SERVICE_NAME + '\n' + CONFIG.SITE_URL + '\nこのメールに返信すると運営に届きます。';
}

// テストの依頼か（会社には送らず、運営者のメールに送る）
function isTest_(r) {
  if (CONFIG.TEST_MODE || !liveSending_()) return true;
  if (/^\s*テスト/.test(String(r['お名前'] || ''))) return true;
  var m = String(r['メール'] || '').trim().toLowerCase();
  var me = ''; try { me = Session.getEffectiveUser().getEmail(); } catch (err) {}
  return [adminEmail_(), me].some(function (a) { return a && m === String(a).toLowerCase(); }); // 運営のアドレス（通知先・スクリプトの持ち主）からの依頼もテスト
}

// 「設定」シートの B1 が「送る」のときだけ、本物の会社に送る（シートが無い・空欄・「止める」ならテスト扱い）
function liveSending_() {
  try {
    var sh = sheet_('設定');
    return !!sh && String(sh.getRange(1, 2).getValue()).trim() === '送る';
  } catch (err) { return false; }
}

function adminEmail_() {
  return CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail();
}

/* ───────── 文面 ───────── */

// ケージの希望を、会社が読んでわかる言葉にする
function cageText_(v) {
  var map = { '持ち込む': 'お客さまがケージを持ってきます', '持っている': 'お客さまがケージを持ってきます', 'なし': 'ケージなしで乗せたい',
    '借りたい': '貴社のケージを借りたい（お客さまは持っていません）', 'どれでも': 'ケージはあり・なしどちらでも大丈夫（貴社のやり方に合わせます）', '持っていない': '貴社のケージを借りたい（お客さまは持っていません）' };
  return String(v || '').split('・').map(function (x) { x = x.trim(); return map[x] || x; }).filter(String).join('／');
}

// 1匹のときの予防接種と介護のくわしいこと（ペットJSON から。2匹以上はペット詳細の行に入っている）
function petExtraText_(r) {
  var p;
  try { p = JSON.parse(r['ペットJSON'] || '[]')[0]; } catch (e) { p = null; }
  if (!p) return '';
  var vac = [p.vaccine === '済' ? '混合ワクチン' : '', p.rabies === '済' ? '狂犬病の予防注射' : ''].filter(String);
  var care = (p.care_need || []).concat(p.care_note ? [p.care_note] : []);
  return [vac.length ? '■ 予防接種：' + vac.join('・') + ' 済み' : '',
          care.length ? '■ 介護のようす：' + care.join('／') : ''].filter(String).join('\n');
}

function rideText_(r) {
  var many = Number(r['ペット数']) >= 2 && r['ペット詳細'];
  var pet = many ? r['ペット数'] + '匹\n' + String(r['ペット詳細']).split('\n').map(function (l) { return '　' + l; }).join('\n')
    : [r['種類'], r['犬種・猫種'], r['体重kg'] ? r['体重kg'] + 'kg' : '', r['年齢'] ? r['年齢'] + '歳' : '', r['性別']].filter(String).join(' ');
  return [
    '■ 希望日時：' + whenText_(r) + '（' + r['片道・往復'] + '）',
    r['区間'] ? '■ 区間：' + r['区間'] + (r['ペアの受付番号'] ? '。' + (/^行き/.test(r['区間']) ? '帰り' : '行き') + 'は別のご依頼です（受付番号 ' + r['ペアの受付番号'] + '）' : '') : '',
    '■ お迎え：' + PREF_FULL[r['都府県']] + ' ' + r['お迎えの場所'],
    r['経由地'] ? '■ 経由地：' + r['経由地'] : '',
    '■ 行き先：' + r['行き先'],
    '■ ペット：' + pet,
    '■ ケージ：' + cageText_(r['キャリー']),
    many ? '■ 同乗：' + r['同乗人数'] : '■ 介助：' + r['介助'] + '　同乗：' + r['同乗人数'],
    many ? '' : petExtraText_(r),
    r['荷物'] ? '■ 荷物：' + r['荷物'] : '',
    r['帰りの日時'] || r['帰りのお迎え'] ? '■ 帰り：' + (r['帰りの日時'] instanceof Date ? fmt_(r['帰りの日時']) + ' ' : '') +
      (r['帰りのお迎え'] || r['行き先']) + ' → ' + (r['帰りの行き先'] || r['お迎えの場所']) : '',
    r['帰りのやり方'] ? '■ 帰りのやり方：' + r['帰りのやり方'] : '',
    r['待ち時間（分）'] ? '■ 待ち時間の目安：' + (/^\d+$/.test(String(r['待ち時間（分）'])) ? r['待ち時間（分）'] + '分' : r['待ち時間（分）']) : '',
    r['メモ'] ? '■ メモ：' + r['メモ'] : ''
  ].filter(String).join('\n');
}

function customerForPartner_(r) {
  return '受付番号：' + r['受付番号'] + '\n■ お名前：' + r['お名前'] + ' 様\n■ 電話：' + String(r['電話番号']).replace(/^'/, '') + '\n■ メール：' + r['メール'] +
    '\n■ ご希望の連絡方法：' + r['連絡方法'] + '\n■ お迎え予定：' + fmt_(r['お迎え予定']) + '\n■ お伝えした確定料金：' + fareText_(r['料金の目安'], r['高速利用時の料金']) + '\n■ お支払い：' + payForPartner_(partnerById_(r['決定した提携先ID'])) + '\n\n' + rideText_(r) +
    '\n\n※ご連絡先は、この送迎のためだけにお使いください。';
}

/* ───────── シート操作 ───────── */

function sheet_(name) { return SpreadsheetApp.getActive().getSheetByName(name); }

function findReq_(id) {
  var sh = sheet_(SHEET_REQ);
  var vals = sh.getDataRange().getValues();
  for (var i = vals.length - 1; i >= 1; i--) {
    if (String(vals[i][0]) === String(id)) return { rowIndex: i + 1, data: toObj_(vals[0], vals[i]) };
  }
  return null;
}

function setReq_(rowIndex, obj) {
  var sh = sheet_(SHEET_REQ);
  var h = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  Object.keys(obj).forEach(function (k) {
    var c = h.indexOf(k);
    if (c >= 0) sh.getRange(rowIndex, c + 1).setValue(obj[k]);
  });
}

function toObj_(h, v) {
  var o = {};
  h.forEach(function (k, i) { o[k] = v[i]; });
  return o;
}

function bumpCount_(pt) {
  var c = sheet_(SHEET_PARTNER).getRange(pt.row, partnerCol_('引き受け件数'));
  c.setValue((Number(c.getValue()) || 0) + 1);
}

function partnerCol_(name) {
  var sh = sheet_(SHEET_PARTNER);
  return sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].indexOf(name) + 1;
}

function newId_(sh) {
  var used = sh.getLastRow() > 1 ? sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().map(function (v) { return String(v[0]); }) : [];
  var day = Utilities.formatDate(new Date(), TZ, 'MMdd');
  for (var i = 0; i < 50; i++) {
    var id = day + '-' + ('000' + Math.floor(Math.random() * 10000)).slice(-4);
    if (used.indexOf(id) < 0) return id;
  }
  throw new Error('受付番号を作れませんでした');
}

function log_(text) {
  var sh = sheet_(SHEET_LOG);
  if (sh) sh.appendRow([new Date(), text]);
}

/* ───────── 小物 ───────── */

function webUrl_() { return CONFIG.WEB_APP_URL || ScriptApp.getService().getUrl(); }

// メールに載せるリンクの行き先（LPの /go/ があればそちら）
function linkBase_() { return CONFIG.PAGE_URL || webUrl_(); }

function acceptUrl_(id, pid) { return linkBase_() + '?a=accept&id=' + encodeURIComponent(id) + '&p=' + encodeURIComponent(pid) + '&k=' + sign_(id + ':' + pid); }

function adminUrl_(id) { return linkBase_() + '?a=admin&id=' + encodeURIComponent(id) + '&k=' + sign_(id + ':admin'); }

function cancelUrl_(id) { return linkBase_() + '?a=cancel&id=' + encodeURIComponent(id) + '&k=' + sign_(id + ':cancel'); }

function sign_(s) {
  var secret = PropertiesService.getScriptProperties().getProperty('SECRET');
  var sig = Utilities.computeHmacSha256Signature(s, secret);
  return Utilities.base64EncodeWebSafe(sig).replace(/=+$/, '').slice(0, 22);
}

function makeCode_() { return 'PT' + ('0000' + Math.floor(Math.random() * 100000)).slice(-5); }

// "2026-10-28T14:00" / "2026-10-28 14:00" → 日本時間の Date
function parseJst_(s) {
  var m = String(s || '').match(/(\d{4})-(\d{1,2})-(\d{1,2})[T ](\d{1,2}):(\d{2})/);
  if (!m) return null;
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4] - 9, +m[5]));
}

// 希望日の表示。日付だけの依頼は「10月28日(水) 時間はご相談」
function whenText_(r) {
  var d = new Date(r['希望日時']);
  if (!r['日付のみ']) return fmt_(d);
  return fmt_(d).replace(/ \d{1,2}:\d{2}$/, '') + ' 時間はご相談';
}

// 引き受け・決定の入力欄の初期値（日付だけの依頼はその日の10:00）
function defaultAt_(r) {
  var d = new Date(r['希望日時']);
  return r['日付のみ'] ? Utilities.formatDate(d, TZ, 'yyyy-MM-dd') + 'T10:00' : Utilities.formatDate(d, TZ, "yyyy-MM-dd'T'HH:mm");
}

// 予約シートの見出しに足りない列があれば右端に足す（あとから増えた列のため）
function ensureReqHeaders_(sh) {
  var head = sh.getRange(1, 1, 1, Math.max(1, sh.getLastColumn())).getValues()[0].filter(String);
  var add = REQ_HEADERS.filter(function (h) { return head.indexOf(h) < 0; });
  if (add.length) {
    sh.getRange(1, head.length + 1, 1, add.length).setValues([add]);
    head = head.concat(add);
  }
  return head;
}

function fmt_(d) {
  if (!(d instanceof Date)) d = new Date(d);
  if (isNaN(d.getTime())) return '';
  var w = '日月火水木金土'.charAt(new Date(d.getTime() + 9 * 3600000).getUTCDay());
  return Utilities.formatDate(d, TZ, 'M月d日') + '(' + w + ') ' + Utilities.formatDate(d, TZ, 'H:mm');
}

function yen_(n) { return String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '円'; }

function shortPref_(s) { return String(s || '').trim().replace(/[都府県]$/, ''); }

function clip_(s, n) { return String(s == null ? '' : s).slice(0, n || 200); }

function toHalf_(s) { return String(s || '').replace(/[０-９Ａ-Ｚａ-ｚ－]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); }).replace(/[ー−‐]/g, '-'); }

function esc_(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

function nl2br_(s) { return String(s).replace(/\n/g, '<br>'); }

function hidden_(n, v) { return '<input type="hidden" name="' + esc_(n) + '" value="' + esc_(v) + '">'; }

// シートの数字を読む（日付として読まれてしまったものは使わない）
function num_(v) { return v instanceof Date ? 0 : Number(v) || 0; }

// 確定料金の書き方（高速を使う場合の料金があれば並べる）
function fareText_(fare, hw) {
  hw = num_(hw);
  return hw ? '一般道で行く場合 ' + yen_(fare) + '／高速道路を使う場合 ' + yen_(hw) + '（高速代込み）' : yen_(fare) + '（高速道路は使いません）';
}

function yenNum_(v) { return Number(String(v || '').replace(/[^\d]/g, '')) || ''; }

// お支払い（提携先シートの「支払い方法」「支払いのタイミング」。空欄なら現地でその会社のやり方で）
function payForCustomer_(pt) {
  var m = pt && pt.payMethod, w = pt && pt.payWhen;
  if (!m && !w) return 'ペットタクシーへ現地で直接（方法はペットタクシーからご案内します）';
  return 'ペットタクシーへ現地で直接、' + (m || '方法はペットタクシーからご案内') + (w ? '（' + w + 'にお支払い）' : '');
}

function payForPartner_(pt) {
  var m = pt && pt.payMethod, w = pt && pt.payWhen;
  if (!m && !w) return 'お客さまから貴社へ現地で直接（方法・タイミングは貴社のやり方でご案内ください）';
  return 'お客さまから貴社へ現地で直接、' + (m || '貴社のやり方で') + (w ? '・' + w : '') + '（貴社の設定としてお客さまにもお伝えしています）';
}

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

function page_(title, inner) {
  var css = 'body{font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;background:#fff8f2;color:#1c1a18;margin:0;padding:24px 16px;line-height:1.7}' +
    '.card{max-width:560px;margin:0 auto;background:#fff;border-radius:20px;padding:24px 20px;box-shadow:0 8px 24px rgba(0,0,0,.06)}' +
    'h1{font-size:1.25rem;margin:0 0 12px}h2{font-size:1.05rem;margin:22px 0 4px}.box{background:#fbfaf9;border:1px solid #eee5dc;border-radius:12px;padding:14px;margin:12px 0;font-size:.95rem}' +
    'label{display:block;font-weight:700;margin:14px 0 4px}input,textarea{display:block;width:100%;box-sizing:border-box;font:inherit;font-size:16px;padding:12px;border:1.5px solid #e6ded6;border-radius:12px;margin-top:4px}' +
    'textarea{min-height:80px}button{display:block;width:100%;margin-top:20px;background:#ff6a1a;color:#fff;border:0;border-radius:999px;padding:16px;font:inherit;font-weight:800;font-size:1.05rem}' +
    'button.gray{background:#5b5650}a.line{display:block;text-align:center;background:#06c755;color:#fff;text-decoration:none;border-radius:999px;padding:12px;font-weight:800;margin:8px 0}' +
    '.pt{border-top:1px solid #eee5dc;padding:12px 0}select{display:block;width:100%;font:inherit;font-size:16px;padding:12px;border:1.5px solid #e6ded6;border-radius:12px;margin-top:4px;background:#fff}' +
    'button.gray{background:#5b5650}.note{font-size:.85rem;color:#5b5650}.brand{text-align:center;color:#e2560a;font-weight:800;margin-bottom:12px}';
  if (JSON_PAGE) {
    return ContentService.createTextOutput(JSON.stringify({ ok: true, title: title, html: inner }))
      .setMimeType(ContentService.MimeType.JSON);
  }
  var html = '<!doctype html><html><head><meta charset="utf-8"><base target="_top"><style>' + css + '</style></head><body><div class="brand">' + esc_(CONFIG.SERVICE_NAME) +
    '</div><div class="card"><h1>' + esc_(title) + '</h1>' + inner + '</div></body></html>';
  return HtmlService.createHtmlOutput(html).setTitle(title + '｜' + CONFIG.SERVICE_NAME)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/* ───────── 社内用：全国の事業者一覧（a=dash） ───────── */
// 各社の公式サイトで調べた一覧を表で見せる。リンク（k=sign_('dash')）を知っている人だけが開ける。
// 口コミの星と件数は規約で保存できないので、押したときだけ地図サービスから取り寄せる（場所のIDだけ覚える）

function dashKey_() { return sign_('dash'); }
function dashLink() { Logger.log(CONFIG.WEB_APP_URL + '?a=dash&k=' + dashKey_()); } // エディタから実行するとリンクが出る

// 一覧のデータは別のファイル DashData.gs の DASH_DATA（公開リポジトリには置かない。Noriさんの Mac の ~/pet-taxi-gas にだけある）
function dashRows_() { return typeof DASH_DATA === 'undefined' ? [] : DASH_DATA; }

function dashPage_(q) {
  if (q.k !== dashKey_()) {
    if (q.send === '1') {
      var props = PropertiesService.getScriptProperties(), last = Number(props.getProperty('DASH_LINK_SENT')) || 0;
      if (Date.now() - last > 10 * 60000) {
        props.setProperty('DASH_LINK_SENT', String(Date.now()));
        var link = CONFIG.WEB_APP_URL + '?a=dash&k=' + dashKey_();
        [adminEmail_(), Session.getEffectiveUser().getEmail()].filter(function(m, i, a) { return m && a.indexOf(m) === i; }).forEach(function(m) {
          MailApp.sendEmail({ to: m, name: CONFIG.SERVICE_NAME, subject: '【社内用】全国の事業者一覧のリンク',
            body: '社内用の事業者一覧のリンクです。ほかの人には送らないでください。\n\n' + link + '\n' });
        });
      }
      return page_('リンクを送りました', '<p>運営者のメールに一覧のリンクを送りました。</p>');
    }
    return page_('リンクが正しくありません', '<p>運営者に届いたリンクから開いてください。</p>');
  }
  var data = JSON.stringify(dashRows_()).replace(/</g, '\\u003c');
  var html = '<!doctype html><html><head><meta charset="utf-8"><base target="_blank"><style>' + DASH_CSS + '</style></head><body>' +
    DASH_BODY + '<script>var DASH=' + data + ',DASH_KEY=' + JSON.stringify(q.k) + ';' + DASH_JS + '</script></body></html>';
  return HtmlService.createHtmlOutput(html).setTitle('全国ペットタクシー事業者一覧（社内用）')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// 一覧の「星を見る」から呼ばれる（google.script.run）。ids は最大20社
function dashScores(k, ids) {
  if (k !== dashKey_()) return { ok: false, error: 'key' };
  var rows = dashRows_(), out = {};
  [].concat(ids || []).slice(0, 20).forEach(function(id) {
    var r = rows.filter(function(x) { return x.id === id; })[0];
    if (!r) return;
    try { out[id] = dashPlace_(r); } catch (e) { log_('一覧の口コミ：エラー ' + id + ' ' + e); out[id] = { error: 'failed' }; }
  });
  return { ok: true, scores: out };
}

function dashPlace_(r) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY');
  var query = r.review_q || r.name;
  if (!apiKey || !query) return { error: 'unavailable' };
  var idKey = 'PLACE_ID_D_' + r.id + '_' + query, placeId = props.getProperty(idKey);
  if (placeId === '-') return { error: 'notfound' };
  if (!placeId) {
    var found = JSON.parse(UrlFetchApp.fetch('https://places.googleapis.com/v1/places:searchText', {
      method:'post', contentType:'application/json', muteHttpExceptions:true,
      headers:{'X-Goog-Api-Key':apiKey,'X-Goog-FieldMask':'places.id,places.displayName'},
      payload:JSON.stringify({textQuery:query,languageCode:'ja',regionCode:'JP'})
    }).getContentText());
    var norm = function(t) { return String(t).normalize('NFKC').replace(/\s/g, '').toLowerCase(); };
    var words = String(r.review_name || '').split(/[\s、,]+/).filter(String);
    var hit = (found.places || []).filter(function(x) {
      var n = norm((x.displayName || {}).text || '');
      return words.length > 0 && words.every(function(w) { return n.indexOf(norm(w)) >= 0; });
    })[0];
    placeId = hit ? hit.id : '-';
    props.setProperty(idKey, placeId);
    if (placeId === '-') return { error: 'notfound' };
  }
  var ym = Utilities.formatDate(new Date(), TZ, 'yyyyMM');
  var month = 'REVIEW_COUNT_' + ym, used = Number(props.getProperty(month)) || 0;
  var dashMonth = 'REVIEW_DASH_COUNT_' + ym, dashUsed = Number(props.getProperty(dashMonth)) || 0;
  if (used >= CONFIG.REVIEW_MONTHLY_LIMIT || dashUsed >= CONFIG.REVIEW_DASH_MONTHLY_LIMIT) return { error: 'limit' };
  props.setProperty(month, String(used + 1));
  props.setProperty(dashMonth, String(dashUsed + 1));
  var res = UrlFetchApp.fetch('https://places.googleapis.com/v1/places/' + encodeURIComponent(placeId) + '?languageCode=ja', {
    muteHttpExceptions:true, headers:{'X-Goog-Api-Key':apiKey,'X-Goog-FieldMask':'displayName,rating,userRatingCount,googleMapsUri'}
  });
  if (res.getResponseCode() !== 200) return { error: 'failed' };
  var v = JSON.parse(res.getContentText());
  return { rating: v.rating || 0, count: Number(v.userRatingCount) || 0, place: (v.displayName || {}).text || '', url: v.googleMapsUri || '' };
}

var DASH_CSS = 'body{font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;background:#f6f4f1;color:#1d1b19;margin:0;padding:20px 16px;line-height:1.5;font-size:14px}' +
  'h1{font-size:1.35rem;margin:0 0 4px;font-weight:600}.lede{color:#5f5a54;margin:0 0 14px;max-width:72ch}' +
  '.ctl{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:0 0 10px}.ctl label{font-size:.85rem;color:#5f5a54;display:inline-flex;gap:6px;align-items:center}' +
  'select,input[type=search]{font:inherit;padding:6px 8px;border:1px solid #d9d2c9;border-radius:8px;background:#fff}' +
  'button{font:inherit;font-size:.85rem;padding:6px 12px;border:1px solid #d9d2c9;border-radius:999px;background:#fff;cursor:pointer}button.on{background:#1d1b19;color:#fff;border-color:#1d1b19}button:disabled{opacity:.5;cursor:default}' +
  '.wrap{overflow:auto;max-height:78vh;border:1px solid #e3ddd5;border-radius:10px;background:#fff}' +
  'table{border-collapse:separate;border-spacing:0;font-size:.82rem}th,td{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid #eee8e1;min-width:9rem;max-width:18rem}' +
  'th{position:sticky;top:0;background:#fbf9f7;z-index:2;white-space:nowrap;font-weight:600}th:nth-child(2),td:nth-child(2){position:sticky;left:0;background:#fff;z-index:1;border-right:1px solid #eee8e1}th:nth-child(2){z-index:3;background:#fbf9f7}' +
  'td:first-child,th:first-child{min-width:5rem}a{color:inherit}.unk{color:#9a938b}.star{color:#b86e00;font-weight:600}.src{font-size:.75rem;color:#7a736b}' +
  '.hide-fare .g-fare,.hide-service .g-service,.hide-company .g-company{display:none}.note{font-size:.78rem;color:#6f6862;max-width:80ch;margin:10px 0 0}.msg{font-size:.82rem;color:#6f6862}';

var DASH_BODY = '<h1>全国ペットタクシー事業者一覧</h1><p class="lede">社内用です。各社の公式サイトに書いてあることだけを載せ、書いていないことは「不明」にしています。料金は各社サイトの表示どおりで、確定料金ではありません。</p>' +
  '<div class="ctl"><label>都道府県 <select id="pref"></select></label><label>さがす <input id="q" type="search" placeholder="名前・地域・メモ"></label>' +
  '<label>並び順 <select id="sort"><option value="pref">都道府県順</option><option value="fare">5kmの料金が安い順</option><option value="trust">信頼度が高い順</option></select></label>' +
  '<label><input id="emg" type="checkbox"> 緊急に対応だけ</label><label><input id="fare" type="checkbox"> 5kmの料金がわかる会社だけ</label></div>' +
  '<div class="ctl"><span class="msg">表示する列：</span><button class="on" data-g="fare">料金</button><button class="on" data-g="service">サービス</button><button class="on" data-g="company">会社・許可・出典</button>' +
  '<button id="bulk">表示中の会社の星をまとめて見る（最大20社）</button><span class="msg" id="count"></span></div>' +
  '<div class="wrap" id="wrap"><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div>' +
  '<p class="note">口コミの星と件数は、押したときに地図サービスから取り寄せます（規約で保存できないため、ページを開き直すと消えます）。月' + CONFIG.REVIEW_DASH_MONTHLY_LIMIT + '回まで。違う場所を拾わないよう、地図での名前が会社名と合うときだけ出し、地図での名前も一緒に表示します。信頼度は提携先シートの5点採点（緑4〜5・黄2〜3・赤は閉鎖や停止、「—」は未採点）です。</p>';

var DASH_JS = String(function() {
  var COLS = [['pref','都道府県'],['name','名前（公式サイト）'],['area','対応エリア'],['ch','受付方法'],['gbp','口コミ（Google Maps）'],
    ['km5','5kmの料金','fare'],['perkm','1kmあたり','fare'],['pick','迎車・送迎代','fare'],['wait','待機代','fare'],['cancel','キャンセルポリシー','fare'],['rt_cancel','往復の帰りだけキャンセル','fare'],['night','夜間・早朝の割増','fare'],['night_span','割増のまたぎ方','fare'],['toll','高速・駐車場','fare'],['extra_fees','書いていない料金','fare'],['pay','お支払い','fare'],['pay_timing','支払いの時期','fare'],['rt_fare','往復の料金（待つ／迎え直し）','fare'],['rt_pay','往復の支払い','fare'],
    ['hours','営業時間','service'],['emg','緊急搬送','service'],['hotel','ホテル・サロン送迎だけか','service'],['care','介護サポート','service'],['cage','ケージ','service'],['cap','乗車キャパ','service'],['large_dog','大型犬（kg・頭数）','service'],['pet_only','ペットだけの乗車','service'],['ride','飼い主の同乗','service'],['animals','乗せられる動物','service'],['lead','予約の期限','service'],
    ['staff','従業員数','company'],['cars','車両（台数・車種）','company'],['op','運営会社・所在地','company'],['lic','許可・ナンバー','company'],['ins','保険','company'],['trust','信頼度（5点）','company'],['partner','うちとの関係','company'],['reply','返事の速さ（問い合わせ）','company'],['note','メモ','company'],['src','出典','company'],['checked','確認日','company']];
  var ORDER = ['東京都','神奈川県','埼玉県','千葉県','茨城県','栃木県','群馬県','北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県','全国'];
  var scores = {}, st = { pref: '', q: '', sort: 'pref', emg: false, fare: false };
  var $ = function(id) { return document.getElementById(id); };
  var el = function(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  var pidx = function(p) { var i = ORDER.indexOf(p); return i < 0 ? 99 : i; };
  var trust = function(t) { t = String(t || ''); var n = parseInt(t.replace(/\D/g, ''), 10) || 0; return (t.charAt(0) === '緑' ? 30 : t.charAt(0) === '黄' ? 20 : t.charAt(0) === '赤' ? 10 : 0) + n; };
  var prefs = DASH.map(function(r) { return r.pref; }).filter(function(p, i, a) { return a.indexOf(p) === i; }).sort(function(a, b) { return pidx(a) - pidx(b); });
  $('pref').appendChild(new Option('すべて（' + DASH.length + '社）', ''));
  prefs.forEach(function(p) { $('pref').appendChild(new Option(p + '（' + DASH.filter(function(r) { return r.pref === p; }).length + '）', p)); });
  COLS.forEach(function(c) { $('head').appendChild(el('th', c[2] ? 'g-' + c[2] : '', c[1])); });
  function shown() {
    var q = st.q.trim().toLowerCase();
    var rows = DASH.filter(function(r) {
      return (!st.pref || r.pref === st.pref) && (!st.emg || r.emg_yes === 'はい') && (!st.fare || r.km5_yen !== '') &&
        (!q || [r.name, r.area, r.note, r.op, r.ch].join(' ').toLowerCase().indexOf(q) >= 0);
    });
    if (st.sort === 'fare') rows.sort(function(a, b) { return (Number(a.km5_yen) || 1e9) - (Number(b.km5_yen) || 1e9); });
    else if (st.sort === 'trust') rows.sort(function(a, b) { return trust(b.trust) - trust(a.trust); });
    else rows.sort(function(a, b) { return pidx(a.pref) - pidx(b.pref) || a.name.localeCompare(b.name, 'ja'); });
    return rows;
  }
  function gbpCell(td, r) {
    var s = scores[r.id];
    if (s === 'loading') { td.appendChild(el('span', 'msg', '取り寄せ中…')); return; }
    if (s && s.rating > 0) {
      var a = el('a', 'star', '★' + s.rating.toFixed(1) + '（' + s.count + '件）'); a.href = s.url || '#'; td.appendChild(a);
      td.appendChild(el('div', 'src', 'Google Maps：' + s.place)); return;
    }
    if (s && s.error) {
      td.appendChild(el('div', 'msg', { notfound: '地図で見つかりませんでした', limit: '今月の上限に届きました', key: 'リンクが古くなっています' }[s.error] || '取り寄せできませんでした'));
    } else if (s && s.rating === 0) td.appendChild(el('div', 'msg', '口コミはまだありません'));
    var b = el('button', '', '星を見る'); b.onclick = function() { fetchScores([r.id]); }; td.appendChild(b);
  }
  function draw() {
    var rows = shown(), body = $('body');
    body.innerHTML = '';
    rows.forEach(function(r) {
      var tr = el('tr');
      COLS.forEach(function(c) {
        var td = el('td', c[2] ? 'g-' + c[2] : ''), v = r[c[0]];
        if (c[0] === 'gbp') gbpCell(td, r);
        else if (c[0] === 'name' && /^https?:\/\//.test(r.url)) { var a = el('a', '', v); a.href = r.url; td.appendChild(a); }
        else { td.textContent = v; if (!v || v === '不明' || v === '未問い合わせ') td.classList.add('unk'); }
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    $('count').textContent = rows.length + '社を表示中';
  }
  function fetchScores(ids) {
    ids = ids.filter(function(id) { return !scores[id] || scores[id].error; }).slice(0, 20);
    if (!ids.length) return;
    ids.forEach(function(id) { scores[id] = 'loading'; }); draw();
    google.script.run.withSuccessHandler(function(res) {
      ids.forEach(function(id) { scores[id] = res && res.ok && res.scores[id] ? res.scores[id] : { error: res && res.error || 'failed' }; }); draw();
    }).withFailureHandler(function() { ids.forEach(function(id) { scores[id] = { error: 'failed' }; }); draw(); }).dashScores(DASH_KEY, ids);
  }
  $('pref').onchange = function() { st.pref = this.value; draw(); };
  $('q').oninput = function() { st.q = this.value; draw(); };
  $('sort').onchange = function() { st.sort = this.value; draw(); };
  $('emg').onchange = function() { st.emg = this.checked; draw(); };
  $('fare').onchange = function() { st.fare = this.checked; draw(); };
  $('bulk').onclick = function() { fetchScores(shown().map(function(r) { return r.id; })); };
  Array.prototype.forEach.call(document.querySelectorAll('[data-g]'), function(b) {
    b.onclick = function() { b.classList.toggle('on'); $('wrap').classList.toggle('hide-' + b.getAttribute('data-g'), !b.classList.contains('on')); };
  });
  draw();
}).replace(/^function\s*\(\)\s*\{|\}$/g, '');

/* ───────── テスト用（エディタから実行） ───────── */

// LPを使わずに、テストの依頼を1件流します。届いたメールのリンクで引き受け→お客さまメールまで確認できます
function testRequest() {
  var d = new Date(Date.now() + 26 * 3600000);
  var res = receive_({
    pref: '東京', pickup: '世田谷区三軒茶屋2丁目', dropoff: 'テスト動物病院（目黒区）',
    datetime: Utilities.formatDate(d, TZ, "yyyy-MM-dd'T'HH:00"), trip: '片道', species: '犬', breed: '柴犬', weight: '8', age: '12', sex: 'オス',
    cage: '持っている', care: '不要', riders: '1人', name: 'テスト 花子', tel: '09000000000', email: adminEmail_(), contact: 'メール', notes: 'これはテストです'
  });
  Logger.log(JSON.stringify(res));
}

/*SELECTION_FARES*/var SELECTION_FARES = {"petexpress": {"名前": "ペットエクスプレス（世田谷）", "出典": "https://pettaxi.tokyo/ 2026-10-27", "base_km": 5, "base": 2200, "tiers": [[100, 220], [200, 165], [null, 110]], "pick": 330, "back": 330, "night": 1.2, "round_flat": null, "note": "東京・世田谷の会社は、乗車料金が5kmまで2,200円、その先は1kmごとに220円（101km〜は165円、201km〜は110円）。お迎え料金と帰りの回送料金がそれぞれ3kmまで330円かかり、お店から遠いと増えます。夕方18時〜朝8時は乗車料金が2割増し、往復は乗車料金が2倍です。病院での待ち時間は10分まで無料、30分まで660円、その後10分ごとに220円です。長い待ち時間の往復や遠くへの移動は、半日貸切（6時間・70kmまで13,200円）や1日貸切（12時間・160kmまで26,400円）のほうが安ければ、そちらで計算します。", "wait": {"30": 660, "60": 1320, "120": 2640}, "pay": "東京・世田谷の会社は、現金で降りるときにお支払いです。", "shop": [35.6339, 139.6697], "pick_free_km": 3, "pick_over": 220, "_迎車メモ": "迎車・回送の3km超の単価は非公開。候補カードでは仮の単価で足さず「330円〜（追加分は要確認）」と出す。pick_over は旧フォーム概算用の仮の値（お店：世田谷区上馬1丁目）", "label": "東京・世田谷の会社", "night_hours": [18, 8], "partner_id": "P002", "review_query": "ペットエクスプレス 世田谷区上馬", "charter": [{"name": "半日貸切", "hours": 6, "km": 70, "price": 13200, "over30": 1100}, {"name": "1日貸切", "hours": 12, "km": 160, "price": 26400, "over30": 880}], "_貸切メモ": "https://pettaxi.tokyo/ 2026-10-31：半日（6時間・70kmまで）13,200円、全日（12時間・160kmまで）26,400円、超過は30分ごと1,100円／880円、有料道路は別。表は税込だが『別途消費税を加算』の記載もあり、迎車・待機・夜間の扱いは書いていない（問い合わせで確かめる）。距離・時間はお店からの行き帰りも含めて計算する"}, "kuriki": {"名前": "くりき（松戸）", "出典": "https://pet-kuriki.com/taxi 2026-10-27", "base_km": 4, "base": 1800, "tiers": [[100, 200], [200, 150], [null, 100]], "pick": 0, "back": 0, "night": 1.0, "round_flat": [10, 3300], "note": "千葉・松戸の会社は、乗車料金が5km未満1,800円、5km以上は1kmごとに200円（101km〜は150円、201km〜は100円）。往復は10kmまで3,300円（病院での待ち時間30分込み）で、その後の待ち時間は30分ごとに500円です。長い距離や長い待ち時間は、その会社のお見積りになります。", "wait": {"30": 0, "60": 500, "120": 1500}, "pay": "千葉・松戸の会社は、お支払い方法を決まったときのメールでご案内します。", "label": "千葉・松戸の会社", "night_hours": null, "partner_id": "P003", "review_query": "ペットタクシー くりき 松戸"}};/*/SELECTION_FARES*/
/* 事業者の検索は予約の保存・メール送信をしない。料金は上の生成データを使う。 */
var QUOTE_FIELDS = ['leg', 'pref', 'pickup', 'via', 'dropoff', 'datetime', 'trip', 'riders', 'luggage', 'species', 'weight', 'cage', 'care', 'pet_count', 'pets_json', 'return_datetime', 'return_pickup', 'return_dropoff', 'route_details'];

function selectionRide_(p) {
  return {
    '都府県': shortPref_(p.pref), '希望日時': parseJst_(p.datetime), '片道・往復': String(p.trip || ''),
    '体重kg': Number(p.weight), '同乗人数': String(p.riders || ''), 'ペット数': Number(p.pet_count),
    'キャリー': String(p.cage || ''), '介助': String(p.care || ''), '荷物': String(p.luggage || ''),
    'ペットJSON': String(p.pets_json || ''), '帰りの日時': p.trip === '往復' ? parseJst_(p.return_datetime) : ''
  };
}

function selectionValid_(p) {
  var at = parseJst_(p.datetime), ret = parseJst_(p.return_datetime);
  if (PREFS.indexOf(shortPref_(p.pref)) < 0 && !CONFIG.SHOW_ALL_CANDIDATES) return 'area'; // 全社準備中のあいだは全国のお迎えでも候補を出す（Nori「全国にして」）。依頼は validateSelection_ で断る
  if (!at || !isFinite(at.getTime()) || at.getTime() < Date.now() + CONFIG.MIN_LEAD_HOURS * 3600000 ||
      (p.trip === '往復' && (!ret || !(ret > at)))) return 'datetime';
  if (['片道', '往復'].indexOf(p.trip) < 0 || !String(p.pickup || '').trim() || !String(p.dropoff || '').trim()) return 'missing';
  if (!(Number(p.weight) > 0) || !(Number(p.pet_count) >= 1 && Number(p.pet_count) <= 5) || !p.cage || !p.care || !p.riders) return 'missing';
  return '';
}

function selectionCandidates_(r) {
  // 同じ都県、または全国対応の会社。近隣都県だけの会社には依頼しない。
  return partners_().filter(function(pt) {
    return pt.active && reachable_(pt) && (pt.areas.indexOf(r['都府県']) >= 0 || pt.areas.indexOf('全国') >= 0) &&
      fitsCar_(pt, r) && fitsCage_(pt, r) && inTime_(pt, r) && (r['介助'] !== '必要' || pt.careOk) && !checks_(pt, r).ng.length;
  });
}

function quoteSignature_(p, id, expires, price) {
  return sign_('selection:' + JSON.stringify(QUOTE_FIELDS.map(function(k) { return String(p[k] || ''); })) + ':' + id + ':' + expires + ':' + JSON.stringify(price));
}

function selectionPrice_(pt, p) {
  var key = Object.keys(SELECTION_FARES).filter(function(k) { return SELECTION_FARES[k].partner_id === pt.id; })[0];
  if (!key) return { amount:null,text:'料金はお見積もり',night:'' };
  var c = SELECTION_FARES[key], d;
  try { d = JSON.parse(p.route_details); } catch (e) { return null; }
  function validKm(v) { return typeof v === 'number' && isFinite(v) && v >= 1 && v <= 250; }
  if (!d || !validKm(d.km) || !validKm(d.backKm)) return null;
  if (!['from','to','backFrom','backTo'].every(function(k) {
    return d[k] && isFinite(d[k].lat) && isFinite(d[k].lng) && d[k].lat>=20 && d[k].lat<=46 && d[k].lng>=122 && d[k].lng<=154;
  })) return null;
  function distance(a,b) {
    var t=Math.PI/180, h=Math.pow(Math.sin((b.lat-a.lat)*t/2),2)+Math.cos(a.lat*t)*Math.cos(b.lat*t)*Math.pow(Math.sin((b.lng-a.lng)*t/2),2);
    return 6371*2*Math.asin(Math.sqrt(Math.min(1,h)));
  }
  function fee(base,at) {
    return base; // 公開されている基本額だけ。3km超の非公開単価は仮置きしない。
  }
  function feeUnknown(at){return !c.shop || distance({lat:c.shop[0],lng:c.shop[1]},at)*1.5>c.pick_free_km;}
  function night(at) {
    var dt=parseJst_(at),h=dt?(dt.getUTCHours()+9)%24:0;
    return !!(c.night_hours && c.night>1 && (h>=c.night_hours[0] || h<c.night_hours[1]));
  }
  function ride(km) {
    var amount=c.base,start=c.base_km;
    c.tiers.forEach(function(t){var end=t[0]==null?Infinity:t[0];if(km>start)amount+=t[1]*(Math.min(km,end)-start);start=end;});
    return amount;
  }
  var nt=night(p.datetime),nt2=night(p.return_datetime),round=p.trip==='往復';
  function nightFee(amount,on){return on?Math.ceil(amount*c.night/10)*10-amount:0;}
  function total(km,backKm) {
    var r1=ride(km),r2=round?ride(backKm):0;
    var separate={ride:r1+r2,pickup:fee(c.pick,d.from)+(round?fee(c.pick,d.backFrom):0),
      returnFee:fee(c.back,d.to)+(round?fee(c.back,d.backTo):0),nightExtra:nightFee(r1,nt)+(round?nightFee(r2,nt2):0),wait:0,pickupUnknown:feeUnknown(d.from)||(round&&feeUnknown(d.backFrom)),returnUnknown:feeUnknown(d.to)||(round&&feeUnknown(d.backTo)),method:round?'帰りにあらためてお迎え':'片道'};
    function sum(x){return x.ride+x.pickup+x.returnFee+x.nightExtra+x.wait;}
    var chosen=separate;
    if(round && p.return_pickup===p.dropoff && p.return_dropoff===p.pickup && c.wait){
      var gap=(parseJst_(p.return_datetime)-parseJst_(p.datetime))/60000-km*3;
      var wk=gap<=30?'30':gap<=60?'60':gap<=120?'120':'';
      if(wk){
        var waiting={ride:r1+r2,pickup:fee(c.pick,d.from),returnFee:fee(c.back,d.backTo),
          nightExtra:nightFee(r1,nt)+nightFee(r2,nt2),wait:Number(c.wait[wk])||0,pickupUnknown:feeUnknown(d.from),returnUnknown:feeUnknown(d.backTo),method:'待っていてもらう往復'};
        if(c.round_flat && km+backKm<=c.round_flat[0]){waiting.ride=c.round_flat[1];waiting.nightExtra=0;}
        if(sum(waiting)<=sum(separate))chosen=waiting;
      }
    }
    // 貸切プラン（半日・1日）のほうが安ければ使う。お店からの行き帰りも距離と時間に入れる。1kmを3分で走るとみる（Nori 2026-10-31「貸し切りのプラン、安いよ」）
    if(c.charter&&c.shop){
      var shop={lat:c.shop[0],lng:c.shop[1]},last=round?d.backTo:d.to;
      var legKm=Math.ceil(distance(shop,d.from)*1.5)+Math.ceil(distance(shop,last)*1.5),allKm=km+(round?backKm:0)+legKm;
      var hours=(round?(parseJst_(p.return_datetime)-parseJst_(p.datetime))/3600000+backKm*3/60:km*3/60)+legKm*3/60;
      c.charter.forEach(function(pl){
        if(allKm>pl.km)return;
        var over=Math.max(0,Math.ceil((hours-pl.hours)*2))*pl.over30;
        var ch={ride:pl.price+over,pickup:0,returnFee:0,nightExtra:0,wait:0,method:pl.name+'（'+pl.hours+'時間・'+pl.km+'kmまで'+(over?'、超過'+yen_(over)+'を含む':'')+'）'};
        if(sum(ch)<sum(chosen))chosen=ch;
      });
    }
    var raw=sum(chosen);chosen.amount=Math.ceil(raw/100)*100;chosen.rounding=chosen.amount-raw;
    return chosen;
  }
  var local=total(d.km,d.backKm),highway=validKm(d.highKm)&&validKm(d.highBackKm)?total(d.highKm,d.highBackKm):null;
  var feePoints=round?[d.from,d.to,d.backFrom,d.backTo]:[d.from,d.to];
  var pickupExtra=c.shop && feePoints.some(function(at){return distance({lat:c.shop[0],lng:c.shop[1]},at)*1.5>c.pick_free_km;});
  return {amount:local.amount,text:yen_(local.amount)+(local.pickupUnknown||local.returnUnknown?'〜':''),local:local,highway:highway,incompleteFees:local.pickupUnknown||local.returnUnknown,
    night:nt || (round&&nt2)?'夜間・早朝の割増 '+yen_(local.nightExtra)+'を含みます':c.night_hours?'指定時刻は夜間・早朝の割増対象外です':'料金表に夜間・早朝の割増はありません',
    pickupNote:pickupExtra?'迎車・回送はそれぞれ'+c.pick_free_km+'kmまで'+yen_(c.pick)+'を含みます。3km超は単価が非公開のため追加分を含めず、事業者のお見積もりで確認します。':!c.shop&&c.pick===0&&c.back===0?'迎車・回送は料金表に別記がないため、この概算では0円で計算しています。無料の確約ではありません。':'迎車・回送の距離は営業所からの概算です。',
    planNote:/貸切/.test(local.method)?local.method+'で計算しています（通常の料金より安いため）。お迎え・回送・待ち時間・夜間の扱いと税は、事業者が確認します。':'',
    routeNote:d.routeEstimated?'道のりを取得できなかったため、距離は直線距離からの概算です。':d.localEstimated?'一般道の距離は、高速区間から長めに推定しています。':''};
}

function selectionQuotes_(p) {
  var error = selectionValid_(p);
  if (error) return {ok:false,error:error};
  // scores：口コミの星を kind=scores でまとめて取り寄せられる版（ページはこれが来たときだけ取り寄せる）
  var out = {ok:true,selection_version:1,scores:1,cards:quoteCards_(p)};
  // 往復は、行きと帰りをそれぞれ別の会社に頼めるように、片道ずつの候補も返す（Nori 2026-10-31）。全社準備中のあいだは出さない
  if (p.trip === '往復' && !CONFIG.SHOW_ALL_CANDIDATES) out.legs = {go:quoteCards_(legParams_(p,'go')), back:quoteCards_(legParams_(p,'back'))};
  return out;
}

// 往復の片方を片道の依頼として見たときの入力（go＝行き、back＝帰り）。料金・署名・候補の判定はこれで片道として計算する
function legParams_(p, leg) {
  var q = {}, d = {};
  Object.keys(p).forEach(function(k) { q[k] = p[k]; });
  try { d = JSON.parse(p.route_details) || {}; } catch (e) {}
  var b = leg === 'back';
  var km = b ? d.backKm : d.km, high = b ? d.highBackKm : d.highKm, from = b ? d.backFrom : d.from, to = b ? d.backTo : d.to;
  q.route_details = JSON.stringify({km:km, backKm:km, highKm:high, highBackKm:high, from:from, to:to, backFrom:from, backTo:to,
    routeEstimated:d.routeEstimated, localEstimated:d.localEstimated});
  q.trip = '片道';
  if (b) {
    q.datetime = p.return_datetime; q.pickup = p.return_pickup || p.dropoff; q.dropoff = p.return_dropoff || p.pickup; q.via = '';
  }
  q.return_datetime = ''; q.return_pickup = ''; q.return_dropoff = '';
  q.leg = leg;
  return q;
}

function quoteCards_(p) {
  var expires = Date.now()+15*60000, r = selectionRide_(p);
  return selectionCandidates_(r).filter(function(pt) { return !isDisplayOnly_(pt.id); }).map(function(pt) {
    var price = selectionPrice_(pt,p);
    if (!price) return null;
    // 全社準備中のあいだは、提携先の会社も表示だけ（トークンを出さない＝依頼できない）
    if (CONFIG.SHOW_ALL_CANDIDATES) return { id:pt.id, label:pt.name, display_only:true, car:pt.car || '車の詳細は確認中です',
      payment:[pt.payMethod,pt.payWhen].filter(String).join('・') || 'お支払い方法は確認中です',
      price:price, review:null, check:[], points:PARTNER_POINTS[pt.id] || [] };
    return { id:pt.id, label:pt.name, car:pt.car || '車の詳細は引き受け時に確認', points:PARTNER_POINTS[pt.id] || [],
      payment:[pt.payMethod,pt.payWhen].filter(String).join('・') || 'お支払い方法は引き受け時にご案内',
      price:price, review:null, check:checks_(pt, r).ask, expires:expires, token:quoteSignature_(p,pt.id,expires,price) };
  }).filter(Boolean).concat(p.leg ? [] : displayCards_(r, p));
}

// 日本時間で同じ日か
function isSameDay_(at, now) {
  if (!at) return false;
  var f = function(d) { return new Date(d.getTime() + 9 * 3600000).toISOString().slice(0, 10); };
  return f(at) === f(now);
}
// 表示だけの会社を、営業時間と当日予約でしぼる（Nori 2026-10-31「当日対応店は空いていて間に合えば可。翌日以降対応や営業時間が終わっている会社は候補に出さない」）
// 分からないことは外さない（出して、カードに「確認中」と書く）
function displayInTime_(c, at, now) {
  if (!at || !isFinite(at.getTime())) return true;
  var j = new Date(at.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
  if ((c.closed || []).indexOf(j.getUTCDay()) >= 0) return false; // 定休日
  if (c.hours && !c.flex && !inHours_(hr, hoursOf_(c.hours))) return false; // お迎えが営業時間の外
  var n = new Date(now.getTime() + 9 * 3600000);
  var days = Math.round((Date.UTC(j.getUTCFullYear(), j.getUTCMonth(), j.getUTCDate()) - Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate())) / 86400000);
  if (c.lead_days != null && days < c.lead_days) return false; // 前日まで・3日前までの会社
  if (days === 0) {
    if (c.cut != null && n.getUTCHours() >= c.cut) return false; // 当日予約の締め切りを過ぎた
    // 今日の営業時間が終わっていて、お迎えまでに開かない会社は出さない。開いてからお迎えまで準備の時間があること
    if (c.hours && at.getTime() - nextOpen_(now, c.hours).getTime() < CONFIG.DEFAULT_LEAD_HOURS * 3600000) return false;
  }
  return true;
}

/*DISPLAY_COMPANIES*/var DISPLAY_COMPANIES = [{"id": "D400f012", "name": "COCOタク 東京小平店", "pref": "東京都", "areas": ["埼玉", "東京"], "area_text": "小平・東村山・立川・国分寺・府中・八王子など多摩一帯、所沢・朝霞・和光など埼玉の一部", "shop": [35.735, 139.475], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://www.cocotaxi-sawan.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・電子マネー", "review_q": "COCOタク 東京小平店 東京", "review_name": "COCOタク 東京小平店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "points": ["24時間受付", "深夜・早朝も相談可", "カード払い可", "追加料金なし"]}, {"id": "Dea620d5", "name": "COCOタク 江戸川店", "pref": "東京都", "areas": ["千葉", "東京"], "area_text": "江戸川・葛飾・江東・足立・台東・墨田・荒川・千葉下総", "shop": [35.684, 139.876], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://g-holding.taxi/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・交通系IC・PayPay・iD・QUICPay・Apple Pay", "review_q": "COCOタク 江戸川店 東京", "review_name": "COCOタク 江戸川店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "前日までキャンセル無料", "カード払い可"]}, {"id": "D3661eb1", "name": "PETTA東京（ペッタ）", "pref": "東京都", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "東京・埼玉・千葉・神奈川、長距離", "shop": null, "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 150], [201, null, 110]], "tax": "税込", "src": "https://www.petta-tokyo.com/cont2/main.html", "pick": {"yen": 880, "unsure": true}, "wait": {"free": 0, "unit": 10, "yen": 250}}, "pay": "", "review_q": "PETTA東京 東京", "review_name": "PETTA東京", "hours": "8-21", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["深夜・早朝も相談可", "深夜・早朝の割増なし", "前日までキャンセル無料", "ワクチン証明は不要"]}, {"id": "D1e44e13", "name": "cocoタク 大田・田園調布店", "pref": "東京都", "areas": ["東京"], "area_text": "大田・世田谷・品川・港・目黒・渋谷", "shop": [35.588, 139.672], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://coco-taxi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・交通系IC・PayPay・iD・QUICPay・Apple Pay", "review_q": "cocoタク 大田・田園調布店 東京", "review_name": "cocoタク 大田・田園調布店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "深夜・早朝も相談可", "前日までキャンセル無料", "カード払い可"]}, {"id": "Da5a2701", "name": "かるたく", "pref": "東京都", "areas": ["東京"], "area_text": "", "shop": [35.688, 139.787], "fare": {"base": [1299, 1], "tiers": [[2, 5, 650], [6, 100, 338], [101, 200, 156], [201, null, 130]], "pick": {"per": 150}, "wait": {"free": 0, "unit": 10, "yen": 250}, "night": {"from": 19, "to": 5, "unknown": true}, "tax": "", "src": "https://pet-taxikarubi.com/"}, "pay": "", "review_q": "かるたく 東京", "review_name": "かるたく", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D355c31f", "name": "サポっ人 中目黒店", "pref": "東京都", "areas": ["東京"], "area_text": "目黒・大田・世田谷・渋谷・港・品川・杉並・中野・新宿", "shop": [35.643, 139.698], "fare": {"base": [2750, 5], "tiers": [[6, 100, 198], [101, 200, 165], [201, null, 132]], "tax": "税込", "src": "https://seikatsunosupport.com/pettaxi/", "pick": {"per": 198}}, "pay": "", "review_q": "サポっ人 中目黒店 東京", "review_name": "サポっ人 中目黒店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "前日までキャンセル無料"]}, {"id": "D7c32399", "name": "ペットタクシー こうのとり（AirLine Haneda）", "pref": "東京都", "areas": ["東京", "神奈川"], "area_text": "大田区中心、23区・川崎の一部（外は予約で相談）", "shop": [35.548, 139.753], "fare": {"base": [2500, 5], "tiers": [[6, null, 250]], "tax": "税込", "src": "https://airline-haneda.com/taxi/", "pick": {"km": 5, "yen": 1500, "per": 150}, "wait": {"free": 0, "first": [30, 1100], "unit": 10, "yen": 550}}, "pay": "現金のみ・降りるとき", "review_q": "ペットタクシー こうのとり 東京", "review_name": "こうのとり", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "Dbe5cb84", "name": "ペットタクシー アズール", "pref": "東京都", "areas": ["東京"], "area_text": "", "shop": [35.659, 139.684], "fare": {"base": [2000, 5], "tiers": [[6, 10, 500, 5], [11, 100, 1000, 5], [101, 200, 170], [201, null, 130]], "pick": {"base": [500, 5], "tiers": [[6, 15, 1000, 5], [16, 100, 500, 5], [101, null, 300, 5]]}, "wait": {"free": 30, "unit": 30, "yen": 500}, "tax": "税込", "src": "https://azul.fivedogs.jp/"}, "pay": "キャッシュレス可・降りるとき", "review_q": "ペットタクシー アズール 東京", "review_name": "アズール", "hours": "9-19", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": true, "ok": [], "no": []}}, {"id": "D0d1c8b4", "name": "ペットタクシー ワンネス", "pref": "東京都", "areas": ["埼玉", "千葉", "東京"], "area_text": "東京23区・埼玉・千葉が中心", "shop": [35.775, 139.804], "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 165], [201, null, 110]], "tax": "税込", "src": "https://oneness-taxi.com/service.html", "pick": {"yen": 1000, "unsure": true}, "wait": {"free": 10, "unit": 10, "yen": 250}}, "pay": "カード・交通系IC・QR", "review_q": "ペットタクシー ワンネス 東京", "review_name": "ワンネス", "hours": "8-20", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["カード払い可"]}, {"id": "D692c9a6", "name": "ペットタクシー ワンハウス", "pref": "東京都", "areas": ["埼玉", "千葉", "東京"], "area_text": "東京23区、埼玉9市、千葉7市（当日対応）。ほかは相談", "shop": [35.802, 139.808], "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 165], [201, null, 110]], "tax": "税込", "src": "https://onehouse.jp/free/pricelist", "pick": {"yen": 770, "unsure": true}, "wait": {"free": 0, "unit": 10, "yen": 220}}, "pay": "", "review_q": "ペットタクシー ワンハウス 東京", "review_name": "ワンハウス", "hours": "8-20", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D7138c0d", "name": "ペットタクシー東京", "pref": "東京都", "areas": ["東京", "神奈川"], "area_text": "東京16区市（目黒・渋谷・品川など）、川崎・横浜の一部。乗るか降りるかがエリア内なら可", "shop": [35.616, 139.653], "fare": {"base": [0, 0], "tiers": [[1, null, 500]], "pick": {"yen": 2000}, "wait": {"free": 0, "unit": 15, "yen": 300}, "night": {"from": 22, "to": 8, "rate": 0.2}, "longDiscount": [[5000, 0.1], [10000, 0.2], [15000, 0.3]], "tax": "税込", "src": "https://pettaxi-tokyo.jp/"}, "pay": "現金・カード・電子マネー・コード決済／着いたとき", "review_q": "ペットタクシー東京 東京", "review_name": "ペットタクシー東京", "hours": "8-22", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}}, {"id": "D7922e74", "name": "ペトタクファインド", "pref": "東京都", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "千葉県全域ほか首都圏・全国に拡大中。長距離は相談", "shop": [35.69, 139.692], "fare": {"base": [3500, 0], "tiers": [[1, 100, 220], [101, 300, 190], [301, null, 170]], "tax": "税込", "src": "https://pettaxi-find.com/chiba/", "pick": {"per": 120}, "wait": {"free": 10, "unit": 10, "yen": 500}, "night": {"from": 21, "to": 7, "flat": 3000}}, "pay": "現金・カード・電子マネー・QR／到着後", "review_q": "ペトタクファインド 東京", "review_name": "ペトタクファインド", "hours": "", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK", "多頭OK", "前日までキャンセル無料", "カード払い可"]}, {"id": "D0d611b0", "name": "COCOタク 湘南店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "藤沢・茅ヶ崎・鎌倉・大和・綾瀬・海老名・寒川・横浜など", "shop": [35.352, 139.497], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "roundContinuous": true, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 22, "to": 8, "flat": 3300}, "tax": "", "src": "https://www.cocotaku-shonan.com/料金プラン"}, "pay": "", "review_q": "COCOタク 湘南店 神奈川", "review_name": "COCOタク 湘南店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "De65cb2d", "name": "Legolas House（レゴラスハウス）", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.513, 139.433], "fare": {"kind": "table", "table": [[5, 3850], [10, 4950], [15, 6050], [20, 7150], [25, 8250], [30, 9350], [35, 10450], [40, 11550], [45, 12650], [50, 13750]], "roundTable": [[5, 6160], [10, 7920], [15, 9680], [20, 11440], [25, 13200], [30, 14960], [35, 16720], [40, 18480], [45, 20240], [50, 22000]], "wait": {"free": 0, "unit": 30, "yen": 550}, "tax": "", "src": "https://www.legolashouse.com/price"}, "pay": "", "review_q": "Legolas House 神奈川", "review_name": "Legolas House", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "D945f580", "name": "ikimono care（イキモノケア）", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "東京・神奈川（ほかは相談）", "shop": [35.42, 139.66], "fare": {"kind": "time", "time": {"first": [90, 5720], "unit": [15, 1430], "discount": {"min": 120, "rate": 0.05}}, "pick": {"km": 10, "yen": 0, "per": 825, "unit": 10}, "back": {"km": 10, "yen": 0, "per": 825, "unit": 10}, "tax": "税込", "src": "https://www.ikimonocare.com/"}, "pay": "", "review_q": "ikimono care 神奈川", "review_name": "ikimono care", "hours": "8-20", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D5598693", "name": "ふわふわペットタクシー", "pref": "神奈川県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "関東近県から全国（沖縄・離島は不可）", "shop": [35.441, 139.528], "fare": {"base": [3100, 5], "tiers": [[6, 100, 200], [101, 200, 130], [201, null, 110]], "tax": "消費税なし", "src": "https://pet-yokohama.com/", "pick": {"km": 8, "yen": 0, "per": 100}, "wait": {"free": 20, "unit": 10, "yen": 250}, "night": {"from": 22, "to": 8, "rate": 0.3}}, "pay": "現金・カード・電子マネー・QR（フェリー長距離は事前決済）", "review_q": "ふわふわペットタクシー 神奈川", "review_name": "ふわふわペットタクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["介助のサポートあり", "大型犬OK", "カード払い可"]}, {"id": "D5604536", "name": "やこうDogはうす", "pref": "神奈川県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "横浜・川崎・東京中心。神奈川・千葉・埼玉、長距離も", "shop": [35.508, 139.676], "fare": {"base": [300, 1], "tiers": [[2, 50, 300], [51, 100, 250], [101, null, 200]], "tax": "税別", "src": "https://yakodoghouse.com/pet-taxi-price/", "pick": {"per": 150}, "back": {}, "wait": {"free": 30, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 7, "rate": 0.2}}, "pay": "", "review_q": "やこうDogはうす 神奈川", "review_name": "やこうDogはうす", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "points": ["大型犬OK", "往復の割引あり"]}, {"id": "Dc7b4703", "name": "わんにゃんハイヤー Angel Buggy", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.568, 139.655], "fare": {"base": [800, 2], "tiers": [[3, null, 400]], "tax": "", "src": "https://www.angel-buggy.com/ryoukin.html", "pick": {"yen": 1300, "unsure": false}}, "pay": "", "review_q": "わんにゃんハイヤー Angel Buggy 神奈川", "review_name": "わんにゃんハイヤー Angel", "hours": "8-19", "flex": false, "closed": [], "lead_days": 0, "cut": 16, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "Dc46d194", "name": "ペッタクん", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "横須賀・三浦・逗子・鎌倉・葉山・横浜。神奈川全域・遠方は相談", "shop": [35.307, 139.622], "fare": {"kind": "table", "table": [[5, 3000]], "pick": {"per": 160}, "back": {"km": 30, "yen": 0, "over": 3000}, "wait": {"free": 20, "unit": 10, "yen": 200}, "night": {"from": 20, "to": 6, "flat": 4000}, "tax": "", "src": "https://pettakun.com/service"}, "pay": "", "review_q": "ペッタクん 神奈川", "review_name": "ペッタクん", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D68f9d95", "name": "ペットタクシー Animals", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "神奈川発、全国", "shop": [35.4, 139.591], "fare": {"base": [2500, 5], "tiers": [[6, 100, 300], [101, 200, 250], [201, null, 200]], "tax": "税込", "src": "https://h12150825.wixsite.com/taxi-animals", "pick": {"km": 3, "yen": 0, "per": 400, "unit": 2}, "back": {}, "wait": {"free": 15, "unit": 15, "yen": 300}, "night": {"from": 20, "to": 8, "rate": 0.2}}, "pay": "", "review_q": "ペットタクシー Animals 神奈川", "review_name": "Animals", "hours": "8-20", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "fish"], "no": []}, "points": ["飼い主さんの同乗無料"]}, {"id": "D8da1ced", "name": "ペットタクシー わんだにゃー", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "神奈川・東京中心に全国", "shop": [35.339, 139.49], "fare": null, "pay": "JCBタクシーチケット取扱", "review_q": "ペットタクシー わんだにゃー 神奈川", "review_name": "わんだにゃー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": true, "ok": [], "no": []}}, {"id": "Daed391e", "name": "ペットタクシー シアンシャ 厚木店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "厚木・伊勢原・海老名・愛甲郡", "shop": [35.441, 139.364], "fare": {"base": [660, 0], "tiers": [[1, null, 330]], "tax": "", "src": "https://chienchat.jp/atsugi/", "pick": {"per": 330}, "wait": {"free": 30, "unit": 30, "yen": 550}}, "pay": "現金・カード／終わったあと", "review_q": "ペットタクシー シアンシャ 厚木店 神奈川", "review_name": "シアンシャ 厚木店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "ケージを無料で使える", "前日までキャンセル無料", "カード払い可"]}, {"id": "D0437ae3", "name": "ペットタクシー シアンシャ 鎌倉店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "鎌倉・逗子・葉山中心、藤沢・茅ヶ崎など", "shop": [35.319, 139.551], "fare": {"base": [660, 0], "tiers": [[1, null, 330]], "tax": "", "src": "https://chienchat.jp/kamakura/", "pick": {"per": 330}, "wait": {"free": 30, "unit": 30, "yen": 550}}, "pay": "現金・カード／終わったあと", "review_q": "ペットタクシー シアンシャ 鎌倉店 神奈川", "review_name": "シアンシャ 鎌倉店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "大型犬OK", "ケージを無料で使える", "前日までキャンセル無料"]}, {"id": "D5f32b1e", "name": "三和交通 ペットタクシー", "pref": "神奈川県", "areas": ["埼玉", "東京", "神奈川"], "area_text": "横浜市北部、東京の多摩の一部、埼玉の和光・朝霞・志木など（23区・武蔵野・三鷹は不可）", "shop": null, "fare": null, "pay": "", "review_q": "三和交通 ペットタクシー 神奈川", "review_name": "三和交通", "hours": "", "flex": false, "closed": [], "lead_days": 1, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "points": ["大型犬OK"]}, {"id": "Daf1e25b", "name": "湘南Dog Life College（ペットタクシー）", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.264, 139.152], "fare": {"base": [2000, 5], "tiers": [[6, null, 200]], "tax": "税抜", "src": "https://www.shonan-dog-college.jp/taxi", "wait": {"free": 0, "unit": 10, "yen": 200}}, "pay": "", "review_q": "湘南Dog Life College 神奈川", "review_name": "湘南Dog Life", "hours": "9-18", "flex": false, "closed": [0, 6], "lead_days": 3, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D0b50c1a", "name": "湘南ペットハイヤー", "pref": "神奈川県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "神奈川・関東近県中心、全国（島しょ除く）", "shop": [35.335, 139.349], "fare": null, "pay": "", "review_q": "湘南ペットハイヤー 神奈川", "review_name": "湘南ペットハイヤー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["bird", "reptile", "fish"], "no": []}}, {"id": "D06b72ea", "name": "鎌倉ペットタクシー", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.354, 139.531], "fare": {"base": [660, 0], "tiers": [[1, null, 300]], "perkmFromStart": true, "pick": {"per": 300}, "night": {"from": 21, "to": 9, "unknown": true}, "tax": "", "src": "https://pets-taxi.net/ja/kamakurapettaxi"}, "pay": "", "review_q": "鎌倉ペットタクシー 神奈川", "review_name": "鎌倉ペットタクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D40a4aa0", "name": "COCOタク さいたま南店", "pref": "埼玉県", "areas": ["埼玉", "東京"], "area_text": "さいたま市中心に県南部、東京の一部", "shop": [35.846, 139.66], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165, "unsure": true}, "wait": {"free": 10, "unit": 10, "yen": 220}, "tax": "税込", "src": "https://cocotaxi-saitama.com/"}, "pay": "現金・カード・PayPay等", "review_q": "COCOタク さいたま南店 埼玉", "review_name": "COCOタク さいたま南店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "大型犬OK", "スロープつき", "カード払い可"]}, {"id": "Dfcb8480", "name": "COCOタク 埼玉川越店", "pref": "埼玉県", "areas": ["埼玉"], "area_text": "川越中心に所沢・入間・狭山・飯能・熊谷など。隣県・全国も", "shop": [35.981, 139.479], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "tax": "", "src": "https://pet-taxi-saitama-kawagoe.jp/"}, "pay": "現金・カード・QR", "review_q": "COCOタク 埼玉川越店 埼玉", "review_name": "COCOタク 埼玉川越店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D853ae97", "name": "COCOタク 埼玉春日部店", "pref": "埼玉県", "areas": ["茨城", "栃木", "群馬", "埼玉", "千葉"], "area_text": "春日部中心、埼玉東部、茨城（古河・五霞・坂東）、千葉（野田・柏・流山）、栃木（小山・野木）、群馬（館林・邑楽）の一部", "shop": [35.96, 139.77], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-kasukabe.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QR", "review_q": "COCOタク 埼玉春日部店 埼玉", "review_name": "COCOタク 埼玉春日部店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "前日までキャンセル無料"]}, {"id": "D3cc1cce", "name": "ペットケア151A", "pref": "埼玉県", "areas": ["埼玉", "東京"], "area_text": "川口・蕨・草加・戸田、東京の北区・足立・板橋。緊急は全国", "shop": [35.808, 139.724], "fare": {"base": [3000, 15], "tiers": [[16, 25, 280], [26, 50, 230], [51, 100, 180], [101, null, 150]], "tax": "税抜", "src": "https://petcare-151a.com/price.html", "wait": {"free": 30, "unit": 30, "yen": 1000}, "night": {"from": 22, "to": 5, "rate": 0.2}}, "pay": "", "review_q": "ペットケア151A 埼玉", "review_name": "ペットケア151A", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "reptile", "fish"], "no": []}}, {"id": "De3f35f2", "name": "コインペットタクシー シエロ", "pref": "千葉県", "areas": ["埼玉", "千葉", "東京"], "area_text": "東京23区・都下、千葉、埼玉の一部", "shop": [35.787, 139.903], "fare": {"base": [550, 3], "tiers": [[4, null, 110]], "pick": {"km": 3, "yen": 550, "per": 110}, "back": {"bands": [[4, 0], [10, 550]], "halfRide": true}, "wait": {"first": [20, 550], "free": 0, "unit": 10, "yen": 110, "after": [60, 220]}, "night": {"bands": [[20, 22, 1100], [22, 24, 2200], [0, 5, 3300], [5, 7, 2200], [7, 8, 1100]]}, "tax": "税込", "src": "https://pettaxi.jp/"}, "pay": "", "review_q": "コインペットタクシー シエロ 千葉", "review_name": "コインペットタクシー シエロ", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird", "reptile"], "no": []}}, {"id": "Dd8c07a8", "name": "ペットタクシー しっぽ", "pref": "千葉県", "areas": ["千葉"], "area_text": "", "shop": [35.67, 140.168], "fare": {"base": [1500, 3], "tiers": [[4, null, 100]], "tax": "税抜", "src": "https://co90p-sippo.crayonsite.info/", "pick": {"yen": 500, "unsure": false}, "wait": {"free": 20, "unit": 10, "yen": 150}}, "pay": "", "review_q": "ペットタクシー しっぽ 千葉", "review_name": "しっぽ", "hours": "8-18", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["bird", "reptile"], "no": []}}, {"id": "D3c85024", "name": "ペットタクシー パールのしっぽ", "pref": "千葉県", "areas": ["千葉"], "area_text": "千葉市中心、県内外の遠方も（事前予約）", "shop": [35.607, 140.106], "fare": {"base": [1500, 5], "tiers": [[6, null, 200]], "pick": {"km": 5, "yen": 0, "per": 100}, "tax": "", "src": "https://pearlno-shippo.com/"}, "pay": "", "review_q": "ペットタクシー パールのしっぽ 千葉", "review_name": "パールのしっぽ", "hours": "9-21", "flex": false, "closed": [4], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK"]}, {"id": "Dedcfcd2", "name": "動物苑（ペット送迎）", "pref": "千葉県", "areas": ["茨城", "千葉"], "area_text": "千葉・茨城中心（松戸・柏・牛久）", "shop": null, "fare": {"base": [2500, 5], "tiers": [[6, null, 250]], "tax": "", "src": "https://www.pet594.com/pet-transport/", "pick": {"per": 250}, "wait": {"free": 0, "unit": 10, "yen": 350}}, "pay": "", "review_q": "動物苑 千葉", "review_name": "動物苑", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D68a3be6", "name": "東葛ペットタクシー", "pref": "千葉県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "東京近郊全域、千葉・埼玉・神奈川など首都圏。全国輸送も", "shop": [35.868, 139.976], "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 170], [201, null, 130]], "pick": {"yen": 1000, "unsure": true}, "back": {}, "wait": {"free": 0, "unit": 10, "yen": 300}, "tax": "税込", "src": "https://pet-taxi.jp/charge/"}, "pay": "", "review_q": "東葛ペットタクシー 千葉", "review_name": "東葛ペットタクシー", "hours": "8-20", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird"], "no": []}}, {"id": "Dc28c19e", "name": "ワンワンハウス（ペットタクシー）", "pref": "群馬県", "areas": ["群馬"], "area_text": "", "shop": [36.4, 139.06], "fare": {"base": [5800, 10], "tiers": [[11, 100, 330], [101, 200, 300], [201, null, 270]], "tax": "税別", "src": "https://wan-wan-house.com/pet-taxi/", "pick": {"km": 5, "yen": 1600, "per": 260}, "back": {"km": 5, "yen": 1600, "per": 260}, "wait": {"free": 0, "unit": 30, "yen": 2500}, "night": {"from": 22, "to": 5, "rate": 0.3}}, "pay": "現金・カード・電子マネー・交通系IC・QR", "review_q": "ワンワンハウス 群馬", "review_name": "ワンワンハウス", "hours": "9-19", "flex": false, "closed": [4], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["飼い主さんの同乗無料", "介助のサポートあり", "カード払い可"]}, {"id": "Db405639", "name": "D-RIDE（ペットタクシー）", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌・北広島・江別と近郊（北海道全域も相談）", "shop": [42.99, 141.45], "fare": {"base": [2980, 7], "tiers": [[8, null, 150]], "tax": "税込", "src": "https://d-ride.jp/pettaxi.html", "pick": {"yen": 0, "unsure": true}, "wait": {"free": 30, "unit": 10, "yen": 200}, "night": {"from": 22, "to": 7, "rate": 0.2}}, "pay": "現金・カード・電子決済", "review_q": "D-RIDE 北海道", "review_name": "D-RIDE", "hours": "8-18", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK", "カード払い可"]}, {"id": "D44948b6", "name": "ぺトタク（札幌・小樽）", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌・小樽近郊", "shop": null, "fare": {"base": [3300, 5], "tiers": [[6, 200, 150], [201, null, 120]], "tax": "税込", "src": "https://pet-tax.com/price", "pick": {"yen": 900, "unsure": false}, "wait": {"free": 10, "unit": 10, "yen": 200}}, "pay": "カード・現金・コンビニ後払い", "review_q": "ぺトタク 北海道", "review_name": "ぺトタク", "hours": "8-20", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["カード払い可"]}, {"id": "D13b7c6f", "name": "ペット専用タクシー aiai", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌・北海道全域（新千歳空港の送迎パックも）", "shop": [43.05, 141.405], "fare": {"base": [3300, 0], "tiers": [[1, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-aiai.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 0, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 5, "flat": 3300}}, "pay": "現金・PayPay（カード・QRの記載も）／送迎後", "review_q": "ペット専用タクシー aiai 北海道", "review_name": "ペット専用タクシー aiai", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "大型犬OK", "往復の割引あり"]}, {"id": "D1f53c72", "name": "COCOタク岩手盛岡店", "pref": "岩手県", "areas": ["岩手"], "area_text": "盛岡市・隣接エリア（県内のほかは相談）", "shop": [39.667, 141.142], "fare": {"base": [3300, 10], "tiers": [[11, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocomorioka.iwate.jp/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}}, "pay": "現金のみ（キャッシュレスは順次）", "review_q": "COCOタク岩手盛岡店 岩手", "review_name": "COCOタク岩手盛岡店", "hours": "9-19", "flex": false, "closed": [0, 6], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["追加料金なし"]}, {"id": "D4adf70b", "name": "PETRIP", "pref": "宮城県", "areas": ["宮城"], "area_text": "仙台・名取・利府・多賀城・塩竈・富谷（ほかもできる限り）", "shop": null, "fare": {"base": [2900, 5], "tiers": [[6, 50, 160], [51, null, 140]], "pick": {"yen": 1000, "unknownOver": 10}, "pickEachLeg": true, "wait": {"free": 100000, "unit": 10, "yen": 0}, "night": {"from": 20, "to": 8, "flat": 3000}, "tax": "", "src": "https://petrip.co.jp/"}, "pay": "現金・PayPay", "review_q": "PETRIP 宮城", "review_name": "PETRIP", "hours": "6-23", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["飼い主さんの同乗無料", "介助のサポートあり", "大型犬OK", "多頭OK"]}, {"id": "D30e1838", "name": "ニャンワンクラブ（ペットタクシー）", "pref": "宮城県", "areas": ["宮城"], "area_text": "", "shop": [38.27, 140.85], "fare": null, "pay": "", "review_q": "ニャンワンクラブ 宮城", "review_name": "ニャンワンクラブ", "hours": "9-18", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["多頭OK", "カード払い可"]}, {"id": "D59e83ab", "name": "万代タクシー（ペットタクシー）", "pref": "新潟県", "areas": ["新潟"], "area_text": "", "shop": [37.915, 139.058], "fare": null, "pay": "", "review_q": "万代タクシー 新潟", "review_name": "万代タクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}}, {"id": "D1132ff9", "name": "冨士タクシー（ペットタクシー）", "pref": "石川県", "areas": ["石川"], "area_text": "金沢・白山・野々市・内灘", "shop": null, "fare": null, "pay": "", "review_q": "冨士タクシー 石川", "review_name": "冨士タクシー", "hours": "", "flex": false, "closed": [], "lead_days": 1, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile"], "no": []}}, {"id": "Da40f372", "name": "ペットタクシー With☆（ウィズ）", "pref": "山梨県", "areas": ["山梨"], "area_text": "全国（長距離の直行便が中心）", "shop": [35.62, 138.555], "fare": null, "pay": "前払い（振込・メールで届くカード決済）", "review_q": "ペットタクシー With☆ 山梨", "review_name": "With☆", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK", "カード払い可"]}, {"id": "Dd472236", "name": "ペットタクシー COCOタク静岡", "pref": "静岡県", "areas": ["静岡"], "area_text": "静岡市・隣接エリア（県内のほかもできる限り）", "shop": [34.993, 138.385], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi-shizuoka.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "カード・PayPay", "review_q": "ペットタクシー COCOタク静岡 静岡", "review_name": "COCOタク静岡", "hours": "8-21", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "points": ["深夜・早朝も相談可", "前日までキャンセル無料", "カード払い可"]}, {"id": "D44cfd16", "name": "HAPPY WITH（ペットタクシー）", "pref": "愛知県", "areas": ["愛知"], "area_text": "", "shop": [35.135, 136.84], "fare": {"kind": "time", "time": {"first": [20, 4400], "unit": [10, 550], "maxKm": 20}, "off": {"from": 9, "to": 18, "perHour": 1650}, "pick": {"km": 3, "yen": 0, "per": 280}, "tax": "税込", "src": "https://happywith.pet/price/"}, "pay": "現金（降りるとき）・事前の振込。カード・QRは不可", "review_q": "HAPPY WITH 愛知", "review_name": "HAPPY WITH", "hours": "8-20", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}}, {"id": "Dcda25a4", "name": "ペットタクシー パウパウ", "pref": "愛知県", "areas": ["愛知"], "area_text": "名古屋市内が基本（市外のお迎えは別料金）", "shop": [35.15, 136.932], "fare": null, "pay": "現金・カード・PayPay", "review_q": "ペットタクシー パウパウ 愛知", "review_name": "パウパウ", "hours": "", "flex": false, "closed": [], "lead_days": 1, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile"], "no": []}}, {"id": "D1834601", "name": "ZEROペットタクシー", "pref": "滋賀県", "areas": ["滋賀"], "area_text": "滋賀県（栗東・守山・草津など）", "shop": [35.03, 135.995], "fare": null, "pay": "現金・カード・交通系IC・QR", "review_q": "ZEROペットタクシー 滋賀", "review_name": "ZEROペットタクシー", "hours": "", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Dc9d8a2b", "name": "PetTAXI24", "pref": "京都府", "areas": ["京都"], "area_text": "京都・木津川", "shop": [34.737, 135.82], "fare": {"base": [3300, 20], "tiers": [[21, null, 110, 10]], "tax": "税込", "night": {"from": 21, "to": 6, "flat": 3300}, "src": "https://j-pettaxi.com/"}, "pay": "", "review_q": "PetTAXI24 京", "review_name": "PetTAXI24", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": ["bird", "reptile"]}, "points": ["24時間受付", "深夜・早朝も相談可", "大型犬OK", "カード払い可"]}, {"id": "D25bac67", "name": "ペットサポート てんりん", "pref": "京都府", "areas": ["京都"], "area_text": "京都中心、全国も", "shop": [34.985, 135.759], "fare": {"base": [3000, 10], "tiers": [[11, 100, 200], [101, 200, 120], [201, null, 100]], "pick": {"km": 10, "yen": 0, "per": 100}, "wait": {"free": 20, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 9, "rate": 0.25}, "tax": "税別", "src": "https://ten-rin.jp/taxi/"}, "pay": "", "review_q": "ペットサポート てんりん 京", "review_name": "ペットサポート てんりん", "hours": "9-21", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "Dfc6c94f", "name": "木谷わんわんタクシー", "pref": "京都府", "areas": ["京都"], "area_text": "京都中心（乗るか降りるかが営業エリア内なら他府県も）", "shop": [35.03, 135.75], "fare": {"kind": "time", "time": {"first": [60, 6280], "unit": [30, 3140]}, "tax": "税込", "src": "https://kitani11taxi.com/"}, "pay": "", "review_q": "木谷わんわんタクシー 京", "review_name": "木谷わんわんタクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK"]}, {"id": "D7d574bf", "name": "ARC（アルク）Pet Taxi & Pet Sitter", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "関西全域（大阪・兵庫・京都・奈良）", "shop": [34.762, 135.516], "fare": {"base": [3300, 10], "tiers": [[11, 100, 220], [101, null, 110]], "tax": "", "src": "https://pet-arc.com/price/", "pick": {"km": 10, "yen": 0, "per": 110}, "wait": {"free": 20, "unit": 10, "yen": 330}}, "pay": "", "review_q": "ARCPet Taxi & Pet Sitter 大阪", "review_name": "ARCPet Taxi", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}}, {"id": "Db8bafea", "name": "Comasuke（コマスケ）", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "茨木・高槻・豊中など、京都市・亀岡・宇治など。近畿一円・全国", "shop": [34.857, 135.548], "fare": {"base": [3000, 5], "tiers": [[6, null, 180]], "pick": {"per": 180}, "back": {}, "wait": {"free": 0, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 7, "flat": 4500}, "tax": "税抜", "src": "https://comasuke.com/"}, "pay": "現金・カード・電子マネー・QR", "review_q": "Comasuke 大阪", "review_name": "Comasuke", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "大型犬OK", "前日までキャンセル無料", "カード払い可"]}, {"id": "D6125f28", "name": "DOG HAIR STUDIO KEN（ペットタクシー）", "pref": "大阪府", "areas": ["大阪"], "area_text": "豊中周辺・伊丹空港。輸送は提携会社で全国", "shop": [34.794, 135.452], "fare": {"base": [4000, 10], "tiers": [[11, null, 200]], "pick": {"yen": 0, "unknownOver": 5}, "wait": {"free": 0, "unit": 10, "yen": 300}, "tax": "税込", "src": "https://doghairstudioken.jp/"}, "pay": "カード・電子マネー・交通系IC", "review_q": "DOG HAIR STUDIO KEN 大阪", "review_name": "DOG HAIR", "hours": "10-18", "flex": false, "closed": [3], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}}, {"id": "D7e284b0", "name": "PetTaxi けいわん堺", "pref": "大阪府", "areas": ["大阪"], "area_text": "大阪府全域（府外は相談）", "shop": [34.54, 135.56], "fare": {"base": [280, 1], "tiers": [[2, null, 280]], "tax": "", "src": "https://keionetp-sakai.com/price/", "pick": {"per": 280}, "wait": {"free": 30, "first": [60, 1000], "unit": 30, "yen": 500}, "night": {"from": 22, "to": 8, "rate": 0.2}}, "pay": "", "review_q": "PetTaxi けいわん堺 大阪", "review_name": "PetTaxi けいわん堺", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "前日までキャンセル無料", "カード払い可"]}, {"id": "D01478c8", "name": "アイアールサービス（ペットタクシー）", "pref": "大阪府", "areas": ["大阪"], "area_text": "大阪市内（北区）", "shop": [34.705, 135.498], "fare": {"base": [3000, 10], "tiers": [[11, null, 190]], "tax": "税込", "src": "https://www.i-and-r.com/pettaxi.html", "pick": {"km": 10, "yen": 0, "per": 100, "unsure": true}}, "pay": "", "review_q": "アイアールサービス 大阪", "review_name": "アイアールサービス", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile", "fish"], "no": []}, "points": ["大型犬OK"]}, {"id": "Da9518d0", "name": "キャリーワン", "pref": "大阪府", "areas": ["大阪"], "area_text": "全国（集荷・お届け）", "shop": [34.814, 135.651], "fare": {"kind": "zones", "zones": [{"label": "枚方市〜枚方市", "a": "枚方市", "b": "枚方市", "one": 3300, "round": 5500}, {"label": "枚方市〜寝屋川市・交野市・八幡市", "a": "枚方市", "b": "寝屋川市|交野市|八幡市", "one": 4400, "round": 6600}, {"label": "枚方市〜高槻市・茨木市・門真市", "a": "枚方市", "b": "高槻市|茨木市|門真市", "one": 5500, "round": 8800}, {"label": "枚方市〜京都市", "a": "枚方市", "b": "京都市", "one": 7700, "round": 11000}, {"label": "枚方市〜大阪市内", "a": "枚方市", "b": "大阪市", "one": 8800, "round": 11000}, {"label": "寝屋川市〜交野市・門真市・茨木市", "a": "寝屋川市", "b": "交野市|門真市|茨木市", "one": 6600, "round": 8800}, {"label": "寝屋川市・交野市・高槻市〜大阪市", "a": "寝屋川市|交野市|高槻市", "b": "大阪市", "one": 7700, "round": 11000}, {"label": "高槻市〜高槻市", "a": "高槻市", "b": "高槻市", "one": 5500, "round": 7700}, {"label": "高槻市〜茨木市", "a": "高槻市", "b": "茨木市", "one": 6600, "round": 8800}], "pick": {"yen": 0, "unknownOver": 10}, "back": {}, "wait": {"free": 30, "unit": 30, "yen": 660}, "tax": "税込", "src": "https://carry-one.net/priceandflow/"}, "pay": "", "review_q": "キャリーワン 大阪", "review_name": "キャリーワン", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}}, {"id": "D66c4625", "name": "ペットタクシー アイボウ（相棒）", "pref": "大阪府", "areas": ["大阪", "兵庫", "奈良", "和歌山"], "area_text": "羽曳野・柏原・藤井寺・八尾・堺中心、奈良・兵庫・和歌山の一部", "shop": [34.54, 135.61], "fare": {"base": [2000, 5], "tiers": [[6, null, 250]], "tax": "税込", "src": "https://www.aibou.com/info/price.html", "pick": {"km": 5, "yen": 1500, "per": 100}, "back": {}, "wait": {"free": 30, "unit": 15, "yen": 750}}, "pay": "カード可", "review_q": "ペットタクシー アイボウ 大阪", "review_name": "アイボウ", "hours": "8-18", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "D874b316", "name": "ペットタクシー マイファミリー", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "北大阪・吹田・摂津・茨木・高槻中心、近畿・全国", "shop": [34.82, 135.61], "fare": {"base": [2000, 5], "tiers": [[6, 55, 230], [56, null, 110]], "heavy": {"kg": 15, "add": 500}, "pick": {"km": 5, "yen": 0, "per": 110}, "back": {}, "wait": {"free": 30, "unit": 15, "yen": 300}, "night": {"bands": [[21, 24, 2000], [0, 6, 2000], [6, 8, 1000]]}, "tax": "税込", "src": "https://my-family-takatsuki.com/price.html"}, "pay": "", "review_q": "ペットタクシー マイファミリー 大阪", "review_name": "マイファミリー", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "大型犬OK"]}, {"id": "D1c2a5e3", "name": "ミントペットタクシー", "pref": "大阪府", "areas": ["大阪"], "area_text": "堺市西区中心、和泉", "shop": [34.54, 135.47], "fare": null, "pay": "", "review_q": "ミントペットタクシー 大阪", "review_name": "ミントペットタクシー", "hours": "9-17", "flex": false, "closed": [0, 6], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["カード払い可"]}, {"id": "D9f338ec", "name": "ペットタクシー アニマルプラス", "pref": "兵庫県", "areas": ["兵庫"], "area_text": "神戸市の長田区〜芦屋市（須磨・西・北・垂水区は除く）", "shop": [34.705, 135.205], "fare": {"base": [3800, 5], "tiers": [[6, 30, 250], [31, 40, 200], [41, 50, 150], [51, null, 100]], "tax": "", "src": "https://animal-plus.p-kit.com/page0002.html", "back": {"km": 10, "yen": 0, "over": 500}, "wait": {"free": 15, "unit": 15, "yen": 250}}, "pay": "", "review_q": "ペットタクシー アニマルプラス 兵庫", "review_name": "アニマルプラス", "hours": "8-19", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK", "ワクチン証明は不要"]}, {"id": "D72024d3", "name": "ラッキーペットサービス", "pref": "兵庫県", "areas": ["大阪", "兵庫"], "area_text": "西宮・芦屋・宝塚・伊丹・尼崎・川西・神戸・大阪", "shop": [34.735, 135.385], "fare": {"base": [2500, 5], "tiers": [[6, 19, 250], [20, 100, 200], [101, null, 150]], "tax": "税抜", "pick": {"per": 150, "unsure": true}, "wait": {"free": 20, "unit": 10, "yen": 250}, "src": "https://lucky-pettaxi.jimdosite.com/%E3%82%A8%E3%83%AA%E3%82%A2%E3%83%BB%E9%80%81%E8%BF%8E%E6%96%99%E9%87%91/"}, "pay": "", "review_q": "ラッキーペットサービス 兵庫", "review_name": "ラッキーペットサービス", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D154d458", "name": "COCOタク ならまち店", "pref": "奈良県", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "奈良市中心・近畿圏（奈良・大阪・兵庫・京都・滋賀・和歌山）", "shop": [34.677, 135.835], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-nara.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "review_q": "COCOタク ならまち店 奈良", "review_name": "COCOタク ならまち店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "前日までキャンセル無料"]}, {"id": "D0a999a3", "name": "ペットタクシー COCOタク奈良", "pref": "奈良県", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "奈良市・大和郡山・生駒・木津川・精華（近畿一円、遠方も相談）", "shop": [34.68, 135.75], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-coco-taxi-nara.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "review_q": "ペットタクシー COCOタク奈良 奈良", "review_name": "COCOタク奈良", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "前日までキャンセル無料"]}, {"id": "D0ff488e", "name": "わんニャンMOB（Heiwa Taxi）", "pref": "岡山県", "areas": ["岡山"], "area_text": "岡山（倉敷地区は除く）", "shop": [34.65, 133.91], "fare": null, "pay": "", "review_q": "わんニャンMOB 岡山", "review_name": "わんニャンMOB", "hours": "", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D225080e", "name": "ペッタク（PETTAXI）", "pref": "広島県", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山", "広島"], "area_text": "広島発・全国（中四国・九州北部・関西が中心）", "shop": [34.335, 132.528], "fare": {"base": [3000, 0], "tiers": [[1, null, 200]], "tax": "", "src": "https://pettaku.com/price-guide/", "pick": {"per": 100}, "wait": {"free": 10, "unit": 10, "yen": 300}}, "pay": "", "review_q": "ペッタク 広島", "review_name": "ペッタク", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D678e01f", "name": "ペットタクシー 響", "pref": "広島県", "areas": ["広島"], "area_text": "広島市全域・呉・大竹", "shop": [34.385, 132.42], "fare": {"kind": "table", "table": [[5, 2200], [10, 3300], [15, 4400], [20, 6600], [25, 8800], [30, 9900], [35, 11000], [40, 12100], [45, 14300], [50, 16500], [55, 18700], [60, 20900], [65, 23100]], "pick": {"yen": 880, "unsure": true}, "wait": {"free": 0, "unit": 10, "yen": 220}, "tax": "", "src": "https://pettaxihibiki.hp.peraichi.com/"}, "pay": "カード・PayPay・d払いなど", "review_q": "ペットタクシー 響 広島", "review_name": "響", "hours": "6-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK", "カード払い可", "PayPay可"]}, {"id": "D8001263", "name": "吉島タクシー（ペットタクシー）", "pref": "広島県", "areas": ["広島"], "area_text": "", "shop": [34.374, 132.448], "fare": null, "pay": "", "review_q": "吉島タクシー 広島", "review_name": "吉島タクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}}, {"id": "D7c41c5f", "name": "トップスター（ペットタクシー）", "pref": "徳島県", "areas": ["徳島"], "area_text": "", "shop": [34.135, 134.58], "fare": {"base": [1000, 2], "tiers": [[3, null, 200]], "tax": "税込", "src": "https://www.topstar-tokushima.com/pettaxi", "pick": {"yen": 2500, "unsure": false}, "wait": {"free": 0, "unit": 30, "yen": 500}}, "pay": "", "review_q": "トップスター 徳島", "review_name": "トップスター", "hours": "10-17", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["大型犬OK"]}, {"id": "Df31960d", "name": "ペットタクシー Happy", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡県内・九州・全国（一部離島は別）", "shop": [33.645, 130.69], "fare": {"base": [3300, 5], "tiers": [[6, null, 175]], "tax": "税込", "src": "https://www.pet-taxi-happy.jp/price/", "pick": {"per": 175, "cap": 1100}, "back": {}, "wait": {"free": 15, "unit": 10, "yen": 250}, "night": {"from": 20, "to": 8, "rate": 0.2}}, "pay": "", "review_q": "ペットタクシー Happy 福岡", "review_name": "Happy", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}}, {"id": "Dbffb89d", "name": "ペットタクシー RinRin", "pref": "福岡県", "areas": ["福岡"], "area_text": "筑豊（飯塚・田川・直方）だけ", "shop": [33.64, 130.805], "fare": {"kind": "table", "table": [[3, 1800], [5, 2400], [10, 3500], [15, 4000], [20, 4500], [25, 5500], [30, 6000], [35, 6500], [40, 7000], [45, 7500], [50, 8500]], "roundTable": [[3, 2800], [5, 3800], [10, 5600], [15, 6400], [20, 7200], [25, 8800], [30, 9600], [35, 10400], [40, 11200], [45, 12000], [50, 13600]], "tableOver": 150, "pick": {"per": 30}, "back": {}, "wait": {"free": 30, "unit": 30, "yen": 550}, "tax": "", "src": "https://npet.jp/rinrin-t/price.html"}, "pay": "", "review_q": "ペットタクシー RinRin 福岡", "review_name": "RinRin", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "Db28bc5b", "name": "福岡わんわんエクスプレス", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡拠点・全国", "shop": [33.584, 130.402], "fare": {"kind": "zone", "zone": {"city": "福岡市", "one": 3000, "round": 5000}, "wait": {"free": 15, "unit": 15, "yen": 1000}, "night": {"from": 20, "to": 8, "flat": 5000}, "pick": {"yen": 0}, "back": {}, "tax": "", "src": "https://wanwan.pet/"}, "pay": "", "review_q": "福岡わんわんエクスプレス 福岡", "review_name": "福岡わんわんエクスプレス", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["24時間受付"]}, {"id": "D7847612", "name": "福岡ペットタクシー HAKAタク", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡市内・大野城・春日・志免など", "shop": [33.59, 130.42], "fare": {"base": [2980, 5], "tiers": [[6, 100, 165], [101, null, 132]], "pick": {"per": 100}, "back": {}, "wait": {"free": 60, "unit": 10, "yen": 200, "cap": 1000}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "", "src": "https://pettaxi-hakataku.wepage.com/"}, "pay": "現金・カード・交通系IC・QR・iD・QUICPay", "review_q": "福岡ペットタクシー HAKAタク 福岡", "review_name": "福岡ペットタクシー HAKAタク", "hours": "9-19", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "points": ["24時間受付", "大型犬OK", "カード払い可", "PayPay可"]}];/*/DISPLAY_COMPANIES*/
// 提携先のカードのアピールポイント（公式サイトに書いてあることだけ。tools/display_companies.py が作り、gen_areas.py が書き込む）
/*PARTNER_POINTS*/var PARTNER_POINTS = {"P002": ["深夜・早朝も相談可", "飼い主さんの同乗無料", "ケージを無料で使える", "多頭OK"], "P003": ["介助のサポートあり", "大型犬OK"]};/*/PARTNER_POINTS*/
function isDisplayOnly_(id) {
  return DISPLAY_COMPANIES.some(function(c) { return c.id === id; });
}
// 表示だけの会社のカード（依頼できない）。口コミの星は、ページがカードを出したあとに selectionScores_ でまとめて取り寄せる
// お迎えの都道府県に対応している会社だけを出し、公式サイトの料金表から料金の目安を計算する（Nori 2026-10-31「大阪の住所で全国の会社が出た。料金も出ない」）
function displayCards_(r, p) {
  if (!CONFIG.SHOW_ALL_CANDIDATES) return [];
  var now = new Date(), same = isSameDay_(r['希望日時'], now), from = null;
  // 犬・猫のほかの子：断る・犬猫のみと書いてある会社は出さない。乗せられると書いてある会社を先に並べ、分からない会社は「確認中」と書く
  var kinds = petsOf_(r).map(animalKind_).filter(function(k, i, a) { return k && a.indexOf(k) === i; });
  var animalOk = function(c) { return kinds.map(function(k) { return displayAnimalOk_(c, k); }); };
  var kindText = kinds.map(function(k) { return ANIMAL_LABEL[k]; }).join('・');
  try { from = JSON.parse((p || {}).route_details || '{}').from; } catch (e) {}
  return DISPLAY_COMPANIES.filter(function(c) { return displayServes_(c, r['都府県'], from) && displayInTime_(c, r['希望日時'], now) && animalOk(c).indexOf(false) < 0; }).map(function(c) {
    var unsure = same && c.lead_days !== 0 ? '当日の予約ができるかは確認中です。' : '', unknown = animalOk(c).indexOf(null) >= 0;
    if (kinds.length) unsure += unknown ? kindText + 'を乗せられるかは確認中です。' : '公式サイトに' + kindText + 'も乗せられると書いてあります。';
    var price = p && displayPrice_(c, p) || {amount:null,text:'料金はお見積もり',night:''};
    return { id:c.id, label:c.name, display_only:true, animal_unknown:unknown, points:c.points || [],
      car:'所在地：' + c.pref + (c.area_text ? '。対応エリア：' + c.area_text + '（公式サイトの記載）' : '（対応エリアは確認中です）') + '。車の詳細はまだ確認中です。' + unsure,
      payment:c.pay ? 'お支払い：' + c.pay + '（公式サイトの記載）' : 'お支払い方法はまだ確認中です',
      price:price, review:null, check:[] };
  }).sort(function(a, b) { // 犬・猫のほかの子を乗せられると書いてある会社を先に。その中で料金が出せる会社を安い順に、そのあとお見積もりの会社
    var x = a.price.amount == null ? Infinity : a.price.amount, y = b.price.amount == null ? Infinity : b.price.amount;
    return (a.animal_unknown ? 1 : 0) - (b.animal_unknown ? 1 : 0) || x - y;
  });
}

// 2点の直線距離（km）
function kmBetween_(a, b) {
  var t = Math.PI / 180, h = Math.pow(Math.sin((b.lat - a.lat) * t / 2), 2) + Math.cos(a.lat * t) * Math.cos(b.lat * t) * Math.pow(Math.sin((b.lng - a.lng) * t / 2), 2);
  return 6371 * 2 * Math.asin(Math.sqrt(Math.min(1, h)));
}
// お迎えの都道府県に対応しているか。お店の位置が分かる会社は、お迎えの場所が遠すぎる（直線で DISPLAY_MAX_KM 超）ときも外す
function displayServes_(c, pref, from) {
  if ((c.areas || []).indexOf(pref) < 0) return false;
  if (c.shop && from && isFinite(from.lat) && isFinite(from.lng) && kmBetween_({lat:c.shop[0], lng:c.shop[1]}, from) > CONFIG.DISPLAY_MAX_KM) return false;
  return true;
}

// 表示だけの会社の料金の目安。tools/display_companies.json の fare（公式サイトの料金表）を決まった式で計算する（AIには計算させない）
// base＝[基本料金, 含まれるkm]、tiers＝[[何km目から, 何km目まで, 1kmごとの円]]、pick/back＝迎車・回送、wait＝待ち時間、night＝夜間・早朝、tax＝税込/税抜
function displayPrice_(c, p) {
  var F = c.fare;
  if (!F) return null;
  var d;
  try { d = JSON.parse(p.route_details); } catch (e) { return null; }
  function validKm(v) { return typeof v === 'number' && isFinite(v) && v >= 1 && v <= 250; }
  function pt(v) { return v && isFinite(v.lat) && isFinite(v.lng) && v.lat >= 20 && v.lat <= 46 && v.lng >= 122 && v.lng <= 154; }
  if (!d || !validKm(d.km) || !validKm(d.backKm) || !pt(d.from) || !pt(d.to)) return null;
  var round = p.trip === '往復';
  if (round && (!pt(d.backFrom) || !pt(d.backTo))) return null;
  var shop = c.shop ? {lat:c.shop[0], lng:c.shop[1]} : null;
  if (F.kind === 'time' && F.time.maxKm && Math.max(d.km, round ? d.backKm : 0) > F.time.maxKm) return null; // その距離は別のプラン（料金が分からない）
  if (F.kind === 'table' && F.tableOver == null && Math.max(d.km, round ? d.backKm : 0) > F.table[F.table.length - 1][0]) return null; // 料金表の距離を超える（お見積もり）
  var zoneHit = F.kind === 'zones' ? findZone(p.pickup, p.dropoff) : null;
  if (F.kind === 'zones' && (!zoneHit || (round && findZone(p.return_pickup || p.dropoff, p.return_dropoff || p.pickup) !== zoneHit))) return null; // 区間の料金表にない
  if (F.kind === 'zone' && !(inZone(p.pickup) && inZone(p.dropoff) && (!round || (inZone(p.return_pickup || p.dropoff) && inZone(p.return_dropoff || p.pickup))))) return null; // 市の外は料金表にない
  function distRide(km) { // 乗った距離の運賃（1km単位に切り上げ）
    km = Math.ceil(km);
    var amount = F.base[0], bk = F.base[1];
    if (F.heavy && Number(p.weight) >= F.heavy.kg) amount += F.heavy.add; // 重い子は基本料金が上がる会社
    F.tiers.forEach(function(t) {
      var a = Math.max(t[0], bk + 1), z = Math.min(km, t[1] == null ? Infinity : t[1]);
      if (z >= a) amount += Math.ceil((z - a + 1) / (t[3] || 1)) * t[2]; // t[3]：何kmごとか（なければ1km）
    });
    return amount;
  }
  // 迎車（お店→乗る場所）・回送（降りた場所→お店）。お店からの距離は直線×1.3の概算
  function leg(rule, at, rideYen) {
    if (rule === undefined) return {yen:0, unknown:false, missing:true}; // 料金表に書いていない
    if (rule.unsure && rule.per == null && rule.yen == null) return {yen:0, unknown:true};
    if (rule.per == null && rule.over == null && rule.unknownOver == null && !rule.tiers && !rule.bands) return {yen:rule.yen || 0, unknown:!!rule.unsure};
    if (!shop) return {yen:rule.yen || 0, unknown:true};
    var km = Math.ceil(kmBetween_(shop, at) * 1.3), free = rule.km || 0, yen = rule.yen || 0;
    if (rule.unknownOver != null) return {yen:yen, unknown:km > rule.unknownOver}; // その距離を超えると別料金（金額は非公開）
    if (rule.tiers) { // 距離の段階で変わる迎車（base＝[円, 含まれるkm]、tiers は乗車と同じ形）
      yen = rule.base[0];
      rule.tiers.forEach(function(t) { var a = Math.max(t[0], rule.base[1] + 1), z = Math.min(km, t[1] == null ? Infinity : t[1]); if (z >= a) yen += Math.ceil((z - a + 1) / (t[3] || 1)) * t[2]; });
      return {yen:yen, unknown:!!rule.unsure};
    }
    if (rule.bands) { // [[何kmまで, 円]]、その先は乗車料金の半額（halfRide）
      for (var i = 0; i < rule.bands.length; i++) if (km <= rule.bands[i][0]) return {yen:rule.bands[i][1], unknown:false};
      return rule.halfRide && rideYen != null ? {yen:Math.ceil(rideYen / 2), unknown:false} : {yen:0, unknown:true};
    }
    if (km > free) {
      if (rule.over != null) yen += rule.over;
      else yen += Math.ceil((km - free) / (rule.unit || 1)) * rule.per;
    }
    if (rule.cap != null) yen = Math.min(yen, rule.cap);
    return {yen:yen, unknown:!!rule.unsure};
  }
  var nightUnknown = false;
  function hourOf(at) { var dt = parseJst_(at); return dt ? (dt.getUTCHours() + 9) % 24 : -1; }
  function nightExtra(amount, at) {
    var N = F.night, h = hourOf(at);
    if (!N || h < 0) return 0;
    if (N.bands) { for (var i = 0; i < N.bands.length; i++) if (h >= N.bands[i][0] && h < N.bands[i][1]) return N.bands[i][2]; return 0; } // 時間帯ごとの定額
    var on = N.from > N.to ? (h >= N.from || h < N.to) : (h >= N.from && h < N.to);
    if (!on) return 0;
    if (N.unknown) { nightUnknown = true; return 0; } // 割増はあるが金額が書いていない
    return N.rate ? Math.ceil(amount * N.rate / 10) * 10 : (N.flat || 0);
  }
  function waitFee(min) { var W = F.wait, y = waitFee0(min); return W.cap != null ? Math.min(y, W.cap) : y; } // cap：待ち時間の上限額
  function waitFee0(min) {
    var W = F.wait;
    if (min <= W.free) return 0;
    if (W.after) { // 途中から単価が変わる（after＝[何分から, 円]）
      var base0 = W.first ? W.first[1] : 0, s0 = W.first ? W.first[0] : W.free;
      return base0 + Math.ceil(Math.max(0, Math.min(min, W.after[0]) - s0) / W.unit) * W.yen + Math.ceil(Math.max(0, min - W.after[0]) / W.unit) * W.after[1];
    }
    if (W.first) return W.first[1] + Math.max(0, Math.ceil((min - W.first[0]) / W.unit)) * W.yen;
    return Math.ceil((min - W.free) / W.unit) * W.yen;
  }
  function sum(x) { return x.ride + x.pickup + x.returnFee + x.nightExtra + x.wait; }
  // 会社ごとの料金のしくみ（Nori 2026-10-31「全ての事業所で違う計算式でもいい。正しい料金が出ることが一番」）
  // kind なし＝距離制（base・tiers）／'time'＝時間制（走る時間は1kmを3分とみる）／'zone'＝決まった市の中なら定額
  var runMin = function(km) { return Math.ceil(km) * 3; };
  function timeFee(min) {
    var T = F.time, y = T.first[1] + Math.max(0, Math.ceil((min - T.first[0]) / T.unit[0])) * T.unit[1];
    if (T.discount && min >= T.discount.min) y = Math.ceil(y * (1 - T.discount.rate)); // 長い時間の割引
    return y;
  }
  function tableFee(km, table) {
    for (var i = 0; i < table.length; i++) if (km <= table[i][0]) return table[i][1];
    var last = table[table.length - 1];
    return F.tableOver != null ? last[1] + Math.ceil(km - last[0]) * F.tableOver : null; // 表の先は1kmごとに足す
  } // [[何kmまで, 円]]
  function offHours(startAt, min) { // 決まった時間（off.from〜off.to）の外を走った時間に、1時間ごとの時間外料金
    var O = F.off, t0 = parseJst_(startAt);
    if (!O || !t0) return 0;
    var outside = 0;
    for (var m = 0; m < min; m += 10) { var h = (new Date(t0.getTime() + m * 60000).getUTCHours() + 9) % 24; if (h < O.from || h >= O.to) outside += 10; }
    return Math.ceil(outside / 60) * O.perHour;
  }
  function inZone(s) { return new RegExp(F.zone.city).test(String(s || '')); }
  // 区間ごとの定額（{a:'市名の正規表現', b:'…', one:片道, round:往復}）。どちら向きでも同じ
  function findZone(x, y) {
    x = String(x || ''); y = String(y || '');
    for (var i = 0; i < (F.zones || []).length; i++) {
      var z = F.zones[i], A = new RegExp(z.a), B = new RegExp(z.b);
      if ((A.test(x) && B.test(y)) || (B.test(x) && A.test(y))) return z;
    }
    return null;
  }
  function ride(km, at) {
    if (F.kind === 'time') return timeFee(runMin(km)) + offHours(at, runMin(km));
    if (F.kind === 'zone') return F.zone.one;
    if (F.kind === 'zones') return zoneHit.one;
    if (F.kind === 'table') return tableFee(km, F.table);
    return distRide(km);
  }
  function total(km, backKm) {
    var r1 = ride(km, p.datetime), r2 = round ? ride(backKm, p.return_datetime) : 0, n1 = nightExtra(r1, p.datetime), n2 = round ? nightExtra(r2, p.return_datetime) : 0;
    var pk = [leg(F.pick, d.from)], bk = [leg(F.back, d.to, r1)];
    if (round) { pk.push(leg(F.pick, d.backFrom)); bk.push(leg(F.back, d.backTo, r2)); }
    function add(list) { return list.reduce(function(s, x) { return s + x.yen; }, 0); }
    function unk(list) { return list.some(function(x) { return x.unknown; }); }
    var chosen = {ride:r1 + r2, pickup:add(pk), returnFee:add(bk), nightExtra:n1 + n2, wait:0, pickupUnknown:unk(pk), returnUnknown:unk(bk),
      backMissing:bk[0].missing, pickMissing:pk[0].missing, method:round ? '帰りにあらためてお迎え' : '片道'};
    // 往復で、病院などで待っていてもらうほうが安ければそちら（行き1回の迎車＋帰り1回の回送＋待ち時間）
    if (round && (F.wait || F.kind === 'time' || F.kind === 'zone' || F.kind === 'zones' || F.roundTable) && p.return_pickup === p.dropoff && p.return_dropoff === p.pickup) {
      var gap = (parseJst_(p.return_datetime) - parseJst_(p.datetime)) / 60000 - runMin(km);
      if (gap > 0 && gap <= 180) {
        var w = {ride:r1 + r2, pickup:pk[0].yen, returnFee:bk[1].yen, nightExtra:n1 + n2, wait:F.wait ? waitFee(Math.ceil(gap)) : 0, pickupUnknown:pk[0].unknown, returnUnknown:bk[1].unknown,
          backMissing:bk[0].missing, pickMissing:pk[0].missing, method:'待っていてもらう往復（待ち時間' + Math.ceil(gap) + '分）'};
        if (F.kind === 'time') { // 時間制は、行き・待ち・帰りを続けて1回の時間で数える
          var all = runMin(km) + Math.ceil(gap) + runMin(backKm);
          w.ride = timeFee(all) + offHours(p.datetime, all); w.wait = 0; w.method = '行き・待ち・帰りを続けた時間制（' + all + '分）';
        }
        if (F.kind === 'zone') w.ride = F.zone.round; // 往復の定額
        if (F.roundContinuous) w.ride = ride(km + backKm, p.datetime); // 行きと帰りを続けて1回の距離で数える会社
        if (F.kind === 'zones') w.ride = zoneHit.round;
        if (F.pickEachLeg) { w.pickup = pk[0].yen + pk[1].yen; w.pickupUnknown = pk[0].unknown || pk[1].unknown; } // 往復でもお迎え料金が2回分の会社
        if (F.kind === 'table' && F.roundTable) w.ride = tableFee(Math.max(km, backKm), F.roundTable); // 往復の料金表
        if (sum(w) < sum(chosen)) chosen = w;
      }
    }
    if (/税抜|税別/.test(F.tax) && !/税込/.test(F.tax)) ['ride', 'pickup', 'returnFee', 'nightExtra', 'wait'].forEach(function(k) { chosen[k] = Math.ceil(chosen[k] * 1.1); });
    if (F.longDiscount) { // 合計の金額で割引（[[何円から, 割引の割合]]）
      var s0 = sum(chosen), rate = 0;
      F.longDiscount.forEach(function(x) { if (s0 >= x[0]) rate = x[1]; });
      if (rate) { chosen.discount = Math.floor(s0 * rate); chosen.ride -= chosen.discount; }
    }
    var raw = sum(chosen); chosen.amount = Math.ceil(raw / 100) * 100; chosen.rounding = chosen.amount - raw;
    return chosen;
  }
  var local = total(d.km, d.backKm), highway = validKm(d.highKm) && validKm(d.highBackKm) ? total(d.highKm, d.highBackKm) : null;
  var notes = [];
  if (round) notes.push(local.method + 'で計算しています。');
  if (/税抜|税別/.test(F.tax) && !/税込/.test(F.tax)) notes.push('料金表は税抜のため、消費税10%を足しています。');
  else if (!F.tax) notes.push('料金表に税込・税抜の記載がないため、表の金額のまま計算しています。');
  if (F.kind === 'time') notes.push('時間制の料金表です。走る時間は1kmを3分として計算しています。');
  if (F.kind === 'table') notes.push('距離ごとの料金表で計算しています。');
  if (F.kind === 'zones') notes.push('区間ごとの定額（' + zoneHit.label + '）で計算しています。');
  if (local.discount) notes.push('合計の金額による割引 ' + yen_(local.discount) + 'を引いています。');
  if (F.heavy && Number(p.weight) >= F.heavy.kg) notes.push(F.heavy.kg + 'kg以上の子の基本料金で計算しています。');
  if (nightUnknown) notes.push('この時間は割増がありますが、金額が公式サイトに書いていないため含めていません。');
  if (F.kind === 'zone') notes.push(F.zone.city + 'の中の移動の定額で計算しています。');
  if (F.base && F.base[0] > 0 && F.base[1] === 0 && !F.perkmFromStart) notes.push('基本料金に含まれる距離の記載がないため、1km目から距離の料金を足しています。');
  if (local.pickMissing) notes.push('迎車料金は料金表に記載がないため0円で計算しています。');
  if (local.backMissing) notes.push('回送料金は料金表に記載がないため0円で計算しています。');
  if (local.wait) notes.push('待ち時間は、着いてから帰りのお迎えまでの時間で計算しています。');
  var nt = local.nightExtra > 0;
  return {amount:local.amount, text:yen_(local.amount) + (local.pickupUnknown || local.returnUnknown || nightUnknown ? '〜' : ''), local:local, highway:highway,
    incompleteFees:local.pickupUnknown || local.returnUnknown || nightUnknown, taxUnknown:!F.tax,
    night:nt ? '夜間・早朝の割増 ' + yen_(local.nightExtra) + 'を含みます' : F.night ? '指定時刻は夜間・早朝の割増対象外です' : '料金表に夜間・早朝の割増の記載はありません',
    pickupNote:F.pick && F.pick.per != null ? (shop ? '迎車・回送の距離は、お店のある市区町村からの概算です。' : 'お店の場所が分からないため、迎車の距離の分は含めていません。') : '',
    planNote:('公式サイトの料金表から計算した目安です。' + notes.join('')),
    routeNote:d.routeEstimated ? '道のりを取得できなかったため、距離は直線距離からの概算です。' : d.localEstimated ? '一般道の距離は、高速区間から長めに推定しています。' : ''};
}

// 口コミの点数と件数。場所のIDだけは規約上保存してよいので覚えておき、点数は毎回取り寄せる
function selectionReview_(pt) {
  try {
    var v = reviewPlace_(pt.id, 'rating,userRatingCount');
    if (!v || !(v.rating > 0)) return null;
    return {rating:v.rating, count:Number(v.userRatingCount) || 0};
  } catch (e) {
    log_('口コミ：エラー ' + pt.id + ' ' + e);
    return null;
  }
}

// 緊急タブの搬送の会社と夜間の病院（提携先ではない）の口コミ用：id → 場所を探すことばと、見つかった場所の名前に含まれるはずのことば
// tools/emergency.json から gen_areas.py が書き込む（ここは手で直さない）
/*EMG_REVIEWS*/var EMG_REVIEWS = {"E01": {"query": "動物救急車 大田区", "name": "動物救急車"}, "E02": {"query": "ペットドクターカー", "name": "ペットドクターカー"}, "E04": {"query": "ペットタクシー Animals 横浜市港南区", "name": "Animals"}, "E05": {"query": "コインペットタクシー シエロ", "name": "シエロ"}, "E06": {"query": "ペットタクシー パールのしっぽ 千葉市", "name": "パールのしっぽ"}, "E07": {"query": "ペットタクシー COCOタク さいたま南店", "name": ["COCO", "さいたま"]}, "E08": {"query": "ペットタクシー COCOタク 埼玉川越店", "name": ["COCO", "川越"]}, "E09": {"query": "ペットタクシー COCOタク 埼玉春日部", "name": ["COCO", "春日部"]}, "E10": {"query": "ペットレスキュー 夜間救急搬送", "name": "ペットレスキュー"}, "E12": {"query": "ペット専用タクシー aiai 札幌市白石区", "name": "aiai"}, "E13": {"query": "ペットタクシー COCOタク 仙台東店", "name": ["COCO", "仙台東"]}, "E14": {"query": "ペットタクシー COCOタク長岡", "name": ["COCO", "長岡"]}, "E15": {"query": "ZEROペットタクシー 栗東市", "name": "ZERO"}, "E16": {"query": "ペットタクシー Comasuke 茨木", "name": "Comasuke"}, "E17": {"query": "PetTaxi けいわん 堺市", "name": "けいわん"}, "E18": {"query": "ペットタクシー マイファミリー 高槻市", "name": "マイファミリー"}, "E19": {"query": "ペットサポートてんりん 京都市東山区", "name": "てんりん"}, "E20": {"query": "ペットタクシー COCOタク ならまち店", "name": ["COCO", "ならまち"]}, "E21": {"query": "ペッタク ペットタクシー 広島市安芸区", "name": "ペッタク"}, "E22": {"query": "福岡わんわんエクスプレス", "name": "わんわんエクスプレス"}, "E23": {"query": "福岡ペットタクシー HAKAタク", "name": "HAKA"}, "E24": {"query": "ペットタクシー COCOタク 福岡空港店", "name": ["COCO", "福岡空港"]}, "E25": {"query": "東京ペット救急車 なごみ", "name": "ペット救急車"}, "E26": {"query": "ペットタクシー シアンシャ 厚木", "name": ["シアンシャ", "厚木"]}, "E27": {"query": "ペットタクシー シアンシャ 鎌倉", "name": ["シアンシャ", "鎌倉"]}, "E28": {"query": "ペトタクファインド", "name": "ペトタクファインド"}, "H001": {"query": "札幌夜間動物病院 札幌市西区", "name": "札幌夜間動物病院"}, "H002": {"query": "アネス動物病院 札幌円山動物麻酔センター 札幌市中央区", "name": ["アネス動物病院", "札幌円山動物麻酔センター"]}, "H003": {"query": "ペテモどうぶつ医療センター 札幌月寒 札幌市豊平区", "name": ["ペテモどうぶつ医療センター", "札幌月寒"]}, "H004": {"query": "北海道大学動物医療センター 札幌市北区", "name": "北海道大学動物医療センター"}, "H005": {"query": "江別白樺通りアニマルクリニック 江別市", "name": "江別白樺通りアニマルクリニック"}, "H006": {"query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "name": ["仙台獣医師会", "夜間救急動物病院"]}, "H007": {"query": "長町南動物病院 仙台市太白区", "name": "長町南動物病院"}, "H008": {"query": "動物夜間急患センター新潟 新潟市中央区", "name": "動物夜間急患センター新潟"}, "H009": {"query": "ふくしま夜間救急動物病院 郡山市", "name": "ふくしま夜間救急動物病院"}, "H010": {"query": "つくば夜間動物病院 つくば市", "name": "つくば夜間動物病院"}, "H011": {"query": "水戸夜間動物救急センター 水戸市", "name": "水戸夜間動物救急センター"}, "H012": {"query": "つくば動物高度医療センター つくば市", "name": "つくば動物高度医療センター"}, "H013": {"query": "宇都宮夜間どうぶつ病院 宇都宮市", "name": "宇都宮夜間どうぶつ病院"}, "H014": {"query": "宇都宮白沢動物病院 宇都宮市", "name": "宇都宮白沢動物病院"}, "H015": {"query": "しもつけVETセンター 下野市", "name": "しもつけVETセンター"}, "H016": {"query": "小山夜間救急 あかりの森どうぶつ病院 小山市", "name": ["小山夜間救急", "あかりの森どうぶつ病院"]}, "H017": {"query": "群馬夜間救急動物病院 前橋市", "name": "群馬夜間救急動物病院"}, "H018": {"query": "伊勢崎動物医療センター 伊勢崎市", "name": "伊勢崎動物医療センター"}, "H019": {"query": "さいとう動物病院 富岡総合医療センター 富岡市", "name": ["さいとう動物病院", "富岡総合医療センター"]}, "H020": {"query": "夜間救急動物病院 さいたま大宮 SONAC さいたま市大宮区", "name": ["夜間救急動物病院", "さいたま大宮", "SONAC"]}, "H021": {"query": "どうぶつの総合病院 専門医療＆救急センター 川口市", "name": ["どうぶつの総合病院", "専門医療＆救急センター"]}, "H022": {"query": "ミライノ動物病院 草加市", "name": "ミライノ動物病院"}, "H023": {"query": "日本小動物医療センター 所沢市", "name": "日本小動物医療センター"}, "H024": {"query": "久喜夜間救急どうぶつ病院 久喜市", "name": "久喜夜間救急どうぶつ病院"}, "H025": {"query": "熊谷夜間救急動物病院 熊谷市", "name": "熊谷夜間救急動物病院"}, "H026": {"query": "ペテモどうぶつ医療センター幕張新都心 千葉市美浜区", "name": "ペテモどうぶつ医療センター幕張新都心"}, "H027": {"query": "JPB動物医療センター千葉 千葉市緑区", "name": "JPB動物医療センター千葉"}, "H028": {"query": "京葉夜間どうぶつ病院 八千代市", "name": "京葉夜間どうぶつ病院"}, "H029": {"query": "柏流山夜間どうぶつ病院 柏市", "name": "柏流山夜間どうぶつ病院"}, "H030": {"query": "とうかつ夜間どうぶつ病院 柏市", "name": "とうかつ夜間どうぶつ病院"}, "H031": {"query": "千葉どうぶつ総合病院 流山市", "name": "千葉どうぶつ総合病院"}, "H032": {"query": "千葉動物医療センター 袖ケ浦市", "name": "千葉動物医療センター"}, "H033": {"query": "港区動物救急医療センター 芝アニマルクリニック 港区", "name": ["港区動物救急医療センター", "芝アニマルクリニック"]}, "H034": {"query": "ライフメイト動物医療センター文京 文京区", "name": "ライフメイト動物医療センター文京"}, "H035": {"query": "夜間救急動物病院 目黒 目黒区", "name": ["夜間救急動物病院", "目黒"]}, "H036": {"query": "TRVA動物医療センター 世田谷区", "name": "TRVA動物医療センター"}, "H037": {"query": "杉並動物夜間救急医療センター 杉並区", "name": "杉並動物夜間救急医療センター"}, "H038": {"query": "ライフメイト動物救急センター練馬 練馬区", "name": "ライフメイト動物救急センター練馬"}, "H039": {"query": "ペテモどうぶつ医療センター ひがし東京 江東区", "name": ["ペテモ", "ひがし東京"]}, "H040": {"query": "武蔵野動物・救急救命センター 武蔵野市", "name": "武蔵野動物・救急救命センター"}, "H041": {"query": "ライフメイト動物医療センター府中 府中市", "name": "ライフメイト動物医療センター府中"}, "H042": {"query": "サムズアップアニマルケアセンター 立川市", "name": "サムズアップアニマルケアセンター"}, "H043": {"query": "ライフメイト動物救命救急センター八王子 八王子市", "name": "ライフメイト動物救命救急センター八王子"}, "H044": {"query": "DVMsどうぶつ医療センター横浜 横浜市神奈川区", "name": "DVMsどうぶつ医療センター横浜"}, "H045": {"query": "横浜動物救急診療センター VECCS横浜 横浜市南区", "name": ["横浜動物救急診療センター", "VECCS横浜"]}, "H046": {"query": "アニマルメディカルセンター 川崎市中原区", "name": "アニマルメディカルセンター"}, "H047": {"query": "川崎市獣医師会 夜間動物病院 川崎市高津区", "name": ["川崎市獣医師会", "夜間動物病院"]}, "H048": {"query": "ペテモどうぶつ医療センター相模原 相模原市南区", "name": "ペテモどうぶつ医療センター相模原"}, "H049": {"query": "藤沢夜間救急動物病院 藤沢市", "name": "藤沢夜間救急動物病院"}, "H050": {"query": "横須賀夜間救急動物病院 横須賀市", "name": "横須賀夜間救急動物病院"}, "H051": {"query": "夜間救急動物医療センター NEAMeC 平塚市", "name": ["夜間救急動物医療センター", "NEAMeC"]}, "H053": {"query": "北陸よつや動物医療センター 高岡市", "name": "北陸よつや動物医療センター"}, "H054": {"query": "チェルシーアニマルクリニック 富山市", "name": "チェルシーアニマルクリニック"}, "H055": {"query": "かなざわ夜間救急動物病院 金沢市", "name": "かなざわ夜間救急動物病院"}, "H056": {"query": "京都夜間動物救急センター 京都市南区", "name": "京都夜間動物救急センター"}, "H057": {"query": "ノア動物病院 城東センター病院 甲府市", "name": ["ノア動物病院", "城東センター病院"]}, "H058": {"query": "きらら動物病院 千塚分院 甲府市", "name": ["きらら動物病院", "千塚分院"]}, "H059": {"query": "長野夜間どうぶつ病院 千曲市", "name": "長野夜間どうぶつ病院"}, "H060": {"query": "佐久・軽井沢夜間どうぶつ病院 佐久市", "name": "佐久・軽井沢夜間どうぶつ病院"}, "H061": {"query": "こやま動物病院 長野市", "name": "こやま動物病院"}, "H062": {"query": "岐阜県獣医師会 夜間救急動物病院 岐阜市", "name": ["岐阜県獣医師会", "夜間救急動物病院"]}, "H063": {"query": "静岡市夜間救急動物病院 静岡市駿河区", "name": "静岡市夜間救急動物病院"}, "H064": {"query": "浜松夜間救急動物病院 浜松市中央区", "name": "浜松夜間救急動物病院"}, "H065": {"query": "VCJ動物医療センター駿河病院 御殿場市", "name": "VCJ動物医療センター駿河病院"}, "H066": {"query": "名古屋夜間動物救急センター 名古屋市中区", "name": "名古屋夜間動物救急センター"}, "H067": {"query": "名古屋西動物夜間救急医療センター 名古屋市西区", "name": "名古屋西動物夜間救急医療センター"}, "H068": {"query": "もりやま犬と猫の病院 名古屋市守山区", "name": "もりやま犬と猫の病院"}, "H069": {"query": "こざわ犬猫病院 名古屋市千種区", "name": "こざわ犬猫病院"}, "H070": {"query": "あいち犬猫医療センター 安城市", "name": "あいち犬猫医療センター"}, "H071": {"query": "ハート動物クリニック 犬猫医療センター 豊橋市", "name": ["ハート動物クリニック", "犬猫医療センター"]}, "H072": {"query": "大阪どうぶつ夜間急病センター 大阪市東成区", "name": "大阪どうぶつ夜間急病センター"}, "H073": {"query": "長浜どうぶつ病院 長浜市", "name": "長浜どうぶつ病院"}, "H074": {"query": "大阪・北摂夜間救急どうぶつ病院 箕面市", "name": "大阪・北摂夜間救急どうぶつ病院"}, "H075": {"query": "京都夜間どうぶつ診療所 久世郡久御山町", "name": "京都夜間どうぶつ診療所"}, "H076": {"query": "右京動物病院 京都市右京区", "name": "右京動物病院"}, "H077": {"query": "大阪夜間ペットクリニック 大阪市東成区", "name": "大阪夜間ペットクリニック"}, "H078": {"query": "堺動物夜間救急クリニック 堺市中区", "name": "堺動物夜間救急クリニック"}, "H079": {"query": "大阪守口夜間どうぶつ診療所 守口市", "name": "大阪守口夜間どうぶつ診療所"}, "H080": {"query": "りんくう動物救急医療協会 泉佐野市", "name": "りんくう動物救急医療協会"}, "H082": {"query": "神戸夜間動物救急センター 神戸市西区", "name": "神戸夜間動物救急センター"}, "H083": {"query": "兵庫ペット医療センター 尼崎本院 尼崎市", "name": ["兵庫ペット医療センター", "尼崎本院"]}, "H084": {"query": "大蔵海岸ペットクリニック 明石市", "name": "大蔵海岸ペットクリニック"}, "H085": {"query": "エルザ動物医療センター 姫路市", "name": "エルザ動物医療センター"}, "H086": {"query": "奈良動物医療センター 奈良市", "name": "奈良動物医療センター"}, "H088": {"query": "岡山夜間どうぶつ救急病院 岡山市南区", "name": "岡山夜間どうぶつ救急病院"}, "H089": {"query": "広島夜間救急動物病院 広島市東区", "name": "広島夜間救急動物病院"}, "H090": {"query": "倉敷夜間ペットクリニック 倉敷市", "name": "倉敷夜間ペットクリニック"}, "H091": {"query": "konomi動物病院 広島市東区", "name": "konomi動物病院"}, "H092": {"query": "竹田動物病院 岩国市", "name": "竹田動物病院"}, "H093": {"query": "北九州夜間救急動物病院 北九州市八幡東区", "name": "北九州夜間救急動物病院"}, "H094": {"query": "おおしま動物病院 板野郡藍住町", "name": "おおしま動物病院"}, "H098": {"query": "福岡夜間救急動物病院 福岡市博多区", "name": "福岡夜間救急動物病院"}, "H099": {"query": "一二三ペットクリニック 熊本市東区", "name": "一二三ペットクリニック"}, "H100": {"query": "きらてとあにまるほすぴたる 熊本市南区", "name": "きらてとあにまるほすぴたる"}, "H102": {"query": "大塚どうぶつ病院 宮崎市", "name": "大塚どうぶつ病院"}, "H103": {"query": "鹿児島大学 共同獣医学部附属動物病院 鹿児島市", "name": ["鹿児島大学", "共同獣医学部附属動物病院"]}, "H105": {"query": "沖縄夜間動物病院 那覇市", "name": "沖縄夜間動物病院"}, "H106": {"query": "動物病院なは 夜間救急医療センター 島尻郡南風原町", "name": ["動物病院なは", "夜間救急医療センター"]}};/*/EMG_REVIEWS*/

// 口コミの場所をどう探すか：提携先（SELECTION_FARES）・緊急タブ（EMG_REVIEWS）・候補カードに表示だけする会社（DISPLAY_COMPANIES）
// words があるときは、違う場所を拾わないよう、見つかった場所の名前にそのことばが全部入っているかを確かめる
function reviewTarget_(id) {
  var key = SELECTION_FARES && Object.keys(SELECTION_FARES).filter(function(k) { return SELECTION_FARES[k].partner_id === id; })[0];
  if (key && SELECTION_FARES[key].review_query) return {query:SELECTION_FARES[key].review_query, words:null, idKey:'PLACE_ID_' + id + '_' + SELECTION_FARES[key].review_query};
  var emg = EMG_REVIEWS[id];
  if (emg && emg.query) return {query:emg.query, words:[].concat(emg.name), idKey:'PLACE_ID_' + id + '_' + emg.query, emg:true};
  var dc = DISPLAY_COMPANIES.filter(function(c) { return c.id === id; })[0];
  // 社内用の事業者一覧（dashPlace_）と同じ場所IDを使う
  // 地図の名前は「COCOタク 小平店」のように登録名と少し違うことが多いので、ブランド名＋支店名の中心のことばで照らし合わせる（loose）。
  // 前の厳しい照らし合わせで「見つからない」と覚えた会社も探し直すよう、覚える場所を D2 に変えた（2026-10-31）
  if (dc && dc.review_q && dc.review_name) return {query:dc.review_q, query2:dc.review_name + ' ペットタクシー', words:String(dc.review_name).split(/[\s、,]+/).filter(String), loose:true, idKey:'PLACE_ID_D2_' + id + '_' + dc.review_q};
  return null;
}
var PLACE_PREF_RE = /^(北海道|青森|岩手|宮城|秋田|山形|福島|茨城|栃木|群馬|埼玉|千葉|東京|神奈川|新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|滋賀|京都|大阪|兵庫|奈良|和歌山|鳥取|島根|岡山|広島|山口|徳島|香川|愛媛|高知|福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|沖縄)[都道府県]?/;
function placeNorm_(x) { return String(x).normalize('NFKC').replace(/[\s　（）()「」『』・\-ー－]/g, '').toLowerCase(); }
// loose のときの照らし合わせのことば：brand＝最初のことば（後ろの都道府県名は外す。例 PETTA東京→petta）、
// branch＝残り（前の都道府県名と後ろの「店・支店・営業所」を外し、「・」で分ける。例 東京小平店→小平、大田・田園調布店→大田／田園調布）
function placeKeys_(words) {
  var brand = String(words[0] || '').replace(/(北海道|東京|神奈川|埼玉|千葉|大阪|京都|兵庫|愛知|福岡)[都道府県]?$/, '') || String(words[0] || '');
  var branch = words.slice(1).join(' ').replace(PLACE_PREF_RE, '').replace(/(支店|営業所|店)$/, '');
  return {brand:placeNorm_(brand), branch:branch ? branch.split(/[・\s]+/).map(placeNorm_).filter(function(b) { return b.length >= 2; }) : []};
}
function placeNameOk_(t, place) {
  if (!t.words) return true;
  var name = ((place || {}).displayName || {}).text || '';
  if (t.loose) {
    var k = placeKeys_(t.words), n = placeNorm_(name);
    if (!k.brand || n.indexOf(k.brand) < 0) return false;
    return !k.branch.length || k.branch.some(function(b) { return n.indexOf(b) >= 0; }); // チェーンは支店名も合うときだけ（ほかの店と取り違えない）
  }
  // 名前のことばが全部入っているか（支店がある会社は支店名も。全角・半角の違いは気にしない）
  var norm = function(x) { return String(x).normalize('NFKC').replace(/\s/g, '').toLowerCase(); };
  var nn = norm(name);
  return t.words.length > 0 && t.words.every(function(w) { return nn.indexOf(norm(w)) >= 0; });
}
function placeSearchRequest_(t, apiKey, second) { // IDだけの検索は無料（名前も見るときは場所1件ごとに一度だけ）
  return {url:'https://places.googleapis.com/v1/places:searchText', method:'post', contentType:'application/json', muteHttpExceptions:true,
    headers:{'X-Goog-Api-Key':apiKey,'X-Goog-FieldMask':t.words ? 'places.id,places.displayName' : 'places.id'},
    payload:JSON.stringify({textQuery:second ? t.query2 : t.query,languageCode:'ja',regionCode:'JP'})};
}
// 検索の結果から場所のIDを決めて覚える（規約上、場所のIDだけは保存してよい）。見つからなければ '-' を覚える（提携先は覚えずに次も探す）
function placeFromSearch_(id, t, text, props, keepTrying) {
  var found = {};
  try { found = JSON.parse(text) || {}; } catch (e) {}
  var hit = (found.places || []).filter(function(x) { return placeNameOk_(t, x); })[0];
  if (!hit || !hit.id) {
    if (keepTrying) return null; // もうひとつの探し方を試す
    log_('口コミ：場所が見つからない ' + id + ' ' + t.query + ' 候補：' + (found.places || []).slice(0, 5).map(function(x) { return (x.displayName || {}).text || ''; }).join('／'));
    if (t.words) props.setProperty(t.idKey, '-');
    return null;
  }
  props.setProperty(t.idKey, hit.id);
  return hit.id;
}
function placeDetailsRequest_(placeId, apiKey, fields) {
  return {url:'https://places.googleapis.com/v1/places/' + encodeURIComponent(placeId) + '?languageCode=ja', muteHttpExceptions:true,
    headers:{'X-Goog-Api-Key':apiKey,'X-Goog-FieldMask':fields}};
}

// 口コミの場所の情報を取り寄せる（fields は取り寄せる項目）。月の回数の上限は点数と口コミ本文で共通
function reviewPlace_(partnerId, fields) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY');
  var t = reviewTarget_(partnerId);
  if (!apiKey || !t) return null;
  var placeId = props.getProperty(t.idKey);
  if (placeId === '-') return null; // 前に探して見つからなかった
  if (!placeId) {
    var q = placeSearchRequest_(t, apiKey), url = q.url; delete q.url;
    placeId = placeFromSearch_(partnerId, t, UrlFetchApp.fetch(url, q).getContentText(), props, !!t.query2);
    if (!placeId && t.query2) {
      var q2 = placeSearchRequest_(t, apiKey, true); delete q2.url;
      placeId = placeFromSearch_(partnerId, t, UrlFetchApp.fetch(url, q2).getContentText(), props);
    }
    if (!placeId) return null;
  }
  var ym = Utilities.formatDate(new Date(), TZ, 'yyyyMM');
  var month = 'REVIEW_COUNT_' + ym, used = Number(props.getProperty(month)) || 0;
  if (used >= CONFIG.REVIEW_MONTHLY_LIMIT) return null;
  if (t.emg) {
    var emgMonth = 'REVIEW_EMG_COUNT_' + ym, emgUsed = Number(props.getProperty(emgMonth)) || 0;
    if (emgUsed >= CONFIG.REVIEW_EMG_MONTHLY_LIMIT) return null;
    props.setProperty(emgMonth, String(emgUsed + 1));
  }
  props.setProperty(month, String(used + 1));
  var d = placeDetailsRequest_(placeId, apiKey, fields), durl = d.url; delete d.url;
  var res = UrlFetchApp.fetch(durl, d);
  if (res.getResponseCode() !== 200) { log_('口コミ：取り寄せ失敗 ' + partnerId + ' ' + res.getResponseCode()); return null; }
  return JSON.parse(res.getContentText());
}

// 候補カードの星と件数をまとめて取り寄せる（Nori 2026-10-31「口コミがあるものはちゃんと出して」）。ids はカンマ区切り、1回に40社まで。
// 画面に出た会社だけ、同時に取り寄せる（UrlFetchApp.fetchAll）。点数は保存せず毎回取り寄せる。月の上限に近いときは、来た順に残りの回数までだけ
function selectionScores_(ids) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY'), out = {};
  if (!apiKey) return {ok:true, scores:out};
  var list = String(ids || '').split(',').filter(function(id, i, a) { return id && a.indexOf(id) === i && !EMG_REVIEWS[id]; }).slice(0, 40)
    .map(function(id) { return {id:id, t:reviewTarget_(id)}; }).filter(function(x) { return x.t; });
  list.forEach(function(x) { x.place = props.getProperty(x.t.idKey); });
  var need = list.filter(function(x) { return !x.place; });
  if (need.length) {
    var res = UrlFetchApp.fetchAll(need.map(function(x) { return placeSearchRequest_(x.t, apiKey); }));
    need.forEach(function(x, i) { x.place = placeFromSearch_(x.id, x.t, res[i].getContentText(), props, !!x.t.query2) || null; });
    var again = need.filter(function(x) { return !x.place && x.t.query2; }); // 見つからなければ「名前＋ペットタクシー」でもう一度
    if (again.length) {
      var res2 = UrlFetchApp.fetchAll(again.map(function(x) { return placeSearchRequest_(x.t, apiKey, true); }));
      again.forEach(function(x, i) { x.place = placeFromSearch_(x.id, x.t, res2[i].getContentText(), props) || '-'; });
    }
    need.forEach(function(x) { if (!x.place) x.place = '-'; });
  }
  list = list.filter(function(x) { return x.place && x.place !== '-'; });
  var ym = Utilities.formatDate(new Date(), TZ, 'yyyyMM'), month = 'REVIEW_COUNT_' + ym, used = Number(props.getProperty(month)) || 0;
  list = list.slice(0, Math.max(0, CONFIG.REVIEW_MONTHLY_LIMIT - used));
  if (!list.length) return {ok:true, scores:out};
  props.setProperty(month, String(used + list.length));
  var got = UrlFetchApp.fetchAll(list.map(function(x) { return placeDetailsRequest_(x.place, apiKey, 'rating,userRatingCount'); }));
  list.forEach(function(x, i) {
    try {
      if (got[i].getResponseCode() !== 200) { log_('口コミ：取り寄せ失敗 ' + x.id + ' ' + got[i].getResponseCode()); return; }
      var v = JSON.parse(got[i].getContentText());
      if (v.rating > 0) out[x.id] = {rating:v.rating, count:Number(v.userRatingCount) || 0};
    } catch (e) { log_('口コミ：エラー ' + x.id + ' ' + e); }
  });
  return {ok:true, scores:out};
}

// 候補カードの「口コミを見る」：口コミ本文（地図サービスが関連度の高い順に返す最大5件）をサイトの中で見せる。
// 規約により、書いた人（名前・アイコン・プロフィールへのリンク）と、口コミそれぞれの元のページへのリンクを一緒に返す。保存はしない
function selectionReviews_(partnerId) {
  if (!reviewTarget_(partnerId)) return {ok:false,error:'unknown'};
  try {
    var v = reviewPlace_(partnerId, 'rating,userRatingCount,reviews');
    if (!v) return {ok:false,error:'reviews_unavailable'};
    return {ok:true, rating:v.rating || 0, count:Number(v.userRatingCount) || 0, reviews:(v.reviews || []).slice(0, 5).map(function(x) {
      var a = x.authorAttribution || {};
      return {rating:x.rating || 0, when:x.relativePublishTimeDescription || '', text:((x.text || x.originalText || {}).text || '').slice(0, 2000),
        author:a.displayName || '', authorUrl:a.uri || '', photo:a.photoUri || '', url:x.googleMapsUri || ''};
    })};
  } catch (e) {
    log_('口コミ本文：エラー ' + partnerId + ' ' + e);
    return {ok:false,error:'reviews_unavailable'};
  }
}

// 緊急タブの搬送の会社・病院の星と件数（ids はカンマ区切り。画面に出てきたところだけ、1回に12件まで）。点数は保存せず毎回取り寄せる
function emgScores_(ids) {
  var out = {};
  ids.split(',').filter(function(id, i, a) { return EMG_REVIEWS[id] && a.indexOf(id) === i; }).slice(0, 12).forEach(function(id) {
    var v = selectionReview_({id:id});
    if (v) out[id] = v;
  });
  return {ok:true, scores:out};
}

function validateSelection_(p) {
  var error = selectionValid_(p);
  if (error) return {ok:false,error:error};
  var expires = Number(p.quote_expires);
  if (!(expires > Date.now() && expires <= Date.now()+15*60000)) return {ok:false,error:'selection_expired'};
  if (CONFIG.SHOW_ALL_CANDIDATES || isDisplayOnly_(p.partner_id)) return {ok:false,error:'selection_unavailable'}; // 全社準備中のあいだ・表示だけの会社には依頼できない
  var pt = selectionCandidates_(selectionRide_(p)).filter(function(x) { return x.id === p.partner_id && !isDisplayOnly_(x.id); })[0];
  if (!pt) return {ok:false,error:'selection_unavailable'};
  var price = selectionPrice_(pt,p);
  if (!price || p.quote_token !== quoteSignature_(p,pt.id,expires,price)) return {ok:false,error:'selection_changed'};
  return {ok:true,partner:pt,price:price};
}

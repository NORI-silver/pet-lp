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
  WEB_APP_URL: 'https://script.google.com/macros/s/AKfycbyxsd8L8g_5Nt3HnApx2ZQnXFyPBsNfuHSvBlJKRVDtAIVr0EnqB-0raxwMPNOVl_Jg/exec',

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
  // 提携先シートの車の情報が空欄のときは、いちばん小さい車（軽バン）とみなす
  DEFAULT_CAR: { riders: 2, pets: 2, big: true, luggage: false },

  // LINE公式アカウント（作ったら入れる。空ならメールだけで動きます）
  LINE_CHANNEL_ACCESS_TOKEN: '',
  LINE_ADD_URL: '', // 友だち追加URL（https://lin.ee/〇〇）

  // 会社カードの口コミの点数（地図サービスから正式に取り寄せる。規約で書き写し・保存はできない）
  // キーはここに書かず、スクリプトのプロパティ PLACES_API_KEY に入れる。空なら点数は出さず「口コミを見る」リンクだけ
  REVIEW_MONTHLY_LIMIT: 900, // 1か月に取り寄せる回数の上限（無料の範囲 1,000回に収める。超えたら月末までリンクだけ）
  REVIEW_EMG_MONTHLY_LIMIT: 300, // そのうち緊急タブの搬送の会社に使ってよい回数（予約の候補カードのぶんを残すため）
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
  'お客さまLINE', '終了日時', 'ペット数', 'ペット詳細', '日付のみ', '経由地', 'ペットJSON', '概算km', '概算料金', '荷物', '高速利用時の料金', '帰りの日時', '帰りのお迎え', '帰りの行き先', '待ち時間（分）', '概算料金の表示', '帰りのやり方', '指定した提携先ID', '指定した提携先'
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

  var selection;
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var r;
  // 二重送信よけ：LPは入力が同じなら同じ req_key を送る。6時間以内の同じ key には同じ受付番号を返す
  var key = String(p.req_key || '').slice(0, 200), cache = key ? CacheService.getScriptCache() : null;
  try {
    if (cache) {
      var dup = cache.get('req_' + key);
      if (dup) return { ok: true, id: dup };
    }
    selection = validateSelection_(p);
    if (!selection.ok) return selection;
    var sh = sheet_(SHEET_REQ);
    var id = newId_(sh);
    r = {
      '受付番号': id, '受付日時': new Date(), '状態': ST.OPEN, '都府県': pref,
      'お迎えの場所': clip_(p.pickup), '行き先': clip_(p.dropoff), '希望日時': when, '片道・往復': clip_(p.trip),
      '種類': clip_(p.species), '犬種・猫種': clip_(p.breed), '体重kg': Number(p.weight) || '', '年齢': clip_(p.age),
      '性別': clip_(p.sex), 'キャリー': clip_(p.cage), '介助': clip_(p.care), '同乗人数': clip_(p.riders),
      'お名前': clip_(p.name), '電話番号': "'" + clip_(p.tel), 'メール': clip_(p.email).trim(), '連絡方法': clip_(p.contact),
      'メモ': clip_(p.notes, 1000), '通知段階': 0, '通知した提携先': '',
      'ペット数': Number(p.pet_count) || 1, 'ペット詳細': clip_(p.pets, 1000), '日付のみ': p.date ? '○' : '',
      '経由地': clip_(p.via), 'ペットJSON': clip_(p.pets_json, 5000),
      '概算km': Number(p.est_km) || '', '概算料金': selection.price.amount || '', '荷物': clip_(p.luggage),
      '帰りの日時': parseJst_(p.return_datetime) || '', '帰りのお迎え': clip_(p.return_pickup), '帰りの行き先': clip_(p.return_dropoff),
      '待ち時間（分）': clip_(p.wait_time, 20),
      '概算料金の表示': selection.price.text, '指定した提携先ID': selection.partner.id, '指定した提携先': selection.partner.name
    };
    var head = ensureReqHeaders_(sh);
    sh.appendRow(head.map(function (h) { return r[h] === undefined ? '' : r[h]; }));
    // 数字の列が「日付」の書式になっていると、読み出したときに日付になってしまうので、書式を数字に固定する
    var last = sh.getLastRow();
    [['体重kg', '0.#'], ['ペット数', '0'], ['概算km', '0.0'], ['概算料金', '#,##0'], ['待ち時間（分）', '@'], ['概算料金の表示', '@']].forEach(function (f) {
      var c = head.indexOf(f[0]);
      if (c >= 0) sh.getRange(last, c + 1).setNumberFormat(f[1]);
    });
    SpreadsheetApp.flush();
    if (cache) cache.put('req_' + key, id, 21600);
  } finally {
    lock.releaseLock();
  }
  r['電話番号'] = String(r['電話番号']).replace(/^'/, '');

  sendReceipt_(r);
  var sent = sendWave_(r['受付番号'], 1);
  notifyAdmin_((isTest_(r) ? '【テスト】' : '') + '新しいご依頼 ' + r['受付番号'] + '（' + pref + '・' + whenText_(r) + '）',
    rideText_(r) + '\n\nお名前：' + r['お名前'] + '\n電話：' + r['電話番号'] + '\nメール：' + r['メール'] + '\n連絡方法：' + r['連絡方法'] +
    '\n\nお知らせした提携先：' + (sent || 'なし（このエリアの提携先がいません）') + '\n\n▼ 手配ページ（LINEで送る・決定の入力）\n' + adminUrl_(r['受付番号']));
  return { ok: true, id: r['受付番号'] };
}

/* ───────── 提携先へのお知らせ ───────── */

// stage 1: そのエリアの提携先 / stage 2: 近くのエリア＋全国対応
// 戻り値：お知らせした提携先名（カンマ区切り）
function sendWave_(id, stage) {
  var row = findReq_(id);
  if (!row || row.data['状態'] !== ST.OPEN) return '';
  var r = row.data;
  var already = String(r['通知した提携先'] || '').split(',').filter(String);
  var selected = r['指定した提携先ID'];
  if (selected && stage !== 1) return '';
  var pool = selected ? selectionCandidates_(r).filter(function(pt) { return pt.id === selected; }) : pickPartners_(r, stage);
  var targets = pool.filter(function (pt) { return already.indexOf(pt.id) < 0; });
  // 第1段で誰もいなければ、すぐ第2段の相手にも送る
  if (!selected && stage === 1 && targets.length === 0) {
    stage = 2;
    targets = pickPartners_(r, 2).filter(function (pt) { return already.indexOf(pt.id) < 0; });
  }
  var manual = [];
  targets = targets.filter(function (pt) {
    var how = deliver_(pt, '【新しいご依頼】' + r['都府県'] + '・' + whenText_(r), requestText_(r, pt), r);
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
    'お受けいただける場合は、下のリンクからお迎え時刻と確定料金（税込）をご入力ください（数字を入れるだけです。先着1社）。\n' + acceptUrl_(r['受付番号'], pt.id) +
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
// ・借りたい → 「ケージ貸し出し」が○の会社だけ（空欄は用意なしとみなす）
// ・なし     → 「ケージ必須」が○の会社は対象外。「ペットだけ」の会社は、飼い主さんが乗らないときだけ対象外
// ・どれでも → 会社のやり方に合わせられるので、しぼりこまない
function fitsCage_(pt, r) {
  var c = String(r['キャリー'] || '');
  var rent = /借り|持っていない/.test(c), none = /なし/.test(c);
  if (rent && pt.cageLend !== true) return false;
  if (none) {
    var must = pt.cageMust;
    if (must !== '' && !/^(×|✕|x|X|いいえ|不要|NG)$/.test(must)) {
      if (!/ペットだけ/.test(must)) return false;
      if (needs_(r).riders === 0) return false;
    }
  }
  return true;
}

// 車に乗るか。空欄の項目は軽バン（CONFIG.DEFAULT_CAR）とみなす
// 間に合うか：メールを読めるのは営業時間だけ。読める時刻からお迎えまで「何時間前まで」以上あること
function inTime_(pt, r, now) {
  var lead = pt.lead === null || pt.lead === undefined ? CONFIG.DEFAULT_LEAD_HOURS : pt.lead;
  var at = parseJst_(defaultAt_(r));
  if (!at) return true;
  var seen = nextOpen_(now ? new Date(now) : new Date(), pt.hours || CONFIG.DEFAULT_PARTNER_HOURS);
  return at.getTime() - seen.getTime() >= lead * 3600000;
}

// 「8-18」「8:00〜18:00」→ [8, 18]
function hoursOf_(v) {
  var m = toHalf_(v).match(/(\d{1,2})(?::\d{2})?\s*[-~〜～]\s*(\d{1,2})/);
  return m ? [Number(m[1]), Number(m[2])] : [0, 24];
}

// その時刻が営業時間ならそのまま、外なら次に開く時刻（日本時間）
function nextOpen_(d, hours) {
  var h = hoursOf_(hours), j = new Date(d.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
  if (hr >= h[0] && hr < h[1]) return d;
  var day = Date.UTC(j.getUTCFullYear(), j.getUTCMonth(), j.getUTCDate()) + (hr >= h[1] ? 86400000 : 0);
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

function fitsCar_(pt, r) {
  var n = needs_(r), d = CONFIG.DEFAULT_CAR;
  var pick = function (v, dv) { return v === null ? dv : v; };
  if (n.riders > pick(pt.riders, d.riders)) return false;
  if (n.pets > pick(pt.pets, d.pets)) return false;
  if (n.big && !pick(pt.big, d.big)) return false;
  if (n.luggage && !pick(pt.luggage, d.luggage)) return false;
  return true;
}

// 依頼の条件を会社ごとに1つずつ確かめる。ng＝受けられないと分かっている（候補に出さない）、
// ask＝会社の答えがまだ分からない、または組み合わせ次第の条件（候補には出し、引き受けるときに会社がチェックして確かめる。Nori 2026-10-31）
function petsOf_(r) {
  var a;
  try { a = JSON.parse(r['ペットJSON'] || '[]'); } catch (e) { a = []; }
  if (!Array.isArray(a) || !a.length) a = [{ weight: r['体重kg'], care: r['介助'] }];
  return a.map(function (p) { return { kg: Number(p.weight) || 0, care: p.care || '', vac: p.vaccine === '済', need: (p.care_need || []).concat(p.care_note ? [p.care_note] : []) }; });
}
function checks_(pt, r) {
  var ng = [], ask = [], n = needs_(r), pets = petsOf_(r), d = CONFIG.DEFAULT_CAR;
  var bigs = pets.filter(function (p) { return p.kg >= CONFIG.LARGE_DOG_KG; }), maxKg = Math.max.apply(null, pets.map(function (p) { return p.kg; }));
  // 時間：お迎え（往復なら帰りも）が送迎できる時間に入っているか
  [r['希望日時'], r['帰りの日時']].forEach(function (t, i) {
    var at = t ? new Date(t) : null;
    if (!at || !isFinite(at.getTime()) || (i === 0 && r['日付のみ'])) return;
    var j = new Date(at.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
    var label = (i ? '帰りの' : '') + 'お迎え ' + j.getUTCHours() + ':' + ('0' + j.getUTCMinutes()).slice(-2);
    if (pt.rideHours) { var h = hoursOf_(pt.rideHours); if (hr < h[0] || hr >= h[1]) ng.push(label + '（送迎できる時間の外）'); }
    else { var h2 = hoursOf_(pt.hours || CONFIG.DEFAULT_PARTNER_HOURS); if (hr < h2[0] || hr >= h2[1]) ask.push(label + 'に送迎できる'); }
  });
  // 人数・頭数・荷物
  if (pt.riders !== null && n.riders > pt.riders) ng.push('大人' + n.riders + '人');
  else if (pt.riders === null && n.riders >= 2) ask.push('大人' + n.riders + '人が一緒に乗れる'); // 定員が分からない会社は2人から確かめる
  if (pt.pets !== null && n.pets > pt.pets) ng.push(n.pets + '匹');
  else if (pt.pets === null && n.pets >= 2) ask.push(n.pets + '匹が一緒に乗れる');
  if (n.luggage && pt.luggage === false) ng.push('荷物が多い');
  else if (n.luggage && pt.luggage === null) ask.push('多めの荷物（スーツケース・大きなケージなど）が載る');
  // 大きさ
  if (bigs.length) {
    if (pt.big === false) ng.push('大型犬');
    else if (pt.maxKg !== null && maxKg > pt.maxKg) ng.push(maxKg + 'kgの子（' + pt.maxKg + 'kgまで）');
    else if (pt.maxKg === null) ask.push(maxKg + 'kgの子が乗れる');
    if (pt.maxBig !== null && bigs.length > pt.maxBig) ng.push('大型犬' + bigs.length + '頭');
    else if (pt.maxBig === null && bigs.length >= 2) ask.push('大型犬' + bigs.length + '頭が一緒に乗れる');
    if (n.riders + bigs.length >= 3) ask.push('大型犬' + bigs.length + '頭と大人' + n.riders + '人が一緒に乗れる');
  }
  // ケージ
  if (!fitsCage_(pt, r)) ng.push('ケージの条件');
  else {
    var c = String(r['キャリー'] || '');
    if (/借り|持っていない/.test(c)) {
      if (pt.lendKg !== null && maxKg > pt.lendKg) ng.push(maxKg + 'kgの子が入るケージの貸し出し');
      else if (pt.lendKg === null && maxKg >= 10) ask.push(maxKg + 'kgの子が入るケージを貸し出せる'); // 小さい子のケージはどこでも用意できる
    }
    if (/なし/.test(c) && pt.cageMust === '') ask.push('ケージなしで乗れる');
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
  var def = defaultAt_(r);
  var html = '<p>' + esc_(pt.name) + ' 様</p>' +
    '<div class="box"><b>お客さまのお名前・電話番号・メールは、下の「引き受ける」を押すとすぐにこの画面に表示されます。</b>同じ内容をメールでもお送りします。先着1社です。</div>' +
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
    '<button type="submit">この内容で引き受ける</button></form>' +
    '';
  return page_('ご依頼を引き受けますか？', html);
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
    if (row.data['指定した提携先ID'] && row.data['指定した提携先ID'] !== pt.id) return {ok:false,msg:'お客さまが選んだ会社と異なるため引き受けできません。'};
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
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】お迎えが決まりました（受付番号 ' + id + '）',
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
    if (!r['指定した提携先ID'] && Number(r['通知段階']) < 2) {
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
    if (age >= CONFIG.GIVE_UP_MIN * k || until < 0) {
      giveUp_(r['受付番号']);
    } else if (!r['指定した提携先ID'] && age >= CONFIG.WAVE2_MIN * k && Number(r['通知段階']) < 2) {
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
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】申し訳ありません、空いている車が見つかりませんでした（受付番号 ' + id + '）',
    r['お名前'] + ' 様\n\nご依頼ありがとうございました。\n' + whenText_(r) + ' のお迎えについて、' + (r['指定した提携先'] ? r['指定した提携先'] + 'に確認しましたが、あいにくお引き受けできませんでした。' : 'エリアのペットタクシーにお声がけしましたが、あいにく空いている車が見つかりませんでした。') + '\nお力になれず、申し訳ありません。\n\n' +
    '時間を少しずらすと見つかることがあります。下のリンクから開くと、前回の内容が入った状態になるので、日時だけ変えてもう一度お送りいただけます。\n' + retryUrl_(id));
  notifyAdmin_('見つからず ' + id, 'お客さまにお詫びを送りました。\n\n' + rideText_(r) + '\n\nお名前：' + r['お名前'] + '\n電話：' + r['電話番号']);
}

/* ───────── お客さまへのメール ───────── */

function sendReceipt_(r) {
  var lineNote = '';
  if (CONFIG.LINE_CHANNEL_ACCESS_TOKEN && CONFIG.LINE_ADD_URL) {
    lineNote = '\n\n▼ LINEでもお知らせを受け取れます\n友だち追加して、受付番号「' + r['受付番号'] + '」を送ってください。\n' + CONFIG.LINE_ADD_URL;
  }
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】受け付けました（受付番号 ' + r['受付番号'] + '）',
    r['お名前'] + ' 様\n\nご依頼ありがとうございます。受け付けました。\n' + (r['指定した提携先'] ? '選んだ会社「' + r['指定した提携先'] + '」に空き状況を確認しています。ほかの会社には依頼しません。' : 'いま、空いているペットタクシーを探しています。') + '引き受けが決まりしだい、お迎えの時間と確定料金をお送りします。\n\n' +
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

/*SELECTION_FARES*/var SELECTION_FARES = {"petexpress": {"名前": "ペットエクスプレス（世田谷）", "出典": "https://pettaxi.tokyo/ 2026-10-27", "base_km": 5, "base": 2200, "tiers": [[100, 220], [200, 165], [null, 110]], "pick": 330, "back": 330, "night": 1.2, "round_flat": null, "note": "東京・世田谷の会社は、乗車料金が5kmまで2,200円、その先は1kmごとに220円（101km〜は165円、201km〜は110円）。お迎え料金と帰りの回送料金がそれぞれ3kmまで330円かかり、お店から遠いと増えます。夕方18時〜朝8時は乗車料金が2割増し、往復は乗車料金が2倍です。病院での待ち時間は10分まで無料、30分まで660円、その後10分ごとに220円です。", "wait": {"30": 660, "60": 1320, "120": 2640}, "pay": "東京・世田谷の会社は、現金で降りるときにお支払いです。", "shop": [35.6339, 139.6697], "pick_free_km": 3, "pick_over": 220, "_迎車メモ": "迎車・回送の3km超の単価は非公開のため、1kmごとに220円として高めに計算（お店：世田谷区上馬1丁目）", "label": "東京・世田谷の会社", "night_hours": [18, 8], "partner_id": "P002", "review_query": "ペットエクスプレス 世田谷区上馬"}, "kuriki": {"名前": "くりき（松戸）", "出典": "https://pet-kuriki.com/taxi 2026-10-27", "base_km": 4, "base": 1800, "tiers": [[100, 200], [200, 150], [null, 100]], "pick": 0, "back": 0, "night": 1.0, "round_flat": [10, 3300], "note": "千葉・松戸の会社は、乗車料金が5km未満1,800円、5km以上は1kmごとに200円（101km〜は150円、201km〜は100円）。往復は10kmまで3,300円（病院での待ち時間30分込み）で、その後の待ち時間は30分ごとに500円です。長い距離や長い待ち時間は、その会社のお見積りになります。", "wait": {"30": 0, "60": 500, "120": 1500}, "pay": "千葉・松戸の会社は、お支払い方法を決まったときのメールでご案内します。", "label": "千葉・松戸の会社", "night_hours": null, "partner_id": "P003", "review_query": "ペットタクシー くりき 松戸"}};/*/SELECTION_FARES*/
/* 事業者の検索は予約の保存・メール送信をしない。料金は上の生成データを使う。 */
var QUOTE_FIELDS = ['pref', 'pickup', 'via', 'dropoff', 'datetime', 'trip', 'riders', 'luggage', 'species', 'weight', 'cage', 'care', 'pet_count', 'pets_json', 'return_datetime', 'return_pickup', 'return_dropoff', 'route_details'];

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
  if (PREFS.indexOf(shortPref_(p.pref)) < 0) return 'area';
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
    return base+(c.shop?Math.max(0,Math.ceil(distance({lat:c.shop[0],lng:c.shop[1]},at)*1.5)-(c.pick_free_km||0))*(c.pick_over||0):0);
  }
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
      returnFee:fee(c.back,d.to)+(round?fee(c.back,d.backTo):0),nightExtra:nightFee(r1,nt)+(round?nightFee(r2,nt2):0),wait:0,method:round?'帰りにあらためてお迎え':'片道'};
    function sum(x){return x.ride+x.pickup+x.returnFee+x.nightExtra+x.wait;}
    var chosen=separate;
    if(round && p.return_pickup===p.dropoff && p.return_dropoff===p.pickup && c.wait){
      var gap=(parseJst_(p.return_datetime)-parseJst_(p.datetime))/60000-km*3;
      var wk=gap<=30?'30':gap<=60?'60':gap<=120?'120':'';
      if(wk){
        var waiting={ride:r1+r2,pickup:fee(c.pick,d.from),returnFee:fee(c.back,d.backTo),
          nightExtra:nightFee(r1,nt)+nightFee(r2,nt2),wait:Number(c.wait[wk])||0,method:'待っていてもらう往復'};
        if(c.round_flat && km+backKm<=c.round_flat[0]){waiting.ride=c.round_flat[1];waiting.nightExtra=0;}
        if(sum(waiting)<=sum(separate))chosen=waiting;
      }
    }
    var raw=sum(chosen);chosen.amount=Math.ceil(raw/100)*100;chosen.rounding=chosen.amount-raw;
    return chosen;
  }
  var local=total(d.km,d.backKm),highway=validKm(d.highKm)&&validKm(d.highBackKm)?total(d.highKm,d.highBackKm):null;
  var feePoints=round?[d.from,d.to,d.backFrom,d.backTo]:[d.from,d.to];
  var pickupExtra=c.shop && feePoints.some(function(at){return distance({lat:c.shop[0],lng:c.shop[1]},at)*1.5>c.pick_free_km;});
  return {amount:local.amount,text:yen_(local.amount),local:local,highway:highway,
    night:nt || (round&&nt2)?'夜間・早朝の割増 '+yen_(local.nightExtra)+'を含みます':c.night_hours?'指定時刻は夜間・早朝の割増対象外です':'料金表に夜間・早朝の割増はありません',
    pickupNote:pickupExtra?'迎車・回送の3km超は単価が非公開のため、1kmにつき220円として仮計算しています。実際の料金は事業者が確認します。':!c.shop&&c.pick===0&&c.back===0?'迎車・回送は料金表に別記がないため、この概算では0円で計算しています。無料の確約ではありません。':'迎車・回送の距離は営業所からの概算です。',
    routeNote:d.routeEstimated?'道のりを取得できなかったため、距離は直線距離からの概算です。':d.localEstimated?'一般道の距離は、高速区間から長めに推定しています。':''};
}

function selectionQuotes_(p) {
  var error = selectionValid_(p);
  if (error) return {ok:false,error:error};
  var expires = Date.now()+15*60000, r = selectionRide_(p);
  var cards = selectionCandidates_(r).map(function(pt) {
    var price = selectionPrice_(pt,p);
    if (!price) return null;
    return { id:pt.id, label:pt.name, car:pt.car || '車の詳細は引き受け時に確認',
      payment:[pt.payMethod,pt.payWhen].filter(String).join('・') || 'お支払い方法は引き受け時にご案内',
      price:price, review:selectionReview_(pt), check:checks_(pt, r).ask, expires:expires, token:quoteSignature_(p,pt.id,expires,price) };
  }).filter(Boolean);
  return {ok:true,selection_version:1,cards:cards};
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

// 緊急タブの搬送の会社（提携先ではない）の口コミ用：id → 場所を探すことばと、見つかった場所の名前に含まれるはずのことば
// tools/emergency.json から gen_areas.py が書き込む（ここは手で直さない）
/*EMG_REVIEWS*/var EMG_REVIEWS = {"E01": {"query": "動物救急車 大田区", "name": "動物救急車"}, "E02": {"query": "ペットドクターカー", "name": "ペットドクターカー"}, "E04": {"query": "ペットタクシー Animals 横浜市港南区", "name": "Animals"}, "E05": {"query": "コインペットタクシー シエロ", "name": "シエロ"}, "E06": {"query": "ペットタクシー パールのしっぽ 千葉市", "name": "パールのしっぽ"}, "E07": {"query": "ペットタクシー COCOタク さいたま南店", "name": ["COCO", "さいたま"]}, "E08": {"query": "ペットタクシー COCOタク 埼玉川越店", "name": ["COCO", "川越"]}, "E09": {"query": "ペットタクシー COCOタク 埼玉春日部", "name": ["COCO", "春日部"]}, "E10": {"query": "ペットレスキュー 夜間救急搬送", "name": "ペットレスキュー"}};/*/EMG_REVIEWS*/

// 口コミの場所の情報を取り寄せる（fields は取り寄せる項目）。月の回数の上限は点数と口コミ本文で共通
function reviewPlace_(partnerId, fields) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY');
  var key = Object.keys(SELECTION_FARES).filter(function(k) { return SELECTION_FARES[k].partner_id === partnerId; })[0];
  var emg = !key && EMG_REVIEWS[partnerId];
  var query = key ? SELECTION_FARES[key].review_query : emg && emg.query;
  if (!apiKey || !query) return null;
  var placeId = props.getProperty('PLACE_ID_' + partnerId + '_' + query);
  if (placeId === '-') return null; // 前に探して見つからなかった
  if (!placeId) {
    // IDだけの検索は無料。緊急タブの会社は、違う場所を拾わないよう名前も確かめる
    var found = JSON.parse(UrlFetchApp.fetch('https://places.googleapis.com/v1/places:searchText', {
      method:'post', contentType:'application/json', muteHttpExceptions:true,
      headers:{'X-Goog-Api-Key':apiKey,'X-Goog-FieldMask':emg ? 'places.id,places.displayName' : 'places.id'},
      payload:JSON.stringify({textQuery:query,languageCode:'ja',regionCode:'JP'})
    }).getContentText());
    var hit = (found.places || []).filter(function(x) {
      if (!emg) return true;
      // 名前のことばが全部入っているか（支店がある会社は支店名も。全角・半角の違いは気にしない）
      var norm = function(t) { return String(t).normalize('NFKC').replace(/\s/g, '').toLowerCase(); };
      var n = norm((x.displayName || {}).text || '');
      return [].concat(emg.name).every(function(w) { return n.indexOf(norm(w)) >= 0; });
    })[0];
    placeId = hit && hit.id;
    if (!placeId) {
      log_('口コミ：場所が見つからない ' + partnerId + ' ' + query);
      if (emg) props.setProperty('PLACE_ID_' + partnerId + '_' + query, '-');
      return null;
    }
    props.setProperty('PLACE_ID_' + partnerId + '_' + query, placeId);
  }
  var ym = Utilities.formatDate(new Date(), TZ, 'yyyyMM');
  var month = 'REVIEW_COUNT_' + ym, used = Number(props.getProperty(month)) || 0;
  if (used >= CONFIG.REVIEW_MONTHLY_LIMIT) return null;
  if (emg) {
    var emgMonth = 'REVIEW_EMG_COUNT_' + ym, emgUsed = Number(props.getProperty(emgMonth)) || 0;
    if (emgUsed >= CONFIG.REVIEW_EMG_MONTHLY_LIMIT) return null;
    props.setProperty(emgMonth, String(emgUsed + 1));
  }
  props.setProperty(month, String(used + 1));
  var res = UrlFetchApp.fetch('https://places.googleapis.com/v1/places/' + encodeURIComponent(placeId) + '?languageCode=ja', {
    muteHttpExceptions:true, headers:{'X-Goog-Api-Key':apiKey,'X-Goog-FieldMask':fields}
  });
  if (res.getResponseCode() !== 200) { log_('口コミ：取り寄せ失敗 ' + partnerId + ' ' + res.getResponseCode()); return null; }
  return JSON.parse(res.getContentText());
}

// 候補カードの「口コミを見る」：口コミ本文（地図サービスが関連度の高い順に返す最大5件）をサイトの中で見せる。
// 規約により、書いた人（名前・アイコン・プロフィールへのリンク）と、口コミそれぞれの元のページへのリンクを一緒に返す。保存はしない
function selectionReviews_(partnerId) {
  if (!EMG_REVIEWS[partnerId] && (!SELECTION_FARES || !Object.keys(SELECTION_FARES).some(function(k) { return SELECTION_FARES[k].partner_id === partnerId; }))) return {ok:false,error:'unknown'};
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

// 緊急タブの搬送の会社の星と件数（ids はカンマ区切り。表示しているその県の会社だけ）。点数は保存せず毎回取り寄せる
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
  var pt = selectionCandidates_(selectionRide_(p)).filter(function(x) { return x.id === p.partner_id; })[0];
  if (!pt) return {ok:false,error:'selection_unavailable'};
  var price = selectionPrice_(pt,p);
  if (!price || p.quote_token !== quoteSignature_(p,pt.id,expires,price)) return {ok:false,error:'selection_changed'};
  return {ok:true,partner:pt,price:price};
}

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
 *   3. 提携先がリンクを開き「確定料金（一般道／高速利用時）」を入れて引き受け（日時はお客さまの希望で固定。日付だけの依頼は時刻も）（先着1社）
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
  MAIL_RESERVE: 20, // メールの残りがこれより少ない日は、運営者あての通知を送らない
  // テスト：true にすると、すべての依頼で会社あての連絡を運営者のメールに送る（会社には届かない）
  // false のままでも、お名前が「テスト」で始まる依頼／メールが運営者と同じ依頼はテスト扱いになる
  TEST_MODE: false,

  // 候補カードに、提携先シートの会社に加えて「掲載候補」の会社（tools/display_companies.json）も表示だけで出す（Nori 2026-10-31）
  // true のあいだは、提携先シートの会社（P002・P003）も含めて全社「準備中」：予約の依頼は誰にも送れない（ボタンは押せず、サーバーでも断る。Nori「その2社もまだ準備中。送信はできないように」）
  // false にすると今までの状態（提携先の2社だけ・依頼できる）に戻る
  SHOW_ALL_CANDIDATES: true,
  // 掲載をOKしてくれた会社（表示だけの会社の ID）。全社準備中のあいだも、社名・口コミつきで出す（問い合わせはまだ送れない。「提携」の印は 2026-11-08 にやめた）
  // いま問い合わせを受け付けている会社（OPEN_PARTNERS）は、ここに入れなくても社名・口コミつきで出る
  // Nori 2026-11-08「aiai掲載していいって。掲載して」
  LISTED_IDS: [],
  // 全社準備中のあいだも、問い合わせを受け付ける会社（提携先シートのID → 料金・口コミ・特長に使う表示だけの会社のID）
  // ここの会社にだけは、設定 B1 が「止める」のままでも本物の会社あてに送る。ほかの会社は今までどおり送らない
  // Nori 2026-11-08「aiaiはOPENにしていい」。ペッタク（P061）も同日「サイトでも、受付開始して」。
  // COCOタク練馬杉並店（P030）・cocoタク福岡東（P062）は 2026-11-10「須藤さんと生形さんのところ、サイトでも受付開始して」
  // PETTA東京（P063）は 2026-11-12 提携の申し込み（中津川さん）、Nori「受付開始して、メール送っておいて」
  // ペットタクシーおさんぽ（P064、フロムハート株式会社）は 2026-11-12 提携の申し込み（三浦さん、黒ナンバー）。お迎えは目安50kmまで（11-13 三浦さんの返事）
  OPEN_PARTNERS: {'P060': 'D13b7c6f', 'P061': 'D225080e', 'P030': 'De308905', 'P062': 'D0ec95b6', 'P063': 'D3661eb1', 'P064': 'Dcb3b5a2', 'P065': 'Dd472236'},
  // 表示だけの会社は、お店からお迎えの場所までが直線でこのkmを超えると出さない（都道府県が合っていても遠すぎる会社を外す）
  DISPLAY_MAX_KM: 80,
  // 県の外へのお迎えを公式サイトに書いている会社（display_companies.json の far）は、その県ではこのkmまで出す（Nori 2026-11-14）
  DISPLAY_FAR_KM: 250,
  // 道のりを聞く道路データの入口（OSRM と同じ形）。ページの ROAD_API と同じにする。いまの公開デモは非営利だけが条件なので、手数料を始める前に商用で使える入口へ替える
  ROAD_API: 'https://router.project-osrm.org',

  // 決まらないときの待ち時間（分）。会社が動いている時間（OPEN_HOURS）だけ数える。夜の依頼は朝から数え始める
  OPEN_HOURS: '8-20',
  WAVE2_MIN: 20,   // これを過ぎたら、近くのエリア・全国対応の提携先にも送る
  GIVE_UP_MIN: 60, // これを過ぎたら、お客さまにお詫びを送って終了
  // 会社のお返事（空き状況と確定料金）で予約できる期限：お返事から QUOTE_VALID_HOURS 時間、ただしお迎えの QUOTE_CUTOFF_MIN 分前まで
  // （何日もたってから「予約する」を押され、会社の空きがもう無い、を防ぐ。2026-11-01 法的な点検）
  QUOTE_VALID_HOURS: 24,
  QUOTE_CUTOFF_MIN: 60,
  // 個人情報を残す期間（日）。お迎えの日（なければ受付日）からこれだけたったら、お名前・連絡先・場所を消す（手数料の計算に要る日時・会社・料金は残す）。個人情報の取り扱いの文と合わせる
  KEEP_PERSONAL_DAYS: 365,
  MIN_LEAD_HOURS: 3, // お迎えは受付から3時間より先だけ（LPと同じ。入力にかかる時間を見て15分は大目に見る）
  URGENT_HOURS: 3, // 希望時刻まで3時間を切っている依頼は、待ち時間を半分にする
  // 送迎のあと、飼い主さんに「無事に送迎できましたか？」を聞く（お迎え予定からこの時間たったら。送るのは RIDE_CHECK_SEND_HOURS の時間帯だけ）
  RIDE_CHECK_AFTER_HOURS: 12,
  RIDE_CHECK_SEND_HOURS: '9-20',

  // 提携先シートの「営業時間」「何時間前まで」が空欄のとき。メールは営業時間に読まれる前提で、読める時刻からお迎えまでこれだけ必要
  DEFAULT_PARTNER_HOURS: '8-18',
  DEFAULT_LEAD_HOURS: 3,

  LARGE_DOG_KG: 30, // Nori 2026-11-10「大型犬は30kg以上にして」
  // この体重以上は「大型犬OK」の提携先にだけ送る
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
var SHEET_AGREE = '規約の同意'; // 提携規約への同意の記録（agreePage_。消さない・書き換えない）

var REQ_HEADERS = [
  '受付番号', '受付日時', '状態', '都府県', 'お迎えの場所', '行き先', '希望日時', '片道・往復',
  '種類', '犬種・猫種', '体重kg', '年齢', '性別', 'キャリー', '介助', '同乗人数',
  'お名前', '電話番号', 'メール', '連絡方法', 'メモ',
  '通知段階', '通知した提携先', '決定した提携先ID', '決定した提携先', 'お迎え予定', '料金の目安', '提携先から一言', '決定日時',
  'お客さまLINE', '終了日時', 'ペット数', 'ペット詳細', '日付のみ', '経由地', 'ペットJSON', '概算km', '概算料金', '荷物', '高速利用時の料金', '帰りの日時', '帰りのお迎え', '帰りの行き先', '待ち時間（分）', '概算料金の表示', '帰りのやり方', '指定した提携先ID', '指定した提携先', '区間', 'ペアの受付番号',
  // 2026-10-31 Nori「複数社に予約・見積もりを依頼できるように。どちらかはお客さまが選ぶ」。依頼の種類＝予約／見積もり、見積もりJSON＝届いた見積もり
  '依頼の種類', '見積もりJSON',
  // 2026-11-01 Nori「キャンセルを直接事業者に伝えられたら、こっちは判断できない」→ 送迎のあとに飼い主さんにも確かめる（手数料の照らし合わせ用）
  '送迎確認', '送迎確認日時',
  // 2026-11-09 Nori「会社の返事の入力欄に、電話とメールアドレスを入れる欄を作ろう」→ お客さまにお伝えする会社の連絡先（会社あての送信先は提携先シートのまま）
  '会社の連絡先（電話）', '会社の連絡先（メール）'
];
var PARTNER_HEADERS = [
  'ID', '事業者名', '担当者名', '対応エリア', 'メール', '電話番号', 'LINE公式ID（先方）', '受付中', '大型犬OK', '介助OK',
  'LINE登録コード', 'LINE userId', '引き受け件数', 'メモ',
  '車のタイプ', '同乗できる人数', '乗せられるペット数', '荷物多めOK',
  'ケージ必須', 'ケージ貸し出し', '支払い方法', '支払いのタイミング', '営業時間', '何時間前まで',
  // 2026-10-31 追加（空欄＝まだ分からない。分からない条件は候補に出し、引き受けるときに会社がチェックして確かめる）
  '送迎できる時間', '大型犬の最大kg', '大型犬の最大頭数', '貸し出しケージの最大kg', 'ペットだけOK', 'ワクチン必須',
  // 2026-11-01 追加：「犬・猫」「犬・猫・うさぎ・鳥」「すべて」など。書いてあればそれ以外の動物の依頼は送らない（列がなくても動く。空欄＝確かめてもらう）
  '乗せられる動物',
  // 2026-11-01 追加：確定のあとのキャンセル料など（例「前日まで無料・当日は運賃の50%」）。書いてあれば予約する前のお客さまに見せる
  'キャンセル規定',
  // 2026-11-10 追加（Nori「お客さまのフォームのあらゆる組み合わせに、マッチングさせられる事業者の情報を」）。提携の申し込み（/partner/）からそのまま入る（applyPartner_）
  // ○＝受けられる／×＝受けられない／空欄・「相談」＝分からない（引き受けるときに確かめる）
  // 組み合わせ（Nori 2026-11-10「大型犬4頭乗せられて、さらに大人2人乗せられるってほんと？」）：大きい子の頭数ごとに一緒に乗れる大人の人数
  '行き先の範囲', '行き先の上限km', '大型犬1頭のときの大人', '大型犬2頭のときの大人', '大型犬3頭のときの大人', '大型犬4頭以上のときの大人',
  '小型だけで最大頭数のときの大人', '大型犬と大きな荷物',
  // お迎えのエリア（Nori 2026-11-10「都道府県以下のレベルの対応エリアももっと工夫して」）：お店の位置とお迎えに行ける範囲（km）。お迎えの場所がお店から範囲の外なら送らない
  'お店の住所', 'お店の緯度経度', 'お迎えの範囲km', '介護でできること', '介護で伺える人数', '介護で運べる体重', '介護の道具', '介護の大型犬', '途中で寄る', 'ワクチンの証明', '申し込みの内容'
];

var ST = { OPEN: '手配中', DONE: '決定', NONE: '見つからず', CANCEL: '取り消し' };
// 1回に問い合わせできる会社の数の上限はない（Nori 2026-11-01「最大5社の上限はなくていい」）。同じ会社が2回入っていたら1回にする

// お客さまが選んだ会社（カンマ区切り）。1社のときも同じ形
function pickedIds_(r) { return String(r['指定した提携先ID'] || '').split(',').filter(String); }
function isQuoteReq_(r) { return r['依頼の種類'] === '見積もり'; }
// 2026-11-01 Nori「事業者を選んでサブミット→事業者が空きと料金を連絡→それを見てお客さまが予約するか決める」。
// 新しい依頼はすべて「問い合わせ」（空き状況と料金の問い合わせ）。1社でも、お客さまが「この内容で予約する」を押すまで決まらない
function isAsk_(r) { return r['依頼の種類'] === '問い合わせ'; }
// お客さまがあとで決める依頼：問い合わせ（いまの依頼すべて）と、前の形の見積もり依頼・複数社への予約依頼。前の形の1社だけの予約依頼は、引き受けた時点で決まる
function needsChoice_(r) { return isAsk_(r) || isQuoteReq_(r) || pickedIds_(r).length > 1; }
// お返事で予約できる期限（ミリ秒）。お返事から QUOTE_VALID_HOURS 時間か、お迎えの QUOTE_CUTOFF_MIN 分前の早いほう
function cutoffText_() { var m = CONFIG.QUOTE_CUTOFF_MIN; return m % 60 ? m + '分' : (m / 60) + '時間'; }
function quoteUntil_(qt) {
  var t = Number(qt && qt.time) || Date.now(), at = Number(qt && qt.at) || Infinity;
  return Math.min(t + CONFIG.QUOTE_VALID_HOURS * 3600000, at - CONFIG.QUOTE_CUTOFF_MIN * 60000);
}
// 予約する前のお客さまに見せるキャンセルの決まり（当サイトはキャンセル料をいただかない）
// キャンセル規定から、アピールに出せる短い言い方（かからない・前日まで無料のときだけ）
function cancelFree_(t) {
  t = String(t || '');
  if (/キャンセル料(なし|は(かかりません|いただきません|無料))|かからない/.test(t)) return 'キャンセル料なし';
  if (/前日まで[^、。]*無料/.test(t)) return '前日までキャンセル無料';
  return '';
}
function cancelRuleText_(pt) {
  var c = String((pt && pt.cancelRule) || '').trim();
  return c ? c + '（' + pt.name + 'の規定）' : pt.name + 'のキャンセル規定によります。予約の前に、' + pt.name + 'の公式サイトなどでご確認ください';
}
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
  if ((e.parameter || {}).kind === 'demo') {
    try { return json_(demoInfo_(e.parameter.demo)); } catch (err) { return json_({ok:false}); }
  }
  if ((e.parameter || {}).kind === 'quotes') {
    try { return json_(selectionQuotes_(e.parameter)); } catch (err) { return json_({ok:false,error:'quotes_unavailable'}); }
  }
  if ((e.parameter || {}).kind === 'emg_scores') {
    try { return json_(emgScores_(String(e.parameter.ids || ''))); } catch (err) { return json_({ok:false,error:'reviews_unavailable'}); }
  }
  if ((e.parameter || {}).kind === 'scores') {
    try { return json_(selectionScores_(String(e.parameter.ids || ''), demoId_(e.parameter.demo))); } catch (err) { return json_({ok:false,error:'reviews_unavailable'}); }
  }
  if ((e.parameter || {}).kind === 'reviews') {
    try { return json_(selectionReviews_(String(e.parameter.partner_id || ''), demoId_(e.parameter.demo))); } catch (err) { return json_({ok:false,error:'reviews_unavailable'}); }
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
  var topic = clip_(p.topic, 80).trim() || 'その他'; // 提携の申し込み（/partner/）は「提携のお申し込み（会社名）」で来る
  // 提携の申し込みは料金の項目が多いので長めに受ける（Nori 2026-11-08「あとから聞かなくていいように」）
  var name = clip_(p.name, 100), email = clip_(p.email, 200).trim(), msg = clip_(p.message, /^提携/.test(topic) ? 8000 : 2000);
  if (!name || !msg || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return { ok: false, error: 'missing' };
  var reqId = clip_(p.req_id, 20);
  var sh = ensureSheet_(SpreadsheetApp.getActive(), '問い合わせ', ['受付日時', '種類', 'お名前', 'メール', '受付番号', '内容', '対応']);
  sh.appendRow([new Date(), topic, name, email, reqId ? "'" + reqId : '', msg, '']);
  // 提携の申し込みは、答えを項目ごとに提携先シートへ写す（受付中は×のまま。2026-11-10 Nori「あらゆる組み合わせにマッチングさせられる情報を」）
  var applied = '';
  if (/^提携のお申し込み/.test(topic) && p.apply) {
    try { applied = applyPartner_(JSON.parse(String(p.apply).slice(0, 20000)), name, email); }
    catch (err) { log_('提携の申し込みの写しでエラー: ' + err); }
  }
  try {
    MailApp.sendEmail({ to: adminEmail_(), replyTo: email, name: CONFIG.SERVICE_NAME,
      subject: '[お問い合わせ] ' + topic + '：' + name + ' 様',
      body: '■ 種類：' + topic + '\n■ お名前：' + name + ' 様\n■ メール：' + email + (reqId ? '\n■ 受付番号：' + reqId : '') +
        '\n\n' + msg + (applied ? '\n\n■ 提携先シートに ' + applied + ' として入れました（受付中は×。提携を始めるときに○にします）' : '') + '\n\n――――――――――\nこのメールに返信すると、お客さま（' + email + '）に届きます。\n予約シート「問い合わせ」タブにも残しています：' + SpreadsheetApp.getActive().getUrl() });
  } catch (err) { log_('問い合わせメールの送信エラー: ' + err); }
  return { ok: true };
}

// 提携の申し込みの答え（/partner/ のフォームの項目名 → 値）を、提携先シートの1行にする。受付中は×（だれにも送らない）。新しいIDを返す
function applyPartner_(a, name, email) {
  if (!a || typeof a !== 'object') return '';
  var g = function (k) { return String(a[k] == null ? '' : a[k]).trim(); };
  var n = function (t) { var m = toHalf_(t).match(/\d+/); return m ? Number(m[0]) : ''; };
  var yn = function (t, yes, no) { return yes.test(t) ? '○' : no.test(t) ? '×' : ''; };
  var co = g('会社名・屋号');
  if (!co) return '';
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sh = ensureSheet_(SpreadsheetApp.getActive(), SHEET_PARTNER, PARTNER_HEADERS);
    var head = sh.getRange(1, 1, 1, Math.max(1, sh.getLastColumn())).getValues()[0].map(String);
    var add = PARTNER_HEADERS.filter(function (h) { return head.indexOf(h) < 0; });
    if (add.length) { sh.getRange(1, head.length + 1, 1, add.length).setValues([add]).setFontWeight('bold').setBackground('#fff1e6'); head = head.concat(add); }
    var ids = sh.getLastRow() > 1 ? sh.getRange(2, head.indexOf('ID') + 1, sh.getLastRow() - 1, 1).getValues().map(function (r) { return Number(String(r[0]).replace(/\D/g, '')) || 0; }) : [];
    var id = 'P' + ('00' + (Math.max.apply(null, [0].concat(ids)) + 1)).slice(-3);
    var same = sh.getLastRow() > 1 && sh.getRange(2, head.indexOf('メール') + 1, sh.getLastRow() - 1, 1).getValues().some(function (r) { return String(r[0]).trim().toLowerCase() === String(email).toLowerCase(); });
    var ride = g('飼い主さんの同乗'), pets = g('乗せられる頭数'), big = g('大型犬（30kg以上）の数') || g('大きい子（20kg以上）の数'), kg = g('乗せられる体重'), cage = g('ケージ'), same0 = g('当日の依頼');
    var lead = n(g('当日の締め切り'));
    if (lead === '') lead = /前日まで/.test(same0) ? 24 : /2日前/.test(same0) ? 48 : /3日前/.test(same0) ? 72 : '';
    var row = {
      'ID': id, '事業者名': co, '担当者名': String(name || '').replace(/（[^）]*）$/, ''), '対応エリア': g('都道府県の一覧') || g('都道府県'), 'メール': email, '受付中': '×',
      '大型犬OK': /乗せられない/.test(big) ? '×' : big ? '○' : '', '介助OK': yn(g('介護が必要な子'), /^受けられる/, /受けられない/),
      'メモ': '提携の申し込み ' + Utilities.formatDate(new Date(), TZ, 'yyyy/MM/dd HH:mm') + '（受付中は×。提携を始めるときに○）' + (same ? '／同じメールの行がほかにもあります' : ''),
      '車のタイプ': g('車'), '同乗できる人数': /できない/.test(ride) ? 0 : /以上/.test(ride) ? 9 : n(ride), '乗せられるペット数': /以上/.test(pets) ? 5 : n(pets),
      '荷物多めOK': /^載せられる/.test(g('大きな荷物')) ? '○' : /載せられない/.test(g('大きな荷物')) ? '×' : '',
      'ケージ必須': /なくても/.test(cage) ? '×' : /必要/.test(cage) ? '○' : '', 'ケージ貸し出し': /貸し出しあり/.test(cage) ? '○' : /貸し出しなし/.test(cage) ? '×' : '',
      '支払い方法': g('お支払い方法'), '支払いのタイミング': g('お支払いのタイミング'), '営業時間': g('受けられる時間帯'), '何時間前まで': lead,
      'お店の住所': g('お店の住所') || g('車が出発する場所'), 'お店の緯度経度': g('お店の位置'),
      'お迎えの範囲km': /遠く/.test(g('お迎えに行ける範囲')) ? '' : n(g('お迎えに行ける範囲')),
      '貸し出しケージの最大kg': /もっと大きい/.test(g('貸し出せるケージ')) ? 999 : n(g('貸し出せるケージ')),
      '送迎できる時間': /受けない/.test(g('時間外の依頼')) ? g('受けられる時間帯') : '',
      '大型犬の最大kg': /超え/.test(kg) ? 999 : n(kg), '大型犬の最大頭数': /乗せられない/.test(big) ? 0 : /以上/.test(big) ? 9 : n(big),
      'ペットだけOK': yn(g('ペットだけの送迎'), /^できる/, /できない/), 'ワクチン必須': /接種していなくても/.test(g('ワクチン')) ? '×' : '',
      '乗せられる動物': g('乗せられる動物'),
      'キャンセル規定': /かからない/.test(g('キャンセル料')) ? 'キャンセル料なし' : /当日はかかる/.test(g('キャンセル料')) ? '前日まで無料、当日は' + (g('当日のキャンセル料') || 'かかる') : g('キャンセル料'),
      '行き先の範囲': g('行き先までの距離'), '行き先の上限km': n(g('行き先までの上限')), 
      '大型犬1頭のときの大人': g('大きい子1頭のときの大人'), '大型犬2頭のときの大人': g('大きい子2頭のときの大人'), '大型犬3頭のときの大人': g('大きい子3頭のときの大人'),
      '大型犬4頭以上のときの大人': g('大きい子4頭のときの大人'), '小型だけで最大頭数のときの大人': g('小さい子だけで頭数がいちばん多いときの大人'), '大型犬と大きな荷物': g('大きい子と大きな荷物'),
      '介護でできること': g('介護でできること'), '介護で伺える人数': g('介護で伺える人数'),
      '介護で運べる体重': g('介護で運べる体重'), '介護の道具': g('介護の道具'), '介護の大型犬': g('介護が必要な大型犬'), '途中で寄る': g('途中で寄る'), 'ワクチンの証明': g('ワクチン'),
      '申し込みの内容': JSON.stringify(a).slice(0, 45000)
    };
    sh.appendRow(head.map(function (h) { return row[h] === undefined ? '' : row[h]; }));
    log_('提携の申し込みを提携先シートに入れました: ' + id + ' ' + co);
    return id;
  } finally { lock.releaseLock(); }
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
    var mode = '問い合わせ'; // 予約と見積もりを分けない（Nori 2026-11-01）。前の LP が送る mode は使わない
    var picks = split ? [] : picksOf_(p);
    if (!split && !picks.length) return { ok: false, error: 'selection_unavailable' };
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
    var how = deliver_(pt, (isAsk_(r) ? '【空き状況と料金のお問い合わせ】' : isQuoteReq_(r) ? '【お見積もりのご依頼】' : '【新しいご依頼】') + r['都府県'] + '・' + whenText_(r), requestText_(r, pt), r, requestHtml_(r, pt));
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
    'ペットタクシーの検索サイト「' + CONFIG.SERVICE_NAME + '」です。飼い主さんから、送迎のお問い合わせが届きました。\n' +
    (isAsk_(r) ? '★飼い主さんのお名前・ご連絡先は、飼い主さんが予約を確定した時点でお知らせします。\n★お返事の内容（お迎え時刻・確定料金）は、お返事から' + CONFIG.QUOTE_VALID_HOURS + '時間（お迎えの' + cutoffText_() + '前まで）有効です。そのあいだに飼い主さんが予約を確定したときは、お引き受けください。お返事のあとにほかのご予約が入ったときは、お返事のリンクを開いて「このお返事を取り下げる」を押してください。\n\n' : '★お客さまのお名前・ご連絡先は、引き受けが決まった時点でお知らせします（リンクから引き受けた場合はその場で表示されます）。\n\n') +
    rideText_(r) + retAsk_(r) + waitRuleForPartner_(r) + estText_(r) + '\n■ お支払い：' + payForPartner_(pt) + askText_(pt, r) + '\n\n' +
    (isAsk_(r) ? '空き状況と料金のお問い合わせです' + (pickedIds_(r).length > 1 ? '（お客さまが選んだ' + pickedIds_(r).length + '社にお声がけしています）' : '') + '。お受けいただける場合は、下のリンクから' + inputWord_(r) + '（税込）をご入力ください（数字を入れるだけです）。お客さまが内容を見て「予約する」を押した時点で決まり、お名前・ご連絡先をお知らせします。\n'
      : isQuoteReq_(r) ? 'お見積もりのご依頼です。お客さまは、ほかの会社のお見積もりとくらべて1社を選びます。\nお受けいただける場合は、下のリンクから' + inputWord_(r) + '（税込）をご入力ください（数字を入れるだけです）。お客さまが貴社を選んだら、お名前・ご連絡先をお知らせします。\n'
      : needsChoice_(r) ? 'お客さまが選んだ' + pickedIds_(r).length + '社にお声がけしています。お受けいただける場合は、下のリンクから' + inputWord_(r) + '（税込）をご入力ください（数字を入れるだけです）。お客さまが引き受けた会社の中から1社を選んだ時点で決まり、お名前・ご連絡先をお知らせします。\n'
      : 'お受けいただける場合は、下のリンクから' + inputWord_(r) + '（税込）をご入力ください（数字を入れるだけです。先着1社）。\n') + acceptUrl_(r['受付番号'], pt.id) +
    '\n\nご返信でお答えいただく場合は、次のどちらかでお願いします。\n' +
    '・受けられる：' + (r['日付のみ'] ? 'お迎え時刻〇時〇分・' : '') + '一般道〇円・高速を使う場合〇円（高速代込み。使わないなら「なし」）' + (isRound_(r) ? '・帰りは「待つ」か「あとで迎え」か' : '') + '\n' +
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
function estShown_(r) { return roundYenText_(String(r['概算料金の表示'] || '').trim() || yen_(num_(r['概算料金'])) + '〜'); }
// 料金の目安（概算）は100円単位にまるめて伝える（Nori 2026-11-01「1円単位まで出さない方がいい」）。確定料金はまるめない
function roundYenText_(s) { return String(s).replace(/(\d{1,3}(?:,\d{3})+|\d+)円/g, function (m, d) { var v = Number(d.replace(/,/g, '')); return v >= 100 ? yen_(Math.round(v / 100) * 100) : m; }); }

function isRound_(r) { return /往復/.test(String(r['片道・往復'] || '')); }
var RET_WAYS = ['待つ（病院などで終わるまで待機）', 'あとで迎え（一度戻って、帰りの時刻に迎えに行く）'];
// 往復のときだけ：待つか一度戻るかは、お客さまの料金が安くなるほうを会社に選んでもらう
function retAsk_(r) {
  return isRound_(r) && !r['帰りのやり方'] ? '\n■ 帰りのやり方：病院などで待つか、一度戻ってあとで迎えに行くかは、お客さまの料金が安くなるほうを貴社で選んでください（確定料金は選んだやり方の往復の合計で）' : '';
}
// 往復の待ち時間は、当日の実際の待ち時間で精算してもらう（Nori 2026-11-09「事業者側にもそこは実際の時間で精算してもらうように」）
// 当日の道路事情（渋滞・通行止め・道順の変更）で料金表どおりに変わる分も、実際の時間・道のりで精算してもらう（Nori 2026-11-09「当日の道路事情などで料金は変わる可能性もある」）
function waitRuleForPartner_(r) {
  return (isRound_(r) ? '\n■ 待ち時間の料金：病院などで待つときは、当日の実際の待ち時間で精算してください。待つやり方の確定料金は、お問い合わせの帰りの時刻まで待った場合の金額でお返事ください' : '') +
    '\n■ 当日の精算：当日の道路事情（渋滞・通行止め・道順の変更など）' + (isRound_(r) ? 'や待ち時間' : '') + 'で貴社の料金表どおりに料金が変わる分は、実際の時間・道のりで精算してください（お客さまにも、当日の事情で最終的なお支払いが変わることがあるとお伝えしています）';
}
// お客さまへの当日の精算の注意。当てはまらない会社には出さない（Nori 2026-11-09「当てはまらない会社は対象外」）：
// 待機料金なし（料金表の wait.yen が0）の会社は待ち時間、「渋滞でも追加料金なし」の会社は交通事情を書かない
function feeFlags_(pt) {
  var d = pt && openDisplay_(pt.id), w = d && d.fare && d.fare.wait;
  return { noWait: !!(w && w.yen === 0), noJam: !!(d && (d.points || []).indexOf('渋滞でも追加料金なし') >= 0) };
}
function changeNote_(pt) {
  var f = feeFlags_(pt);
  return [f.noJam ? '' : '当日の交通事情', f.noWait ? '' : '待ち時間', '道順・行き先の変更'].filter(String).join('・') + 'などで、実際の料金が変わることがあります。';
}
function waitRuleForCustomer_(r, pt) {
  return isRound_(r) && !feeFlags_(pt).noWait ? '　※病院などで待っていてもらうときの待ち時間の料金は、当日の実際の待ち時間で精算します。用事が長引いたときなど、最終的なお支払いは上の料金から変わることがあります。\n' : '';
}
function retWayOf_(v) { return RET_WAYS.filter(function (w) { return w === v; })[0] || ''; }
function retSelect_() {
  return '<label>帰りのやり方（お客さまの料金が安くなるほう）<select name="ret_way" required><option value="">選んでください</option>' +
    RET_WAYS.map(function (w) { return '<option>' + esc_(w) + '</option>'; }).join('') + '</select></label>';
}

function decidedText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\nありがとうございます。こちらのご依頼をお願いすることになりました。\nお客さまへ直接ご連絡をお願いします。\n\n' + customerForPartner_(r) +
    '\n\n▼ やむを得ずお受けできなくなったとき（押すとお客さまにお知らせし、このご予約は取り消しになります）\n' + partnerCancelUrl_(r['受付番号'], pt.id) +
    '\n\n当サイトへのご連絡（お客さまとの間で困ったこと、条件の変更など）は、このメールに返信してください。';
}

function closedText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\n' + CONFIG.SERVICE_NAME + 'です。先日ご相談した ' + whenText_(r) + ' のご依頼（受付番号 ' + r['受付番号'] + '）は、締め切りとなりました。\nご確認いただき、ありがとうございました。またよろしくお願いします。';
}

function cancelText_(r, pt) {
  return pt.name + ' ' + (pt.person ? pt.person + '様' : 'ご担当者さま') + '\n\nお客さまがご依頼を取り消されました。お迎えは不要です。\n\n受付番号：' + r['受付番号'] + '\nお迎え予定：' + fmt_(r['お迎え予定']) + '\nお客さま：' + r['お名前'] + ' 様\n\nキャンセル料がかかる場合は、貴社のキャンセル規定にしたがって、お客さまへ直接ご案内ください（お客さまにも、規定によりキャンセル料がかかることがあるとお伝えしています）。\n\nご対応いただきありがとうございました。';
}

// お客さまに見せる会社の連絡先だけを差しかえた写し（会社あての送信は元の pt を使う）
function custPt_(pt, tel, mail) {
  if (!pt) return pt;
  var o = {};
  Object.keys(pt).forEach(function (k) { o[k] = pt[k]; });
  if (tel || mail) { o.tel = String(tel || '').trim(); o.email = String(mail || '').trim(); }
  return o;
}
// 決まった会社の、お客さま向けの連絡先（返事で会社が入れたもの。なければ提携先シート）
function decidedPt_(r) {
  return custPt_(partnerById_(r['決定した提携先ID']), r['会社の連絡先（電話）'], r['会社の連絡先（メール）']);
}
// 返事の画面で会社が入れた連絡先を確かめる。電話かメールの少なくとも一つ
function replyContact_(q, pt) {
  if (q.ctel === undefined && q.cmail === undefined) return { tel: '', mail: '' }; // 欄のない古い画面からの返事は提携先シートの連絡先のまま
  var tel = String(q.ctel || '').replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); }).replace(/[ー－―]/g, '-').trim();
  var mail = String(q.cmail || '').trim();
  var digits = tel.replace(/[^\d]/g, '');
  if (tel && (!/^[\d\-+() ]+$/.test(tel) || digits.length < 10 || digits.length > 11)) return { err: '電話番号の形が正しくありません（10〜11けたの数字）。' };
  if (mail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) return { err: 'メールアドレスの形が正しくありません。' };
  if (!tel && !mail) return { err: 'お客さまからの連絡を受ける電話番号かメールアドレスを、少なくとも一つ入れてください。' };
  return { tel: tel, mail: mail };
}

// 予約が確定したあと、お客さまが会社に直接連絡するための連絡先（Nori 2026-11-09「おすすめ通りでOK」：
// 会社が遅れた・来ないときにお客さまが困らないように。電話番号はサイトには出さず、確定したお客さまへのメールにだけ書く）
function partnerContactText_(pt) {
  var c = [pt.tel ? '電話 ' + pt.tel : '', pt.email ? 'メール ' + pt.email : ''].filter(String).join('／');
  return c ? '■ ' + pt.name + 'の連絡先：' + c + '\n' : '';
}

// 確定後の取り消し・キャンセル料の案内（同）
function cancelAfterText_(pt) {
  var rule = String(pt.cancelRule || '').trim();
  return '確定後の取り消しには「' + pt.name + '」のキャンセル規定' + (rule ? '（' + rule + '）' : '') + 'が適用され、キャンセル料がかかることがあります。キャンセル料のお支払いは、ペットタクシーへ直接です（当サイトのキャンセル料はありません）。';
}

function pickPartners_(r, stage) {
  var pref = r['都府県'];
  var areas = stage === 1 ? [pref] : (NEIGHBORS[pref] || []).concat(['全国']);
  var care = r['介助'] === '必要';
  return partners_().filter(function (pt) {
    if (!pt.active) return false;
    if ((CONFIG.SHOW_ALL_CANDIDATES && !isOpen_(pt.id)) || isDisplayOnly_(pt.id)) return false; // 全社準備中のあいだ（受け付けを始めた会社を除く）・表示だけの会社には送らない
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
      animals: animalsOf_(cell('乗せられる動物')), big: tri('大型犬OK'), luggage: tri('荷物多めOK'), riders: num('同乗できる人数'), pets: num('乗せられるペット数'),
      car: cell('車のタイプ'), cancelRule: cell('キャンセル規定'),
      cageMust: cell('ケージ必須'), cageLend: tri('ケージ貸し出し'),
      payMethod: cell('支払い方法'), payWhen: cell('支払いのタイミング'),
      hours: cell('営業時間'), lead: num('何時間前まで'),
      careTri: tri('介助OK'), rideHours: cell('送迎できる時間'), maxKg: num('大型犬の最大kg'), maxBig: num('大型犬の最大頭数'),
      lendKg: num('貸し出しケージの最大kg'), petOnly: tri('ペットだけOK'), vacMust: tri('ワクチン必須'),
      destScope: cell('行き先の範囲'), destKm: num('行き先の上限km'), combo: [comboOf_(cell('小型だけで最大頭数のときの大人')), comboOf_(cell('大型犬1頭のときの大人')), comboOf_(cell('大型犬2頭のときの大人')),
        comboOf_(cell('大型犬3頭のときの大人')), comboOf_(cell('大型犬4頭以上のときの大人'))], comboLug: tri3_(cell('大型犬と大きな荷物')),
      shopLL: (function (t) { var m = toHalf_(t).match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/); return m ? { lat: Number(m[1]), lng: Number(m[2]) } : null; })(cell('お店の緯度経度')),
      radiusKm: num('お迎えの範囲km'),
      careBig: tri3_(cell('介護の大型犬')), careBigSet: !!cell('介護の大型犬'), careCan: cell('介護でできること'), careStaff: num('介護で伺える人数'), careStaffMore: /増や/.test(cell('介護で伺える人数')),
      careKg: /超え/.test(cell('介護で運べる体重')) ? Infinity : num('介護で運べる体重'), careTools: cell('介護の道具'), via: tri3_(cell('途中で寄る')),
      vacProof: cell('ワクチンの証明')
    });
  }
  return out;
}

// 申し込みの答え（受けられる／相談して決める／受けられない、できる／できない、○／×）→ true / false / null（相談・空欄＝分からない）
function tri3_(v) {
  v = String(v || '').trim();
  if (!v || /相談/.test(v)) return null;
  if (/^(×|✕|x|いいえ|no)$/i.test(v) || /受けられない|乗せられない|できない/.test(v)) return false;
  return true;
}
// 組み合わせの答え → 一緒に乗れる大人の人数。-1＝その頭数は乗せられない、null＝分からない
function comboOf_(v) {
  v = String(v || '').trim();
  if (!v) return null;
  if (/乗せられない|^×$/.test(v)) return -1;
  if (/乗れない|ペットだけ/.test(v)) return 0;
  if (/以上/.test(v)) return 9;
  var m = toHalf_(v).match(/\d+/);
  return m ? Number(m[0]) : null;
}
// 47都道府県（行き先の住所から都道府県を読む）
var PREF47 = ['北海道','青森','岩手','宮城','秋田','山形','福島','茨城','栃木','群馬','埼玉','千葉','東京','神奈川','新潟','富山','石川','福井','山梨','長野','岐阜','静岡','愛知','三重','滋賀','京都','大阪','兵庫','奈良','和歌山','鳥取','島根','岡山','広島','山口','徳島','香川','愛媛','高知','福岡','佐賀','長崎','熊本','大分','宮崎','鹿児島','沖縄'];
function prefIn_(t) {
  t = String(t || '');
  var hit = PREF47.filter(function (x) { return t.indexOf(x === '北海道' ? x : x + (x === '東京' ? '都' : /^(大阪|京都)$/.test(x) ? '府' : '県')) >= 0; });
  return hit.length === 1 ? hit[0] : '';
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
  return a.map(function (p) { return { kg: Number(p.weight) || 0, care: p.care || '', vac: p.vaccine === '済', sp: String(p.species || ''), breed: String(p.breed || ''), need: (p.care_need || []).concat(p.care_note ? [p.care_note] : []), needList: p.care_need || [],
    rabies: p.rabies === '済' }; });
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
// 提携先シートの「乗せられる動物」を読む。例「犬・猫」「犬・猫・うさぎ・鳥」「犬のみ」「すべて」。空欄は null（分からない）
function animalsOf_(t) {
  t = String(t || '').trim();
  if (!t) return null;
  if (/すべて|全て|なんでも|何でも|制限なし/.test(t)) return { all: true };
  var a = { all: false };
  if (/犬/.test(t)) a.dog = true;
  if (/猫/.test(t)) a.cat = true;
  if (/小動物|うさぎ|ウサギ|フェレット|ハムスター|モルモット|チンチラ|ハリネズミ/.test(t)) a.small = true;
  if (/鳥|インコ|オウム|文鳥/.test(t)) a.bird = true;
  if (/爬虫|両生|カメ|亀|トカゲ|ヘビ|蛇/.test(t)) a.reptile = true;
  if (/魚|金魚|メダカ/.test(t)) a.fish = true;
  return a;
}
// true＝乗せられる、false＝乗せない、null＝分からない（確かめてもらう）
function partnerAnimalOk_(pt, kind) {
  var a = pt && pt.animals;
  if (!a) return null;
  if (a.all) return true;
  return !!a[kind];
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
  // 種類：提携先シートの「乗せられる動物」に書いてあれば、それ以外は送らない（Nori 2026-11-01「条件に合う依頼だけ届く」）。空欄の会社は確かめてもらう
  pets.forEach(function (p) {
    var k = /^犬$/.test(String(p.sp || '')) ? 'dog' : /^猫$/.test(String(p.sp || '')) ? 'cat' : animalKind_(p);
    if (!k) return;
    var ok = partnerAnimalOk_(pt, k);
    if (ok === false) ng.push((p.breed || p.sp) + '（乗せられる動物の外）');
    else if (ok === null && k !== 'dog' && k !== 'cat') ask.push('犬・猫のほかの子（' + (p.breed || p.sp) + '）を乗せられる');
  });
  // 大きさ
  if (bigs.length) {
    if (pt.big === false) ng.push('大型犬');
    else if (pt.maxKg !== null && maxKg > pt.maxKg) ng.push(maxKg + 'kgの子（' + pt.maxKg + 'kgまで）');
    else if (pt.maxKg === null && maxKg >= CONFIG.ASK_KG) ask.push(maxKg + 'kgの子が乗れる'); // 20〜29kgは軽バンでも乗れるので聞かない
    var maxBig = pt.maxBig !== null ? pt.maxBig : isVan_(pt) ? CONFIG.VAN_BIG_DOGS : null;
    if (maxBig !== null && bigs.length > maxBig) ng.push('大型犬' + bigs.length + '頭' + (pt.maxBig === null ? '（軽バンは' + maxBig + '頭まで）' : ''));
    else if (maxBig === null && bigs.length >= 2) ask.push('大型犬' + bigs.length + '頭が一緒に乗れる');
    // 組み合わせ：申し込みで大きい子の頭数ごとの大人の人数が分かっていれば、それで決める
    var cap = (pt.combo || [])[Math.min(bigs.length, 4)];
    if (cap === -1) ng.push('大型犬' + bigs.length + '頭');
    else if (cap !== null && cap !== undefined) {
      ask = ask.filter(function (x) { return x !== '大人' + n.riders + '人が一緒に乗れる'; }); // 人数は組み合わせの答えで分かる
      if (n.riders > cap) ng.push('大型犬' + bigs.length + '頭と大人' + n.riders + '人（' + (cap ? '大人' + cap + '人まで' : '大人は乗れない') + '）'); }
    else if (n.riders + bigs.length >= 3) ask.push('大型犬' + bigs.length + '頭と大人' + n.riders + '人が一緒に乗れる');
    if (n.luggage) { if (pt.comboLug === false) ng.push('大型犬と大きな荷物'); else if (pt.comboLug == null && pt.luggage === true) ask.push('大型犬と多めの荷物を一緒に載せられる'); }
  } else if (n.pets >= 2 && pt.combo && pt.combo[0] !== null && pt.combo[0] !== undefined && n.riders > pt.combo[0]) {
    // 小さい子だけ：いちばん多い頭数のときの大人の人数を超えるときは、その頭数なら外し、少ない頭数なら確かめる
    if (pt.pets !== null && n.pets >= pt.pets) ng.push(n.pets + '匹と大人' + n.riders + '人');
    else ask.push(n.pets + '匹と大人' + n.riders + '人が一緒に乗れる');
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
    if (/どれでも/.test(c) && maxKg >= 20 && pt.cageLend !== false && pt.lendKg === null) ask.push('ケージを使う場合、' + maxKg + 'kgの子が入る大きさのケージを用意できる');
  }
  // 介護
  var careNeed = r['介助'] === '必要' || pets.some(function (p) { return p.care === '必要'; });
  if (careNeed) careChecks_(pt, pets, ng, ask);
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
  // ワクチン：申し込みの「ワクチンの証明」があればそれで（狂犬病だけ／狂犬病と混合）、なければ前の列「ワクチン必須」（混合）
  var dogs = pets.filter(function (p) { return /^犬$/.test(p.sp) || (!p.sp && !animalKind_(p)); });
  if (/狂犬病/.test(pt.vacProof)) {
    if (dogs.some(function (p) { return !p.rabies; })) ask.push('狂犬病の予防注射が記入されていない犬がいるが、乗れる（証明が必要な会社）');
    if (/混合/.test(pt.vacProof) && pets.some(function (p) { return !p.vac; })) ask.push('混合ワクチンの接種が記入されていない子がいるが、乗れる（証明が必要な会社）');
  } else if (/接種していれば/.test(pt.vacProof)) {
    if (pets.some(function (p) { return !p.vac; })) ask.push('混合ワクチンの接種が記入されていない子がいるが、乗れる');
  } else if (!pt.vacProof && pt.vacMust === true && pets.some(function (p) { return !p.vac; })) ask.push('混合ワクチンの接種が記入されていない子がいるが、乗れる');
  moreChecks_(pt, r, pets, n, ng, ask);
  return { ng: ng, ask: ask };
}

// 2026-11-10 追加の条件（提携の申し込みの答えで判定。分からない会社は確かめてもらう）
function moreChecks_(pt, r, pets, n, ng, ask) {
  var tri = function (v, what, ngText, askText) { if (v === false) ng.push(ngText); else if (v == null || v === undefined) ask.push(askText); };
  // お迎えの範囲：お店からお迎えの場所まで（直線）が範囲を超えたら外す。道のりより短く測るので、範囲ぎりぎりの依頼は外さない
  var from = (r._route || {}).from;
  if (pt.radiusKm && pt.shopLL && from && isFinite(from.lat) && isFinite(from.lng)) {
    var dk = kmBetween_(pt.shopLL, from);
    if (dk > pt.radiusKm) ng.push('お迎えの場所がお店から' + Math.round(dk) + 'km（' + pt.radiusKm + 'kmまで）');
  }
  // 行き先までの距離
  var km = Number(r['概算km']) || Number(((r._route || {}).km)) || 0;
  if (pt.destKm && km > pt.destKm) ng.push('乗る距離 ' + Math.round(km) + 'km（' + pt.destKm + 'kmまで）');
  if (/都道府県の中だけ/.test(pt.destScope || '')) {
    var to = prefIn_(r['行き先']);
    if (to && to !== r['都府県']) ng.push('行き先が' + to + '（お迎えの都道府県の中だけ）');
    else if (!to && km > 40) ask.push('行き先（' + Math.round(km) + 'km先）まで行ける');
  }
  // 途中で寄る
  if (String(r['経由地'] || '').trim()) tri(pt.via, '', '途中で寄る', '途中で寄れる（' + clip_(r['経由地'], 40) + '）');
}

// 介護：お客さまが選んだ「どんな手助けが必要ですか？」と、会社の「介護でできること」「運べる体重」「人数」「道具」をくらべる
// 受けられない会社は外す。できることがそろっている会社は確かめない（2026-11-10。前は介護の依頼はいつも確かめていた）
function careChecks_(pt, pets, ng, ask) {
  if (pt.careTri === false) { ng.push('介護が必要な子'); return; }
  var cared = pets.filter(function (p) { return p.care === '必要'; });
  if (!cared.length) cared = pets;
  // 新しい申し込みは「介護が必要な大型犬を運べるか」だけで決める。小さい子は飼い主さんが抱っこできるので問わない（Nori 2026-11-10）
  if (pt.careBigSet) {
    var bigCare = cared.filter(function (p) { return p.kg >= CONFIG.LARGE_DOG_KG; });
    if (bigCare.length && pt.careBig === false) ng.push('介護が必要な大型犬（' + CONFIG.LARGE_DOG_KG + 'kg以上）');
    else if (bigCare.length && pt.careBig === null) ask.push('介護が必要な大型犬（' + Math.max.apply(null, bigCare.map(function (p) { return p.kg; })) + 'kg）を運べる');
    else if (pt.careTri === null) ask.push('介護が必要な子の送迎ができる');
    return;
  }
  var needs = [].concat.apply([], cared.map(function (p) { return p.needList || []; })).filter(function (x, i, a) { return a.indexOf(x) === i; });
  var notes = [].concat.apply([], cared.map(function (p) { return (p.need || []).filter(function (x) { return (p.needList || []).indexOf(x) < 0; }); }));
  var maxKg = Math.max.apply(null, cared.map(function (p) { return p.kg; }));
  var lift = needs.some(function (x) { return /歩けない|寝たきり|階段/.test(x); });
  if (!pt.careCan) { // 申し込みの答えがない会社（前からの会社）は、いままでどおり確かめる
    ask.push('介護が必要な子の送迎' + (needs.concat(notes).length ? '（' + needs.concat(notes).join('／') + '）' : '') + 'ができる');
    return;
  }
  var miss = needs.filter(function (x) { return pt.careCan.indexOf(x) < 0; });
  if (miss.length) ask.push('介護が必要な子の送迎（' + miss.join('／') + '）ができる');
  if (lift && pt.careKg !== null && pt.careKg !== undefined && maxKg > pt.careKg) ng.push(maxKg + 'kgの子を抱えて・担架で運ぶ（' + pt.careKg + 'kgまで）');
  else if (lift && maxKg >= CONFIG.LARGE_DOG_KG && pt.careStaff === 1 && !pt.careStaffMore) ask.push(maxKg + 'kgの子を1人で抱えて・担架で運べる');
  var tools = pt.careTools || '';
  if (tools) {
    if (needs.some(function (x) { return /寝たきり/.test(x); }) && !/ストレッチャー|マット/.test(tools)) ask.push('寝たきりの子を運ぶ担架やマットを用意できる');
    if (needs.some(function (x) { return /酸素|点滴/.test(x); }) && !/酸素/.test(tools)) ask.push('酸素ボンベや点滴を車に置ける・固定できる');
    if (needs.some(function (x) { return /カート|バギー/.test(x); }) && !/スロープ|カート/.test(tools)) ask.push('カートやバギーごと乗れる');
  }
  if (notes.length) ask.push('介護のくわしいこと（' + notes.join('／') + '）に合わせられる');
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
    if (q.a === 'withdraw') return withdrawPage_(q);
    if (q.a === 'pcancel') return partnerCancelPage_(q);
    if (q.a === 'ride') return ridePage_(q);
    if (q.a === 'admin') return adminPage_(q);
    if (q.a === 'prefill') return prefill_(q);
    if (q.a === 'dash') return dashPage_(q);
    if (q.a === 'agree') return agreePage_(q);
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
    var at = replyAt_(r, q);
    var way = retWayOf_(q.ret_way);
    var asks = checks_(pt, r).ask;
    if (asks.some(function (x, i) { return q['ok' + i] !== '1'; })) return page_('確認が終わっていません', '<p>「引き受ける前にご確認ください」の項目に、すべてチェックを入れてください。できない項目があるときは、お受けにならないでください。</p><p><a href="javascript:history.back()">戻る</a></p>');
    var ct = replyContact_(q, pt);
    if (ct.err) return page_('連絡先を確かめてください', '<p>' + esc_(ct.err) + '</p><p><a href="javascript:history.back()">戻る</a></p>');
    if (!fare || !at || (isRound_(r) && !way)) return page_('入力が足りません', '<p>' + (r['日付のみ'] ? 'お迎え時刻・' : '') + '確定料金（円）' + (isRound_(r) ? '・帰りのやり方' : '') + 'を入れてください。</p><p><a href="javascript:history.back()">戻る</a></p>');
    if (needsChoice_(r) && at.getTime() - CONFIG.QUOTE_CUTOFF_MIN * 60000 <= Date.now()) return page_('お迎えが近すぎます', '<p>お迎えの' + cutoffText_() + '前を過ぎるお返事は、お客さまが予約を確定できないため、お送りできません。お迎えの時刻を確かめてください。</p><p><a href="javascript:history.back()">戻る</a></p>');
    if (needsChoice_(r)) {
      var qr = quote_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way, ct);
      if (!qr.ok) return page_('締め切りました', '<p>' + esc_(qr.msg) + '</p>');
      if (isAsk_(r)) return page_('お返事を送りました', '<p>お客さまに、空き状況（お迎え時刻）と確定料金をお届けしました。<b>お客さまが「予約する」を押したら、お名前・ご連絡先をメールでお知らせします。</b>予約にならなかったときは「締め切り」のお知らせをお送りします。</p><p>このお返事は' + CONFIG.QUOTE_VALID_HOURS + '時間（お迎えの' + cutoffText_() + '前まで）有効です。そのあいだに予約が確定したときは、お引き受けください。</p>' + withdrawNote_(q.id, pt.id));
      return page_(isQuoteReq_(r) ? 'お見積もりを送りました' : '引き受けのお返事を送りました', '<p>お客さまに' + (isQuoteReq_(r) ? 'お見積もり' : '引き受けのお返事と確定料金') + 'をお届けしました。<b>お客さまが貴社を選んだら、お名前・ご連絡先をメールでお知らせします。</b>選ばれなかったときは「締め切り」のお知らせをお送りします。</p>');
    }
    var res = accept_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way, ct);
    if (!res.ok) return page_('締め切りました', '<p>' + esc_(res.msg) + '</p>');
    var c = res.r;
    return page_('ありがとうございます！決まりました', '<p>お客さまに「決まりました」とお知らせしました。<b>お客さまへ直接ご連絡をお願いします。</b>この画面の内容を控えておいてください。</p>' +
      '<div class="box">' + nl2br_(esc_(customerForPartner_(c))) + '</div>');
  }

  if (r['状態'] === ST.DONE && r['決定した提携先ID'] === pt.id) {
    return page_('あなたに決まっています', '<p>お客さまへ直接ご連絡をお願いします。</p><div class="box">' + nl2br_(esc_(customerForPartner_(r))) + '</div>' +
      '<p class="note">やむを得ずお受けできなくなったときは、<a href="' + esc_(partnerCancelUrl_(q.id, pt.id)) + '" target="_top">こちら</a>から取り消してください。お客さまにお知らせします。</p>');
  }
  if (r['状態'] !== ST.OPEN) return page_('締め切りました', '<p>このご依頼は締め切りました。ご確認ありがとうございました。</p>');
  var quoted = needsChoice_(r) && quotesOf_(r).filter(function (x) { return x.pid === pt.id; })[0];
  if (quoted && quoted.withdrawn) return page_('お返事は取り下げ済みです', '<p>このお問い合わせへのお返事は取り下げました。お客さまには、この内容では予約できないことをお知らせしています。</p>');
  if (quoted) return page_(isQuoteReq_(r) ? 'お見積もりをお送り済みです' : 'お返事をお送り済みです', '<p>確定料金 ' + esc_(fareText_(quoted.fare, quoted.fareHw)) + '・お迎え予定 ' + esc_(fmt_(new Date(quoted.at))) + ' でお客さまにお届けしています。お客さまが' + (isAsk_(r) ? '予約を決めたら' : '選んだら') + 'お知らせします。</p>' + withdrawNote_(q.id, pt.id));
  var def = defaultAt_(r);
  var html = '<p>' + esc_(pt.name) + ' 様</p>' +
    (isAsk_(r) ? '<div class="box"><b>空き状況と料金のお問い合わせです' + (pickedIds_(r).length > 1 ? '（お客さまが' + pickedIds_(r).length + '社にお声がけしています）' : '') + '。</b>お受けできる場合は、' + inputWord_(r) + 'を入れてください。お客さまが内容を見て「予約する」を押した時点で決まり、お名前・ご連絡先をお知らせします。</div>'
      : isQuoteReq_(r) ? '<div class="box"><b>お見積もりのご依頼です。</b>入れた確定料金をお客さまにお届けし、お客さまがほかの会社とくらべて1社を選びます。選ばれたら、お名前・ご連絡先をお知らせします。</div>'
      : needsChoice_(r) ? '<div class="box"><b>お客さまが' + pickedIds_(r).length + '社にお声がけしています。</b>引き受ける場合は確定料金を入れてください。お客さまが引き受けた会社の中から1社を選んだ時点で決まり、お名前・ご連絡先をお知らせします。</div>'
      : '<div class="box"><b>お客さまのお名前・電話番号・メールは、下の「引き受ける」を押すとすぐにこの画面に表示されます。</b>同じ内容をメールでもお送りします。先着1社です。</div>') +
    '<h2 class="sec">📋 ご依頼の内容<span class="tag">お客さまの希望・変えられません</span></h2>' +
    '<div class="fixed"><div class="when">🕙 ' + esc_(whenText_(r)) + '</div>' +
    nl2br_(esc_(rideText_(r).replace(/^■ 希望日時：[^\n]*\n?/, '') + retAsk_(r) + waitRuleForPartner_(r) + '\n■ お支払い：' + payForPartner_(pt))) + '</div>' +
    (r['日付のみ'] ? '' : '<p class="note">この日時でお受けできないときは、お返事しないでください（日時は変えられません）。</p>') +
    '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' +
    hidden_('a', 'accept') + hidden_('id', q.id) + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') +
    '<h2 class="sec">✏️ 貴社に入れていただくこと</h2>' +
    askBoxes_(pt, r) +
    (r['日付のみ'] ? '<label>お迎え予定の時刻（' + esc_(whenText_(r).replace(/ 時間はご相談$/, '')) + '）<input type="time" name="t" value="' + def.slice(11) + '" required></label>' : '') +
    (isRound_(r) ? retSelect_() : '') +
    '<label>確定料金・一般道で行く場合（円・税込' + (isRound_(r) ? '、往復の合計' : '') + '）<input type="number" name="fare" inputmode="numeric" min="0" step="10" placeholder="例：4800" required></label>' +
    '<label>確定料金・高速道路を使う場合（円・税込、高速代込み）<input type="number" name="fare_hw" inputmode="numeric" min="0" step="10" placeholder="高速を使わないなら空欄"></label>' +
    '<p class="note">入れた金額を、お客さまに確定の料金としてお伝えします。</p>' +
    '<label>お客さまからの連絡を受ける電話番号<input type="tel" name="ctel" inputmode="tel" autocomplete="tel" value="' + esc_(pt.tel || '') + '" placeholder="例：090-1234-5678"></label>' +
    '<label>お客さまからの連絡を受けるメールアドレス<input type="email" name="cmail" autocomplete="email" value="' + esc_(pt.email || '') + '" placeholder="例：info@example.jp"></label>' +
    '<p class="note">予約が決まったら、この電話番号とメールアドレスをお客さまにお伝えします（どちらか一つでも大丈夫です）。登録の内容が入っています。違うときは書きかえてください。</p>' +
    '<label>お客さまへ一言（なくてもOK。往復で待つときは、待機料の単価を書いていただくとお客さまに伝わります）<textarea name="msg" maxlength="300" placeholder="例：前日にお電話します／待機料は10分ごとに300円です"></textarea></label>' +
    '<button type="submit">' + (isAsk_(r) ? 'この内容でお返事する' : isQuoteReq_(r) ? 'この内容でお見積もりを送る' : 'この内容で引き受ける') + '</button></form>' +
    '';
  return page_(isAsk_(r) ? '空き状況と料金をお返事しますか？' : isQuoteReq_(r) ? 'お見積もりを出しますか？' : 'ご依頼を引き受けますか？', html);
}

// 引き受け画面のチェック欄（すべてにチェックしないと引き受けられない）
function askBoxes_(pt, r) {
  var a = checks_(pt, r).ask;
  if (!a.length) return '';
  return '<div class="box"><b>引き受ける前にご確認ください</b>（できない項目があるときは、お受けにならないでください）' +
    a.map(function (x, i) { return '<label style="display:flex;gap:8px;align-items:flex-start;font-weight:400"><input type="checkbox" name="ok' + i + '" value="1" required style="width:auto;margin-top:4px"> ' + esc_(x) + '</label>'; }).join('') + '</div>';
}

function accept_(id, pt, at, fare, msg, fareHw, retWay, contact) {
  fareHw = fareHw || '';
  contact = contact || {};
  var cpt = custPt_(pt, contact.tel, contact.mail);
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
    ensureReqHeaders_(sheet_(SHEET_REQ));
    setReq_(row.rowIndex, {
      '会社の連絡先（電話）': contact.tel || '', '会社の連絡先（メール）': contact.mail || '',
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
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】ご予約が確定しました（受付番号 ' + id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\nペットタクシーのご予約が確定しました！\n\n' +
    '■ ペットタクシー：' + pt.name + '\n' +
    '■ お迎え予定：' + fmt_(at) + '\n' +
    '■ 料金（確定・税込）：' + fareText_(fare, fareHw) + '\n' +
    '　※' + changeNote_(pt) + 'くわしくは会社にご確認ください。\n' + waitRuleForCustomer_(r, pt) +
    (retWay ? '■ 帰りのやり方：' + retWay + '（料金が安くなるほうをペットタクシーに選んでもらいました）\n' : '') +
    '■ お支払い：' + payForCustomer_(pt) + '\n' +
    (msg ? '■ ペットタクシーから：' + msg + '\n' : '') +
    partnerContactText_(cpt) +
    '\nこのあと「' + pt.name + '」から、ご連絡先あてに直接ご連絡があります。ペットの様子などのご質問も、ペットタクシーと直接やりとりしてください。領収書が必要なときも、ペットタクシーにお申し出ください。\n' +
    'お迎えの時刻が近づいても連絡がない・遅れているときは、まず「' + pt.name + '」へご連絡ください。つながらないときは、このメールに返信してください。\n' +
    '送迎のご契約は、お客さまと「' + pt.name + '」との間で結ばれます（当サイトは送迎を行わず、契約の当事者ではありません）。\n\n' +
    '▼ 取り消す場合はこちら\n' + cancelUrl + '\n' + cancelAfterText_(pt) + 'お迎えの3時間前を過ぎてから取り消すときは、このリンクを押す前に「' + pt.name + '」へ直接ご連絡ください。', confirmHtml_(r, cpt, at, fare, fareHw, retWay, msg, cancelUrl));
  var how = deliver_(pt, '【決定】' + id + ' お客さまのご連絡先', decidedText_(r, pt), r, decidedHtml_(r, pt));
  closeOthers_(r, pt.id);
  notifyAdmin_((how === 'manual' ? '【LINEで決定を伝えてください】' : '') + '決定 ' + id + '：' + pt.name,
    (how === 'manual' ? pt.name + 'はLINE公式アカウントだけの会社です。手配ページの「決定をLINEで伝える」を押してください（お客さまの連絡先が入った文面です）。\n\n' : '') +
    '■ ' + pt.name + '\n■ お迎え予定：' + fmt_(at) + '\n■ 確定料金：' + fareText_(fare, fareHw) + '\n\n' + rideText_(r) + '\n\n▼ 手配ページ\n' + adminUrl_(id));
  return { ok: true, r: r };
}

/* ───────── 見積もり依頼（2026-10-31 Nori「見積もり依頼か予約依頼かはユーザに選択できるように」） ───────── */

// 会社のお見積もりを受け取り、お客さまに「この会社に決める」リンクつきでお届けする。お客さまの連絡先はまだ渡さない
function quote_(id, pt, at, fare, msg, fareHw, retWay, contact) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var r;
  try {
    var row = findReq_(id);
    if (!row || row.data['状態'] !== ST.OPEN) return { ok: false, msg: 'このご依頼は締め切りました。ご確認ありがとうございました。' };
    if (pickedIds_(row.data).indexOf(pt.id) < 0) return { ok: false, msg: 'お客さまが選んだ会社と異なるため、お見積もりを出せません。' };
    var list = quotesOf_(row.data).filter(function (x) { return x.pid !== pt.id; });
    var mine = { pid: pt.id, at: at.getTime(), fare: fare, fareHw: fareHw || '', way: retWay || '', msg: msg || '', time: Date.now(), tel: (contact && contact.tel) || '', mail: (contact && contact.mail) || '' };
    list.push(mine);
    setReq_(row.rowIndex, { '見積もりJSON': JSON.stringify(list) });
    SpreadsheetApp.flush();
    r = findReq_(id).data;
  } finally {
    lock.releaseLock();
  }
  log_(id + ' 見積もり: ' + pt.id + ' ' + fare);
  var word = isAsk_(r) ? '空き状況と料金のお返事' : isQuoteReq_(r) ? 'お見積もり' : '引き受けのお返事';
  var many = pickedIds_(r).length > 1;
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】' + word + 'が届きました：' + pt.name + '（受付番号 ' + id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\n「' + pt.name + '」から' + word + 'が届きました。' + (isAsk_(r) ? '下のお迎え予定の時刻で空いています。\n※まだ予約は確定していません。内容に納得できたら、下のリンクから「この内容で予約する」を押してください。\n\n' : 'まだ予約は決まっていません。\n\n') +
    '■ ペットタクシー：' + pt.name + '\n■ お迎え予定：' + fmt_(at) + '\n■ 料金（確定・税込）：' + fareText_(fare, fareHw) + '\n' +
    '　※' + changeNote_(pt) + 'くわしくは会社にご確認ください。\n' + waitRuleForCustomer_(r, pt) +
    (retWay ? '■ 帰りのやり方：' + retWay + '\n' : '') + '■ お支払い：' + payForCustomer_(pt) + '\n' + '■ 予約したあとのキャンセル：' + cancelRuleText_(pt) + '\n' + (msg ? '■ ペットタクシーから：' + msg + '\n' : '') +
    '■ この内容で予約できる期限：' + fmt_(new Date(quoteUntil_(mine))) + 'まで（過ぎると会社の空き状況が変わるため、この内容では予約できません）\n' +
    (isAsk_(r) ? '\n▼ この内容で予約する（押すと予約が確定し、この会社からご連絡があります）\n' : '\n▼ この会社に決める（押すと予約が決まり、この会社からご連絡があります）\n') + chooseUrl_(id, pt.id) +
    '\n\n' + (!isAsk_(r) || many ? 'ほかの会社の' + word + 'も、届きしだいお送りします。くらべてから決めてかまいません。' : '') +
    (isAsk_(r) ? '予約しない場合は、何もしなくて大丈夫です（下のリンクで取り消すこともできます）。\n' : 'どの会社にも決めない場合は、何もしなくて大丈夫です（下のリンクで取り消すこともできます）。\n') + cancelUrl_(id), quoteHtml_(r, pt, at, fare, fareHw, retWay, msg, mine, word, many));
  notifyAdmin_(word + ' ' + id + '：' + pt.name, '■ ' + pt.name + '\n■ お迎え予定：' + fmt_(at) + '\n■ 確定料金：' + fareText_(fare, fareHw) + '\n\n' + rideText_(r));
  return { ok: true };
}

// 会社がお返事を取り下げるリンク（Nori 2026-11-08：お返事のあとにほかの予約が入ったとき）
function withdrawUrl_(id, pid) { return linkBase_() + '?a=withdraw&id=' + encodeURIComponent(id) + '&p=' + encodeURIComponent(pid) + '&k=' + sign_(id + ':' + pid + ':withdraw'); }
function withdrawNote_(id, pid) {
  return '<p class="note">お返事のあとにほかのご予約が入って受けられなくなったときは、お客さまが予約する前に <a href="' + esc_(withdrawUrl_(id, pid)) + '" target="_top">このお返事を取り下げる</a> を押してください。お客さまはこの内容では予約できなくなります。このリンクは、お問い合わせのメールの「お返事する」リンクを開くといつでも出ます。</p>';
}
function withdrawPage_(q) {
  if (!q.id || !q.p || q.k !== sign_(q.id + ':' + q.p + ':withdraw')) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var pt = partnerById_(q.p);
  if (!pt) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  if (q.go !== '1') {
    var row0 = findReq_(q.id);
    if (!row0) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
    return page_('お返事を取り下げますか？', '<p>押すと、お客さまはこのお返事の内容では予約できなくなります。お客さまには、ほかのご予約が入ったためとお知らせします。</p>' +
      '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'withdraw') + hidden_('id', q.id) + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') +
      '<button type="submit">お返事を取り下げる</button></form>');
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var r;
  try {
    var row = findReq_(q.id);
    if (!row) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
    r = row.data;
    if (r['状態'] === ST.DONE && r['決定した提携先ID'] === pt.id) return page_('すでに予約が確定しています', '<p>お客さまが先に予約を確定しました。受けられない場合は、<a href="' + esc_(partnerCancelUrl_(q.id, pt.id)) + '" target="_top">こちら</a>から取り消してください。お客さまにお知らせします。</p>');
    if (r['状態'] !== ST.OPEN) return page_('締め切りました', '<p>このご依頼はもう締め切られています。取り下げは必要ありません。</p>');
    var list = quotesOf_(r), mine = list.filter(function (x) { return x.pid === pt.id; })[0];
    if (!mine) return page_('お返事が見つかりません', '<p>このお問い合わせへのお返事はまだありません。</p>');
    if (mine.withdrawn) return page_('取り下げ済みです', '<p>このお返事は、もう取り下げています。</p>');
    mine.withdrawn = Date.now();
    setReq_(row.rowIndex, { '見積もりJSON': JSON.stringify(list) });
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
  log_(q.id + ' 取り下げ: ' + pt.id);
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】' + pt.name + 'のお返事が取り下げられました（受付番号 ' + q.id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\n「' + pt.name + '」から、ほかのご予約が入ったため、さきほどのお返事を取り下げるとの連絡がありました。このお返事の内容では予約できません。申し訳ありません。\n\n' +
    (quotesOf_(findReq_(q.id).data).some(function (x) { return x.pid !== pt.id && !x.withdrawn; }) ? 'ほかの会社からのお返事は、そのままご予約いただけます。届いたメールをご確認ください。\n' : 'お手数ですが、同じ内容でもう一度お問い合わせいただけます。\n' + retryUrl_(q.id) + '\n'));
  notifyAdmin_('取り下げ ' + q.id + '：' + pt.name, pt.name + 'がお返事を取り下げました。\n\n' + rideText_(r));
  return page_('お返事を取り下げました', '<p>お客さまに、この内容では予約できないことをお知らせしました。ご連絡ありがとうございました。</p>');
}
// 予約が確定したあとで、会社がやむを得ず受けられなくなったとき（Nori 2026-11-08「破綻しないか」）
function partnerCancelUrl_(id, pid) { return linkBase_() + '?a=pcancel&id=' + encodeURIComponent(id) + '&p=' + encodeURIComponent(pid) + '&k=' + sign_(id + ':' + pid + ':pcancel'); }
function partnerCancelPage_(q) {
  if (!q.id || !q.p || q.k !== sign_(q.id + ':' + q.p + ':pcancel')) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var pt = partnerById_(q.p), row0 = findReq_(q.id);
  if (!pt || !row0) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  if (row0.data['状態'] !== ST.DONE || row0.data['決定した提携先ID'] !== pt.id) return page_('取り消しは必要ありません', '<p>このご予約は、いま貴社に決まっていません（お客さまが取り消したか、受付が終わっています）。</p>');
  if (q.go !== '1') {
    return page_('このご予約を取り消しますか？', '<div class="box">' + nl2br_(esc_('受付番号：' + q.id + '\nお迎え予定：' + fmt_(row0.data['お迎え予定']) + '\nお客さま：' + row0.data['お名前'] + ' 様')) + '</div>' +
      '<p>押すと、お客さまに「ペットタクシーの都合でお受けできなくなりました」とお知らせし、このご予約は取り消しになります。お客さまにすでにご連絡している場合も、念のためお知らせします。</p>' +
      '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'pcancel') + hidden_('id', q.id) + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') +
      '<button type="submit" class="gray">このご予約を取り消す</button></form>');
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var row = findReq_(q.id);
    if (row.data['状態'] !== ST.DONE || row.data['決定した提携先ID'] !== pt.id) return page_('取り消しは必要ありません', '<p>このご予約は、いま貴社に決まっていません。</p>');
    setReq_(row.rowIndex, { '状態': ST.CANCEL, '終了日時': new Date() });
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
  var r = findReq_(q.id).data;
  log_(q.id + ' 会社の都合で取り消し: ' + pt.id);
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】ご予約をお受けできなくなりました（受付番号 ' + q.id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\n申し訳ありません。「' + pt.name + '」から、やむを得ない事情で ' + fmt_(r['お迎え予定']) + ' のご予約をお受けできなくなったと連絡がありました。このご予約は取り消しになりました。キャンセル料はかかりません。\n\nお手数ですが、同じ内容でほかの会社に問い合わせる場合は、こちらからどうぞ。\n' + retryUrl_(q.id));
  notifyAdmin_('【会社の都合で取り消し】' + q.id + '：' + pt.name, pt.name + 'が確定後に取り消しました。お客さまに連絡が届いているか、必要なら確かめてください。\n\n' + rideText_(r));
  return page_('ご予約を取り消しました', '<p>お客さまにお知らせしました。ご連絡ありがとうございました。</p>');
}
function chooseUrl_(id, pid) { return linkBase_() + '?a=choose&id=' + encodeURIComponent(id) + '&p=' + encodeURIComponent(pid) + '&k=' + sign_(id + ':' + pid + ':choose'); }

// お客さまが見積もりの中から1社に決めるページ
function choosePage_(q) {
  if (!q.id || !q.p || q.k !== sign_(q.id + ':' + q.p + ':choose')) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var row = findReq_(q.id), pt = partnerById_(q.p);
  if (!row || !pt) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  var r = row.data, qt = quotesOf_(r).filter(function (x) { return x.pid === pt.id; })[0];
  if (r['状態'] === ST.DONE) return page_(r['決定した提携先ID'] === pt.id ? (isAsk_(r) ? 'ご予約は確定しています' : 'この会社に決まっています') : 'ほかの会社に決まっています', '<p>' + esc_(r['決定した提携先'] || '') + 'に決まっています。決定のメールをご確認ください。</p>');
  if (r['状態'] !== ST.OPEN || !qt) return page_('締め切りました', '<p>このご依頼は締め切りました。</p>');
  if (qt.withdrawn) return page_('このお返事は取り下げられました', '<p>「' + esc_(pt.name) + '」は、ほかのご予約が入ったため、このお返事を取り下げました。この内容では予約できません。</p><p>お手数ですが、<a href="' + esc_(retryUrl_(q.id)) + '" target="_top">同じ内容でもう一度問い合わせる</a>からお問い合わせください。</p>');
  if (Date.now() > quoteUntil_(qt)) return page_('お返事の期限が過ぎました', '<p>「' + esc_(pt.name) + '」のお返事で予約できる期限（' + esc_(fmt_(new Date(quoteUntil_(qt)))) + '）が過ぎました。会社の空き状況が変わっている場合があるため、この内容では予約できません。</p><p>お手数ですが、<a href="' + esc_(retryUrl_(q.id)) + '" target="_top">同じ内容でもう一度問い合わせる</a>からお問い合わせください。</p>');
  if (q.go === '1') {
    var res = accept_(q.id, pt, new Date(qt.at), qt.fare, qt.msg, qt.fareHw, qt.way, { tel: qt.tel, mail: qt.mail });
    if (!res.ok) return page_('決められませんでした', '<p>' + esc_(res.msg) + '</p>');
    return page_(isAsk_(r) ? 'ご予約が確定しました' : '決まりました', '<p>「' + esc_(pt.name) + '」' + (isAsk_(r) ? 'のご予約が確定しました。確定のメールをお送りしました。' : 'に決まりました。決定のメールをお送りしました。') + 'このあと、' + esc_(pt.name) + 'からご連絡があります。</p>');
  }
  return page_(isAsk_(r) ? 'この内容で予約しますか？' : 'この会社に決めますか？', '<div class="box">■ ペットタクシー：' + esc_(pt.name) + '<br>■ お迎え予定：' + esc_(fmt_(new Date(qt.at))) + '<br>■ 料金（確定・税込）：' + esc_(fareText_(qt.fare, qt.fareHw)) + '<br>　※' + esc_(changeNote_(pt)) +
    (qt.way ? '<br>■ 帰りのやり方：' + esc_(qt.way) : '') + '<br>■ お支払い：' + esc_(payForCustomer_(pt)) + '<br>■ 予約したあとのキャンセル：' + esc_(cancelRuleText_(pt)) + '<br>■ 予約できる期限：' + esc_(fmt_(new Date(quoteUntil_(qt)))) + 'まで</div>' +
    '<p>' + (isAsk_(r) ? '押すと予約が確定し、' + esc_(pt.name) + 'にお名前・ご連絡先をお知らせします。' + (pickedIds_(r).length > 1 ? 'ほかの会社へのお問い合わせは締め切ります。' : '') : '決めると、ほかの会社へのご依頼は締め切ります。') + '</p>' +
    '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'choose') + hidden_('id', q.id) + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') +
    '<button type="submit">' + (isAsk_(r) ? 'この内容で予約する' : 'この会社に決める') + '</button></form>');
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
      // お客さまがあとで決める依頼は、会社の返事をお客さまに届けるだけ（決めるのはお客さま。Nori 2026-11-01）
      var res = needsChoice_(row.data) ? quote_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way) : accept_(q.id, pt, at, fare, clip_(q.msg, 300), yenNum_(q.fare_hw), way);
      notice = '<p class="note"><b>' + esc_(res.ok ? (needsChoice_(row.data) ? 'お客さまに空き状況と料金を送りました。お客さまが「予約する」を押すと決まります。' : '決定しました。お客さまへお知らせを送りました。') : res.msg) + '</b></p>';
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
      html += needsChoice_(r) ? '<h2>返信で答えてきた会社の空き状況と料金をお客さまに送る</h2><p class="note">リンクから入力してもらえた場合は自動で届くので、ここは不要です。決めるのはお客さまです。</p>' :
        '<h2>返信で答えてきた会社に決める</h2><p class="note">リンクから入力してもらえた場合は自動で決まるので、ここは不要です。</p>';
      html += '' +
        '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'admin') + hidden_('id', q.id) + hidden_('k', q.k) + hidden_('go', '1') +
        '<label>会社<select name="p" required>' + asked.map(function (pt) { return '<option value="' + esc_(pt.id) + '">' + esc_(pt.name) + '</option>'; }).join('') + '</select></label>' +
        '<label>お迎え予定の時刻<input type="datetime-local" name="at" value="' + def + '" required></label>' +
        (isRound_(r) ? retSelect_() : '') +
        '<label>確定料金・一般道（円・税込）<input type="number" name="fare" inputmode="numeric" min="0" step="10" required></label>' +
        '<label>確定料金・高速を使う場合（円・税込、なければ空欄）<input type="number" name="fare_hw" inputmode="numeric" min="0" step="10"></label>' +
        '<label>会社からの一言（なくてもOK）<textarea name="msg" maxlength="300"></textarea></label>' +
        '<button type="submit">' + (needsChoice_(r) ? 'この内容をお客さまに送る' : 'この会社に決めて、お客さまに知らせる') + '</button></form>';
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
    var cpt = decidedPt_(r);
    warn = '<p class="note">ペットタクシー「' + esc_(r['決定した提携先']) + '」に決まっています。取り消すと、こちらからペットタクシーへお伝えします。' +
      (cpt ? '<br>' + esc_(cancelAfterText_(cpt)) : '') +
      (left < 3 ? '<br><b>お迎えの3時間前を過ぎています。押す前に、ペットタクシーへ直接ご連絡ください。</b>' + (cpt ? '<br>' + esc_(partnerContactText_(cpt).replace(/^■ /, '').trim()) : '') : '') + '</p>';
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
  var pt = before === ST.DONE ? partnerById_(r['決定した提携先ID']) : null;
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】ご依頼を取り消しました（受付番号 ' + id + '）',
    r['お名前'] + ' 様\n\nご依頼を取り消しました。\n希望日時：' + whenText_(r) + '\n' +
    (pt ? '\n' + cancelAfterText_(pt) + '\n' + partnerContactText_(decidedPt_(r)) : '') +
    '\nまたいつでもご利用ください。\n' + CONFIG.SITE_URL);
  if (before === ST.DONE) {
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

/* ───────── 古い個人情報を消す（1日1回。個人情報の取り扱い「お迎えの日から1年」） ───────── */

var PERSONAL_REQ_COLS = ['お名前', '電話番号', 'メール', '連絡方法', 'メモ', 'お迎えの場所', '行き先', '経由地', '帰りのお迎え', '帰りの行き先', 'お客さまLINE'];
var PERSONAL_CONTACT_COLS = ['お名前', 'メール', '内容'];
var PURGED = '（削除済み）';

// 消してよい行か：基準の日（お迎え予定→希望日時→帰りの日時→受付日時のいちばん遅い日）から days 日たっている
function purgeDue_(r, now, days) {
  var t = ['お迎え予定', '希望日時', '帰りの日時', '受付日時'].map(function (k) { var d = r[k] ? new Date(r[k]).getTime() : NaN; return isNaN(d) ? 0 : d; });
  var base = Math.max.apply(null, t);
  return base > 0 && now - base > days * 86400000;
}

function purgeSheet_(sh, cols, now, days) {
  if (!sh) return 0;
  var rng = sh.getDataRange(), vals = rng.getValues(), h = vals[0], n = 0;
  var idx = cols.map(function (c) { return h.indexOf(c); }).filter(function (i) { return i >= 0; });
  for (var i = 1; i < vals.length; i++) {
    var r = toObj_(h, vals[i]);
    if (!purgeDue_(r, now, days)) continue;
    var changed = false;
    idx.forEach(function (j) { if (vals[i][j] !== '' && vals[i][j] !== PURGED) { vals[i][j] = PURGED; changed = true; } });
    if (changed) { sh.getRange(i + 1, 1, 1, h.length).setValues([vals[i]]); n++; }
  }
  return n;
}

function purgeOldPersonal_() {
  var day = Utilities.formatDate(new Date(), TZ, 'yyyyMMdd'), props = PropertiesService.getScriptProperties();
  if (props.getProperty('purge_day') === day) return;
  props.setProperty('purge_day', day);
  var now = Date.now(), days = CONFIG.KEEP_PERSONAL_DAYS;
  var n = purgeSheet_(sheet_(SHEET_REQ), PERSONAL_REQ_COLS, now, days) + purgeSheet_(sheet_('問い合わせ'), PERSONAL_CONTACT_COLS, now, days);
  // 運営者あての通知（送信済み・受信箱とも）と、お客さまあてのメールの控えも、同じ期間をこえたらごみ箱へ（30日で消える）。トリガーは pettaxi のアカウントで動かす（ほかのアカウントで動かすとそのアカウントのメールが対象になる）
  var q = ['subject:"[運営]" older_than:' + days + 'd', 'in:sent subject:"【' + CONFIG.SERVICE_NAME + '】" older_than:' + days + 'd'];
  // 検索は記号を無視して広く当たるので、件名がこのしくみのメールの形で始まるスレッドだけにしぼる（「サイト運営について」など他人のメールは消さない）
  var mine = function (t) { var sub = String(t.getFirstMessageSubject() || ''); return sub.indexOf('[運営] ') === 0 || sub.indexOf('【' + CONFIG.SERVICE_NAME + '】') === 0; };
  q.forEach(function (s) { try { var th = GmailApp.search(s, 0, 100).filter(mine); if (th.length) GmailApp.moveThreadsToTrash(th); n += th.length; } catch (e) {} });
  if (n) log_('古い個人情報を消しました：' + n + '件');
}

/* ───────── 決まらないときの自動対応（5分ごとに実行） ───────── */

function checkPending() {
  try { purgeOldPersonal_(); } catch (err) { log_('個人情報の削除でエラー: ' + err); } // 1日1回だけ動く
  var sh = sheet_(SHEET_REQ);
  try { ensureReqHeaders_(sh); } catch (err) {} // 「送迎確認」の列を先に足しておく（足せなくても rideCheckDue_ が列のない行には送らない）
  var vals = sh.getDataRange().getValues();
  var h = vals[0];
  var now = Date.now();
  for (var i = 1; i < vals.length; i++) {
    var r = toObj_(h, vals[i]);
    if (rideCheckDue_(r, now)) { sendRideCheck_(r['受付番号']); continue; }
    if (r['状態'] !== ST.OPEN) continue;
    var age = openMinutes_(r['受付日時'], now, CONFIG.OPEN_HOURS); // 会社が動いている時間だけ数える
    var until = (new Date(r['希望日時']).getTime() - now) / 3600000;
    var today = Utilities.formatDate(new Date(), TZ, 'yyyyMMdd') === Utilities.formatDate(new Date(r['希望日時']), TZ, 'yyyyMMdd');
    var k = (r['日付のみ'] ? today : until < CONFIG.URGENT_HOURS) ? 0.5 : 1;
    // 見積もりが届いているあいだは、お客さまが選ぶのを待つ（お迎えの時刻を過ぎたら終わり）
    if (until < 0 || (age >= CONFIG.GIVE_UP_MIN * k && !(needsChoice_(r) && quotesOf_(r).filter(function (x) { return !x.withdrawn; }).length))) {
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
    (r['ペアの受付番号'] ? 'これは往復の' + legTag_(r).slice(1) + 'のご依頼です。もう片方（受付番号 ' + r['ペアの受付番号'] + '）は、そのまま続いています。取り消す場合は、そちらのメールのリンクからどうぞ。\n\n' : '') +
    '時間を少しずらすと見つかることがあります。下のリンクから開くと、前回の内容が入った状態になるので、日時だけ変えてもう一度お送りいただけます。\n' + retryUrl_(id));
  notifyAdmin_('見つからず ' + id, 'お客さまにお詫びを送りました。\n\n' + rideText_(r) + '\n\nお名前：' + r['お名前'] + '\n電話：' + r['電話番号']);
}

/* ───────── 送迎のあとの確認（飼い主さんに聞いて、会社の月末の申告と照らし合わせる） ───────── */

// 決まった予約で、お迎え予定から RIDE_CHECK_AFTER_HOURS たち、まだ聞いていない、いまが送ってよい時間帯
function rideCheckDue_(r, now) {
  if (!('送迎確認' in r) || r['状態'] !== ST.DONE || r['送迎確認'] || !r['メール']) return false; // 列がない古いシートでは送らない（同じメールをくり返さないため）
  var at = new Date(r['お迎え予定']).getTime();
  if (!isFinite(at) || now - at < CONFIG.RIDE_CHECK_AFTER_HOURS * 3600000) return false;
  if (now - at > 14 * 24 * 3600000) return false; // 古すぎる予約には聞かない
  return inHours_(Number(Utilities.formatDate(new Date(now), TZ, 'H')), hoursOf_(CONFIG.RIDE_CHECK_SEND_HOURS));
}

function rideUrl_(id) { return linkBase_() + '?a=ride&id=' + encodeURIComponent(id) + '&k=' + sign_(id + ':ride'); }

function sendRideCheck_(id) {
  var row = findReq_(id);
  if (!row || row.data['送迎確認']) return;
  setReq_(row.rowIndex, { '送迎確認': '確認中' });
  var r = row.data;
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】無事に送迎できましたか？（受付番号 ' + id + '）' + legTag_(r),
    r['お名前'] + ' 様\n\n先日はご利用ありがとうございました。\n' + fmt_(r['お迎え予定']) + ' の「' + r['決定した提携先'] + '」の送迎について、ひとつだけ教えてください。\n\n' +
    '▼ 送迎できたか・キャンセルしたかを答える（1回押すだけです）\n' + rideUrl_(id) + '\n\n' +
    'サービスをよくするため、また提携の会社との確認のために使います。お答えの内容が、お客さまと会社とのやり取りに影響することはありません。');
  log_(id + ' 送迎の確認を送った');
}

function ridePage_(q) {
  if (!q.id || q.k !== sign_(q.id + ':ride')) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var row = findReq_(q.id);
  if (!row) return page_('見つかりません', '<p>このご依頼は見つかりませんでした。</p>');
  var r = row.data;
  var ANS = { done: '送迎あり', cancel: 'キャンセル（お客さま回答）', other: '予定と違った（お客さま回答）' };
  if (q.go === '1' && ANS[q.ans]) {
    setReq_(row.rowIndex, { '送迎確認': ANS[q.ans], '送迎確認日時': new Date() });
    log_(q.id + ' 送迎の確認：' + ANS[q.ans]);
    if (q.ans !== 'done') notifyAdmin_('送迎の確認：' + ANS[q.ans] + ' ' + q.id, '飼い主さんの答え：' + ANS[q.ans] + '\n会社：' + r['決定した提携先'] + '\n\n' + rideText_(r));
    return page_('ありがとうございました', '<p>お答えを受け付けました。またいつでもご利用ください。</p>');
  }
  if (r['送迎確認'] && r['送迎確認'] !== '確認中') return page_('お答えいただいています', '<p>「' + esc_(r['送迎確認']) + '」で受け付けています。ありがとうございました。</p>');
  function btn(ans, label, gray) {
    return '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'ride') + hidden_('id', q.id) + hidden_('k', q.k) + hidden_('go', '1') + hidden_('ans', ans) +
      '<button type="submit"' + (gray ? ' class="gray"' : '') + '>' + esc_(label) + '</button></form>';
  }
  return page_('無事に送迎できましたか？', '<div class="box">' + nl2br_(esc_('受付番号：' + q.id + '\nペットタクシー：' + r['決定した提携先'] + '\nお迎え予定：' + fmt_(r['お迎え予定']))) + '</div>' +
    btn('done', 'はい、送迎してもらいました') + btn('cancel', 'キャンセルしました', true) + btn('other', '日時や内容が予定と違いました', true));
}

/* ───────── お客さまへのメール ───────── */

function sendReceipt_(r) {
  var lineNote = '';
  if (CONFIG.LINE_CHANNEL_ACCESS_TOKEN && CONFIG.LINE_ADD_URL) {
    lineNote = '\n\n▼ LINEでもお知らせを受け取れます\n友だち追加して、受付番号「' + r['受付番号'] + '」を送ってください。\n' + CONFIG.LINE_ADD_URL;
  }
  toCustomer_(r, '【' + CONFIG.SERVICE_NAME + '】' + (isAsk_(r) ? 'お問い合わせを受け付けました' : '受け付けました') + '（受付番号 ' + r['受付番号'] + '）' + legTag_(r),
    r['お名前'] + ' 様\n\nお問い合わせありがとうございます。受け付けました。\n' + (isAsk_(r) ? '※まだ予約は確定していません。\n\n選んだ会社「' + r['指定した提携先'] + '」に、この日時の空き状況と料金を問い合わせています。ほかの会社には問い合わせません。\n会社から空き状況と確定料金のお返事が届いたら、メールでお送りします' + (pickedIds_(r).length > 1 ? '（届くたびにお送りします）' : '') + '。内容に納得できたら、メールの「この内容で予約する」を押してください。押した時点で予約が確定します' + (pickedIds_(r).length > 1 ? '（ほかの会社へのお問い合わせは締め切ります）' : '') + '。\n\n'
      : isQuoteReq_(r) ? '選んだ会社「' + r['指定した提携先'] + '」にお見積もりを依頼しています。ほかの会社には依頼しません。お見積もりが届くたびにメールでお送りするので、料金をくらべて、決める会社のリンクを押してください。押すまで予約は決まりません。\n\n'
      : needsChoice_(r) ? '選んだ会社「' + r['指定した提携先'] + '」に空き状況を確認しています。ほかの会社には依頼しません。引き受けた会社から、お迎えの時間と確定料金が届くたびにメールでお送りするので、決める会社のリンクを押してください。押した時点で予約が決まり、ほかの会社への依頼は取り消します。\n\n'
      : (r['指定した提携先'] ? '選んだ会社「' + r['指定した提携先'] + '」に空き状況を確認しています。ほかの会社には依頼しません。' : 'いま、空いているペットタクシーを探しています。') + '引き受けが決まりしだい、お迎えの時間と確定料金をお送りします。\n\n') +
    '受付番号：' + r['受付番号'] + '\n' + rideText_(r) +
    (num_(r['概算料金']) ? '\n■ 料金の目安（概算）：' + estShown_(r) + '\n　※各社の公式サイトの料金表から計算した概算（100円単位）です。当日の道順などで変わります。確定料金は、問い合わせた会社の返事でお知らせします' : '') + lineNote +
    '\n\n▼ 取り消す場合はこちら（予約が確定する前ならいつでも無料です）\n' + cancelUrl_(r['受付番号']) +
    '\n\n※このメールは自動でお送りしています。');
}

function toCustomer_(r, subject, text, html) {
  if (r['メール']) mail_(r['メール'], subject, text + footer_(), html || '');
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
function deliver_(pt, subject, text, r, html) {
  if (r && isTest_(r)) {
    if (!pt.email && !pt.lineId && !pt.oaId && !pt.lineUrl) return false;
    var to = pt.email || (pt.lineId ? 'こちらのLINE' : 'LINE公式 ' + (pt.oaId || pt.lineUrl));
    return mail_(adminEmail_(), '【テスト｜本来は ' + pt.name + '（' + to + '）へ】' + subject, text + footer_(), html || '') ? 'auto' : false;
  }
  if (pt.lineId && CONFIG.LINE_CHANNEL_ACCESS_TOKEN && linePush_(pt.lineId, text)) return 'auto';
  if (pt.email && mail_(pt.email, '【' + CONFIG.SERVICE_NAME + '】' + subject, text + footer_(), html || '')) return 'auto';
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
  // メールの1日の上限が近いときは、お客さま・会社あてを先に残すため、運営者あての通知を止める（ログには残る）
  try { if (MailApp.getRemainingDailyQuota() < CONFIG.MAIL_RESERVE) { log_('上限が近いので運営者への通知を省略：' + subject); return; } } catch (e) {}
  mail_(adminEmail_(), '[運営] ' + subject, text + '\n\n予約シート：' + SpreadsheetApp.getActive().getUrl());
}

function mail_(to, subject, body, html) {
  try {
    var replyTo = CONFIG.REPLY_TO || CONFIG.FROM_EMAIL || adminEmail_();
    if (fromOk_()) {
      var opt = { from: CONFIG.FROM_EMAIL, name: CONFIG.SERVICE_NAME, replyTo: replyTo };
      if (html) opt.htmlBody = html;
      GmailApp.sendEmail(to, subject, body, opt);
    } else {
      var m = { to: to, subject: subject, body: body, name: CONFIG.SERVICE_NAME, replyTo: replyTo };
      if (html) m.htmlBody = html;
      MailApp.sendEmail(m);
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

/* ───────── 見た目のあるメール（Nori 2026-11-09「文字が多くてげんなり」「案にアップデートして・GASも」） ─────────
   文字だけの本文（body）はそのまま残し、メールアプリが対応していれば同じ内容を見やすい形（htmlBody）で見せる。
   書いてある内容・条件は文字だけの本文と同じ。カードに載せない細かい説明は、下に小さく残す。 */
var MAIL_C = { orange: '#EE6A1F', blue: '#2F6FA8', green: '#2E8B57', ink: '#1F2A37', sub: '#6B665F', bg: '#F3F1EE', note: '#FFF4EA', line: '#F0ECE6' };
function mh_(s) { return nl2br_(esc_(s)); }
function mailPage_(inner) {
  return '<!doctype html><html><body style="margin:0;padding:0;background:' + MAIL_C.bg + '">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:' + MAIL_C.bg + '"><tr><td align="center" style="padding:16px 12px">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;font-family:-apple-system,\'Hiragino Sans\',\'Noto Sans JP\',sans-serif;color:' + MAIL_C.ink + '">' +
    '<tr><td style="text-align:center;font-size:13px;font-weight:700;color:' + MAIL_C.orange + ';padding:4px 0 12px">' + esc_(CONFIG.SERVICE_NAME) + '</td></tr>' +
    inner +
    '<tr><td style="font-size:11px;color:#8A857E;line-height:1.6;padding:20px 4px 8px;text-align:center">' + esc_(CONFIG.SERVICE_NAME) + '　<a href="' + esc_(CONFIG.SITE_URL) + '" style="color:#8A857E">' + esc_(CONFIG.SITE_URL) + '</a><br>このメールに返信すると運営に届きます。</td></tr>' +
    '</table></td></tr></table></body></html>';
}
function mailHead_(badge, title, color) {
  return '<tr><td style="text-align:center;padding:4px 0 16px">' +
    (badge ? '<span style="display:inline-block;background:' + (color || MAIL_C.orange) + ';color:#fff;border-radius:999px;padding:4px 14px;font-size:12px;font-weight:700">' + esc_(badge) + '</span>' : '') +
    '<div style="font-size:22px;font-weight:800;line-height:1.4;margin-top:10px">' + title + '</div></td></tr>';
}
function mailCard_(rows) {
  rows = rows.filter(function (x) { return x && x[2]; });
  return '<tr><td style="background:#fff;border-radius:16px;padding:4px 16px">' + rows.map(function (x, i) {
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"' + (i ? ' style="border-top:1px solid ' + MAIL_C.line + '"' : '') + '><tr>' +
      '<td width="34" valign="top" style="font-size:20px;padding:12px 0">' + x[0] + '</td>' +
      '<td style="padding:12px 0"><div style="font-size:12px;color:' + MAIL_C.sub + '">' + esc_(x[1]) + '</div>' +
      '<div style="font-size:16px;font-weight:700;line-height:1.5">' + mh_(x[2]) + '</div>' +
      (x[3] ? '<div style="font-size:12px;color:' + MAIL_C.sub + ';line-height:1.5">' + mh_(x[3]) + '</div>' : '') + '</td></tr></table>';
  }).join('') + '</td></tr>';
}
function mailButton_(label, url, sub) {
  return '<tr><td style="padding:18px 0 4px;text-align:center"><a href="' + esc_(url) + '" style="display:block;background:' + MAIL_C.orange + ';color:#fff;text-decoration:none;border-radius:999px;padding:14px;font-size:17px;font-weight:800">' + esc_(label) + '</a>' +
    (sub ? '<div style="font-size:12px;color:' + MAIL_C.sub + ';margin-top:6px">' + mh_(sub) + '</div>' : '') + '</td></tr>';
}
function mailButtons2_(list) {
  list = list.filter(function (x) { return x && x[1]; });
  if (!list.length) return '';
  return '<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>' + list.map(function (x, i) {
    return '<td width="' + Math.floor(100 / list.length) + '%" style="' + (i ? 'padding-left:10px' : '') + '"><a href="' + esc_(x[1]) + '" style="display:block;text-align:center;border:2px solid ' + MAIL_C.orange + ';color:' + MAIL_C.orange + ';text-decoration:none;border-radius:999px;padding:10px;font-size:15px;font-weight:800">' + esc_(x[0]) + '</a></td>';
  }).join('') + '</tr></table></td></tr>';
}
// 連絡先のボタン（押す前にどこへかかるか分かるよう、番号・アドレスをボタンに書く。Nori 2026-11-09）
function mailContactButtons_(tel, telShown, email) {
  var list = [tel ? ['📞', telShown + ' に電話する', 'tel:' + tel] : null, email ? ['✉', email + ' にメールする', 'mailto:' + email] : null].filter(Boolean);
  if (!list.length) return '';
  return list.map(function (x) {
    return '<tr><td style="padding:10px 0 0"><a href="' + esc_(x[2]) + '" style="display:block;text-align:center;border:2px solid ' + MAIL_C.orange + ';color:' + MAIL_C.orange + ';text-decoration:none;border-radius:999px;padding:10px 12px;font-size:15px;font-weight:800;word-break:break-all">' + esc_(x[0] + ' ' + x[1]) + '</a></td></tr>';
  }).join('');
}
function mailNotes_(items) {
  items = items.filter(function (x) { return x && x[1]; });
  if (!items.length) return '';
  return '<tr><td style="padding-top:14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:' + MAIL_C.note + ';border-radius:14px"><tr><td style="padding:6px 14px">' +
    items.map(function (x) { return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td width="26" valign="top" style="font-size:15px;padding:7px 0">' + x[0] + '</td><td style="font-size:14px;line-height:1.6;padding:7px 0">' + mh_(x[1]) + '</td></tr></table>'; }).join('') +
    '</td></tr></table></td></tr>';
}
function mailSteps_(steps) {
  return '<tr><td style="padding-top:14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>' + steps.map(function (x, i) {
    return '<td width="' + Math.floor(100 / steps.length) + '%" valign="top" style="' + (i ? 'padding-left:6px' : '') + '"><div style="background:#fff;border-radius:12px;padding:10px 6px;text-align:center;font-size:12px;line-height:1.4">' +
      '<div style="width:24px;height:24px;line-height:24px;border-radius:12px;background:' + MAIL_C.orange + ';color:#fff;font-weight:800;margin:0 auto 4px">' + (i + 1) + '</div>' + mh_(x) + '</div></td>';
  }).join('') + '</tr></table></td></tr>';
}
// 細かい説明（小さく灰色）。links は [文言, URL]
function mailFine_(parts) {
  parts = parts.filter(Boolean);
  if (!parts.length) return '';
  return '<tr><td style="font-size:12px;color:' + MAIL_C.sub + ';line-height:1.7;padding:16px 4px 0">' + parts.map(function (x) {
    return Array.isArray(x) ? '<a href="' + esc_(x[1]) + '" style="color:' + MAIL_C.sub + '">' + esc_(x[0]) + '</a>' : mh_(x);
  }).join('<br>') + '</td></tr>';
}
// 依頼のくわしい内容（会社あて。文字だけの本文と同じ項目を小さく）
function mailDetail_(title, text) {
  return '<tr><td style="padding-top:14px"><div style="background:#fff;border-radius:14px;padding:12px 14px;font-size:13px;line-height:1.7;color:' + MAIL_C.ink + '"><div style="font-weight:700;color:' + MAIL_C.sub + ';font-size:12px;margin-bottom:4px">' + esc_(title) + '</div>' + mh_(String(text).replace(/^\n+/, '')) + '</div></td></tr>';
}
function petSummary_(r) {
  if (Number(r['ペット数']) >= 2 && r['ペット詳細']) return r['ペット数'] + '匹';
  return [r['種類'], r['犬種・猫種'] ? '（' + r['犬種・猫種'] + '）' : '', r['体重kg'] ? r['体重kg'] + 'kg' : '', r['年齢'] ? '・' + r['年齢'] + '歳' : ''].filter(String).join('');
}
function backText_(r) {
  return r['帰りの日時'] instanceof Date ? '帰りは ' + fmt_(r['帰りの日時']).replace(/^.*\) /, '') : '';
}

// 会社へ：空き状況と料金のお問い合わせ（問い合わせの形のときだけ。ほかの形は文字だけ）
function requestHtml_(r, pt) {
  if (!isAsk_(r)) return '';
  var round = isRound_(r), checks = checks_(pt, r).ask;
  return mailPage_(
    mailHead_('お名前・連絡先は、予約が決まったらお知らせします', '空き状況と料金の<br>お問い合わせです', MAIL_C.blue) +
    mailCard_([
      ['🕙', '日時', whenText_(r), [r['片道・往復'], backText_(r)].filter(String).join('・')],
      ['📍', '区間', PREF_FULL[r['都府県']] + ' ' + r['お迎えの場所'] + '\n→ ' + r['行き先'], r['経由地'] ? '経由：' + r['経由地'] : ''],
      ['🐾', 'ペット', petSummary_(r), [cageText_(r['キャリー']), r['同乗人数'] ? '同乗' + r['同乗人数'] : '', r['荷物'] ? '荷物' + r['荷物'] : ''].filter(String).join('・')],
      ['💴', 'お支払い', payForPartner_(pt).replace(/（貴社の設定としてお客さまにもお伝えしています）$/, '')]
    ]) +
    mailButton_('空き状況と料金を返事する', acceptUrl_(r['受付番号'], pt.id), inputWord_(r) + 'を入れるだけ') +
    mailNotes_([
      checks.length ? ['☑', '引き受ける前にご確認ください（できない場合はお受けにならないでください）\n' + checks.map(function (x) { return '・' + x; }).join('\n')] : null,
      ['⏱', '当日の道路事情' + (round ? 'や待ち時間' : '') + 'で料金表どおりに変わる分は、当日の実際の時間・道のりで精算してください'],
      round ? ['🔁', '待つ場合の確定料金は、帰りの時刻まで待った金額でお返事ください'] : null
    ]) +
    mailDetail_('くわしい内容', rideText_(r) + retAsk_(r) + estText_(r)) +
    mailFine_([
      'お返事の内容は' + CONFIG.QUOTE_VALID_HOURS + '時間（お迎えの' + cutoffText_() + '前まで）有効です。お返事のあとにほかのご予約が入ったときは、お返事のリンクを開いて「このお返事を取り下げる」を押してください。',
      pickedIds_(r).length > 1 ? 'お客さまが選んだ' + pickedIds_(r).length + '社にお声がけしています。' : '',
      'ご返信でお答えいただく場合：受けられる（' + (r['日付のみ'] ? 'お迎え時刻・' : '') + '一般道〇円・高速を使う場合〇円' + (round ? '・帰りは「待つ」か「あとで迎え」か' : '') + '）か、難しい、でお願いします。',
      'ペットの様子などのご質問は、決まったあとにお客さまへ直接どうぞ。ご都合が合わない場合、お返事は不要です。'
    ]));
}

// お客さまへ：お返事が届きました
function quoteHtml_(r, pt, at, fare, fareHw, retWay, msg, mine, word, many) {
  var ask = isAsk_(r), f = feeFlags_(pt);
  return mailPage_(
    mailHead_(ask ? 'まだ予約は確定していません' : 'まだ決まっていません', esc_(pt.name) + 'から<br>' + (ask ? 'お返事' : esc_(word)) + 'が届きました') +
    mailCard_([
      ['🕙', 'お迎え', fmt_(at)],
      ['💴', '確定料金（税込）', yen_(fare) + (num_(fareHw) ? '' : '（高速道路は使いません）'), num_(fareHw) ? '一般道で行く場合。高速道路を使うと ' + yen_(fareHw) + '（高速代込み）' : ''],
      ['🔁', '帰り', retWay],
      ['💳', 'お支払い', payForCustomer_(pt)],
      ['💬', pt.name + 'から', msg]
    ]) +
    mailButton_(ask ? 'この内容で予約する' : 'この会社に決める', chooseUrl_(r['受付番号'], pt.id), fmt_(new Date(quoteUntil_(mine))) + 'まで') +
    mailNotes_([
      ['⏱', changeNote_(pt) + 'くわしくは会社にご確認ください。'],
      isRound_(r) && !f.noWait ? ['🔁', '待っていてもらうときの待ち時間の料金は、当日の実際の待ち時間で精算します。'] : null,
      ['✕', '予約したあとのキャンセル：' + cancelRuleText_(pt)]
    ]) +
    mailFine_([
      '期限を過ぎると会社の空き状況が変わるため、この内容では予約できません。',
      !ask || many ? 'ほかの会社の' + word + 'も、届きしだいお送りします。くらべてから決めてかまいません。' : '',
      (ask ? '予約しない場合は、何もしなくて大丈夫です。' : 'どの会社にも決めない場合は、何もしなくて大丈夫です。'),
      ['問い合わせを取り消す', cancelUrl_(r['受付番号'])],
      '受付番号 ' + r['受付番号']
    ]));
}

// お客さまへ：ご予約が確定しました
function confirmHtml_(r, pt, at, fare, fareHw, retWay, msg, cancelUrl) {
  var tel = String(pt.tel || '').replace(/[^\d+]/g, ''), f = feeFlags_(pt);
  return mailPage_(
    mailHead_('✓ 確定', 'ご予約が<br>確定しました', MAIL_C.green) +
    mailCard_([
      ['🚕', 'ペットタクシー', pt.name],
      ['🕙', 'お迎え', fmt_(at)],
      ['💴', '料金（確定・税込）', yen_(fare) + (num_(fareHw) ? '' : '（高速道路は使いません）'), num_(fareHw) ? '一般道で行く場合。高速道路を使うと ' + yen_(fareHw) + '（高速代込み）' : ''],
      ['🔁', '帰り', retWay ? retWay + '（料金が安くなるほう）' : ''],
      ['💳', 'お支払い', payForCustomer_(pt)],
      ['💬', pt.name + 'から', msg]
    ]) +
    mailSteps_([pt.name + 'から\n連絡が来ます', '当日\nお迎え', 'お支払いは\n会社へ直接']) +
    mailContactButtons_(tel, pt.tel, pt.email) +
    mailNotes_([
      ['⏰', '連絡がない・遅れているときは、まず' + pt.name + 'へ。つながらなければ、このメールに返信してください'],
      ['⏱', changeNote_(pt)],
      isRound_(r) && !f.noWait ? ['🔁', '待ち時間の料金は、当日の実際の待ち時間で精算します'] : null,
      ['🧾', '領収書は' + pt.name + 'にお申し出ください。ペットの様子などのご質問も、会社と直接どうぞ']
    ]) +
    mailFine_([
      cancelAfterText_(pt) + 'お迎えの3時間前を過ぎてから取り消すときは、押す前に「' + pt.name + '」へ直接ご連絡ください。',
      ['予約を取り消す', cancelUrl],
      '送迎のご契約は、お客さまと「' + pt.name + '」との間で結ばれます（当サイトは送迎を行わず、契約の当事者ではありません）。',
      '受付番号 ' + r['受付番号']
    ]));
}

// 会社へ：ご依頼が決まりました（お客さまの連絡先）
function decidedHtml_(r, pt) {
  var tel = String(r['電話番号'] || '').replace(/^'/, '').replace(/[^\d+]/g, '');
  return mailPage_(
    mailHead_('✓ 決定', 'ご依頼が<br>決まりました', MAIL_C.green) +
    mailCard_([
      ['👤', 'お客さま', r['お名前'] + ' さま', 'ご希望の連絡方法：' + r['連絡方法']],
      ['📞', '電話・メール', String(r['電話番号'] || '').replace(/^'/, '') + '\n' + r['メール']],
      ['🕙', 'お迎え', fmt_(r['お迎え予定']), r['お迎えの場所'] + ' → ' + r['行き先']],
      ['💴', 'お伝えした確定料金', fareText_(r['料金の目安'], r['高速利用時の料金'])]
    ]) +
    mailContactButtons_(tel, String(r['電話番号'] || '').replace(/^'/, ''), r['メール']) +
    mailNotes_([
      ['📣', 'お客さまへ直接ご連絡をお願いします'],
      ['⏱', '当日の道路事情' + (isRound_(r) ? 'や待ち時間' : '') + 'で料金表どおりに変わる分は、当日の実際の時間・道のりで精算してください'],
      ['🔒', 'ご連絡先は、この送迎のためだけにお使いください']
    ]) +
    mailDetail_('くわしい内容', rideText_(r) + '\n■ お支払い：' + payForPartner_(pt)) +
    mailFine_([
      'やむを得ずお受けできなくなったときは、こちらから取り消してください（お客さまにお知らせし、このご予約は取り消しになります）。',
      ['このご予約を取り消す', partnerCancelUrl_(r['受付番号'], pt.id)],
      '当サイトへのご連絡（お客さまとの間で困ったこと、条件の変更など）は、このメールに返信してください。',
      '受付番号 ' + r['受付番号']
    ]));
}

function footer_() {
  return '\n\n――――――――――\n' + CONFIG.SERVICE_NAME + '\n' + CONFIG.SITE_URL + '\nこのメールに返信すると運営に届きます。';
}

// テストの依頼か（会社には送らず、運営者のメールに送る）
function isTest_(r) {
  if (CONFIG.TEST_MODE) return true;
  var ids = pickedIds_(r); // 受け付けを始めた会社だけに宛てた依頼は、B1 が「止める」でも会社に送る（Nori 2026-11-08「aiaiはOPENにしていい」）
  if (!liveSending_() && !(ids.length && ids.every(isOpen_))) return true;
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

// 会社が返事で入れるもの。日時はお客さまが決めたもので変えられない（日付だけの依頼だけ時刻を入れる。Nori 2026-11-09）
function inputWord_(r) { return r['日付のみ'] ? 'お迎え時刻と確定料金' : '確定料金'; }

// 返事のお迎え時刻。時刻つきの依頼は希望日時に固定（画面の値は使わない）。日付だけの依頼はその日の入力された時刻
function replyAt_(r, q) {
  if (!r['日付のみ']) return new Date(r['希望日時']);
  var m = String(q.t || '').match(/^(\d{1,2}):(\d{2})$/);
  if (!m) return null;
  return parseJst_(Utilities.formatDate(new Date(r['希望日時']), TZ, 'yyyy-MM-dd') + 'T' + ('0' + m[1]).slice(-2) + ':' + m[2]);
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
    'button.gray{background:#5b5650}.note{font-size:.85rem;color:#5b5650}.sec{font-size:1rem;margin:20px 0 6px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}.sec .tag{font-size:.75rem;font-weight:600;color:#5b5650;background:#ece8e3;border-radius:999px;padding:2px 10px}.fixed{background:#f1efec;border-radius:12px;padding:14px;margin:6px 0 8px;font-size:.92rem;color:#3d3833}.fixed .when{font-size:1.15rem;font-weight:800;color:#2b2622;margin-bottom:8px}.brand{text-align:center;color:#e2560a;font-weight:800;margin-bottom:12px}';
  if (JSON_PAGE) {
    return ContentService.createTextOutput(JSON.stringify({ ok: true, title: title, html: inner }))
      .setMimeType(ContentService.MimeType.JSON);
  }
  var html = '<!doctype html><html><head><meta charset="utf-8"><base target="_top"><style>' + css + '</style></head><body><div class="brand">' + esc_(CONFIG.SERVICE_NAME) +
    '</div><div class="card"><h1>' + esc_(title) + '</h1>' + inner + '</div></body></html>';
  return HtmlService.createHtmlOutput(html).setTitle(title + '｜' + CONFIG.SERVICE_NAME)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/* ───────── 提携規約への同意（a=agree。Nori 2026-11-09「サイト上でクリックして」「logをちゃんと取っておいて」） ───────── */
// 提携規約の版（gen_areas.py が partner_terms.py から書き込む。改定日と本文の指紋）
/*PTERMS_VER*/var PTERMS_VER = {"revised": "2026年11月9日", "hash": "898dc30393da"};/*/PTERMS_VER*/
var AGREE_HEADERS = ['同意した日時', '提携先ID', '会社名', '同意した方のお名前', '役職・担当', '規約の改定日', '規約の版の番号', '規約のURL', '受け付けた画面'];
function agreeUrl_(pid) { return linkBase_() + '?a=agree&p=' + encodeURIComponent(pid) + '&k=' + sign_('agree:' + pid); }
function agreeRows_(pid) {
  var sh = sheet_(SHEET_AGREE);
  if (!sh || sh.getLastRow() < 2) return [];
  return sh.getRange(2, 1, sh.getLastRow() - 1, AGREE_HEADERS.length).getValues().filter(function(v) { return String(v[1]) === String(pid); });
}
function agreePage_(q) {
  if (!q.p || q.k !== sign_('agree:' + q.p)) return page_('リンクが正しくありません', '<p>お手数ですが、届いたメールのリンクからもう一度開いてください。</p>');
  var pt = partnerById_(q.p);
  if (!pt) return page_('見つかりません', '<p>このリンクの会社が見つかりませんでした。お手数ですが、メールでお知らせください。</p>');
  var termsUrl = CONFIG.SITE_URL.replace(/\/$/, '') + '/partner/terms/';
  var ver = PTERMS_VER.revised + ' 改定（版の番号 ' + PTERMS_VER.hash + '）';
  var done = agreeRows_(q.p).filter(function(v) { return String(v[6]) === PTERMS_VER.hash; })[0];
  var when = function(d) { return Utilities.formatDate(new Date(d), TZ, 'yyyy年M月d日 H:mm'); };
  if (done) return page_('提携規約に同意済みです', '<p>' + esc_(pt.name) + ' さまは、この版の提携規約に同意いただいています。</p>' +
    '<div class="box">同意した日時：' + esc_(when(done[0])) + '<br>同意した方：' + esc_(done[3]) + '<br>規約：' + esc_(ver) + '</div>' +
    '<p><a href="' + esc_(termsUrl) + '" target="_blank">提携規約を見る</a></p>');
  if (q.go === '1') {
    var name = String(q.name || '').trim().slice(0, 60), role = String(q.role || '').trim().slice(0, 60);
    if (!name || q.ok !== '1' || q.v !== PTERMS_VER.hash) {
      if (q.v && q.v !== PTERMS_VER.hash) return page_('規約が新しくなりました', '<p>ページを開いたあとに提携規約が改定されました。お手数ですが、もう一度このリンクを開いて、新しい規約をご確認ください。</p>');
      q.err = 1;
    } else {
      var lock = LockService.getScriptLock();
      lock.waitLock(20000);
      try {
        var sh = ensureSheet_(SpreadsheetApp.getActive(), SHEET_AGREE, AGREE_HEADERS);
        var now = new Date();
        sh.appendRow([now, pt.id, pt.name, name, role, PTERMS_VER.revised, PTERMS_VER.hash, termsUrl, JSON_PAGE ? 'サイトの画面' : '直接のリンク']);
        sh.getRange(sh.getLastRow(), 1).setNumberFormat('yyyy/MM/dd HH:mm:ss');
      } finally { lock.releaseLock(); }
      log_('規約の同意：' + pt.id + ' ' + pt.name + ' ' + name + ' 版 ' + PTERMS_VER.hash);
      notifyAdmin_('提携規約に同意がありました：' + pt.name, pt.name + '（' + pt.id + '）が提携規約に同意しました。\n同意した方：' + name + (role ? '（' + role + '）' : '') +
        '\n規約：' + ver + '\n記録：予約シートの「' + SHEET_AGREE + '」タブ' + (isOpen_(pt.id) ? '' : '\n\n問い合わせの受け付けを始めるのは、運営者が確かめてからです。'));
      return page_('提携規約への同意を受け付けました', '<p>' + esc_(pt.name) + ' さま、ありがとうございます。提携規約への同意を記録しました。</p>' +
        '<div class="box">同意した日時：' + esc_(when(now)) + '<br>同意した方：' + esc_(name) + (role ? '（' + esc_(role) + '）' : '') + '<br>規約：' + esc_(ver) + '</div>' +
        '<p>このページは控えとして保存しておいてください。規約はいつでも <a href="' + esc_(termsUrl) + '" target="_blank">提携規約のページ</a> で見られます。</p>');
    }
  }
  var old = agreeRows_(q.p).slice(-1)[0];
  return page_('提携規約への同意', '<p>' + esc_(pt.name) + ' さま、提携のお申し込みありがとうございます。<br>次の提携規約をお読みいただき、内容に同意いただける場合は、下の「提携規約に同意する」を押してください。</p>' +
    '<div class="box"><b>提携規約</b>（' + esc_(ver) + '）<br><a href="' + esc_(termsUrl) + '" target="_blank">提携規約の全文を開く ↗</a></div>' +
    (old ? '<p class="note">前の版（' + esc_(old[5]) + ' 改定）には ' + esc_(when(old[0])) + ' に同意いただいています。規約が改定されたので、新しい版をご確認ください。</p>' : '') +
    (q.err ? '<p style="color:#c0392b;font-weight:700">お名前を入れて、「同意します」にチェックしてください。</p>' : '') +
    '<form method="get" action="' + esc_(linkBase_()) + '" target="_top">' + hidden_('a', 'agree') + hidden_('p', q.p) + hidden_('k', q.k) + hidden_('go', '1') + hidden_('v', PTERMS_VER.hash) +
    '<label>同意される方のお名前（必須）<input name="name" required maxlength="60" value="' + esc_(q.name || '') + '"></label>' +
    '<label>役職・担当（任意）<input name="role" maxlength="60" value="' + esc_(q.role || '') + '"></label>' +
    '<label style="display:flex;gap:8px;align-items:flex-start;font-weight:600"><input type="checkbox" name="ok" value="1" required style="width:auto;margin-top:6px">' +
    '<span>' + esc_(pt.name) + ' として、提携規約（' + esc_(ver) + '）を読み、同意します。</span></label>' +
    '<button type="submit">提携規約に同意する</button></form>' +
    '<p class="note">押すと、同意した日時・お名前・規約の版を当サイトの記録に残します。' + (isOpen_(pt.id) ? 'お問い合わせの受け付けはすでに始まっています。' : '同意しただけでは、まだお問い合わせは届きません。受け付けの開始は、あらためてメールでお知らせします。') + '</p>');
}
// 同意のページのリンクを「同意のリンク」タブに書き出す（スクリプトの画面で1回動かす。何も送らない）
function makeAgreeLinks() {
  var sh = ensureSheet_(SpreadsheetApp.getActive(), '同意のリンク', ['提携先ID', '会社名', '同意のページのリンク', '同意した版']);
  var rows = partners_().filter(function(pt) { return pt.id; }).map(function(pt) {
    var last = agreeRows_(pt.id).slice(-1)[0];
    return [pt.id, pt.name, agreeUrl_(pt.id), last ? last[5] + '（' + last[6] + '）' : ''];
  });
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 4).clearContent();
  if (rows.length) sh.getRange(2, 1, rows.length, 4).setValues(rows);
  return rows.length;
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
    'ペットJSON': String(p.pets_json || ''), '帰りの日時': p.trip === '往復' ? parseJst_(p.return_datetime) : '',
    '経由地': String(p.via || ''), '行き先': String(p.dropoff || ''),
    '_route': (function() { try { return JSON.parse(p.route_details || '{}') || {}; } catch (e) { return {}; } })()
  };
}
// 受け付けを始めた会社のうち、お店の位置が分かる会社は、お迎えか行き先がお店の近く（CONFIG.DISPLAY_MAX_KM 以内）のときだけ候補にする
// （ペッタクの申し込み 2026-11-08「広島周辺から全国へ、全国から広島周辺へ」。対応エリアは全国でも、遠い所どうしの送迎には出さない）
function openNear_(pt, r) {
  var od = openDisplay_(pt.id), d = (r || {})._route || {};
  if (!od || !od.shop) return true;
  var shop = {lat:od.shop[0], lng:od.shop[1]}, ok = function(v) { return v && isFinite(v.lat) && isFinite(v.lng); };
  // 申し込みで答えてもらったお迎えの範囲（お迎えの範囲km）が80kmより広い会社は、その範囲まで出す（2026-11-14 点検：CoCoタク静岡は100kmまでと答えているのに80kmで切っていた）
  var lim = Math.max(CONFIG.DISPLAY_MAX_KM, Number(pt.radiusKm) || 0);
  var near = function(v) { return ok(v) && kmBetween_(shop, v) <= lim; };
  if (!ok(d.from) && !ok(d.to)) return true;
  return near(d.from) || near(d.to);
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
      fitsCar_(pt, r) && fitsCage_(pt, r) && inTime_(pt, r) && (r['介助'] !== '必要' || pt.careOk) && !checks_(pt, r).ng.length && openNear_(pt, r);
  });
}

function quoteSignature_(p, id, expires, price) {
  return sign_('selection:' + JSON.stringify(QUOTE_FIELDS.map(function(k) { return String(p[k] || ''); })) + ':' + id + ':' + expires + ':' + JSON.stringify(price));
}

function selectionPrice_(pt, p) {
  var od = openDisplay_(pt.id);
  if (od) { // 受け付けを始めた会社は、表示だけの会社と同じ公式サイトの料金表で計算する（お店からの道のりも同じく調べる）
    var rd = {}; try { rd = JSON.parse(p.route_details || '{}') || {}; } catch (e) {}
    if (od.shop && od.fare) loadRoadKm_([{lat:od.shop[0], lng:od.shop[1]}], [rd.from, rd.to, rd.backFrom, rd.backTo]);
    return displayPrice_(od, p) || {amount:null,text:'料金はお見積もり',night:''};
  }
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
  p.demo_id = demoId_(p.demo); // ページから来た demo_id は使わず、署名を確かめて決める
  // scores：口コミの星を kind=scores でまとめて取り寄せられる版（ページはこれが来たときだけ取り寄せる）
  var out = {ok:true,selection_version:1,scores:1,cards:quoteCards_(p)};
  try { if (!p.demo_id) demandLog_(p, out.cards); } catch (e) {} // 記録に失敗しても検索は止めない
  // 往復は、行きと帰りをそれぞれ別の会社に頼めるように、片道ずつの候補も返す（Nori 2026-10-31）。全社準備中のあいだは出さない
  if (p.trip === '往復' && !CONFIG.SHOW_ALL_CANDIDATES) out.legs = {go:quoteCards_(legParams_(p,'go')), back:quoteCards_(legParams_(p,'back'))};
  return out;
}

// 需要の記録（Nori 2026-11-08「すすめていいよ」）：どの地域で検索があり、どの会社が候補に出たかだけを残す。
// 提携していない会社に「この地域でお客さまからの検索がありました」とお伝えして、提携にお誘いするため。
// お名前・連絡先・番地・ペットの詳しい内容は残さない（市区町村まで）。同じ条件の検索は30分に1回だけ数える。
function cityOf_(s) {
  var t = String(s || '').replace(/\s/g, ''), par = t.match(/[（(]([^）)]*[市区町村])[）)]/);
  if (par) t = par[1]; // 「渋谷駅 南口（渋谷区）」のような候補の書き方
  var m = t.match(/^(?:.{2,3}?[都道府県])?(.+?郡.+?[町村]|.+?市.+?区|.+?[市区町村])/);
  return m && m[1].length <= 12 ? m[1] : '';
}
function demandLog_(p, cards) {
  var key = 'dm:' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, [p.pref, p.pickup, p.dropoff, String(p.datetime).slice(0, 10)].join('|')));
  var cache = CacheService.getScriptCache();
  if (cache.get(key)) return;
  cache.put(key, '1', 1800);
  var ids = (cards || []).map(function(c) { return c.id; });
  var open = (cards || []).filter(function(c) { return c.listed && c.token; }).length;
  var sh = ensureSheet_(SpreadsheetApp.getActive(), '需要の記録', DEMAND_HEAD_);
  if (sh.getRange(1, 9).getValue() !== '運営者') sh.getRange(1, 9).setValue('運営者').setFontWeight('bold').setBackground('#fff1e6');
  sh.appendRow([new Date(), shortPref_(p.pref), cityOf_(p.pickup), cityOf_(p.dropoff), String(p.datetime || '').slice(0, 10), String(p.trip || ''), ids.join(','), open, p.staff === '1' ? '運営者' : '']);
}
// 9列目「運営者」：運営者の動作確認の検索（その端末で一度 https://pet.shiokonbu.com/?staff=1 を開くと、ページが staff=1 を付けて送る。?staff=0 で解除）。
// お誘いのメールの数字は、ここが空の行だけで数える（2026-11-10 戦略担当・提携担当）。
var DEMAND_HEAD_ = ['日時', 'お迎えの都道府県', 'お迎えの市区町村', '行き先の市区町村', 'お迎えの日', '片道・往復', '候補に出た会社', '問い合わせできた会社の数', '運営者'];

// 前の記録に、あとから運営者の印を付ける（何も送らない）。from・to は '2026-11-08 10:00' の形、
// pref を渡すとその都道府県（「東京」のように都道府県の字なし）だけ。印を付けた行の数を返す。
// 例：markDemandStaff('2026-11-08 00:00', '2026-11-08 23:59')
function markDemandStaff(from, to, pref) {
  var sh = SpreadsheetApp.getActive().getSheetByName('需要の記録');
  if (!sh || sh.getLastRow() < 2) return 0;
  var a = new Date(String(from).replace(/-/g, '/')), b = new Date(String(to).replace(/-/g, '/'));
  sh.getRange(1, 9).setValue('運営者');
  var v = sh.getRange(2, 1, sh.getLastRow() - 1, 9).getValues(), n = 0;
  var col = v.map(function(r) {
    var t = r[0] instanceof Date ? r[0] : new Date(r[0]), hit = t >= a && t <= b && (!pref || r[1] === pref);
    if (hit && r[8] !== '運営者') n++;
    return [hit ? '運営者' : r[8]];
  });
  sh.getRange(2, 9, col.length, 1).setValues(col);
  return n;
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
    var od = openDisplay_(pt.id);
    // 車：申し込みで車種（エブリイなど）が分かる会社は車種を出す。キャンセル料がかからない会社はそれもアピールに（Nori 2026-11-12「キャンセル無料とか、車も車種がわかるやつはそれも出して」）
    if (od) return { id:pt.id, label:pt.name, listed:true, car:(/[ァ-ヴー]{3,}|N-?VAN/.test(pt.car || '') && !/^軽バン$/.test(pt.car) ? '車：' + pt.car : od.car_type ? '車：' + od.car_type + '（公式サイトの記載）' : pt.car || '車の詳細は引き受け時に確認'),
      points:od.points || [], limits:od.limits || [], shop:od.shop || null, cancelFree:cancelFree_(pt.cancelRule),
      payment:od.pay ? 'お支払い：' + od.pay + '（公式サイトの記載）' : [pt.payMethod,pt.payWhen].filter(String).join('・') || 'お支払い方法は引き受け時にご案内',
      price:price, review:null, check:checks_(pt, r).ask, expires:expires, token:quoteSignature_(p,pt.id,expires,price) };
    if (CONFIG.SHOW_ALL_CANDIDATES) return anonCard_({ id:pt.id, label:pt.name, display_only:true, car:pt.car || '車の詳細は確認中です',
      payment:[pt.payMethod,pt.payWhen].filter(String).join('・') || 'お支払い方法は確認中です',
      price:price, review:null, check:[], points:PARTNER_POINTS[pt.id] || [], limits:PARTNER_LIMITS[pt.id] || [], shop:partnerShop_(pt.id) }, r['都府県'], '', p.demo_id);
    return { id:pt.id, label:pt.name, car:pt.car || '車の詳細は引き受け時に確認', points:PARTNER_POINTS[pt.id] || [], limits:PARTNER_LIMITS[pt.id] || [], shop:partnerShop_(pt.id),
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
// 営業時間が分からないことでは外さない。当日予約だけは、はっきり受けると書いてある会社に限る（2026-11-02）
function displayInTime_(c, at, now) {
  if (!at || !isFinite(at.getTime())) return true;
  var j = new Date(at.getTime() + 9 * 3600000), hr = j.getUTCHours() + j.getUTCMinutes() / 60;
  if ((c.closed || []).indexOf(j.getUTCDay()) >= 0) return false; // 定休日
  if (c.hours && !c.flex && !inHours_(hr, hoursOf_(c.hours))) return false; // お迎えが営業時間の外
  var n = new Date(now.getTime() + 9 * 3600000);
  var days = Math.round((Date.UTC(j.getUTCFullYear(), j.getUTCMonth(), j.getUTCDate()) - Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate())) / 86400000);
  if (c.lead_days != null && days < c.lead_days) return false; // 前日まで・3日前までの会社
  if (days === 0) {
    // 当日は、公式サイトか会社の返事に「当日も受ける」とはっきり書いてある会社（lead_days=0）だけを出す。分からない会社は出さない（Nori 2026-11-02「東京めっちゃ出てくる」）
    if (c.lead_days !== 0) return false;
    if (c.cut != null && n.getUTCHours() >= c.cut) return false; // 当日予約の締め切りを過ぎた
    // 今日の営業時間が終わっていて、お迎えまでに開かない会社は出さない。開いてからお迎えまで準備の時間があること
    if (c.hours && at.getTime() - nextOpen_(now, c.hours).getTime() < CONFIG.DEFAULT_LEAD_HOURS * 3600000) return false;
  }
  return true;
}

/*DISPLAY_COMPANIES*/var DISPLAY_COMPANIES = [{"id": "De5faaf3", "name": "COCOタク 杉並店", "pref": "東京都", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "杉並区・中野区・世田谷区・練馬区・新宿区・渋谷区・武蔵野市・三鷹市を中心に東京・神奈川・千葉・埼玉", "shop": [35.705, 139.636], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-tokyo-suginami.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-tokyo-suginami.com/", "review_q": "COCOタク 杉並店 東京", "review_name": "COCOタク 杉並店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "De33f4b4", "name": "COCOタク 東京世田谷店", "pref": "東京都", "areas": ["東京"], "area_text": "世田谷区を中心に東京23区・調布・狛江・三鷹・西東京・新座", "shop": [35.648, 139.663], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://petcocotaxi-setagaya.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金のみ", "url": "https://petcocotaxi-setagaya.com/", "review_q": "COCOタク 東京世田谷店 東京", "review_name": "COCOタク 東京世田谷店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "limits": ["現金のみ"], "points": ["24時間受付"]}, {"id": "D2644ea0", "name": "COCOタク 東京中央店", "pref": "東京都", "areas": ["東京"], "area_text": "東京（文京区湯島）", "shop": [35.707, 139.77], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://tc-cocotaxi.com/"}, "pay": "現金・PayPay（送迎後）", "url": "https://tc-cocotaxi.com/", "review_q": "COCOタク 東京中央店 東京", "review_name": "COCOタク 東京中央店", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["渋滞でも追加料金なし", "PayPay可"]}, {"id": "Ddc3e31e", "name": "COCOタク 東京墨田店", "pref": "東京都", "areas": ["東京"], "area_text": "墨田・江東・江戸川・台東・葛飾、その他23区は相談", "shop": [35.705, 139.818], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi-pet-tokyo-sumida.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金", "url": "https://cocotaxi-pet-tokyo-sumida.com/", "review_q": "COCOタク 東京墨田店 東京", "review_name": "COCOタク 東京墨田店", "hours": "10-22", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "Df5f495f", "name": "COCOタク 東京多摩店", "pref": "東京都", "areas": ["東京"], "area_text": "多摩市", "shop": [35.654, 139.452], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://coco-pet-taxi-tokyo-tama.com/"}, "pay": "", "url": "https://coco-pet-taxi-tokyo-tama.com/", "review_q": "COCOタク 東京多摩店 東京", "review_name": "COCOタク 東京多摩店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "D400f012", "name": "COCOタク 東京小平店", "pref": "東京都", "areas": ["埼玉", "東京"], "area_text": "小平・東村山・立川・国分寺・府中・八王子など多摩一帯、所沢・朝霞・和光など埼玉の一部", "shop": [35.735, 139.475], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://www.cocotaxi-sawan.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・電子マネー", "url": "https://www.cocotaxi-sawan.com/", "review_q": "COCOタク 東京小平店 東京", "review_name": "COCOタク 東京小平店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["24時間受付", "深夜・早朝も相談可", "カード払い可", "追加料金なし"]}, {"id": "D3f74ac5", "name": "COCOタク 東京荒川店", "pref": "東京都", "areas": ["東京"], "area_text": "荒川区を中心に足立区・葛飾区・江戸川区", "shop": [35.737, 139.783], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-adachi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-adachi.com/", "review_q": "COCOタク 東京荒川店 東京", "review_name": "COCOタク 東京荒川店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D0e1ab9c", "name": "COCOタク 東京足立店", "pref": "東京都", "areas": ["埼玉", "東京"], "area_text": "足立区・北区・板橋区・荒川区・豊島区・文京区・台東区・葛飾区・墨田区・江戸川区・川口市・草加市", "shop": [35.768, 139.77], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxiadachi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード", "url": "https://cocotaxiadachi.com/", "review_q": "COCOタク 東京足立店 東京", "review_name": "COCOタク 東京足立店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D57763aa", "name": "COCOタク 武蔵野店", "pref": "東京都", "areas": ["東京"], "area_text": "武蔵野市を中心に三鷹市・西東京市・東久留米市・小金井市・国分寺市・調布市", "shop": [35.705, 139.58], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://coco-taxi-musashino.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://coco-taxi-musashino.com/", "review_q": "COCOタク 武蔵野店 東京", "review_name": "COCOタク 武蔵野店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D98b1024", "name": "COCOタク 渋谷店", "pref": "東京都", "areas": ["東京"], "area_text": "渋谷区を拠点に東京都内全域", "shop": [35.658, 139.698], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://cocotaku-shibuya.com/"}, "pay": "", "url": "https://cocotaku-shibuya.com/", "review_q": "COCOタク 渋谷店 東京", "review_name": "COCOタク 渋谷店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "追加料金なし"]}, {"id": "De308905", "name": "COCOタク 練馬杉並店", "pref": "東京都", "areas": ["東京"], "area_text": "練馬区・杉並区を中心に中野区・板橋区・豊島区・新宿区・渋谷区・目黒区・世田谷区・武蔵野市・西東京市・三鷹市・調布市・小金井市など東京都全域", "shop": [35.737, 139.652], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaku-nerima-suginami.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300, "by": "start"}}, "pay": "現金・カード・電子マネー・QRコード決済", "url": "https://cocotaku-nerima-suginami.com/", "review_q": "COCOタク 練馬杉並店 東京", "review_name": "COCOタク 練馬杉並店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile"], "no": []}, "points": ["24時間受付", "カード払い可"], "limits": ["同乗は3人まで"]}, {"id": "D45d6d56", "name": "COCOタク 西東京店", "pref": "東京都", "areas": ["東京"], "area_text": "武蔵野市・三鷹市・西東京市・小金井市・東村山市・東久留米市・清瀬市・小平市・国分寺市・立川市", "shop": [35.733, 139.548], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi.tokyo/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード（事前申告）・銀行振込", "url": "https://cocotaxi.tokyo/", "review_q": "COCOタク 西東京店 東京", "review_name": "COCOタク 西東京店", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["カード払い可"]}, {"id": "Db508c4d", "name": "COCOタク 足立中央本町店", "pref": "東京都", "areas": ["埼玉", "千葉", "東京"], "area_text": "葛飾区・足立区・江戸川区など東京東部、千葉・埼玉", "shop": [35.781, 139.8], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://pet-cocotaxi-katusika.com/content3.html"}, "pay": "", "url": "https://pet-cocotaxi-katusika.com/", "review_q": "COCOタク 足立中央本町店 東京", "review_name": "COCOタク 足立中央本町店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "追加料金なし"]}, {"id": "Dbcd4199", "name": "COCOタク 青山店", "pref": "東京都", "areas": ["東京"], "area_text": "港区・渋谷区など都心部", "shop": [35.67, 139.719], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "", "src": "https://cocotaku.com/料金表/"}, "pay": "", "url": "https://cocotaku.com/", "review_q": "COCOタク 青山店 東京", "review_name": "COCOタク 青山店", "hours": "9-21", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D3661eb1", "name": "PETTA東京（ペッタ）", "pref": "東京都", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "東京・埼玉・千葉・神奈川、長距離", "shop": [35.694, 139.819], "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 150], [201, null, 110]], "tax": "税込", "src": "https://www.petta-tokyo.com/cont2/main.html", "pick": {"per": 110}, "wait": {"free": 0, "unit": 10, "yen": 250}, "back": {"per": 110}}, "pay": "現金・電子マネー・QRコード決済", "url": "https://www.petta-tokyo.com/", "long": true, "review_q": "PETTA東京 東京", "review_name": "PETTA東京", "hours": "6-22", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽自動車またはミニバン", "limits": ["車：軽自動車またはミニバン", "同乗は2人まで", "2〜3頭OK", "大型犬2頭OK"], "points": ["当日予約可", "深夜・早朝も相談可", "深夜・早朝の割増なし", "前日までキャンセル無料"]}, {"id": "D1e44e13", "name": "cocoタク 大田・田園調布店", "pref": "東京都", "areas": ["東京"], "area_text": "大田・世田谷・品川・港・目黒・渋谷", "shop": [35.588, 139.672], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://coco-taxi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・交通系IC・PayPay・iD・QUICPay・Apple Pay", "url": "https://coco-taxi.com/", "review_q": "cocoタク 大田・田園調布店 東京", "review_name": "cocoタク 大田・田園調布店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2〜3頭OK", "同乗は3人まで"], "points": ["24時間受付", "深夜・早朝も相談可", "前日までキャンセル無料", "カード払い可"]}, {"id": "D355c31f", "name": "サポっ人 中目黒店", "pref": "東京都", "areas": ["東京"], "area_text": "目黒・大田・世田谷・渋谷・港・品川・杉並・中野・新宿", "shop": [35.643, 139.698], "fare": {"base": [2750, 5], "tiers": [[6, 100, 198], [101, 200, 165], [201, null, 132]], "tax": "税込", "src": "https://seikatsunosupport.com/pettaxi/", "pick": {"per": 198, "freeWithin": 3}, "kmMode": "exact", "night": {"from": 22, "to": 8, "rate": 0.5, "onAll": true}}, "pay": "", "url": "https://seikatsunosupport.com/pettaxi/", "review_q": "サポっ人 中目黒店 東京", "review_name": "サポっ人 中目黒店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "2〜3頭OK", "同乗は3人まで"], "points": ["当日予約可", "24時間受付", "前日までキャンセル無料"]}, {"id": "D7c32399", "name": "ペットタクシー こうのとり（AirLine Haneda）", "pref": "東京都", "areas": ["東京", "神奈川"], "area_text": "大田区中心、23区・川崎の一部（外は予約で相談）", "shop": [35.548, 139.753], "fare": {"base": [2500, 5], "tiers": [[6, null, 250]], "tax": "税込", "src": "https://airline-haneda.com/taxi/", "pick": {"km": 5, "yen": 1500, "per": 150}, "wait": {"free": 0, "first": [30, 1100], "unit": 10, "yen": 550}}, "pay": "現金のみ・降りるとき", "url": "https://airline-haneda.com/taxi/", "review_q": "ペットタクシー こうのとり 東京", "review_name": "こうのとり", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "limits": ["カード払い不可"]}, {"id": "D0d1c8b4", "name": "ペットタクシー ワンネス", "pref": "東京都", "areas": ["埼玉", "千葉", "東京"], "area_text": "東京23区・埼玉・千葉が中心", "shop": [35.775, 139.804], "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 165], [201, null, 110]], "tax": "税込", "src": "https://oneness-taxi.com/service.html", "pick": {"yen": 1000, "unsure": true}, "wait": {"free": 10, "unit": 10, "yen": 250}}, "pay": "カード・交通系IC・QR", "url": "https://oneness-taxi.com/", "review_q": "ペットタクシー ワンネス 東京", "review_name": "ワンネス", "hours": "8-20", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["当日予約可", "カード払い可"]}, {"id": "D692c9a6", "name": "ペットタクシー ワンハウス", "pref": "東京都", "areas": ["埼玉", "千葉", "東京"], "area_text": "東京23区、埼玉9市、千葉7市（当日対応）。ほかは相談", "shop": [35.802, 139.808], "fare": {"base": [2200, 5], "tiers": [[6, 100, 220], [101, 200, 165], [201, null, 110]], "tax": "税込", "src": "https://onehouse.jp/free/pricelist", "pick": {"yen": 770, "unsure": true}, "wait": {"free": 0, "unit": 10, "yen": 220}}, "pay": "", "url": "https://onehouse.jp/", "review_q": "ペットタクシー ワンハウス 東京", "review_name": "ワンハウス", "hours": "8-20", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D7922e74", "name": "ペトタクファインド", "pref": "東京都", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "千葉県全域ほか首都圏・全国に拡大中。長距離は相談", "shop": [35.69, 139.692], "fare": {"base": [3500, 0], "tiers": [[1, 100, 220], [101, 300, 190], [301, null, 170]], "tax": "税込", "src": "https://pettaxi-find.com/chiba/", "pick": {"per": 120}, "wait": {"free": 10, "unit": 10, "yen": 500}, "night": {"from": 21, "to": 7, "flat": 3000}}, "pay": "現金・カード・電子マネー・QR／到着後", "url": "https://pettaxi-find.com/chiba/", "long": true, "review_q": "ペトタクファインド 東京", "review_name": "ペトタクファインド", "hours": "", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "頭数で料金は変わらない", "同乗は2人まで"], "points": ["当日予約可", "大型犬OK", "前日までキャンセル無料"]}, {"id": "D72ab934", "name": "COCOタク 川崎店", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "川崎市・横浜市、東京の大田区・世田谷区・目黒区・杉並区", "shop": [35.519, 139.712], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://www.growing-group.co.jp/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・交通系電子マネー・PayPayなど", "url": "https://www.growing-group.co.jp/", "review_q": "COCOタク 川崎店 神奈川", "review_name": "COCOタク 川崎店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可", "PayPay可"]}, {"id": "D789b979", "name": "COCOタク 横浜店", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "横浜市中区・西区・南区・保土ケ谷区・港南区・磯子区、神奈川全域・23区も相談", "shop": [35.443, 139.63], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi-yokohama.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金", "url": "https://cocotaxi-yokohama.com/", "review_q": "COCOタク 横浜店 神奈川", "review_name": "COCOタク 横浜店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "Dfc12ca3", "name": "COCOタク 横浜港北店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "横浜市（港北区・神奈川区・西区・中区・都筑区・鶴見区）を中心に神奈川県全域", "shop": [35.493, 139.627], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi-yokohama-kouhoku.com/", "pick": {"yen": 0, "unsure": false}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・交通系電子マネー・QRコード決済（送迎後）", "url": "https://cocotaxi-yokohama-kouhoku.com/", "review_q": "COCOタク 横浜港北店 神奈川", "review_name": "COCOタク 横浜港北店", "hours": "0-24", "flex": false, "closed": [3], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Da1ed552", "name": "COCOタク 横浜磯子店", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "磯子区を中心に、事前予約で神奈川全域・状況により東京も", "shop": [35.395, 139.618], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-yokohama-isogo.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-yokohama-isogo.com/", "review_q": "COCOタク 横浜磯子店 神奈川", "review_name": "COCOタク 横浜磯子店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Dbf4a40c", "name": "COCOタク 湘南平塚店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "平塚市と近隣市町村、小田原市", "shop": [35.345, 139.358], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://coco-taxi-shonan-hiratuka.com/"}, "pay": "", "url": "https://coco-taxi-shonan-hiratuka.com/", "review_q": "COCOタク 湘南平塚店 神奈川", "review_name": "COCOタク 湘南平塚店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "D0d611b0", "name": "COCOタク 湘南店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "藤沢・茅ヶ崎・鎌倉・大和・綾瀬・海老名・寒川・横浜など", "shop": [35.352, 139.497], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "roundContinuous": true, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 22, "to": 8, "flat": 3300}, "tax": "", "src": "https://www.cocotaku-shonan.com/料金プラン"}, "pay": "", "url": "https://www.cocotaku-shonan.com/", "review_q": "COCOタク 湘南店 神奈川", "review_name": "COCOタク 湘南店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "大型犬2頭OK", "2頭OK", "同乗は2人まで"], "points": ["当日予約可", "24時間受付", "前日までキャンセル無料"]}, {"id": "Dd6859ef", "name": "COCOタク 神奈川中央店", "pref": "神奈川県", "areas": ["東京", "神奈川", "静岡"], "area_text": "神奈川県全域、東京都多摩地区、静岡県東部（海老名・座間・大和・綾瀬が中心）", "shop": [35.446, 139.391], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://coco-pettaxi-kanagawa-chuo.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://coco-pettaxi-kanagawa-chuo.com/", "review_q": "COCOタク 神奈川中央店 神奈川", "review_name": "COCOタク 神奈川中央店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D3cc975b", "name": "COCOタク 神奈川北店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "川崎市全区、横浜市（港北・鶴見・都筑・青葉・神奈川・保土ケ谷・緑・旭）、近隣も相談", "shop": [35.59, 139.6], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi-wans.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://cocotaxi-wans.com/", "review_q": "COCOタク 神奈川北店 神奈川", "review_name": "COCOタク 神奈川北店", "hours": "8-20", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D227d031", "name": "COCOタク 西湘秦野店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "秦野・伊勢原・厚木・小田原・平塚を中心に長距離も相談", "shop": [35.375, 139.2], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-cocotaku-hadano.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード", "url": "https://pet-taxi-cocotaku-hadano.com/", "long": true, "review_q": "COCOタク 西湘秦野店 神奈川", "review_name": "COCOタク 西湘秦野店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "De65cb2d", "name": "Legolas House（レゴラスハウス）", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.513, 139.433], "fare": {"kind": "table", "table": [[5, 3850], [10, 4950], [15, 6050], [20, 7150], [25, 8250], [30, 9350], [35, 10450], [40, 11550], [45, 12650], [50, 13750]], "roundTable": [[5, 6160], [10, 7920], [15, 9680], [20, 11440], [25, 13200], [30, 14960], [35, 16720], [40, 18480], [45, 20240], [50, 22000]], "wait": {"free": 0, "unit": 30, "yen": 550}, "tax": "", "src": "https://www.legolashouse.com/price"}, "pay": "", "url": "https://www.legolashouse.com/", "review_q": "Legolas House 神奈川", "review_name": "Legolas House", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "同乗は1人まで"], "points": ["24時間受付"]}, {"id": "D945f580", "name": "ikimono care（イキモノケア）", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "東京・神奈川（ほかは相談）", "shop": [35.42, 139.66], "fare": {"kind": "time", "time": {"first": [90, 5720], "unit": [15, 1430], "discount": {"min": 120, "rate": 0.05}}, "pick": {"km": 10, "yen": 0, "per": 825, "unit": 10}, "back": {"km": 10, "yen": 0, "per": 825, "unit": 10}, "tax": "税込", "src": "https://www.ikimonocare.com/"}, "pay": "", "url": "https://www.ikimonocare.com/", "review_q": "ikimono care 神奈川", "review_name": "ikimono care", "hours": "8-20", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "大きめのワゴン（ハイエース）", "limits": ["車：大きめのワゴン（ハイエース）"], "points": ["当日予約可"]}, {"id": "D5598693", "name": "ふわふわペットタクシー", "pref": "神奈川県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "関東近県から全国（沖縄・離島は不可）", "shop": [35.441, 139.528], "fare": {"base": [3100, 5], "tiers": [[6, 100, 200], [101, 200, 130], [201, null, 110]], "tax": "消費税なし", "src": "https://pet-yokohama.com/", "pick": {"km": 8, "yen": 0, "per": 100}, "wait": {"free": 20, "unit": 10, "yen": 250}, "night": {"from": 22, "to": 8, "rate": 0.3}}, "pay": "現金・カード・電子マネー・QR（フェリー長距離は事前決済）", "url": "https://pet-yokohama.com/", "long": true, "review_q": "ふわふわペットタクシー 神奈川", "review_name": "ふわふわペットタクシー", "hours": "", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird"], "no": []}, "car_type": "ミニバン・ワゴン", "limits": ["車：ミニバン・ワゴン", "大型犬1頭まで", "頭数で料金は変わらない", "同乗は3人まで"], "points": ["当日予約可", "24時間受付", "介助のサポートあり"]}, {"id": "D5604536", "name": "やこうDogはうす", "pref": "神奈川県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "横浜・川崎・東京中心。神奈川・千葉・埼玉、長距離も", "shop": [35.508, 139.676], "fare": {"base": [300, 1], "tiers": [[2, 50, 300], [51, 100, 250], [101, null, 200]], "tax": "税別", "src": "https://yakodoghouse.com/pet-taxi-price/", "pick": {"per": 150}, "back": {}, "wait": {"free": 30, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 7, "rate": 0.2}, "fixed": [{"a": "羽田空港|東京国際空港", "b": "成田空港|成田国際空港", "yen": 28000, "toll": true, "label": "羽田空港⇔成田空港の固定料金、高速道路料金込み"}, {"a": "羽田空港|東京国際空港", "b": "横須賀基地|米海軍横須賀|Navy Lodge|ネイビーロッジ|横須賀市本町|横須賀市稲岡町|横須賀市楠ケ浦町|横須賀市楠ヶ浦町", "yen": 25000, "toll": true, "label": "羽田空港⇔横須賀（基地周辺）の固定料金、高速道路料金込み"}, {"a": "成田空港|成田国際空港", "b": "横須賀基地|米海軍横須賀|Navy Lodge|ネイビーロッジ|横須賀市本町|横須賀市稲岡町|横須賀市楠ケ浦町|横須賀市楠ヶ浦町", "yen": 38000, "toll": true, "label": "成田空港⇔横須賀（基地周辺）の固定料金、高速道路料金込み"}, {"a": "羽田空港|東京国際空港", "b": "横田基地", "yen": 26000, "toll": true, "label": "羽田空港⇔横田基地の固定料金、高速道路料金込み"}, {"a": "成田空港|成田国際空港", "b": "横田基地", "yen": 36000, "toll": true, "label": "成田空港⇔横田基地の固定料金、高速道路料金込み"}]}, "pay": "", "url": "https://yakodoghouse.com/", "long": true, "review_q": "やこうDogはうす 神奈川", "review_name": "やこうDogはうす", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "頭数で料金は変わらない", "現金のみ"], "points": ["大型犬OK", "往復の割引あり"]}, {"id": "Dc7b4703", "name": "わんにゃんハイヤー Angel Buggy", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.568, 139.655], "fare": {"base": [800, 2], "tiers": [[3, null, 400]], "tax": "", "src": "https://www.angel-buggy.com/ryoukin.html", "pick": {"yen": 1300, "unsure": false}}, "pay": "", "url": "https://www.angel-buggy.com/", "review_q": "わんにゃんハイヤー Angel Buggy 神奈川", "review_name": "わんにゃんハイヤー Angel", "hours": "8-19", "flex": false, "closed": [], "lead_days": 0, "cut": 16, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["当日予約可"]}, {"id": "D68f9d95", "name": "ペットタクシー Animals", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "神奈川発、全国", "shop": [35.4, 139.591], "fare": {"base": [2500, 5], "tiers": [[6, 100, 300], [101, 200, 250], [201, null, 200]], "tax": "税込", "src": "https://h12150825.wixsite.com/taxi-animals", "pick": {"km": 3, "yen": 0, "per": 400, "unit": 2}, "back": {}, "wait": {"free": 15, "unit": 15, "yen": 300}, "night": {"from": 20, "to": 8, "rate": 0.2}}, "pay": "", "url": "https://h12150825.wixsite.com/taxi-animals", "long": true, "review_q": "ペットタクシー Animals 神奈川", "review_name": "Animals", "hours": "8-20", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "fish"], "no": []}, "car_type": "ミニバン・ワゴン", "limits": ["車：ミニバン・ワゴン"], "points": ["飼い主さんの同乗無料"]}, {"id": "D8da1ced", "name": "ペットタクシー わんだにゃー", "pref": "神奈川県", "areas": ["東京", "神奈川"], "area_text": "神奈川・東京中心に全国", "shop": [35.339, 139.49], "fare": null, "pay": "JCBタクシーチケット取扱", "url": "https://wan.da-nya.com/", "long": true, "review_q": "ペットタクシー わんだにゃー 神奈川", "review_name": "わんだにゃー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": true, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"]}, {"id": "Daed391e", "name": "ペットタクシー シアンシャ 厚木店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "厚木・伊勢原・海老名・愛甲郡", "shop": [35.441, 139.364], "fare": {"base": [660, 0], "tiers": [[1, null, 330]], "tax": "", "src": "https://chienchat.jp/atsugi/", "pick": {"per": 330}, "wait": {"free": 30, "unit": 30, "yen": 550}}, "pay": "現金・カード／終わったあと", "url": "https://chienchat.jp/atsugi/", "review_q": "ペットタクシー シアンシャ 厚木店 神奈川", "review_name": "シアンシャ 厚木店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン"], "points": ["24時間受付", "ケージを無料で使える", "前日までキャンセル無料", "カード払い可"]}, {"id": "D0437ae3", "name": "ペットタクシー シアンシャ 鎌倉店", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "鎌倉・逗子・葉山中心、藤沢・茅ヶ崎など", "shop": [35.319, 139.551], "fare": {"base": [660, 0], "tiers": [[1, null, 330]], "tax": "", "src": "https://chienchat.jp/kamakura/", "pick": {"per": 330}, "wait": {"free": 30, "unit": 30, "yen": 550}}, "pay": "現金・カード／終わったあと", "url": "https://chienchat.jp/kamakura/", "review_q": "ペットタクシー シアンシャ 鎌倉店 神奈川", "review_name": "シアンシャ 鎌倉店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン"], "points": ["24時間受付", "大型犬OK", "ケージを無料で使える", "前日までキャンセル無料"]}, {"id": "D5f32b1e", "name": "三和交通 ペットタクシー", "pref": "神奈川県", "areas": ["埼玉", "東京", "神奈川"], "area_text": "横浜市北部、東京の多摩の一部、埼玉の和光・朝霞・志木など（23区・武蔵野・三鷹は不可）", "shop": null, "fare": null, "pay": "", "url": "https://www.sanwakoutsu.co.jp/special/pet/", "review_q": "三和交通 ペットタクシー 神奈川", "review_name": "三和交通", "hours": "", "flex": false, "closed": [], "lead_days": 1, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "car_type": "セダン・ワゴン", "limits": ["車：セダン・ワゴン", "同乗は4人まで"], "points": ["大型犬OK"]}, {"id": "Daf1e25b", "name": "湘南Dog Life College（ペットタクシー）", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.264, 139.152], "fare": {"base": [2000, 5], "tiers": [[6, null, 200]], "tax": "税抜", "src": "https://www.shonan-dog-college.jp/taxi", "wait": {"free": 0, "unit": 10, "yen": 200}}, "pay": "", "url": "https://www.shonan-dog-college.jp/taxi", "review_q": "湘南Dog Life College 神奈川", "review_name": "湘南Dog Life", "hours": "9-18", "flex": false, "closed": [0, 6], "lead_days": 3, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "D0b50c1a", "name": "湘南ペットハイヤー", "pref": "神奈川県", "areas": ["埼玉", "千葉", "東京", "神奈川"], "area_text": "神奈川・関東近県中心、全国（島しょ除く）", "shop": [35.335, 139.349], "fare": null, "pay": "", "url": "https://www.shonan-web.com/sub6.html", "long": true, "review_q": "湘南ペットハイヤー 神奈川", "review_name": "湘南ペットハイヤー", "hours": "", "flex": false, "closed": [], "lead_days": 3, "cut": null, "animals": {"all": false, "only": false, "ok": ["bird", "reptile", "fish"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "大型犬2頭OK"]}, {"id": "D06b72ea", "name": "鎌倉ペットタクシー", "pref": "神奈川県", "areas": ["神奈川"], "area_text": "", "shop": [35.354, 139.531], "fare": {"base": [660, 0], "tiers": [[1, null, 300]], "perkmFromStart": true, "pick": {"per": 300}, "night": {"from": 21, "to": 9, "unknown": true}, "tax": "", "src": "https://pets-taxi.net/ja/kamakurapettaxi"}, "pay": "", "url": "https://pets-taxi.net/ja/kamakurapettaxi", "review_q": "鎌倉ペットタクシー 神奈川", "review_name": "鎌倉ペットタクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン"]}, {"id": "D40a4aa0", "name": "COCOタク さいたま南店", "pref": "埼玉県", "areas": ["埼玉", "東京"], "area_text": "さいたま市中心に県南部、東京の一部", "shop": [35.846, 139.66], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165, "rate": 0.5}, "wait": {"free": 10, "unit": 10, "yen": 220}, "tax": "税込", "src": "https://cocotaxi-saitama.com/"}, "pay": "現金・カード・PayPay等", "url": "https://cocotaxi-saitama.com/", "review_q": "COCOタク さいたま南店 埼玉", "review_name": "COCOタク さいたま南店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "2〜3頭OK", "同乗は3人まで"], "points": ["当日予約可", "24時間受付", "大型犬OK", "スロープつき"]}, {"id": "Dfcb8480", "name": "COCOタク 埼玉川越店", "pref": "埼玉県", "areas": ["埼玉"], "area_text": "川越中心に所沢・入間・狭山・飯能・熊谷など。隣県・全国も", "shop": [35.981, 139.479], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "tax": "", "src": "https://pet-taxi-saitama-kawagoe.jp/"}, "pay": "現金・カード・QR", "url": "https://pet-taxi-saitama-kawagoe.jp/", "long": true, "review_q": "COCOタク 埼玉川越店 埼玉", "review_name": "COCOタク 埼玉川越店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "limits": ["同乗は3人まで"], "points": ["24時間受付", "カード払い可"]}, {"id": "D853ae97", "name": "COCOタク 埼玉春日部店", "pref": "埼玉県", "areas": ["茨城", "栃木", "群馬", "埼玉", "千葉"], "area_text": "春日部中心、埼玉東部、茨城（古河・五霞・坂東）、千葉（野田・柏・流山）、栃木（小山・野木）、群馬（館林・邑楽）の一部", "shop": [35.96, 139.77], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-kasukabe.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QR", "url": "https://pet-taxi-kasukabe.com/", "review_q": "COCOタク 埼玉春日部店 埼玉", "review_name": "COCOタク 埼玉春日部店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2〜3頭OK"], "points": ["24時間受付", "前日までキャンセル無料"]}, {"id": "D83f23cc", "name": "COCOタク 川口店", "pref": "埼玉県", "areas": ["埼玉", "東京"], "area_text": "川口市を中心に東京・埼玉", "shop": [35.836, 139.738], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocokawaguchi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード", "url": "https://cocokawaguchi.com/", "review_q": "COCOタク 川口店 埼玉", "review_name": "COCOタク 川口店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D2a4caa6", "name": "COCOタク 練馬店", "pref": "埼玉県", "areas": ["埼玉", "東京"], "area_text": "新座市を中心に東京の練馬区・杉並区・世田谷区・板橋区、埼玉の和光・朝霞・志木・所沢・富士見・三芳", "shop": [35.778, 139.569], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-nerima.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-nerima.com/", "review_q": "COCOタク 練馬店 埼玉", "review_name": "COCOタク 練馬店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D3cc1cce", "name": "ペットケア151A", "pref": "埼玉県", "areas": ["埼玉", "東京"], "area_text": "川口・蕨・草加・戸田、東京の北区・足立・板橋。緊急は全国", "shop": [35.808, 139.724], "fare": {"base": [3000, 15], "tiers": [[16, 25, 280], [26, 50, 230], [51, 100, 180], [101, null, 150]], "tax": "税抜", "src": "https://petcare-151a.com/price.html", "wait": {"free": 30, "unit": 30, "yen": 1000}, "night": {"from": 22, "to": 5, "rate": 0.2}}, "pay": "", "url": "https://petcare-151a.com/pettaxi.html", "review_q": "ペットケア151A 埼玉", "review_name": "ペットケア151A", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "reptile", "fish"], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン"]}, {"id": "Dcfbfbf2", "name": "COCOタク 船橋店", "pref": "千葉県", "areas": ["千葉"], "area_text": "船橋市・鎌ケ谷市・習志野市・浦安市・千葉市・江戸川区・葛飾区・成田空港・羽田空港など", "shop": [35.68, 139.987], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaku-funabashi.moe/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード", "url": "https://cocotaku-funabashi.moe/", "review_q": "COCOタク 船橋店 千葉", "review_name": "COCOタク 船橋店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "De3f35f2", "name": "コインペットタクシー シエロ", "pref": "千葉県", "areas": ["埼玉", "千葉", "東京"], "area_text": "東京23区・都下、千葉、埼玉の一部", "shop": [35.787, 139.903], "fare": {"base": [550, 3], "tiers": [[4, null, 110]], "pick": {"km": 3, "yen": 550, "per": 110}, "back": {"bands": [[4, 0], [10, 550]], "halfRide": true}, "wait": {"first": [20, 550], "free": 0, "unit": 10, "yen": 110, "after": [60, 220]}, "night": {"bands": [[20, 22, 1100], [22, 24, 2200], [0, 5, 3300], [5, 7, 2200], [7, 8, 1100]], "by": "start"}, "tax": "税込", "src": "https://pettaxi.jp/", "fixed": [{"a": "市川市|松戸市|船橋市", "b": "羽田空港|東京国際空港", "yen": 10000, "toll": true, "label": "羽田空港送迎 市川市・松戸市・船橋市から、高速道路料金込み"}, {"a": "市川市|松戸市|船橋市", "b": "成田空港|成田国際空港", "yen": 15000, "toll": true, "label": "成田空港送迎 市川市・松戸市・船橋市から、高速道路料金込み"}]}, "pay": "", "url": "https://pettaxi.jp/", "review_q": "コインペットタクシー シエロ 千葉", "review_name": "コインペットタクシー シエロ", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird", "reptile"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "大型犬2頭OK", "同乗は2人まで", "現金のみ"]}, {"id": "D3c85024", "name": "ペットタクシー パールのしっぽ", "pref": "千葉県", "areas": ["千葉"], "area_text": "千葉市中心、県内外の遠方も（事前予約）", "shop": [35.607, 140.106], "fare": {"base": [1500, 5], "tiers": [[6, null, 200]], "pick": {"km": 5, "yen": 0, "per": 100}, "tax": "", "src": "https://pearlno-shippo.com/"}, "pay": "", "url": "https://pearlno-shippo.com/", "review_q": "ペットタクシー パールのしっぽ 千葉", "review_name": "パールのしっぽ", "hours": "9-21", "flex": false, "closed": [4], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["当日予約可", "大型犬OK"]}, {"id": "Dedcfcd2", "name": "動物苑（ペット送迎）", "pref": "千葉県", "areas": ["茨城", "千葉"], "area_text": "千葉・茨城中心（松戸・柏・牛久）", "shop": null, "fare": {"base": [2500, 5], "tiers": [[6, null, 250]], "tax": "", "src": "https://www.pet594.com/pet-transport/", "pick": {"per": 250}, "wait": {"free": 0, "unit": 10, "yen": 350}}, "pay": "", "url": "https://www.pet594.com/pet-transport/", "review_q": "動物苑 千葉", "review_name": "動物苑", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}}, {"id": "Dc28c19e", "name": "ワンワンハウス（ペットタクシー）", "pref": "群馬県", "areas": ["群馬"], "area_text": "", "shop": [36.4, 139.06], "fare": {"base": [5800, 10], "tiers": [[11, 100, 330], [101, 200, 300], [201, null, 270]], "tax": "税別", "src": "https://wan-wan-house.com/pet-taxi/", "pick": {"km": 5, "yen": 1600, "per": 260}, "back": {"km": 5, "yen": 1600, "per": 260}, "wait": {"free": 0, "unit": 30, "yen": 2500}, "night": {"from": 22, "to": 5, "rate": 0.3}}, "pay": "現金・カード・電子マネー・交通系IC・QR", "url": "https://wan-wan-house.com/pet-taxi/", "review_q": "ワンワンハウス 群馬", "review_name": "ワンワンハウス", "hours": "9-19", "flex": false, "closed": [4], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "同乗は2人まで"], "points": ["飼い主さんの同乗無料", "介助のサポートあり", "カード払い可"]}, {"id": "Dc05105b", "name": "COCOタク 新札幌店", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌市と北海道全域", "shop": [43.03, 141.47], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-sc.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード（送迎後）", "url": "https://pet-taxi-sc.com/", "review_q": "COCOタク 新札幌店 北海道", "review_name": "COCOタク 新札幌店", "hours": "0-24", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "深夜・早朝も相談可", "カード払い可"]}, {"id": "Db405639", "name": "D-RIDE（ペットタクシー）", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌・北広島・江別と近郊（北海道全域も相談）", "shop": [42.99, 141.45], "fare": {"base": [2980, 7], "tiers": [[8, null, 150]], "tax": "税込", "src": "https://d-ride.jp/pettaxi.html", "pick": {"yen": 0}, "wait": {"free": 30, "unit": 10, "yen": 200}, "night": {"from": 22, "to": 7, "rate": 0.2}, "round": 10}, "pay": "現金・カード・電子決済", "url": "https://d-ride.jp/pettaxi.html", "review_q": "D-RIDE 北海道", "review_name": "D-RIDE", "hours": "8-18", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "大型犬3頭まで", "同乗は3人まで"], "points": ["当日予約可", "カード払い可"]}, {"id": "D44948b6", "name": "ぺトタク（札幌・小樽）", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌・小樽近郊", "shop": null, "fare": {"base": [3300, 5], "tiers": [[6, 200, 150], [201, null, 120]], "tax": "税込", "src": "https://pet-tax.com/price", "pick": {"yen": 900, "unsure": false}, "wait": {"free": 10, "unit": 10, "yen": 200}}, "pay": "カード・現金・コンビニ後払い", "url": "https://pet-tax.com/", "review_q": "ぺトタク 北海道", "review_name": "ぺトタク", "hours": "8-20", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "同乗は1人まで"], "points": ["当日予約可", "カード払い可"]}, {"id": "D13b7c6f", "name": "ペット専用タクシー aiai", "pref": "北海道", "areas": ["北海道"], "area_text": "札幌・北海道全域（新千歳空港の送迎パックも）", "shop": [43.05, 141.405], "fare": {"base": [3300, 0], "tiers": [[1, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-aiai.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 0, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 9, "flat": 3300, "by": "start"}, "fixed": [{"a": "札幌市", "b": "新千歳空港|千歳空港", "yen": 20000, "cap": true, "label": "千歳空港⇔札幌市内の送迎パック便"}]}, "pay": "現金・PayPay（カード・QRの記載も）／送迎後", "url": "https://pet-taxi-aiai.com/", "review_q": "ペットタクシー aiai 札幌", "review_name": "aiai", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "大型犬2頭OK", "2〜3頭OK", "同乗は2人まで"], "points": ["当日予約可", "24時間受付", "往復の割引あり"]}, {"id": "D1f53c72", "name": "COCOタク岩手盛岡店", "pref": "岩手県", "areas": ["岩手"], "area_text": "盛岡市・隣接エリア（県内のほかは相談）", "shop": [39.667, 141.142], "fare": {"base": [3300, 10], "tiers": [[11, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocomorioka.iwate.jp/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}}, "pay": "現金のみ（キャッシュレスは順次）", "url": "https://cocomorioka.iwate.jp/", "review_q": "COCOタク岩手盛岡店 岩手", "review_name": "COCOタク岩手盛岡店", "hours": "9-19", "flex": false, "closed": [0, 6], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2〜3頭OK", "同乗は3人まで", "現金のみ"], "points": ["当日予約可", "深夜・早朝の割増なし", "追加料金なし"]}, {"id": "D18363bd", "name": "COCOタク 仙台店", "pref": "宮城県", "areas": ["宮城"], "area_text": "仙台市を中心に近郊市町村", "shop": [38.33, 140.86], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-sendai.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-sendai.com/", "review_q": "COCOタク 仙台店 宮城", "review_name": "COCOタク 仙台店", "hours": "8-18", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D4adf70b", "name": "PETRIP", "pref": "宮城県", "areas": ["宮城"], "area_text": "仙台・名取・利府・多賀城・塩竈・富谷（ほかもできる限り）", "shop": null, "fare": {"base": [2900, 5], "tiers": [[6, 50, 160], [51, null, 140]], "pick": {"yen": 1000, "unknownOver": 10}, "pickEachLeg": true, "wait": {"free": 100000, "unit": 10, "yen": 0}, "night": {"from": 20, "to": 8, "flat": 3000}, "tax": "", "src": "https://petrip.co.jp/"}, "pay": "現金・PayPay", "url": "https://petrip.co.jp/", "review_q": "PETRIP 宮城", "review_name": "PETRIP", "hours": "6-23", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "多頭OK"], "points": ["飼い主さんの同乗無料", "介助のサポートあり", "大型犬OK"]}, {"id": "D30e1838", "name": "ニャンワンクラブ（ペットタクシー）", "pref": "宮城県", "areas": ["宮城"], "area_text": "", "shop": [38.27, 140.85], "fare": null, "pay": "", "url": "https://nyanwan.jp/", "long": true, "review_q": "ニャンワンクラブ 宮城", "review_name": "ニャンワンクラブ", "hours": "9-18", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン"], "points": ["多頭OK", "カード払い可"]}, {"id": "D1132ff9", "name": "冨士タクシー（ペットタクシー）", "pref": "石川県", "areas": ["石川"], "area_text": "金沢・白山・野々市・内灘", "shop": null, "fare": null, "pay": "", "url": "https://www.fuji-taxinet.jp/service/pet-taxi.php", "review_q": "冨士タクシー 石川", "review_name": "冨士タクシー", "hours": "", "flex": false, "closed": [], "lead_days": 1, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile"], "no": []}, "car_type": "セダン・ワゴン", "limits": ["車：セダン・ワゴン", "同乗は4人まで"]}, {"id": "Da40f372", "name": "ペットタクシー With☆（ウィズ）", "pref": "山梨県", "areas": ["山梨"], "area_text": "全国（長距離の直行便が中心）", "shop": [35.62, 138.555], "fare": null, "pay": "前払い（振込・メールで届くカード決済）", "url": "https://pet-taxi.sakura.ne.jp/", "long": true, "review_q": "ペットタクシー With☆ 山梨", "review_name": "With☆", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "limits": ["頭数で料金は変わらない"], "points": ["大型犬OK", "カード払い可"]}, {"id": "Dd472236", "name": "ペットタクシー COCOタク静岡", "pref": "静岡県", "areas": ["静岡"], "area_text": "静岡市・隣接エリア（県内のほかもできる限り）", "shop": [34.993, 138.385], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaxi-shizuoka.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "roundContinuous": true}, "pay": "現金・カード・電子マネー・QRコード決済", "url": "https://cocotaxi-shizuoka.com/", "review_q": "ペットタクシー COCOタク静岡 静岡", "review_name": "COCOタク静岡", "hours": "0-24", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2〜3頭OK", "同乗は3人まで", "大型犬3頭まで"], "points": ["深夜・早朝も相談可", "前日までキャンセル無料", "カード払い可"]}, {"id": "Dc2d8672", "name": "COCOタク 三河豊田店", "pref": "愛知県", "areas": ["愛知"], "area_text": "豊田市を中心に岡崎・刈谷・安城・西尾・豊橋・豊川・蒲郡・新城・田原など三河地方", "shop": [35.03, 137.15], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-aichi-mikawa.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金のみ", "url": "https://pet-taxi-aichi-mikawa.com/", "review_q": "COCOタク 三河豊田店 愛知", "review_name": "COCOタク 三河豊田店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "limits": ["現金のみ"], "points": ["24時間受付"]}, {"id": "D7d26cb4", "name": "COCOタク 名古屋尾張店", "pref": "愛知県", "areas": ["岐阜", "愛知"], "area_text": "江南市を拠点に愛知県・岐阜県の全域（名古屋市・尾張が中心）", "shop": [35.33, 136.87], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-nagoya-owari.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・電子マネー・QRコード決済", "url": "https://pet-taxi-nagoya-owari.com/", "review_q": "COCOタク 名古屋尾張店 愛知", "review_name": "COCOタク 名古屋尾張店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "深夜・早朝も相談可", "カード払い可", "追加料金なし"]}, {"id": "D6c3b09b", "name": "COCOタク 愛知稲沢店", "pref": "愛知県", "areas": ["岐阜", "愛知", "三重"], "area_text": "愛知県全域、三重県（桑名・いなべ・四日市など）、岐阜県（海津・羽島・岐阜など）", "shop": [35.23, 136.76], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotaku-inazawa-aichi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・電子マネー・QRコード決済", "url": "https://cocotaku-inazawa-aichi.com/", "review_q": "COCOタク 愛知稲沢店 愛知", "review_name": "COCOタク 愛知稲沢店", "hours": "0-24", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile"], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D611ee5f", "name": "COCOタク 知多武豊店", "pref": "愛知県", "areas": ["愛知"], "area_text": "知多・三河が中心に愛知県全域（名古屋・豊橋・豊田など）", "shop": [34.85, 136.91], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-aichi-chita-taketoyo.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・QRコード決済・カード", "url": "https://pet-taxi-aichi-chita-taketoyo.com/", "review_q": "COCOタク 知多武豊店 愛知", "review_name": "COCOタク 知多武豊店", "hours": "8-20", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["カード払い可"]}, {"id": "Df997a81", "name": "COCOタク 穂の国店", "pref": "愛知県", "areas": ["静岡", "愛知"], "area_text": "豊橋・東三河、西三河、静岡県の一部（湖西市・浜松市）、愛知県全域", "shop": [34.74, 137.42], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-aicih-toyohashi-honokuni.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "", "url": "https://pet-taxi-aicih-toyohashi-honokuni.com/", "review_q": "COCOタク 穂の国店 愛知", "review_name": "COCOタク 穂の国店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "points": ["当日予約可", "24時間受付", "深夜・早朝も相談可"]}, {"id": "D44cfd16", "name": "HAPPY WITH（ペットタクシー）", "pref": "愛知県", "areas": ["愛知"], "area_text": "", "shop": [35.135, 136.84], "fare": {"kind": "time", "time": {"first": [20, 4400], "unit": [10, 550], "maxKm": 20, "maxTotalKm": 20}, "off": {"from": 9, "to": 18, "perHour": 1650}, "pick": {"km": 3, "yen": 0, "per": 280}, "tax": "税込", "src": "https://happywith.pet/price/"}, "pay": "現金（降りるとき）・事前の振込。カード・QRは不可", "url": "https://happywith.pet/pettaxi/", "review_q": "HAPPY WITH 愛知", "review_name": "HAPPY WITH", "hours": "8-20", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン"], "points": ["当日予約可"]}, {"id": "D1834601", "name": "ZEROペットタクシー", "pref": "滋賀県", "areas": ["滋賀"], "area_text": "滋賀県（栗東・守山・草津など）", "shop": [35.03, 135.995], "fare": null, "pay": "現金・カード・交通系IC・QR", "url": "https://zero808.co.jp/pettaxi/", "review_q": "ZEROペットタクシー 滋賀", "review_name": "ZEROペットタクシー", "hours": "", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["当日予約可", "24時間受付", "カード払い可"]}, {"id": "D7f0d2a2", "name": "COCOタク 京都店", "pref": "京都府", "areas": ["滋賀", "京都"], "area_text": "京都・滋賀", "shop": [34.98, 135.775], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://pet-taxi-kyoto.com/"}, "pay": "", "url": "https://pet-taxi-kyoto.com/", "review_q": "COCOタク 京都店 京", "review_name": "COCOタク 京都店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "Dc9d8a2b", "name": "PetTAXI24", "pref": "京都府", "areas": ["京都"], "area_text": "京都・木津川", "shop": [34.737, 135.82], "fare": {"base": [3300, 20], "tiers": [[21, null, 110, 10]], "tax": "税込", "night": {"from": 21, "to": 6, "flat": 3300}, "src": "https://j-pettaxi.com/"}, "pay": "", "url": "https://j-pettaxi.com/", "review_q": "PetTAXI24 京", "review_name": "PetTAXI24", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": ["bird", "reptile"]}, "limits": ["同乗は2人まで"], "points": ["24時間受付", "深夜・早朝も相談可", "大型犬OK", "カード払い可"]}, {"id": "D25bac67", "name": "ペットサポート てんりん", "pref": "京都府", "areas": ["京都"], "area_text": "京都中心、全国も", "shop": [34.985, 135.759], "fare": {"base": [3000, 10], "tiers": [[11, 100, 200], [101, 200, 120], [201, null, 100]], "pick": {"km": 10, "yen": 0, "per": 100}, "wait": {"free": 20, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 9, "rate": 0.25}, "tax": "税別", "src": "https://ten-rin.jp/taxi/", "fixed": [{"pref": ["京都", "滋賀", "大阪"], "b": "伊丹空港|大阪国際空港", "yen": 12000, "round": 21000, "tax": true, "label": "京都府・滋賀県・大阪府から伊丹空港の空港送迎"}, {"pref": ["京都", "滋賀", "大阪"], "b": "関西国際空港|関西空港|関空", "yen": 21000, "round": 37000, "tax": true, "label": "京都府・滋賀県・大阪府から関西国際空港の空港送迎"}, {"pref": ["京都", "滋賀", "大阪"], "b": "中部国際空港|セントレア", "yen": 40000, "round": 72000, "tax": true, "label": "京都府・滋賀県・大阪府から中部空港の空港送迎"}]}, "pay": "", "url": "https://ten-rin.jp/", "long": true, "review_q": "ペットサポート てんりん 京", "review_name": "ペットサポート てんりん", "hours": "9-21", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["当日予約可", "24時間受付", "深夜・早朝の割増なし", "前日までキャンセル無料"]}, {"id": "Dfc6c94f", "name": "木谷わんわんタクシー", "pref": "京都府", "areas": ["京都"], "area_text": "京都中心（乗るか降りるかが営業エリア内なら他府県も）", "shop": [35.03, 135.75], "fare": {"kind": "time", "time": {"first": [60, 6280], "unit": [30, 3140]}, "tax": "税込", "src": "https://kitani11taxi.com/"}, "pay": "", "url": "https://kitani11taxi.com/", "review_q": "木谷わんわんタクシー 京", "review_name": "木谷わんわんタクシー", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["大型犬OK"]}, {"id": "D7d574bf", "name": "ARC（アルク）Pet Taxi & Pet Sitter", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "関西全域（大阪・兵庫・京都・奈良）", "shop": [34.762, 135.516], "fare": {"base": [3300, 10], "tiers": [[11, 100, 220], [101, null, 110]], "tax": "", "src": "https://pet-arc.com/price/", "pick": {"km": 10, "yen": 0, "per": 110}, "wait": {"free": 20, "unit": 10, "yen": 330}}, "pay": "", "url": "https://pet-arc.com/", "review_q": "ARCPet Taxi & Pet Sitter 大阪", "review_name": "ARCPet Taxi", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "limits": ["頭数で料金は変わらない"]}, {"id": "D436a86d", "name": "COCOタク 南大阪店", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "富田林市を拠点に堺市・大阪狭山市・河内長野市、大阪・奈良・和歌山など近畿一円", "shop": [34.49, 135.59], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://coco-taxi-minami-osaka.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード", "url": "https://coco-taxi-minami-osaka.com/", "review_q": "COCOタク 南大阪店 大阪", "review_name": "COCOタク 南大阪店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "D7d5e5d1", "name": "COCOタク 大阪・東住吉店", "pref": "大阪府", "areas": ["大阪"], "area_text": "大阪市", "shop": [34.61, 135.53], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://pet-cocotaku-higashi-sumiyoshi.com/"}, "pay": "", "url": "https://pet-cocotaku-higashi-sumiyoshi.com/", "review_q": "COCOタク 大阪・東住吉店 大阪", "review_name": "COCOタク 大阪・東住吉店", "hours": "0-24", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "追加料金なし"]}, {"id": "D9895b9b", "name": "COCOタク 大阪柏原店", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "柏原市・八尾市・藤井寺市・羽曳野市・松原市・堺市・大阪市（天王寺・阿倍野・中央・平野）、関西全域", "shop": [34.58, 135.63], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "", "src": "https://cocotaxi-kashiwara.com/price/"}, "pay": "現金・キャッシュレス決済", "url": "https://cocotaxi-kashiwara.com/", "review_q": "COCOタク 大阪柏原店 大阪", "review_name": "COCOタク 大阪柏原店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["当日予約可", "24時間受付"]}, {"id": "D3413153", "name": "COCOタク 守口店", "pref": "大阪府", "areas": ["大阪"], "area_text": "守口市を拠点に門真・枚方・高槻・茨木・吹田など北河内・三島", "shop": [34.73, 135.57], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://coco-taxi-osaka-moriguchi.com/"}, "pay": "", "url": "https://coco-taxi-osaka-moriguchi.com/", "review_q": "COCOタク 守口店 大阪", "review_name": "COCOタク 守口店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付"]}, {"id": "D713b363", "name": "COCOタク 新大阪店", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "大阪市内と近隣市町、兵庫県の一部、伊丹・関西空港", "shop": [34.74, 135.5], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3000}, "tax": "税込", "src": "https://pet-taxi-coco-taku-shin-osaka.com/#section-109"}, "pay": "現金・カード・各種ペイ（送迎後）", "url": "https://pet-taxi-coco-taku-shin-osaka.com/", "review_q": "COCOタク 新大阪店 大阪", "review_name": "COCOタク 新大阪店", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["カード払い可", "追加料金なし"]}, {"id": "D91cc62f", "name": "COCOタク 東大阪店", "pref": "大阪府", "areas": ["大阪"], "area_text": "東大阪市を拠点に大阪東部", "shop": [34.68, 135.62], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://cocotaku-higashiosaka.com/price/"}, "pay": "現金・カード・QRコード決済", "url": "https://cocotaku-higashiosaka.com/", "review_q": "COCOタク 東大阪店 大阪", "review_name": "COCOタク 東大阪店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Db8bafea", "name": "Comasuke（コマスケ）", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "茨木・高槻・豊中など、京都市・亀岡・宇治など。近畿一円・全国", "shop": [34.857, 135.548], "fare": {"base": [3000, 5], "tiers": [[6, null, 180]], "pick": {"per": 180}, "back": {}, "wait": {"free": 0, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 7, "flat": 4500}, "tax": "税抜", "src": "https://comasuke.com/", "round": 10}, "pay": "現金・カード・電子マネー・QR", "url": "https://comasuke.com/", "long": true, "review_q": "Comasuke 大阪", "review_name": "Comasuke", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2頭OK", "同乗は2人まで"], "points": ["当日予約可", "24時間受付", "大型犬OK", "前日までキャンセル無料"]}, {"id": "D6125f28", "name": "DOG HAIR STUDIO KEN（ペットタクシー）", "pref": "大阪府", "areas": ["大阪"], "area_text": "豊中周辺・伊丹空港。輸送は提携会社で全国", "shop": [34.794, 135.452], "fare": {"base": [4000, 10], "tiers": [[11, null, 200]], "pick": {"yen": 0, "unknownOver": 5}, "wait": {"free": 0, "unit": 10, "yen": 300}, "tax": "税込", "src": "https://doghairstudioken.jp/"}, "pay": "カード・電子マネー・交通系IC", "url": "https://doghairstudioken.jp/", "review_q": "DOG HAIR STUDIO KEN 大阪", "review_name": "DOG HAIR", "hours": "10-18", "flex": false, "closed": [3], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}}, {"id": "D01478c8", "name": "アイアールサービス（ペットタクシー）", "pref": "大阪府", "areas": ["大阪"], "area_text": "大阪市内（北区）", "shop": [34.705, 135.498], "fare": {"base": [3000, 10], "tiers": [[11, null, 190]], "tax": "税込", "src": "https://www.i-and-r.com/pettaxi.html", "pick": {"km": 10, "yen": 0, "per": 100, "unsure": true}}, "pay": "", "url": "https://www.i-and-r.com/pettaxi.html", "review_q": "アイアールサービス 大阪", "review_name": "アイアールサービス", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird", "reptile", "fish"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["大型犬OK"]}, {"id": "Da9518d0", "name": "キャリーワン", "pref": "大阪府", "areas": ["大阪"], "area_text": "全国（集荷・お届け）", "shop": [34.814, 135.651], "fare": {"kind": "zones", "zones": [{"label": "枚方市〜枚方市", "a": "枚方市", "b": "枚方市", "one": 3300, "round": 5500}, {"label": "枚方市〜寝屋川市・交野市・八幡市", "a": "枚方市", "b": "寝屋川市|交野市|八幡市", "one": 4400, "round": 6600}, {"label": "枚方市〜高槻市・茨木市・門真市", "a": "枚方市", "b": "高槻市|茨木市|門真市", "one": 5500, "round": 8800}, {"label": "枚方市〜京都市", "a": "枚方市", "b": "京都市", "one": 7700, "round": 11000}, {"label": "枚方市〜大阪市内", "a": "枚方市", "b": "大阪市", "one": 8800, "round": 11000}, {"label": "寝屋川市〜交野市・門真市・茨木市", "a": "寝屋川市", "b": "交野市|門真市|茨木市", "one": 6600, "round": 8800}, {"label": "寝屋川市・交野市・高槻市〜大阪市", "a": "寝屋川市|交野市|高槻市", "b": "大阪市", "one": 7700, "round": 11000}, {"label": "高槻市〜高槻市", "a": "高槻市", "b": "高槻市", "one": 5500, "round": 7700}, {"label": "高槻市〜茨木市", "a": "高槻市", "b": "茨木市", "one": 6600, "round": 8800}], "pick": {"yen": 0, "unknownOver": 10}, "back": {}, "wait": {"free": 30, "unit": 30, "yen": 660}, "tax": "税込", "src": "https://carry-one.net/priceandflow/"}, "pay": "", "url": "https://carry-one.net/", "long": true, "review_q": "キャリーワン 大阪", "review_name": "キャリーワン", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "limits": ["同乗は3人まで"]}, {"id": "D66c4625", "name": "ペットタクシー アイボウ（相棒）", "pref": "大阪府", "areas": ["大阪", "兵庫", "奈良", "和歌山"], "area_text": "羽曳野・柏原・藤井寺・八尾・堺中心、奈良・兵庫・和歌山の一部", "shop": [34.54, 135.61], "fare": {"base": [2000, 5], "tiers": [[6, null, 250]], "tax": "税込", "src": "https://www.aibou.com/info/price.html", "pick": {"km": 5, "yen": 1500, "per": 100}, "back": {}, "wait": {"free": 30, "unit": 15, "yen": 750}}, "pay": "カード可", "url": "https://www.aibou.com/", "review_q": "ペットタクシー アイボウ 大阪", "review_name": "アイボウ", "hours": "8-18", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "limits": ["頭数で料金は変わらない"], "points": ["渋滞でも追加料金なし", "24時間受付"]}, {"id": "D874b316", "name": "ペットタクシー マイファミリー", "pref": "大阪府", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "北大阪・吹田・摂津・茨木・高槻中心、近畿・全国", "shop": [34.82, 135.61], "fare": {"base": [2000, 5], "tiers": [[6, 55, 230], [56, null, 110]], "heavy": {"kg": 15, "add": 500}, "pick": {"km": 5, "yen": 0, "per": 110}, "back": {}, "wait": {"free": 30, "unit": 15, "yen": 300}, "night": {"bands": [[21, 24, 2000], [0, 6, 2000], [6, 8, 1000]]}, "tax": "税込", "src": "https://my-family-takatsuki.com/price.html"}, "pay": "", "url": "https://my-family-takatsuki.com/", "long": true, "review_q": "ペットタクシー マイファミリー 大阪", "review_name": "マイファミリー", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "limits": ["大型犬1頭まで"], "points": ["24時間受付"]}, {"id": "D1c2a5e3", "name": "ミントペットタクシー", "pref": "大阪府", "areas": ["大阪"], "area_text": "堺市西区中心、和泉", "shop": [34.54, 135.47], "fare": {"kind": "table", "table": [[5, 1705], [10, 3410], [15, 5115], [20, 6820]], "pick": {"table": [[5, 1100], [10, 2200], [15, 3300], [20, 4400]]}, "back": {}, "wait": {"free": 30, "unit": 10, "yen": 550}, "night": {"from": 17, "to": 24, "flat": 3300, "by": "start"}, "tax": "税込", "src": "https://www.vet-system.jp/price", "tableOver": 231}, "pay": "", "url": "https://www.vet-system.jp/", "review_q": "ミントペットタクシー 大阪", "review_name": "ミントペットタクシー", "hours": "9-17", "flex": true, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "limits": ["大型犬2頭OK"], "points": ["当日予約可", "カード払い可"]}, {"id": "D09687f4", "name": "COCOタク 神戸西店", "pref": "兵庫県", "areas": ["兵庫"], "area_text": "兵庫県内と長距離", "shop": [34.69, 135.06], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://www.cocotaxi-kobewest.com/"}, "pay": "", "url": "https://cocotaxi-kobewest.com/", "long": true, "review_q": "COCOタク 神戸西店 兵庫", "review_name": "COCOタク 神戸西店", "hours": "9-19", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}}, {"id": "D9f338ec", "name": "ペットタクシー アニマルプラス", "pref": "兵庫県", "areas": ["兵庫"], "area_text": "神戸市の長田区〜芦屋市（須磨・西・北・垂水区は除く）", "shop": [34.705, 135.205], "fare": {"base": [3800, 5], "tiers": [[6, 30, 250], [31, 40, 200], [41, 50, 150], [51, null, 100]], "tax": "", "src": "https://animal-plus.p-kit.com/page0002.html", "back": {"km": 10, "yen": 0, "over": 500}, "wait": {"free": 15, "unit": 15, "yen": 250}}, "pay": "", "url": "https://animal-plus.p-kit.com/", "review_q": "ペットタクシー アニマルプラス 兵庫", "review_name": "アニマルプラス", "hours": "8-19", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "大型犬2頭OK", "現金のみ"]}, {"id": "D72024d3", "name": "ラッキーペットサービス", "pref": "兵庫県", "areas": ["大阪", "兵庫"], "area_text": "西宮・芦屋・宝塚・伊丹・尼崎・川西・神戸・大阪", "shop": [34.757, 135.388], "fare": {"base": [2500, 5], "tiers": [[6, 19, 250], [20, 100, 200], [101, null, 150]], "tax": "税抜", "pick": {"places": [["芦屋市奥池", 1500], ["西宮市(山口町|塩瀬町|名塩|生瀬|北六甲台|すみれ台|東山台|花の峯)", 1500], ["西宮市", 600], ["芦屋市", 800], ["宝塚市|尼崎市|伊丹市|東灘区", 1200]], "per": 150}, "wait": {"free": 20, "unit": 10, "yen": 250}, "night": {"bands": [[19, 20, 1000], [20, 21, 2000], [21, 24, 5000], [0, 6, 5000], [6, 8, 2000]]}, "round": 100, "src": "https://luckypetsv.com/"}, "pay": "", "url": "https://lucky-pettaxi.jimdosite.com/", "review_q": "ラッキーペットサービス 兵庫", "review_name": "ラッキーペットサービス", "hours": "", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "大型犬2頭OK"], "points": ["当日予約可", "深夜・早朝も相談可"]}, {"id": "D154d458", "name": "COCOタク ならまち店", "pref": "奈良県", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "奈良市中心・近畿圏（奈良・大阪・兵庫・京都・滋賀・和歌山）", "shop": [34.677, 135.835], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-nara.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-nara.com/", "review_q": "COCOタク ならまち店 奈良", "review_name": "COCOタク ならまち店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2〜3頭OK", "同乗は3人まで"], "points": ["当日予約可", "24時間受付", "前日までキャンセル無料"]}, {"id": "D0a999a3", "name": "ペットタクシー COCOタク奈良", "pref": "奈良県", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"], "area_text": "奈良市・大和郡山・生駒・木津川・精華（近畿一円、遠方も相談）", "shop": [34.68, 135.75], "fare": {"base": [3300, 0], "tiers": [[1, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-coco-taxi-nara.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300, "by": "start"}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-coco-taxi-nara.com/", "review_q": "ペットタクシー COCOタク奈良 奈良", "review_name": "COCOタク奈良", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車", "2〜3頭OK", "同乗は3人まで"], "points": ["当日予約可", "24時間受付", "前日までキャンセル無料"]}, {"id": "D225080e", "name": "ペッタク（PETTAXI）", "pref": "広島県", "areas": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山", "広島"], "area_text": "広島発・全国（中四国・九州北部・関西が中心）", "shop": [34.335, 132.528], "fare": {"base": [3000, 0], "tiers": [[1, null, 200]], "tax": "税込", "src": "https://pettaku.com/price-guide/", "pick": {"per": 100, "freeToShopKm": 80}, "wait": {"free": 10, "unit": 10, "yen": 300}, "night": {"from": 20, "to": 8, "flat": 3000}, "back": {}}, "pay": "現金・カード・電子マネー・QRコード決済", "url": "https://pettaku.com/", "long": true, "review_q": "ペッタク ペット専門の輸送サービス", "review_exact": "ペッタク 【ペット専門の輸送サービス】", "review_place": "ChIJATs-MDNz2IcRU0HCm0bwaU4", "review_name": "ペッタク", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "同乗は2人まで"], "points": ["当日予約可", "24時間受付", "カード払い可"], "far": ["青森", "岩手", "宮城", "秋田", "山形", "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川", "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "鳥取", "島根", "岡山", "山口", "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島"]}, {"id": "D678e01f", "name": "ペットタクシー 響", "pref": "広島県", "areas": ["広島"], "area_text": "広島市全域・呉・大竹", "shop": [34.385, 132.42], "fare": {"kind": "table", "table": [[5, 2200], [10, 3300], [15, 4400], [20, 6600], [25, 8800], [30, 9900], [35, 11000], [40, 12100], [45, 14300], [50, 16500], [55, 18700], [60, 20900], [65, 23100]], "pick": {"yen": 880, "unsure": true}, "wait": {"free": 0, "unit": 10, "yen": 220}, "tax": "", "src": "https://pettaxihibiki.hp.peraichi.com/", "oneWayRate": 0.2, "kmMode": "floor", "night": {"from": 22, "to": 6, "rate": 0.2}}, "pay": "カード・PayPay・d払いなど", "url": "https://pettaxihibiki.hp.peraichi.com/", "review_q": "ペットタクシー 響 広島", "review_name": "響", "hours": "6-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "同乗は3人まで"], "points": ["大型犬OK", "カード払い可", "PayPay可"]}, {"id": "D7c41c5f", "name": "トップスター（ペットタクシー）", "pref": "徳島県", "areas": ["徳島"], "area_text": "", "shop": [34.135, 134.58], "fare": {"base": [1000, 2], "tiers": [[3, null, 200]], "tax": "税込", "src": "https://www.topstar-tokushima.com/pettaxi", "pick": {"yen": 2500, "unsure": false}, "wait": {"free": 0, "unit": 30, "yen": 500}}, "pay": "", "url": "https://www.topstar-tokushima.com/pettaxi", "review_q": "トップスター 徳島", "review_name": "トップスター", "hours": "10-17", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": ["small", "bird"], "no": []}, "points": ["大型犬OK"]}, {"id": "Db726555", "name": "COCOタク 北九州小倉店", "pref": "福岡県", "areas": ["福岡"], "area_text": "北九州市（小倉）", "shop": [33.84, 130.89], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "税込", "src": "https://pet-taxi-kitakyusyu-kokuraten.com/"}, "pay": "", "url": "https://pet-taxi-kitakyusyu-kokuraten.com/", "review_q": "COCOタク 北九州小倉店 福岡", "review_name": "COCOタク 北九州小倉店", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["当日予約可", "24時間受付"]}, {"id": "D0ec95b6", "name": "COCOタク 福岡東店", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡市東区・古賀市・福津市・新宮町・宗像市・北九州市", "shop": [33.73, 130.47], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://cocotakufukuokahigashi.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300, "by": "start"}, "roundBack": {"per": 165}, "notes": ["高速道路を使う場合、通行料金は別にかかります。", "タクシーチケットは使えません。"]}, "pay": "現金・カード・電子マネー・QRコード決済", "url": "https://cocotakufukuokahigashi.com/", "review_q": "COCOタク 福岡東店 福岡", "review_name": "COCOタク 福岡東店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"], "far": ["山口", "佐賀", "熊本"], "limits": ["同乗は2人まで", "2頭OK", "大型犬1頭まで"]}, {"id": "Df71b3ed", "name": "COCOタク 福岡空港店", "pref": "福岡県", "areas": ["福岡"], "area_text": "糟屋郡を中心に福岡県全域", "shop": [33.62, 130.53], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-fukuoka-airport.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-fukuoka-airport.com/", "review_q": "COCOタク 福岡空港店 福岡", "review_name": "COCOタク 福岡空港店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": true, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Dfad4b87", "name": "COCOタク 福岡筑紫野店", "pref": "福岡県", "areas": ["福岡", "佐賀"], "area_text": "筑紫野・太宰府・春日・大野城・小郡・筑前町・久留米・大牟田、佐賀県（基山・鳥栖）、九州一円", "shop": [33.49, 130.53], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://coco-taxi-fukuoka-chikushino.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QR決済・電子マネー", "url": "https://coco-taxi-fukuoka-chikushino.com/", "review_q": "COCOタク 福岡筑紫野店 福岡", "review_name": "COCOタク 福岡筑紫野店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Df31960d", "name": "ペットタクシー Happy", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡県内・九州・全国（一部離島は別）", "shop": [33.645, 130.69], "fare": {"base": [3300, 5], "tiers": [[6, null, 175]], "tax": "税込", "src": "https://www.pet-taxi-happy.jp/price/", "pick": {"per": 175, "cap": 1100, "capKm": 30}, "back": {}, "wait": {"free": 15, "unit": 10, "yen": 250}, "night": {"from": 20, "to": 8, "rate": 0.2}}, "pay": "", "url": "https://www.pet-taxi-happy.jp/", "long": true, "review_q": "ペットタクシー Happy 福岡", "review_name": "Happy", "hours": "", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["渋滞でも追加料金なし"], "far": ["山口"]}, {"id": "Db28bc5b", "name": "福岡わんわんエクスプレス", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡拠点・全国", "shop": [33.584, 130.402], "fare": {"kind": "zone", "zone": {"city": "福岡市", "one": 3000, "round": 5000}, "wait": {"free": 15, "unit": 15, "yen": 1000}, "night": {"from": 20, "to": 8, "flat": 5000}, "pick": {"yen": 0}, "back": {}, "tax": "", "src": "https://wanwan.pet/"}, "pay": "", "url": "https://wanwan.pet/", "long": true, "review_q": "福岡わんわんエクスプレス 福岡", "review_name": "福岡わんわんエクスプレス", "hours": "0-24", "flex": false, "closed": [], "lead_days": 0, "cut": null, "animals": {"all": false, "only": false, "ok": ["small", "bird"], "no": []}, "car_type": "軽バン", "limits": ["車：軽バン", "大型犬2頭OK", "同乗は1人まで", "現金のみ"], "points": ["当日予約可", "24時間受付"]}, {"id": "D7847612", "name": "福岡ペットタクシー HAKAタク", "pref": "福岡県", "areas": ["福岡"], "area_text": "福岡市内・大野城・春日・志免など", "shop": [33.59, 130.42], "fare": {"base": [2980, 5], "tiers": [[6, 100, 165], [101, null, 132]], "pick": {"per": 100}, "back": {}, "wait": {"free": 60, "unit": 10, "yen": 200, "cap": 1000}, "night": {"from": 21, "to": 8, "flat": 3300}, "tax": "", "src": "https://pettaxi-hakataku.wepage.com/"}, "pay": "現金・カード・交通系IC・QR・iD・QUICPay", "url": "https://pettaxi-hakataku.wepage.com/", "review_q": "福岡ペットタクシー HAKAタク 福岡", "review_name": "福岡ペットタクシー HAKAタク", "hours": "9-19", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": ["small"], "no": []}, "car_type": "軽自動車", "limits": ["車：軽自動車"], "points": ["24時間受付", "大型犬OK", "カード払い可", "PayPay可"]}, {"id": "Db9067d3", "name": "COCOタク 長崎店", "pref": "長崎県", "areas": ["長崎"], "area_text": "長崎市を中心に長崎県全域（離島は問い合わせ）", "shop": [32.76, 129.87], "fare": {"base": [3300, 5], "tiers": [[6, 100, 165], [101, 200, 132], [201, null, 110]], "tax": "税込", "src": "https://pet-taxi-nagasaki.com/", "pick": {"per": 165}, "back": {}, "wait": {"free": 10, "unit": 10, "yen": 220}, "night": {"from": 21, "to": 8, "flat": 3300}}, "pay": "現金・カード・QRコード決済", "url": "https://pet-taxi-nagasaki.com/", "review_q": "COCOタク 長崎店 長崎", "review_name": "COCOタク 長崎店", "hours": "0-24", "flex": false, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "points": ["24時間受付", "カード払い可"]}, {"id": "Dcb3b5a2", "name": "ペットタクシーおさんぽ", "pref": "神奈川県", "areas": ["茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川", "山梨", "長野", "静岡"], "area_text": "相模原市を中心に厚木市・海老名市・愛川町・町田市・八王子市・多摩市", "shop": [35.582, 139.351], "fare": {"base": [0, 0], "tiers": [[1, 5, 480], [6, 50, 330], [51, null, 230]], "tax": "税込", "src": "https://pettaxi-osanpo.com/pettaxi", "pick": {"yen": 1800, "unknownOver": 20}, "back": {}, "wait": {"free": 0, "unit": 10, "yen": 300}, "night": {"from": 21, "to": 6, "rate": 0.2, "onAll": true}}, "pay": "現金・カード", "url": "https://pettaxi-osanpo.com/", "review_q": "ペットタクシーおさんぽ 相模原", "review_name": "おさんぽ", "hours": "0-24", "flex": true, "closed": [], "lead_days": null, "cut": null, "animals": {"all": false, "only": false, "ok": [], "no": []}, "limits": ["同乗は1人まで", "大型犬2頭OK"], "points": ["24時間受付", "カード払い可"]}];/*/DISPLAY_COMPANIES*/
// 提携先のカードのアピールポイント（公式サイトに書いてあることだけ。tools/display_companies.py が作り、gen_areas.py が書き込む）
/*PARTNER_POINTS*/var PARTNER_POINTS = {"P002": ["当日予約可", "深夜・早朝も相談可", "飼い主さんの同乗無料", "ケージを無料で使える"], "P003": ["介助のサポートあり", "大型犬OK"]};/*/PARTNER_POINTS*/
// 条件のタグ（乗れる人数・頭数・お支払いの決まり。Nori 2026-11-01）。tools/display_companies.py が作り、gen_areas.py が書き込む
/*PARTNER_LIMITS*/var PARTNER_LIMITS = {"P002": ["車：軽バン", "多頭OK", "現金のみ"], "P003": ["車：セダン"]};/*/PARTNER_LIMITS*/
/* ───────── 提携していない会社は名前を出さない・お誘いした会社だけの見本画面（Nori 2026-11-02「AとC」） ───────── */

// 名前・口コミ・お店の正確な場所を出さない会社か。問い合わせできない会社（表示だけ・全社準備中のあいだの提携先）はすべて。見本の会社だけ例外
function isOpen_(id) { return !!(CONFIG.OPEN_PARTNERS || {})[id]; }
function openDisplay_(id) { var d = (CONFIG.OPEN_PARTNERS || {})[id]; return d ? DISPLAY_COMPANIES.filter(function(c) { return c.id === d; })[0] || null : null; }
function openDisplayIds_() { var o = CONFIG.OPEN_PARTNERS || {}; return Object.keys(o).map(function(k) { return o[k]; }); }
function isListed_(id) { return (CONFIG.LISTED_IDS || []).indexOf(id) >= 0; }
function isAnon_(id, demoId) {
  if (demoId && id === demoId) return false;
  if (isListed_(id) || isOpen_(id)) return false;
  return isDisplayOnly_(id) || !!CONFIG.SHOW_ALL_CANDIDATES;
}
// 「東京都・杉並区あたりの会社」。対応エリアの最初の市区町村から（都道府県の名前と同じなら付けない）
function anonLabel_(pref, areaText) {
  pref = String(pref || '');
  var m = String(areaText || '').match(/^([^・、,，\s（(を]+?[区市町村])(?=[・、,，\s（(を]|$)/), city = m ? m[1] : '';
  if (city && pref && city.indexOf(pref.replace(/[都道府県]$/, '')) === 0) city = '';
  return (pref || 'お近く') + (city ? '・' + city + 'あたり' : '') + 'の会社';
}
// カードを名前なしにする。見本の会社は名前を出し、提携したときの見え方にする（問い合わせは送れない）
function anonCard_(card, pref, areaText, demoId) {
  if (demoId && card.id === demoId) {
    card.demo = true; card.display_only = false; delete card.token; delete card.expires;
    card.check = [];
    return card;
  }
  if (isListed_(card.id)) { card.listed = true; return card; }
  if (!isAnon_(card.id, demoId)) return card;
  card.label = anonLabel_(pref, areaText); card.anon = true;
  if (card.shop) card.shop = [Math.round(card.shop[0] * 100) / 100, Math.round(card.shop[1] * 100) / 100]; // 道のりの目安に使うだけ（1kmくらいにまるめる）
  return card;
}
// 見本のリンクの合言葉：<会社のID>.<署名>
function demoToken_(id) { return id + '.' + sign_('demo:' + id); }
function demoId_(tok) {
  var m = String(tok || '').match(/^([A-Za-z0-9_-]{2,40})\.([A-Za-z0-9_-]{10,40})$/);
  if (!m || sign_('demo:' + m[1]) !== m[2]) return '';
  return isDisplayOnly_(m[1]) || partnerById_(m[1]) ? m[1] : '';
}
function demoInfo_(tok) {
  var id = demoId_(tok);
  if (!id) return {ok:false};
  var c = DISPLAY_COMPANIES.filter(function(x) { return x.id === id; })[0], pt = c ? null : partnerById_(id);
  return {ok:true, id:id, name:c ? c.name : pt.name, pref:c ? c.pref : ''};
}
function demoUrl_(id) { return CONFIG.SITE_URL + '?demo=' + encodeURIComponent(demoToken_(id)) + '#form'; }
// お誘い用の見本のリンクを「見本リンク」タブに書き出す（スクリプトの画面で1回動かす。何も送らない）
function makeDemoLinks() {
  var sh = ensureSheet_(SpreadsheetApp.getActive(), '見本リンク', ['ID', '会社', '都道府県', '見本のリンク']);
  var rows = DISPLAY_COMPANIES.map(function(c) { return [c.id, c.name, c.pref, demoUrl_(c.id)]; });
  // 提携先シートの会社（準備中のあいだは名前を伏せているので、見本のリンクも作る。Nori 2026-11-08「見本のリンクつくってよ」）
  partners_().forEach(function(pt) { if (pt.id && !isDisplayOnly_(pt.id)) rows.push([pt.id, pt.name, (pt.areas || []).join('・'), demoUrl_(pt.id)]); });
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 4).clearContent();
  if (rows.length) sh.getRange(2, 1, rows.length, 4).setValues(rows);
  return rows.length;
}
function isDisplayOnly_(id) {
  return DISPLAY_COMPANIES.some(function(c) { return c.id === id; });
}
// 表示だけの会社のカード（依頼できない）。口コミの星は、ページがカードを出したあとに selectionScores_ でまとめて取り寄せる
// お迎えの都道府県に対応している会社だけを出し、公式サイトの料金表から料金の目安を計算する（Nori 2026-10-31「大阪の住所で全国の会社が出た。料金も出ない」）
function displayCards_(r, p) {
  if (!CONFIG.SHOW_ALL_CANDIDATES) return [];
  var now = new Date(), from = null;
  // 犬・猫のほかの子：断る・犬猫のみと書いてある会社は出さない。乗せられると書いてある会社を先に並べ、分からない会社は「確認中」と書く
  var kinds = petsOf_(r).map(animalKind_).filter(function(k, i, a) { return k && a.indexOf(k) === i; });
  var animalOk = function(c) { return kinds.map(function(k) { return displayAnimalOk_(c, k); }); };
  var kindText = kinds.map(function(k) { return ANIMAL_LABEL[k]; }).join('・');
  var rd = {};
  try { rd = JSON.parse((p || {}).route_details || '{}') || {}; from = rd.from; } catch (e) {}
  var opened = openDisplayIds_();
  var list = DISPLAY_COMPANIES.filter(function(c) { return opened.indexOf(c.id) < 0 && displayServes_(c, r['都府県'], from) && displayInTime_(c, r['希望日時'], now) && animalOk(c).indexOf(false) < 0; });
  if (p) loadRoadKm_(list.filter(function(c) { return c.shop && c.fare; }).map(function(c) { return {lat:c.shop[0], lng:c.shop[1]}; }), [rd.from, rd.to, rd.backFrom, rd.backTo]);
  return list.map(function(c) {
    var unsure = '', unknown = animalOk(c).indexOf(null) >= 0;
    if (kinds.length) unsure += unknown ? kindText + 'を乗せられるかは確認中です。' : '公式サイトに' + kindText + 'も乗せられると書いてあります。';
    var price = p && displayPrice_(c, p) || {amount:null,text:'料金はお見積もり',night:''};
    var card = { id:c.id, label:c.name, display_only:true, animal_unknown:unknown, points:c.points || [], limits:c.limits || [], shop:c.shop || null,
      car:'所在地：' + c.pref + (c.area_text ? '。対応エリア：' + c.area_text + '（公式サイトの記載）' : '（対応エリアは確認中です）') + (c.car_type ? '。車：' + c.car_type + '（公式サイトの記載・会社の回答より）。' : '。車の詳細はまだ確認中です。') + unsure,
      payment:c.pay ? 'お支払い：' + c.pay + '（公式サイトの記載）' : 'お支払い方法はまだ確認中です',
      price:price, review:null, check:[] };
    if (isAnon_(c.id, p && p.demo_id)) card.car = (c.car_type ? '車：' + c.car_type + '（公式サイトの記載・会社の回答より）。' : '車の詳細はまだ確認中です。') + unsure;
    return anonCard_(card, c.pref, c.area_text, p && p.demo_id);
  }).sort(function(a, b) { // 犬・猫のほかの子を乗せられると書いてある会社を先に。その中で料金が出せる会社を安い順に、そのあとお見積もりの会社
    var x = a.price.amount == null ? Infinity : a.price.amount, y = b.price.amount == null ? Infinity : b.price.amount;
    return (a.animal_unknown ? 1 : 0) - (b.animal_unknown ? 1 : 0) || x - y;
  });
}

// カードの shop（お店の位置）：ページが道路データでお店→お迎えの場所の車の道のりを調べ、近い順に並べたり距離でしぼったりする
// （Nori 2026-11-01「直線で出すのやめて。クルマでの最短ルートでだして」）。分からなければ null
// 提携先のお店の位置（tools/fares.json の shop）。分からなければ null
function partnerShop_(id) {
  if (typeof SELECTION_FARES === 'undefined' || !SELECTION_FARES) return null;
  var key = Object.keys(SELECTION_FARES).filter(function(k) { return SELECTION_FARES[k].partner_id === id; })[0];
  return key && SELECTION_FARES[key].shop || null;
}
// 2点の直線距離（km）
function kmBetween_(a, b) {
  var t = Math.PI / 180, h = Math.pow(Math.sin((b.lat - a.lat) * t / 2), 2) + Math.cos(a.lat * t) * Math.cos(b.lat * t) * Math.pow(Math.sin((b.lng - a.lng) * t / 2), 2);
  return 6371 * 2 * Math.asin(Math.sqrt(Math.min(1, h)));
}
// お店→お迎えの場所、降りた場所→お店の車の道のり（km）。Nori 2026-11-01「直線距離はやめて。車での最短距離にして」
// displayCards_ が道路データ（ページの地図と同じ OSRM）にまとめて聞いて ROAD_KM に入れる。取れなかったときだけ直線×1.3の概算（カードにそう書く）
var ROAD_KM = null;
function roadKey_(a, b) { return [a.lat, a.lng, b.lat, b.lng].map(function(v) { return Number(v).toFixed(4); }).join(','); }
function roadKm_(shop, at, back) {
  var v = ROAD_KM && ROAD_KM[back ? roadKey_(at, shop) : roadKey_(shop, at)];
  return typeof v === 'number' && isFinite(v) ? v : null;
}
function legKm_(shop, at, back) { var r = roadKm_(shop, at, back); return r != null ? r : kmBetween_(shop, at) * 1.3; }
// お店たち×場所たちの車の道のりを1回でまとめて聞く（お店→場所と場所→お店の両方）。場所は約10mに丸める。結果は6時間覚えておく
function loadRoadKm_(shops, pts) {
  ROAD_KM = ROAD_KM || {};
  var ok = function(v) { return v && isFinite(v.lat) && isFinite(v.lng); }, seen = {};
  pts = pts.filter(function(v) { var k = ok(v) && roadKey_(v, v); if (!k || seen[k]) return false; seen[k] = 1; return true; });
  shops = shops.filter(function(v) { var k = ok(v) && 's' + roadKey_(v, v); if (!k || seen[k]) return false; seen[k] = 1; return true; });
  for (var i = 0; i < shops.length; i += 90) (function(part) {
    var todo = part.filter(function(sp) { return pts.some(function(pt) { return roadKm_(sp, pt) == null || roadKm_(sp, pt, true) == null; }); });
    if (!todo.length || !pts.length) return;
    var all = pts.concat(todo), n = pts.length;
    var url = CONFIG.ROAD_API + '/table/v1/driving/' + all.map(function(v) { return Number(v.lng).toFixed(5) + ',' + Number(v.lat).toFixed(5); }).join(';') + '?annotations=distance';
    try {
      var cache = null, key = '', j = null;
      try { cache = CacheService.getScriptCache(); key = 'road:' + Utilities.base64Encode(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, url)); var hit = cache.get(key); if (hit) j = JSON.parse(hit); } catch (e) { cache = null; }
      if (!j) {
        var res = UrlFetchApp.fetch(url, {muteHttpExceptions:true});
        if (res.getResponseCode() !== 200) throw new Error('HTTP ' + res.getResponseCode());
        j = JSON.parse(res.getContentText());
        if (j.code !== 'Ok' || !j.distances) throw new Error(j.code);
        try { if (cache) cache.put(key, JSON.stringify({code:j.code, distances:j.distances}), 21600); } catch (e) {}
      }
      todo.forEach(function(sp, k) {
        pts.forEach(function(pt, q) {
          var go = j.distances[n + k] && j.distances[n + k][q], back = j.distances[q] && j.distances[q][n + k];
          if (go != null && isFinite(go)) ROAD_KM[roadKey_(sp, pt)] = go / 1000;
          if (back != null && isFinite(back)) ROAD_KM[roadKey_(pt, sp)] = back / 1000;
        });
      });
    } catch (e) { try { log_('車の道のり：取れない ' + e); } catch (e2) {} }
  })(shops.slice(i, i + 90));
}
// お迎えの都道府県に対応しているか。お店の位置が分かる会社は、お迎えの場所が遠すぎる（直線で DISPLAY_MAX_KM 超）ときも外す
// far＝公式サイトに「◯◯県へお迎えに行く」とはっきり書いてある県の外（Nori 2026-11-14）。その県ではお店からの上限を DISPLAY_FAR_KM にする
function displayServes_(c, pref, from) {
  var far = (c.far || []).indexOf(pref) >= 0;
  if ((c.areas || []).indexOf(pref) < 0 && !far) return false;
  if (c.shop && from && isFinite(from.lat) && isFinite(from.lng) && kmBetween_({lat:c.shop[0], lng:c.shop[1]}, from) > (far ? CONFIG.DISPLAY_FAR_KM : CONFIG.DISPLAY_MAX_KM)) return false;
  return true;
}

// 表示だけの会社の料金の目安。tools/display_companies.json の fare（公式サイトの料金表）を決まった式で計算する（AIには計算させない）
// base＝[基本料金, 含まれるkm]、tiers＝[[何km目から, 何km目まで, 1kmごとの円]]、pick/back＝迎車・回送、wait＝待ち時間、night＝夜間・早朝、tax＝税込/税抜
// 公式サイトに書いてある区間の定額（空港送迎など。Nori 2026-11-02「空港とか定額が載ってるならそれ使ってよあたりまえ」）。距離の式より先に見る。
// F.fixed＝[{a:'乗る場所の正規表現', pref:[お迎えの都道府県], b:'行き先の正規表現', yen:片道, round:往復, label:'説明', tax:true＝税別, toll:true＝高速代込み, cap:true＝距離の式のほうが安ければそちら}]。
// どちら向きでも同じ。往復は行きと帰りの両方が同じ定額に当たるときだけ（round がなければ片道×2）
function displayFixed_(c, p) {
  var F = c.fare, round = p.trip === '往復';
  function side(z, s, isPickup) {
    s = String(s || '');
    if (z.a) return new RegExp(z.a).test(s);
    return (isPickup && (z.pref || []).indexOf(p.pref) >= 0) || (z.pref || []).some(function(x) { return s.indexOf(x) >= 0; });
  }
  function hit(x, y) {
    for (var i = 0; i < (F.fixed || []).length; i++) {
      var z = F.fixed[i], B = new RegExp(z.b);
      if ((side(z, x, true) && B.test(String(y || ''))) || (B.test(String(x || '')) && side(z, y, false))) return z;
    }
    return null;
  }
  var z = hit(p.pickup, p.dropoff), z2 = round && z ? hit(p.return_pickup || p.dropoff, p.return_dropoff || p.pickup) : null;
  if (!z || (round && z2 !== z)) return null;
  var y = round ? (z.round || z.yen * 2) : z.yen;
  if (z.tax) y = Math.ceil(y * 11 / 10);
  var l = {ride:y, pickup:0, returnFee:0, nightExtra:0, wait:0, rounding:0, amount:y};
  return {amount:y, text:yen_(y), local:l, highway:null, fixed:true, cap:!!z.cap, tollIncluded:!!z.toll, incompleteFees:false, taxUnknown:false, night:'', pickupNote:'', routeNote:'',
    planNote:'公式サイトに書いてある定額（' + z.label + '）で出した目安です。' + (round ? (z.round ? '往復の定額です。' : '行きと帰りの2回分です。') : '') + (z.tax ? '定額は税別のため、消費税10%を足しています。' : '') + (z.toll ? '' : '有料道路を使うときは実費が別にかかります。')};
}
function displayPrice_(c, p) {
  var fx = c.fare && c.fare.fixed ? displayFixed_(c, p) : null;
  if (fx && !fx.cap) return fx;
  var r = displayPriceCalc_(c, p);
  return fx && (!r || fx.amount < r.amount) ? fx : r; // cap：距離の式のほうが安ければそちら（aiai の返事は札幌市東区→新千歳で式どおり17,325円。パック便は20,000円）
}
function displayPriceCalc_(c, p) {
  var F = c.fare;
  if (!F) return null;
  var d;
  try { d = JSON.parse(p.route_details); } catch (e) { return null; }
  // 長距離（250km超）は、長距離を受けている会社（display_companies.py の long＝対応地域に「全国」「長距離」）だけ3000kmまで計算する。
  // ほかの会社は、受けない距離の大きな金額を出さないよう「お見積もり」（Nori 2026-11-08「長距離の計算をするのは長距離を請け合ってる会社だけ」）
  var maxKm = c.long ? 3000 : 250;
  function validKm(v) { return typeof v === 'number' && isFinite(v) && v >= 1 && v <= maxKm; }
  function pt(v) { return v && isFinite(v.lat) && isFinite(v.lng) && v.lat >= 20 && v.lat <= 46 && v.lng >= 122 && v.lng <= 154; }
  if (!d || !validKm(d.km) || !validKm(d.backKm) || !pt(d.from) || !pt(d.to)) return null;
  var round = p.trip === '往復';
  if (round && (!pt(d.backFrom) || !pt(d.backTo))) return null;
  var shop = c.shop ? {lat:c.shop[0], lng:c.shop[1]} : null;
  if (F.kind === 'time' && F.time.maxKm && Math.max(d.km, round ? d.backKm : 0) > F.time.maxKm) return null; // その距離は別のプラン（料金が分からない）
  if (F.kind === 'time' && F.time.maxTotalKm && shop && d.km + legKm_(shop, d.from) > F.time.maxTotalKm) return null; // 迎車と乗車を合わせて超えると距離のプラン（金額が「〜」でしか分からない。HAPPY WITH の返事）
  if (F.kind === 'table' && F.tableOver == null && Math.max(d.km, round ? d.backKm : 0) > F.table[F.table.length - 1][0]) return null; // 料金表の距離を超える（お見積もり）
  var zoneHit = F.kind === 'zones' ? findZone(p.pickup, p.dropoff) : null;
  if (F.kind === 'zones' && (!zoneHit || (round && findZone(p.return_pickup || p.dropoff, p.return_dropoff || p.pickup) !== zoneHit))) return null; // 区間の料金表にない
  if (F.kind === 'zone' && !(inZone(p.pickup) && inZone(p.dropoff) && (!round || (inZone(p.return_pickup || p.dropoff) && inZone(p.return_dropoff || p.pickup))))) return null; // 市の外は料金表にない
  // 距離の数え方：ふつうは1km単位に切り上げ。kmMode 'exact'＝小数のまま（円未満は切り捨て）、'floor'＝1km未満を切り捨て（返事の内訳で分かった会社）
  function kmOf(km) { return F.kmMode === 'exact' ? Math.round(km * 10) / 10 : F.kmMode === 'floor' ? Math.floor(km) : Math.ceil(km); }
  function distRide(km) { // 乗った距離の運賃
    km = kmOf(km);
    var amount = F.base[0], bk = F.base[1];
    if (F.heavy && Number(p.weight) >= F.heavy.kg) amount += F.heavy.add; // 重い子は基本料金が上がる会社
    F.tiers.forEach(function(t) {
      var a = Math.max(t[0], bk + 1), z = Math.min(km, t[1] == null ? Infinity : t[1]);
      if (z >= a) amount += (F.kmMode === 'exact' && !t[3] ? (z - a + 1) : Math.ceil((z - a + 1) / (t[3] || 1))) * t[2]; // t[3]：何kmごとか（なければ1km）
    });
    return Math.floor(amount); // 小数の距離のときは円未満を切り捨て
  }
  // 迎車（お店→乗る場所）・回送（降りた場所→お店）。お店からの距離は直線×1.3の概算
  var legGuess = false; // お迎え・回送の距離を、車の道のりが取れず直線×1.3で出したか
  function leg(rule, at, rideYen, back, place, dest) {
    if (rule === undefined) return {yen:0, unknown:false, missing:true}; // 料金表に書いていない
    // 遠くからお店の近くへ送るときは、お迎えに向かう距離の料金をとらない（高速代の実費だけ。ペッタクの申し込み 2026-11-08）
    if (rule && rule.freeToShopKm != null && shop && dest && kmBetween_(shop, dest) <= rule.freeToShopKm && kmBetween_(shop, at) > rule.freeToShopKm) return {yen:0, unknown:false};
    if (rule.places) { // 市区町村ごとの定額（[[場所の正規表現, 円]]、上から順に見る）。どれにも当たらなければ下の距離の決まり（ラッキーペットサービス）
      for (var pi = 0; pi < rule.places.length; pi++) if (new RegExp(rule.places[pi][0]).test(String(place || ''))) return {yen:rule.places[pi][1], unknown:false};
    }
    if (rule.unsure && rule.per == null && rule.yen == null) return {yen:0, unknown:true};
    if (rule.per == null && rule.over == null && rule.unknownOver == null && !rule.tiers && !rule.bands && !rule.table) return {yen:rule.yen || 0, unknown:!!rule.unsure};
    if (!shop) return {yen:rule.yen || 0, unknown:true};
    if (roadKm_(shop, at, back) == null) legGuess = true;
    var km = kmOf(legKm_(shop, at, back)), free = rule.km || 0, yen = rule.yen || 0;
    if (rule.freeWithin != null && km <= rule.freeWithin) return {yen:0, unknown:!!rule.unsure}; // お店の近くはお迎え無料（返事で分かった会社）
    if (rule.unknownOver != null) return {yen:yen, unknown:km > rule.unknownOver}; // その距離を超えると別料金（金額は非公開）
    if (rule.tiers) { // 距離の段階で変わる迎車（base＝[円, 含まれるkm]、tiers は乗車と同じ形）
      yen = rule.base[0];
      rule.tiers.forEach(function(t) { var a = Math.max(t[0], rule.base[1] + 1), z = Math.min(km, t[1] == null ? Infinity : t[1]); if (z >= a) yen += Math.ceil((z - a + 1) / (t[3] || 1)) * t[2]; });
      return {yen:yen, unknown:!!rule.unsure};
    }
    if (rule.table) { // 距離ごとの料金表（[[何kmまで, 円]]）。表の先は金額が分からない（ミント）
      for (var ti = 0; ti < rule.table.length; ti++) if (km <= rule.table[ti][0]) return {yen:rule.table[ti][1], unknown:!!rule.unsure};
      return {yen:rule.table[rule.table.length - 1][1], unknown:true};
    }
    if (rule.bands) { // [[何kmまで, 円]]、その先は乗車料金の半額（halfRide）
      for (var i = 0; i < rule.bands.length; i++) if (km <= rule.bands[i][0]) return {yen:rule.bands[i][1], unknown:false};
      return rule.halfRide && rideYen != null ? {yen:Math.ceil(rideYen / 2), unknown:false} : {yen:0, unknown:true};
    }
    if (km > free) {
      if (rule.over != null) yen += rule.over;
      else yen += (F.kmMode === 'exact' && !rule.unit ? (km - free) : Math.ceil((km - free) / (rule.unit || 1))) * rule.per;
    }
    var overCap = rule.capKm != null && km > rule.capKm; // capKm：打ち止めはこの距離まで（その先は公式サイトに書いていない）
    if (rule.cap != null && !overCap) yen = Math.min(yen, rule.cap);
    if (overCap) return {yen:Math.floor(yen), unknown:true};
    if (rule.rate != null) yen = yen * rule.rate; // お迎え料金の割引（例：半額セール 0.5）
    return {yen:Math.floor(yen), unknown:!!rule.unsure};
  }
  var nightUnknown = false;
  function hourOf(at) { var dt = parseJst_(at); return dt ? (dt.getUTCHours() + 9) % 24 : -1; }
  // 夜間・早朝の割増。乗っているあいだ（乗る時刻〜着く時刻）に少しでも割増の時間帯に入れば、その乗車の全部にかける。
  // 着く時刻は1kmを2.4分とみる（見積もりの返事：D-RIDE 23kmで50分、ペッタク 23kmで55分）
  // （D-RIDE・Comasuke・静岡・サポっ人の見積もりと同じ。Nori 2026-11-01「Drideの計算が一番いいね」）。乗る時刻だけで決める会社は N.by = 'start'（奈良・aiai）
  function nightExtra(amount, at, km) {
    var N = F.night, t0 = parseJst_(at);
    if (!N || !t0) return 0;
    var span = N.by === 'start' || !km ? 0 : Math.ceil(km * 2.4), hours = [];
    for (var m = 0; m <= span; m += 5) hours.push((new Date(t0.getTime() + Math.min(m, span) * 60000).getUTCHours() + 9) % 24);
    if (span % 5) hours.push((new Date(t0.getTime() + span * 60000).getUTCHours() + 9) % 24);
    if (N.bands) { // 時間帯ごとの定額（乗っているあいだで一番高いもの）
      var best = 0;
      hours.forEach(function(h) { N.bands.forEach(function(b) { if (h >= b[0] && h < b[1]) best = Math.max(best, b[2]); }); });
      return best;
    }
    var inN = function(h) { return N.from > N.to ? (h >= N.from || h < N.to) : (h >= N.from && h < N.to); };
    var on = hours.some(inN);
    if (!on) return 0;
    if (N.unknown) { nightUnknown = true; return 0; } // 割増はあるが金額が書いていない
    // 長距離（250km超）で割合の割増の会社は、夜間・早朝に走る分だけにかける（一部が夜にかかるだけで運賃全部を割増にしない。Nori 2026-11-08）
    if (N.rate && km > 250) return Math.floor(amount * N.rate * hours.filter(inN).length / hours.length);
    return N.rate ? Math.floor(amount * N.rate) : (N.flat || 0);
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
    if (F.kind === 'table') return tableFee(F.kmMode ? kmOf(km) : km, F.table);
    return distRide(km);
  }
  function total(km, backKm) {
    var r1 = ride(km, p.datetime), r2 = round ? ride(backKm, p.return_datetime) : 0;
    if (!round && F.oneWayRate) r1 = Math.floor(r1 * (1 + F.oneWayRate)); // 片道（乗り捨て）の割増（返事で分かった会社）
    var pk = [leg(F.pick, d.from, null, false, p.pickup, d.to)], bk = [leg(F.back, d.to, r1, true, p.dropoff)];
    if (round) { pk.push(leg(F.pick, d.backFrom, null, false, p.return_pickup || p.dropoff, d.backTo)); bk.push(leg(F.back, d.backTo, r2, true, p.return_dropoff || p.pickup)); }
    var nAll = F.night && F.night.onAll; // 割増を迎車・回送にもかける会社
    var n1 = nightExtra(r1 + (nAll ? pk[0].yen + bk[0].yen : 0), p.datetime, km), n2 = round ? nightExtra(r2 + (nAll ? pk[1].yen + bk[1].yen : 0), p.return_datetime, backKm) : 0;
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
    // 往復のときだけ、目的地からお迎えの場所に戻る回送代（距離×円）がかかる会社（COCOタク福岡東の返事 2026-11-10）
    if (round && F.roundBack && F.roundBack.per) chosen.returnFee += Math.floor(kmOf(km) * F.roundBack.per);
    if (/税抜|税別/.test(F.tax) && !/税込/.test(F.tax)) ['ride', 'pickup', 'returnFee', 'nightExtra', 'wait'].forEach(function(k) { chosen[k] = Math.ceil(chosen[k] * 1.1); });
    if (F.longDiscount) { // 合計の金額で割引（[[何円から, 割引の割合]]）
      var s0 = sum(chosen), rate = 0;
      F.longDiscount.forEach(function(x) { if (s0 >= x[0]) rate = x[1]; });
      if (rate) { chosen.discount = Math.floor(s0 * rate); chosen.ride -= chosen.discount; }
    }
    // 計算どおりの金額（円未満は切り捨て）。10円未満を切り捨てる会社は F.round = 10（返事の見積もりで分かった会社）
    var raw = sum(chosen), unit = F.round || 1; chosen.amount = Math.floor(raw / unit) * unit; chosen.rounding = chosen.amount - raw;
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
  if (round && F.roundBack && F.roundBack.per) notes.push('往復のときにかかる、目的地からお迎えの場所に戻る回送代（1kmごと' + yen_(F.roundBack.per) + '）を足しています。');
  (F.notes || []).forEach(function(t) { notes.push(t); }); // 会社の返事で分かった、計算に入れない決まり（高速代は別など）
  var nt = local.nightExtra > 0;
  return {amount:local.amount, text:yen_(local.amount) + (local.pickupUnknown || local.returnUnknown || nightUnknown ? '〜' : ''), local:local, highway:highway,
    incompleteFees:local.pickupUnknown || local.returnUnknown || nightUnknown, taxUnknown:!F.tax,
    night:nt ? '夜間・早朝の割増 ' + yen_(local.nightExtra) + 'を含みます' : F.night ? '指定時刻は夜間・早朝の割増対象外です' : '料金表に夜間・早朝の割増の記載はありません',
    pickupNote:F.pick && F.pick.per != null ? (!shop ? 'お店の場所が分からないため、迎車の距離の分は含めていません。' : legGuess ? '迎車・回送の距離は、道路データが取れなかったため、お店のある市区町村からの直線距離をもとにした概算です。' : '迎車・回送の距離は、お店のある市区町村から車の道のりで計算しています。') : '',
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
/*EMG_REVIEWS*/var EMG_REVIEWS = {"E01": {"query": "動物救急車 大田区", "name": "動物救急車"}, "E02": {"query": "ペットドクターカー", "name": "ペットドクターカー"}, "E04": {"query": "ペットタクシー Animals 横浜市港南区", "name": "Animals"}, "E05": {"query": "コインペットタクシー シエロ", "name": "シエロ"}, "E06": {"query": "ペットタクシー パールのしっぽ 千葉市", "name": "パールのしっぽ"}, "E07": {"query": "ペットタクシー COCOタク さいたま南店", "name": ["COCO", "さいたま"]}, "E08": {"query": "ペットタクシー COCOタク 埼玉川越店", "name": ["COCO", "川越"]}, "E09": {"query": "ペットタクシー COCOタク 埼玉春日部", "name": ["COCO", "春日部"]}, "E10": {"query": "ペットレスキュー 夜間救急搬送", "name": "ペットレスキュー"}, "E12": {"query": "ペット専用タクシー aiai 札幌市白石区", "name": "aiai"}, "E13": {"query": "ペットタクシー COCOタク 仙台東店", "name": ["COCO", "仙台東"]}, "E14": {"query": "ペットタクシー COCOタク長岡", "name": ["COCO", "長岡"]}, "E15": {"query": "ZEROペットタクシー 栗東市", "name": "ZERO"}, "E16": {"query": "ペットタクシー Comasuke 茨木", "name": "Comasuke"}, "E18": {"query": "ペットタクシー マイファミリー 高槻市", "name": "マイファミリー"}, "E19": {"query": "ペットサポートてんりん 京都市東山区", "name": "てんりん"}, "E20": {"query": "ペットタクシー COCOタク ならまち店", "name": ["COCO", "ならまち"]}, "E21": {"query": "ペッタク ペットタクシー 広島市安芸区", "name": "ペッタク"}, "E22": {"query": "福岡わんわんエクスプレス", "name": "わんわんエクスプレス"}, "E23": {"query": "福岡ペットタクシー HAKAタク", "name": "HAKA"}, "E24": {"query": "ペットタクシー COCOタク 福岡空港店", "name": ["COCO", "福岡空港"]}, "E25": {"query": "東京ペット救急車 なごみ", "name": "ペット救急車"}, "E26": {"query": "ペットタクシー シアンシャ 厚木", "name": ["シアンシャ", "厚木"]}, "E27": {"query": "ペットタクシー シアンシャ 鎌倉", "name": ["シアンシャ", "鎌倉"]}, "E28": {"query": "ペトタクファインド", "name": "ペトタクファインド"}, "H001": {"query": "札幌夜間動物病院 札幌市西区", "name": "札幌夜間動物病院"}, "H002": {"query": "アネス動物病院 札幌円山動物麻酔センター 札幌市中央区", "name": ["アネス動物病院", "札幌円山動物麻酔センター"]}, "H003": {"query": "ペテモどうぶつ医療センター 札幌月寒 札幌市豊平区", "name": ["ペテモどうぶつ医療センター", "札幌月寒"]}, "H004": {"query": "北海道大学動物医療センター 札幌市北区", "name": "北海道大学動物医療センター"}, "H005": {"query": "江別白樺通りアニマルクリニック 江別市", "name": "江別白樺通りアニマルクリニック"}, "H006": {"query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "name": ["仙台獣医師会", "夜間救急動物病院"]}, "H007": {"query": "長町南動物病院 仙台市太白区", "name": "長町南動物病院"}, "H008": {"query": "動物夜間急患センター新潟 新潟市中央区", "name": "動物夜間急患センター新潟"}, "H009": {"query": "ふくしま夜間救急動物病院 郡山市", "name": "ふくしま夜間救急動物病院"}, "H010": {"query": "つくば夜間動物病院 つくば市", "name": "つくば夜間動物病院"}, "H011": {"query": "水戸夜間動物救急センター 水戸市", "name": "水戸夜間動物救急センター"}, "H012": {"query": "つくば動物高度医療センター つくば市", "name": "つくば動物高度医療センター"}, "H013": {"query": "宇都宮夜間どうぶつ病院 宇都宮市", "name": "宇都宮夜間どうぶつ病院"}, "H014": {"query": "宇都宮白沢動物病院 宇都宮市", "name": "宇都宮白沢動物病院"}, "H015": {"query": "しもつけVETセンター 下野市", "name": "しもつけVETセンター"}, "H016": {"query": "小山夜間救急 あかりの森どうぶつ病院 小山市", "name": ["小山夜間救急", "あかりの森どうぶつ病院"]}, "H017": {"query": "群馬夜間救急動物病院 前橋市", "name": "群馬夜間救急動物病院"}, "H018": {"query": "伊勢崎動物医療センター 伊勢崎市", "name": "伊勢崎動物医療センター"}, "H019": {"query": "さいとう動物病院 富岡総合医療センター 富岡市", "name": ["さいとう動物病院", "富岡総合医療センター"]}, "H020": {"query": "夜間救急動物病院 さいたま大宮 SONAC さいたま市大宮区", "name": ["夜間救急動物病院", "さいたま大宮", "SONAC"]}, "H021": {"query": "どうぶつの総合病院 専門医療＆救急センター 川口市", "name": ["どうぶつの総合病院", "専門医療＆救急センター"]}, "H022": {"query": "ミライノ動物病院 草加市", "name": "ミライノ動物病院"}, "H023": {"query": "日本小動物医療センター 所沢市", "name": "日本小動物医療センター"}, "H024": {"query": "久喜夜間救急どうぶつ病院 久喜市", "name": "久喜夜間救急どうぶつ病院"}, "H025": {"query": "熊谷夜間救急動物病院 熊谷市", "name": "熊谷夜間救急動物病院"}, "H026": {"query": "ペテモどうぶつ医療センター幕張新都心 千葉市美浜区", "name": "ペテモどうぶつ医療センター幕張新都心"}, "H027": {"query": "JPB動物医療センター千葉 千葉市緑区", "name": "JPB動物医療センター千葉"}, "H028": {"query": "京葉夜間どうぶつ病院 八千代市", "name": "京葉夜間どうぶつ病院"}, "H029": {"query": "柏流山夜間どうぶつ病院 柏市", "name": "柏流山夜間どうぶつ病院"}, "H030": {"query": "とうかつ夜間どうぶつ病院 柏市", "name": "とうかつ夜間どうぶつ病院"}, "H031": {"query": "千葉どうぶつ総合病院 流山市", "name": "千葉どうぶつ総合病院"}, "H032": {"query": "千葉動物医療センター 袖ケ浦市", "name": "千葉動物医療センター"}, "H033": {"query": "港区動物救急医療センター 芝アニマルクリニック 港区", "name": ["港区動物救急医療センター", "芝アニマルクリニック"]}, "H034": {"query": "ライフメイト動物医療センター文京 文京区", "name": "ライフメイト動物医療センター文京"}, "H035": {"query": "夜間救急動物病院 目黒 目黒区", "name": ["夜間救急動物病院", "目黒"]}, "H036": {"query": "TRVA動物医療センター 世田谷区", "name": "TRVA動物医療センター"}, "H037": {"query": "杉並動物夜間救急医療センター 杉並区", "name": "杉並動物夜間救急医療センター"}, "H038": {"query": "ライフメイト動物救急センター練馬 練馬区", "name": "ライフメイト動物救急センター練馬"}, "H039": {"query": "ペテモどうぶつ医療センター ひがし東京 江東区", "name": ["ペテモ", "ひがし東京"]}, "H040": {"query": "武蔵野動物・救急救命センター 武蔵野市", "name": "武蔵野動物・救急救命センター"}, "H041": {"query": "ライフメイト動物医療センター府中 府中市", "name": "ライフメイト動物医療センター府中"}, "H042": {"query": "サムズアップアニマルケアセンター 立川市", "name": "サムズアップアニマルケアセンター"}, "H043": {"query": "ライフメイト動物救命救急センター八王子 八王子市", "name": "ライフメイト動物救命救急センター八王子"}, "H044": {"query": "DVMsどうぶつ医療センター横浜 横浜市神奈川区", "name": "DVMsどうぶつ医療センター横浜"}, "H045": {"query": "横浜動物救急診療センター VECCS横浜 横浜市南区", "name": ["横浜動物救急診療センター", "VECCS横浜"]}, "H046": {"query": "アニマルメディカルセンター 川崎市中原区", "name": "アニマルメディカルセンター"}, "H047": {"query": "川崎市獣医師会 夜間動物病院 川崎市高津区", "name": ["川崎市獣医師会", "夜間動物病院"]}, "H048": {"query": "ペテモどうぶつ医療センター相模原 相模原市南区", "name": "ペテモどうぶつ医療センター相模原"}, "H049": {"query": "藤沢夜間救急動物病院 藤沢市", "name": "藤沢夜間救急動物病院"}, "H050": {"query": "横須賀夜間救急動物病院 横須賀市", "name": "横須賀夜間救急動物病院"}, "H051": {"query": "夜間救急動物医療センター NEAMeC 平塚市", "name": ["夜間救急動物医療センター", "NEAMeC"]}, "H053": {"query": "北陸よつや動物医療センター 高岡市", "name": "北陸よつや動物医療センター"}, "H054": {"query": "チェルシーアニマルクリニック 富山市", "name": "チェルシーアニマルクリニック"}, "H055": {"query": "かなざわ夜間救急動物病院 金沢市", "name": "かなざわ夜間救急動物病院"}, "H056": {"query": "京都夜間動物救急センター 京都市南区", "name": "京都夜間動物救急センター"}, "H057": {"query": "ノア動物病院 城東センター病院 甲府市", "name": ["ノア動物病院", "城東センター病院"]}, "H058": {"query": "きらら動物病院 千塚分院 甲府市", "name": ["きらら動物病院", "千塚分院"]}, "H059": {"query": "長野夜間どうぶつ病院 千曲市", "name": "長野夜間どうぶつ病院"}, "H060": {"query": "佐久・軽井沢夜間どうぶつ病院 佐久市", "name": "佐久・軽井沢夜間どうぶつ病院"}, "H061": {"query": "こやま動物病院 長野市", "name": "こやま動物病院"}, "H062": {"query": "岐阜県獣医師会 夜間救急動物病院 岐阜市", "name": ["岐阜県獣医師会", "夜間救急動物病院"]}, "H063": {"query": "静岡市夜間救急動物病院 静岡市駿河区", "name": "静岡市夜間救急動物病院"}, "H064": {"query": "浜松夜間救急動物病院 浜松市中央区", "name": "浜松夜間救急動物病院"}, "H065": {"query": "VCJ動物医療センター駿河病院 御殿場市", "name": "VCJ動物医療センター駿河病院"}, "H066": {"query": "名古屋夜間動物救急センター 名古屋市中区", "name": "名古屋夜間動物救急センター"}, "H067": {"query": "名古屋西動物夜間救急医療センター 名古屋市西区", "name": "名古屋西動物夜間救急医療センター"}, "H068": {"query": "もりやま犬と猫の病院 名古屋市守山区", "name": "もりやま犬と猫の病院"}, "H069": {"query": "こざわ犬猫病院 名古屋市千種区", "name": "こざわ犬猫病院"}, "H070": {"query": "あいち犬猫医療センター 安城市", "name": "あいち犬猫医療センター"}, "H071": {"query": "ハート動物クリニック 犬猫医療センター 豊橋市", "name": ["ハート動物クリニック", "犬猫医療センター"]}, "H072": {"query": "大阪どうぶつ夜間急病センター 大阪市東成区", "name": "大阪どうぶつ夜間急病センター"}, "H073": {"query": "長浜どうぶつ病院 長浜市", "name": "長浜どうぶつ病院"}, "H074": {"query": "大阪・北摂夜間救急どうぶつ病院 箕面市", "name": "大阪・北摂夜間救急どうぶつ病院"}, "H075": {"query": "京都夜間どうぶつ診療所 久世郡久御山町", "name": "京都夜間どうぶつ診療所"}, "H076": {"query": "右京動物病院 京都市右京区", "name": "右京動物病院"}, "H077": {"query": "大阪夜間ペットクリニック 大阪市東成区", "name": "大阪夜間ペットクリニック"}, "H078": {"query": "堺動物夜間救急クリニック 堺市中区", "name": "堺動物夜間救急クリニック"}, "H079": {"query": "大阪守口夜間どうぶつ診療所 守口市", "name": "大阪守口夜間どうぶつ診療所"}, "H080": {"query": "りんくう動物救急医療協会 泉佐野市", "name": "りんくう動物救急医療協会"}, "H082": {"query": "神戸夜間動物救急センター 神戸市西区", "name": "神戸夜間動物救急センター"}, "H083": {"query": "兵庫ペット医療センター 尼崎本院 尼崎市", "name": ["兵庫ペット医療センター", "尼崎本院"]}, "H084": {"query": "大蔵海岸ペットクリニック 明石市", "name": "大蔵海岸ペットクリニック"}, "H085": {"query": "エルザ動物医療センター 姫路市", "name": "エルザ動物医療センター"}, "H086": {"query": "奈良動物医療センター 奈良市", "name": "奈良動物医療センター"}, "H088": {"query": "岡山夜間どうぶつ救急病院 岡山市南区", "name": "岡山夜間どうぶつ救急病院"}, "H089": {"query": "広島夜間救急動物病院 広島市東区", "name": "広島夜間救急動物病院"}, "H090": {"query": "倉敷夜間ペットクリニック 倉敷市", "name": "倉敷夜間ペットクリニック"}, "H091": {"query": "konomi動物病院 広島市東区", "name": "konomi動物病院"}, "H092": {"query": "竹田動物病院 岩国市", "name": "竹田動物病院"}, "H093": {"query": "北九州夜間救急動物病院 北九州市八幡東区", "name": "北九州夜間救急動物病院"}, "H094": {"query": "おおしま動物病院 板野郡藍住町", "name": "おおしま動物病院"}, "H098": {"query": "福岡夜間救急動物病院 福岡市博多区", "name": "福岡夜間救急動物病院"}, "H099": {"query": "一二三ペットクリニック 熊本市東区", "name": "一二三ペットクリニック"}, "H100": {"query": "きらてとあにまるほすぴたる 熊本市南区", "name": "きらてとあにまるほすぴたる"}, "H102": {"query": "大塚どうぶつ病院 宮崎市", "name": "大塚どうぶつ病院"}, "H103": {"query": "鹿児島大学 共同獣医学部附属動物病院 鹿児島市", "name": ["鹿児島大学", "共同獣医学部附属動物病院"]}, "H105": {"query": "沖縄夜間動物病院 那覇市", "name": "沖縄夜間動物病院"}, "H106": {"query": "動物病院なは 夜間救急医療センター 島尻郡南風原町", "name": ["動物病院なは", "夜間救急医療センター"]}, "V001": {"query": "GOGO動物クリニック 世田谷区", "name": "GOGO動物クリニック"}, "V002": {"query": "はる動物診療所 三鷹市", "name": "はる動物診療所"}, "V003": {"query": "わんにゃん保健室 中央区", "name": "わんにゃん保健室"}, "V004": {"query": "ペットドクターカー 杉並区", "name": "ペットドクターカー"}, "V005": {"query": "さかうえ動物病院 中野区", "name": "さかうえ動物病院"}, "V006": {"query": "訪問診療アベリア動物病院 練馬区", "name": "訪問診療アベリア動物病院"}, "V007": {"query": "イース往診どうぶつ診療所 江東区", "name": "イース往診どうぶつ診療所"}, "V008": {"query": "あおば動物クリニック 東久留米市", "name": "あおば動物クリニック"}, "V009": {"query": "アニホック往診専門動物病院 港区", "name": "アニホック往診専門動物病院"}, "V011": {"query": "ほしのどうぶつクリニック 調布市", "name": "ほしのどうぶつクリニック"}, "V012": {"query": "往診専門森のくま動物病院 杉並区", "name": "往診専門森のくま動物病院"}, "V013": {"query": "往診専門 るりあ動物病院 墨田区", "name": "往診専門 るりあ動物病院"}, "V014": {"query": "往診専門リヨン動物病院 東村山市", "name": "往診専門リヨン動物病院"}, "V015": {"query": "マリどうぶつ診療所 文京区", "name": "マリどうぶつ診療所"}, "V016": {"query": "往診専門 なべしま動物病院 西東京市", "name": "往診専門 なべしま動物病院"}, "V020": {"query": "横浜往診どうぶつ病院 横浜市", "name": "横浜往診どうぶつ病院"}, "V021": {"query": "かもめ往診ペットクリニック 茅ヶ崎市", "name": "かもめ往診ペットクリニック"}, "V022": {"query": "往診動物病院 Pinoa. 藤沢市", "name": "往診動物病院 Pinoa."}, "V023": {"query": "犬猫往診Dear One 横浜市中区", "name": "犬猫往診Dear One"}, "V024": {"query": "Az往診ペットクリニック 横浜市", "name": "Az往診ペットクリニック"}, "V025": {"query": "うみかぜ動物病院 茅ヶ崎市・藤沢市", "name": "うみかぜ動物病院"}, "V026": {"query": "往診専門動物病院 アニマルライフパートナー 藤沢市", "name": "アニマルライフパートナー"}, "V027": {"query": "金乃時アニマルクリニック 横浜市", "name": "金乃時アニマルクリニック"}, "V028": {"query": "ホームズ動物往診所 川崎市", "name": "ホームズ動物往診所"}, "V029": {"query": "往診専門 Coccole わんにゃんクリニック 伊勢原市", "name": "Coccole"}, "V030": {"query": "往診専門ルル動物病院 八千代市", "name": "往診専門ルル動物病院"}, "V031": {"query": "往診型動物病院そよかぜ 越谷市", "name": "そよかぜ"}, "V032": {"query": "いぬとねこの訪問診療ぱろ 東松山市", "name": "いぬとねこの訪問診療ぱろ"}, "V033": {"query": "犬猫往診専門 虹の橋どうぶつ病院 さいたま市緑区", "name": "虹の橋どうぶつ病院"}, "V034": {"query": "動物往診＋在宅ケアサービス にくきゅう 鶴ヶ島市", "name": "にくきゅう"}, "V035": {"query": "VHVぶなの木動物病院 桶川市", "name": "VHVぶなの木動物病院"}, "V036": {"query": "ペコ犬猫往診所 比企郡鳩山町", "name": "ペコ犬猫往診所"}, "V037": {"query": "学園の森訪問診療アニマルクリニック つくば市", "name": "学園の森訪問診療アニマルクリニック"}, "V038": {"query": "AMIGO往診獣医療 稲敷郡阿見町", "name": "AMIGO往診獣医療"}, "V039": {"query": "たけふじ動物病院 諏訪市", "name": "たけふじ動物病院"}, "V040": {"query": "ポラリス往診どうぶつ病院 北佐久郡軽井沢町", "name": "ポラリス往診どうぶつ病院"}, "V041": {"query": "まりこ動物往診所 中新川郡立山町", "name": "まりこ動物往診所"}, "V042": {"query": "往診専門 るい動物病院 常滑市", "name": "往診専門 るい動物病院"}, "V043": {"query": "往診専門きとう動物クリニック 豊田市", "name": "往診専門きとう動物クリニック"}, "V044": {"query": "メープルファミリー動物病院 名古屋市", "name": "メープルファミリー動物病院"}, "V045": {"query": "バディ動物クリニック 津市", "name": "バディ動物クリニック"}, "V046": {"query": "リッカペットクリニック 堺市", "name": "リッカペットクリニック"}, "V047": {"query": "ホッと往診動物診療所 大阪市", "name": "ホッと往診動物診療所"}, "V048": {"query": "さくらアニマルクリニック 八尾市", "name": "さくらアニマルクリニック"}, "V049": {"query": "よつば動物病院 神戸市・明石市", "name": "よつば動物病院"}, "V050": {"query": "アカラペットクリニック 神戸市・明石市", "name": "アカラペットクリニック"}, "V051": {"query": "往診専門クルーアニマルクリニック 京都市", "name": "往診専門クルーアニマルクリニック"}, "V052": {"query": "往診専門 comaペットクリニック 和歌山市", "name": "comaペットクリニック"}, "V053": {"query": "おうちdeペットクリニック 福岡市", "name": "おうちdeペットクリニック"}, "V054": {"query": "なかやま犬猫病院 熊本市", "name": "なかやま犬猫病院"}, "V055": {"query": "往診専門犬猫クリニックあしおと 中津市", "name": "あしおと"}, "V056": {"query": "かやま往診専門動物病院 いちき串木野市", "name": "かやま往診専門動物病院"}, "V057": {"query": "るぼんず 沙流郡日高町", "name": "るぼんず"}, "C001": {"query": "札幌ねこの病院 札幌市中央区", "name": "札幌ねこの病院"}, "C002": {"query": "みやぎキャットクリニック 仙台市宮城野区", "name": "みやぎキャットクリニック"}, "C003": {"query": "新潟ねこの病院 新潟市中央区", "name": "新潟ねこの病院"}, "C004": {"query": "ねこの病院と保護ねこルーム ぽのいえ さいたま市西区", "name": "ねこの病院と保護ねこルーム ぽのいえ"}, "C005": {"query": "Tokyo Cat Specialists 港区", "name": "Tokyo Cat Specialists"}, "C006": {"query": "東京猫医療センター 江東区", "name": "東京猫医療センター"}, "C007": {"query": "グラース猫の病院 杉並区", "name": "グラース猫の病院"}, "C008": {"query": "アリーズ猫医療センター 渋谷区", "name": "アリーズ猫医療センター"}, "C009": {"query": "猫の診療室モモ 品川区", "name": "猫の診療室モモ"}, "C010": {"query": "むさし小金井キャットクリニック 小金井市", "name": "むさし小金井キャットクリニック"}, "C011": {"query": "ねこの診療室ココ 横浜市南区", "name": "ねこの診療室ココ"}, "C012": {"query": "横浜ねこ病院 横浜市神奈川区", "name": "横浜ねこ病院"}, "C013": {"query": "バステトキャットクリニック 名古屋市中区", "name": "バステトキャットクリニック"}, "C014": {"query": "動物病院 京都 ねこの病院 京都市上京区", "name": "動物病院 京都 ねこの病院"}, "C015": {"query": "猫専門病院ノアのねこ舟 豊中市", "name": "猫専門病院ノアのねこ舟"}, "C016": {"query": "猫の診療室 堺市北区", "name": "猫の診療室"}, "C017": {"query": "キャットクリニック広島 広島市東区", "name": "キャットクリニック広島"}, "C018": {"query": "福岡ねこの病院 福岡市城南区", "name": "福岡ねこの病院"}, "X001": {"query": "ポックル動物病院 札幌市手稲区", "name": "ポックル動物病院"}, "X002": {"query": "とちぎ うさぎ・ことり・ちびっこ動物の病院 小山市", "name": "とちぎ うさぎ・ことり・ちびっこ動物の病院"}, "X003": {"query": "あず小鳥の診療所 さいたま市南区", "name": "あず小鳥の診療所"}, "X004": {"query": "small animal clinic 千葉市中央区登戸", "name": "small animal clinic"}, "X005": {"query": "BEN犬猫エキゾの病院 千葉市若葉区", "name": "BEN犬猫エキゾの病院"}, "X006": {"query": "みわエキゾチック動物病院 豊島区", "name": "みわエキゾチック動物病院"}, "X007": {"query": "吉祥寺エキゾチック動物病院 武蔵野市", "name": "吉祥寺エキゾチック動物病院"}, "X008": {"query": "葛西エキゾチック動物病院 江戸川区", "name": "葛西エキゾチック動物病院"}, "X009": {"query": "バニーグラス 葛飾区", "name": "バニーグラス"}, "X010": {"query": "エキゾチックメディカルセンター 川崎市中原区", "name": "エキゾチックメディカルセンター"}, "X011": {"query": "横浜エキゾチック動物病院 横浜市戸塚区", "name": "横浜エキゾチック動物病院"}, "X012": {"query": "京都小動物クリニック 京都市伏見区", "name": "京都小動物クリニック"}, "X013": {"query": "ダクタリ動物病院 京都医療センター 京都市西京区", "name": ["ダクタリ", "京都医療センター"]}, "X014": {"query": "小泉ネスト動物病院 北九州市八幡西区", "name": "小泉ネスト動物病院"}, "X015": {"query": "うさぎの病院 熊本市中央区出水", "name": "うさぎの病院"}, "L001": {"query": "おおた動物病院 さいたま市大宮区", "name": "おおた動物病院"}, "L002": {"query": "日本動物医療センター 渋谷区", "name": "日本動物医療センター"}, "L003": {"query": "クラーク動物病院 八王子市", "name": "クラーク動物病院"}, "L004": {"query": "溝呂木動物病院 横浜市南区", "name": "溝呂木動物病院"}, "L005": {"query": "よこい動物クリニック 豊田市", "name": "よこい動物クリニック"}, "L006": {"query": "串田動物病院 京都市西京区", "name": "串田動物病院"}, "L007": {"query": "山之上動物病院 枚方市", "name": "山之上動物病院"}, "L008": {"query": "神戸アニマルクリニック 神戸市垂水区", "name": "神戸アニマルクリニック"}, "L009": {"query": "オタニ動物病院 神戸市長田区", "name": "オタニ動物病院"}, "L010": {"query": "永原動物病院 岡山市南区", "name": "永原動物病院"}, "L011": {"query": "博多犬猫医療センター 福岡市博多区", "name": "博多犬猫医療センター"}, "L012": {"query": "みやた動物病院 北九州市八幡西区", "name": "みやた動物病院"}, "R001": {"query": "愛犬本舗 札幌市白石区", "name": "愛犬本舗"}, "R002": {"query": "ニャンワンクラブ 仙台市青葉区八幡", "name": "ニャンワンクラブ"}, "R003": {"query": "いぬ&ねこの家 クラスメイト 秋田市", "name": "クラスメイト"}, "R004": {"query": "老犬ホーム ひまわり つくば市沼田", "name": "ひまわり"}, "R005": {"query": "桑原動物病院 前橋市六供町", "name": "桑原動物病院"}, "R006": {"query": "ささき動物病院 さいたま市北区植竹町", "name": "ささき動物病院"}, "R007": {"query": "あにまるケアハウス 加須市久下", "name": "あにまるケアハウス"}, "R008": {"query": "老犬ホーム Smile Flower 千葉市緑区平川町", "name": "Smile Flower"}, "R009": {"query": "老犬ホーム 九十九里パーク 九十九里町小関", "name": "九十九里パーク"}, "R010": {"query": "シニアDOGハイム 足立区小台", "name": "シニアDOGハイム"}, "R011": {"query": "THE ケネルズ東京 目黒区洗足", "name": "ケネルズ"}, "R012": {"query": "東京ペットホーム 大田区大森南", "name": "東京ペットホーム"}, "R013": {"query": "わんダ～らん 新潟市西区槇尾", "name": "わんダ"}, "R014": {"query": "ドッグハウス・ダディー 御代田町", "name": "ダディー"}, "R015": {"query": "セカンドハウス 羽島店 羽島市竹鼻町", "name": "セカンドハウス"}, "R016": {"query": "老犬ホーム暖家 揖斐川町", "name": "暖家"}, "R017": {"query": "I・STYLE 焼津市東小川", "name": "STYLE"}, "R018": {"query": "KAMALEI 沼津市足高", "name": "KAMALEI"}, "R019": {"query": "ちびママの家 浜松市中区城北", "name": "ちびママ"}, "R020": {"query": "ワンワンパラダイス 新城市富岡", "name": "ワンワンパラダイス"}, "R021": {"query": "Furkidsun 蒲郡市旭町", "name": "Furkidsun"}, "R022": {"query": "ペットホームOHANA 四日市市生桑町", "name": "OHANA"}, "R023": {"query": "ワンワンハートSAKURA 四日市市桜町", "name": "SAKURA"}, "R024": {"query": "Catホッと 長浜市", "name": "Catホッと"}, "R025": {"query": "老犬介護ホーム ろうたす 京都市伏見区", "name": "ろうたす"}, "R026": {"query": "犬のケアハウスうらら 京丹波町", "name": "うらら"}, "R027": {"query": "老犬ホームあん 京丹波町井尻", "name": "あん"}, "R028": {"query": "老犬介護ホーム メロー 大阪市城東区放出西", "name": "メロー"}, "R029": {"query": "老犬ホーム Smile Flower Osaka 八尾市西山本町", "name": "Smile Flower"}, "R030": {"query": "老犬ホーム norn 市川町屋形", "name": "norn"}, "R031": {"query": "Caramelpapa 明石市林崎町", "name": "Caramelpapa"}, "R032": {"query": "関西ドッグスクール 三宅町但馬", "name": "関西ドッグスクール"}, "R033": {"query": "アニマルレストハウス 橋本市隅田町", "name": "アニマルレストハウス"}, "R034": {"query": "MommySociety 岡山市東区城東台西", "name": "MommySociety"}, "R035": {"query": "老犬ホーム KOMUGI 宇部市則貞", "name": "KOMUGI"}, "R036": {"query": "ドッグケアハウス伝 山口市下小鯖", "name": "伝"}, "R037": {"query": "いぬのケアハウス シェリー 新宮町原上", "name": "シェリー"}, "R038": {"query": "ドッグハウスなぎさ 中間市長津", "name": "なぎさ"}, "R039": {"query": "老犬介護ホーム てるハウス 北九州市八幡東区", "name": "てるハウス"}, "R040": {"query": "老犬ホーム REGALO 読谷村座喜味", "name": "REGALO"}, "R041": {"query": "しっぽフリフリ 相模原市緑区鳥屋", "name": "しっぽフリフリ"}, "R042": {"query": "うめねこ 横浜市鶴見区下末吉", "name": "うめねこ"}, "R043": {"query": "オレンジライフ湘南 平塚市平塚", "name": "オレンジライフ湘南"}, "R044": {"query": "WANCOTT 横浜市中区山下町", "name": "WANCOTT"}, "R045": {"query": "老犬ホーム シルヴィ 甲斐市大垈", "name": "シルヴィ"}, "R047": {"query": "わんにゃんハウス オレンジ 千葉市中央区亥鼻", "name": "わんにゃんハウス"}, "R048": {"query": "まるねこ 大田区羽田", "name": "まるねこ"}, "R049": {"query": "Familio 茨木市南耳原", "name": "Familio"}, "R050": {"query": "老犬ホーム あおいそら 神戸市北区有野町", "name": "あおいそら"}, "R051": {"query": "犬野苑 奈良市公納堂町", "name": "犬野苑"}, "R052": {"query": "シニアドッグケアホームこころ あま市甚目寺", "name": "こころ"}, "R053": {"query": "わんわん保育園あおぞら 名古屋市名東区香南", "name": "あおぞら"}, "R054": {"query": "ペットケアホーム リュッカ 日進市岩崎町", "name": "リュッカ"}, "R055": {"query": "老犬ホーム ワンハピネス 高山市大洞町", "name": "ワンハピネス"}, "R056": {"query": "ani TERRACE 多気町ヴィソン", "name": "ani TERRACE"}, "R057": {"query": "老犬ホーム 御殿場 大坂234", "name": "老犬ホーム 御殿場"}, "R058": {"query": "ワンBOX 小松市平面町", "name": "ワンBOX"}, "R059": {"query": "菅原動物病院 仙台市宮城野区福住町", "name": "菅原動物病院"}, "R060": {"query": "逢犬はうす 札幌市北区篠路町", "name": "逢犬はうす"}, "R061": {"query": "ティアハイム ノア 札幌市東区北22条東", "name": "noah"}, "R062": {"query": "老犬ホーム セタ 札幌市北区新川6条", "name": "セタ"}, "R063": {"query": "ほのぼのホーム 広島市佐伯区八幡", "name": "ほのぼのホーム"}, "R065": {"query": "らんずケア さぬき市志度", "name": "らんずケア"}, "R066": {"query": "ペットホームえひめ 松山市堀江町", "name": "ペットホームえひめ"}, "R067": {"query": "老犬ホーム晴 大村市中岳町", "name": "老犬ホーム晴"}, "R068": {"query": "ドッグケア soraと 福岡市中央区平尾", "name": "soraと"}, "R080": {"query": "老犬ホーム トップ 菊池市", "name": "老犬ホーム トップ"}, "R081": {"query": "ペットラウンジ ルシアン 熊本市西区", "name": "ルシアン"}, "R082": {"query": "みんとの杜 福島市", "name": "みんとの杜"}, "R083": {"query": "甲斐っトランド いわき市", "name": "甲斐っトランド"}, "R084": {"query": "すいーとほーむ 山形市南原町", "name": "すいーとほーむ"}, "R085": {"query": "ペットステーション ジュエル 徳島市", "name": "ジュエル"}, "R086": {"query": "ペットケアハウスなな 南国市", "name": "ペットケアハウスなな"}, "R087": {"query": "もふもふの気持ち 宮崎市青島", "name": "もふもふの気持ち"}, "R088": {"query": "lavie. 老犬ホーム 取手市", "name": "lavie"}, "R089": {"query": "老犬ホーム ゆるやか 龍ケ崎市", "name": "ゆるやか"}, "R090": {"query": "DOG PARTNERS 横浜市中区", "name": "DOG PARTNERS"}, "R091": {"query": "らものいえ 所沢市", "name": "らものいえ"}, "R092": {"query": "ワンダブル 和歌山市", "name": "ワンダブル"}, "R093": {"query": "アサワペット 小田原市", "name": "アサワペット"}, "R094": {"query": "Smile Home 老犬介護 近江八幡市", "name": "SmileHome"}, "T001": {"query": "WISE DOG 札幌市南区真駒内", "name": "WISE DOG"}, "T003": {"query": "いぬスクールDo犬 札幌市中央区宮の森", "name": "Do犬"}, "T004": {"query": "犬の幼稚園HappyDog 札幌市清田区平岡", "name": "HappyDog"}, "T005": {"query": "ドッグボンド 札幌市西区平和", "name": "ドッグボンド"}, "T006": {"query": "わんぷろ 青森市本町", "name": "わんぷろ"}, "T007": {"query": "ドッグトレーニングこんの 山形市西原", "name": "こんの"}, "T008": {"query": "Dog School Eight 仙台市青葉区八幡", "name": "Eight"}, "T009": {"query": "ぱれっと動物病院 仙台市若林区", "name": "ぱれっと動物病院"}, "T012": {"query": "スタディ・ドッグ・スクール 宇都宮市西原町", "name": "スタディ"}, "T013": {"query": "飯塚動物病院 佐野市多田町", "name": "飯塚動物病院"}, "T014": {"query": "けあかんぱにー 高崎市", "name": "けあかんぱにー"}, "T015": {"query": "犬のほいくえんVita 安中市松井田町", "name": "Vita"}, "T016": {"query": "シンビオーシス さいたま市北区吉野町", "name": "シンビオーシス"}, "T019": {"query": "トラステッド・ペット・シェルター 東金市", "name": "トラステッド"}, "T021": {"query": "WARABY 市原市栢橋", "name": "WARABY"}, "T023": {"query": "犬の学園 ファミリーナガーデン 南青山", "name": "ファミリーナ"}, "T024": {"query": "wamiハッピードッグ 日野市程久保", "name": "ハッピードッグ"}, "T025": {"query": "空ドッグスクール 練馬区石神井", "name": "空ドッグスクール"}, "T026": {"query": "WanByWan 世田谷区三宿", "name": "WanByWan"}, "T028": {"query": "Puppy Beans 品川区二葉", "name": "Puppy Beans"}, "T029": {"query": "犬のじどうかん POOCH PAL 新宿区西落合", "name": "POOCH PAL"}, "T030": {"query": "Dogrelaxing 板橋区高島平", "name": "Dogrelaxing"}, "T031": {"query": "Can Do Pet Dog School 世田谷区", "name": "Pet Dog School"}, "T034": {"query": "ドッグリー東京 台東区", "name": "ドッグリー"}, "T038": {"query": "スタディ・ドッグ・スクール 相模原市中央区氷川町", "name": "スタディ"}, "T040": {"query": "Gu.uT 川崎市宮前区神木", "name": "Gu.uT"}, "T042": {"query": "HAPPY DOG LIFE EMA 横浜市旭区笹野台", "name": "EMA"}, "T046": {"query": "いぬの保育園 ペロ 野々市市稲荷", "name": "ペロ"}, "T047": {"query": "軽井沢ドッグビヘイビア 小諸市塩野", "name": "ドッグビヘイビア"}, "T048": {"query": "Only WAN 愛犬のお庭 伊東市富戸", "name": "WAN"}, "T050": {"query": "わんポイント 豊川市当古町", "name": "わんポイント"}, "T051": {"query": "倉田ドッグトレーニングスクール 名古屋市天白区", "name": "倉田"}, "T052": {"query": "ドッグスルーム 東海市富木島町", "name": "ドッグスルーム"}, "T054": {"query": "Secil wan Company 名古屋市緑区鳴海町", "name": "Secil"}, "T055": {"query": "きたなごやドッグスクール 北名古屋市", "name": "きたなごやドッグスクール"}, "T056": {"query": "アルカドッグトレーニング 大津市大物", "name": "アルカ"}, "T057": {"query": "Ready to Train 京都市伏見区納所町", "name": "Ready to Train"}, "T058": {"query": "DOG WOOF popomeip 守口市", "name": "popomeip"}, "T062": {"query": "シリウス・ドッグトレーニングスクール 宝塚市", "name": "シリウス"}, "T063": {"query": "ワンちゃんの学校 イン・クローバー 神戸市灘区", "name": "クローバー"}, "T064": {"query": "ドルチェカーネ中塚 神戸市北区藤原台", "name": "ドルチェカーネ"}, "T065": {"query": "ちゃくる 加古川市加古川町木村", "name": "ちゃくる"}, "T066": {"query": "アフェット 姫路市飾磨区加茂", "name": "アフェット"}, "T067": {"query": "犬のこんしぇるじゅプラスわん 備前市", "name": "プラスわん"}, "T069": {"query": "Shake Hand's 広島市中区舟入南", "name": "Shake"}, "T071": {"query": "Happy Dogs' Garden 観音寺市豊浜町", "name": "Happy Dogs"}, "T073": {"query": "犬の学校 ドッグわん 福岡市西区生の松原", "name": "ドッグわん"}, "T074": {"query": "POSITIVE WIND 宮若市沼口", "name": "POSITIVE WIND"}, "T075": {"query": "WanLife 北九州市小倉北区重住", "name": "WanLife"}, "T076": {"query": "In Their Natural 佐賀市南佐賀", "name": "Natural"}, "T077": {"query": "VaBene 熊本市南区田井島", "name": "VaBene"}, "T078": {"query": "スカイドッグスクール 湧水町川西", "name": "スカイドッグスクール"}, "T080": {"query": "ドッグスクール山岡 秋田市雄和椿川", "name": "ドッグスクール山岡"}, "T081": {"query": "福島警察犬訓練所 福島市平石", "name": "福島警察犬訓練所"}, "T084": {"query": "ドッグスクールJOY 輪之内町大藪", "name": "ドッグスクールJOY"}, "T085": {"query": "ドッグスクール西井 松阪市久保町", "name": "ドッグスクール西井"}, "T086": {"query": "Dog Answer 四日市市尾平町", "name": "Dog Answer"}, "T087": {"query": "田中警察犬訓練所 四日市市西坂部町", "name": "ドッグスクールタナカ"}, "T089": {"query": "京奈和ドッグスクール 大和郡山市井戸野町", "name": "京奈和ドッグスクール"}, "T091": {"query": "ドッグスクール ニシヤマ かつらぎ町笠田東", "name": "ニシヤマ"}, "T093": {"query": "ハッピーランドハレルヤ 山口市朝倉町", "name": "ハッピーランドハレルヤ"}, "T094": {"query": "柴の家 山口市吉敷", "name": "柴の家"}, "T095": {"query": "ノイマンドッグスクール 板野町川端", "name": "ノイマンドッグスクール"}, "T096": {"query": "SEIWASOHドッグスクール 高知市仁井田", "name": "SEIWASOH"}, "T097": {"query": "長崎企画 長崎市葉山町", "name": "長崎企画"}, "T098": {"query": "アヅマランド 長崎市若竹町", "name": "アヅマランド"}, "T099": {"query": "シオン警察犬訓練所 糸満市阿波根", "name": "シオン警察犬訓練所"}, "T101": {"query": "ドッグトレーナー カウツ 松江市上佐陀町", "name": "カウツ"}, "T102": {"query": "ドッグスクール縁 松江市宍道町", "name": "ドッグスクール縁"}, "T103": {"query": "ジャンプドッグスクール 米子市淀江町", "name": "ジャンプドッグスクール"}, "T104": {"query": "大分県警察犬訓練所 大分市鴛野", "name": "大分県警察犬訓練所"}, "T105": {"query": "ONE'S COOL 別府市石垣西", "name": "ONE'S COOL"}, "T108": {"query": "わんぷろ 青森市本町", "name": "わんぷろ"}, "T111": {"query": "犬のようちえん 代官山教室 恵比寿南", "name": "犬のようちえん"}, "T112": {"query": "犬のようちえん 駒沢公園教室 八雲", "name": "犬のようちえん"}, "S8ec33a": {"query": "旭川ひばりが丘ペット火葬園 上川郡鷹栖町", "name": "旭川ひばりが丘ペット火葬園"}, "Sfb5dce": {"query": "帯広ペット霊園 中川郡幕別町", "name": "帯広ペット霊園"}, "S117853": {"query": "ペット霊園やすらぎ 中川郡幕別町", "name": "ペット霊園やすらぎ"}, "S2a7749": {"query": "道南ペット霊園函館 亀田郡七飯町", "name": "道南ペット霊園函館"}, "S75bd01": {"query": "ペット霊園古潭 旭川市", "name": "ペット霊園古潭"}, "S942ea0": {"query": "愛ペット動物霊園 札幌市中央区", "name": "愛ペット動物霊園"}, "S220475": {"query": "北海道動物霊園 札幌市南区", "name": "北海道動物霊園"}, "Sa25e7d": {"query": "ペットメモリアルZoo 札幌市白石区", "name": "ペットメモリアルZoo"}, "Sfae8b9": {"query": "ペットメモリアルパーク天使の里 石狩市", "name": "ペットメモリアルパーク天使の里"}, "Sb428bd": {"query": "ペットメモリアルサービス 苫小牧市", "name": "ペットメモリアルサービス"}, "S9b3bec": {"query": "青い森ペット斎場・やすらぎの里ペット霊園 青森市", "name": "青い森ペット斎場・やすらぎの里ペット霊園"}, "S761d97": {"query": "ペットエンゼル岩手 滝沢市", "name": "ペットエンゼル岩手"}, "Sdbddec": {"query": "サニーサンペットメモリアル 盛岡市", "name": "サニーサンペットメモリアル"}, "S7755d5": {"query": "仙台ペット霊園 SOLINA 仙台市太白区", "name": "仙台ペット霊園 SOLINA"}, "S78a99f": {"query": "大崎ペット斎場 大崎市", "name": "大崎ペット斎場"}, "Sa4611d": {"query": "アキタアニマル倶楽部 大仙ホール 大仙市", "name": "アキタアニマル倶楽部 大仙ホール"}, "S53b034": {"query": "アキタアニマル倶楽部 秋田ホール 秋田市", "name": "アキタアニマル倶楽部 秋田ホール"}, "Sd0edb1": {"query": "山形霊園ペット事業部 山形市", "name": "山形霊園ペット事業部"}, "S870493": {"query": "庄内ペット霊園 酒田市", "name": "庄内ペット霊園"}, "Se1bf8d": {"query": "いわきペット霊園 いわき市", "name": "いわきペット霊園"}, "Scf5387": {"query": "玉川ペット霊園 石川郡玉川村", "name": "玉川ペット霊園"}, "Sa9a9b5": {"query": "ペット葬祭センター福島 福島市", "name": "ペット葬祭センター福島"}, "S70883b": {"query": "愛心ペットセレモ つくば市", "name": "愛心ペットセレモ"}, "S5996ec": {"query": "ペット霊園 みどり野 ひたちなか市", "name": "ペット霊園 みどり野"}, "S7c8f28": {"query": "本願寺付嘱ペット霊園 佐野市", "name": "本願寺付嘱ペット霊園"}, "See9362": {"query": "ペット霊園宇都宮 日光市", "name": "ペット霊園宇都宮"}, "S523e5a": {"query": "イセサキPKサービス 伊勢崎市", "name": "イセサキPKサービス"}, "Sa1ae09": {"query": "天明寺 前橋市", "name": "天明寺"}, "Sccf329": {"query": "清山堂 高崎市", "name": "清山堂"}, "S41ef0e": {"query": "浦和ペット霊園 さいたま市桜区", "name": "浦和ペット霊園"}, "Sfd6400": {"query": "大宮武蔵野ペット霊園 上尾市", "name": "大宮武蔵野ペット霊園"}, "Sd1aa41": {"query": "ディアペットさいたま 上尾市", "name": "ディアペットさいたま"}, "Safcc83": {"query": "川口動物霊堂 川口市", "name": "川口動物霊堂"}, "S20803e": {"query": "狭山湖動物霊園 所沢市", "name": "狭山湖動物霊園"}, "S084b60": {"query": "ペットメモリアルパーク慈愛園 春日部市", "name": "ペットメモリアルパーク慈愛園"}, "S23b93a": {"query": "むさし動物霊園 越谷市", "name": "むさし動物霊園"}, "S42cba6": {"query": "ペット葬儀 ペット火葬 あすかの郷 越谷市", "name": "ペット葬儀 ペット火葬 あすかの郷"}, "Sa7529a": {"query": "東松山ペットメモリアルパーク 東松山市", "name": "メモリアルパーク"}, "Sece5b2": {"query": "武蔵野ペット霊園 入間郡毛呂山町", "name": "武蔵野ペット霊園"}, "S06fda3": {"query": "八千代ペット霊園 八千代市", "name": "八千代ペット霊園"}, "Se0a0fe": {"query": "ペットセレモニープレア千葉式場 千葉市稲毛区", "name": "ペットセレモニープレア千葉式場"}, "Se79f4e": {"query": "ペットメモリアル日本霊園 千葉市緑区", "name": "ペットメモリアル日本霊園"}, "Sb22bec": {"query": "不動の杜ペット霊園 千葉市若葉区", "name": "不動の杜ペット霊園"}, "Sa2fae7": {"query": "市川ペット霊園 市川市", "name": "市川ペット霊園"}, "S5299d7": {"query": "竺園寺別院 慈生院 市川市", "name": "竺園寺別院 慈生院"}, "S74b4b1": {"query": "動物苑 柏市", "name": "動物苑"}, "S85955a": {"query": "船橋ペット斎場 船橋市", "name": "船橋ペット斎場"}, "S078ca1": {"query": "ペットセレモニープレア松戸 松戸市", "name": "プレア"}, "S0d9e61": {"query": "大蔵動物霊園 世田谷区", "name": "大蔵動物霊園"}, "S0d1740": {"query": "蓮華寺付属 哲学堂動物霊園 中野区", "name": "蓮華寺付属 哲学堂動物霊園"}, "S9e38f7": {"query": "八王子動物霊園 八王子市", "name": "八王子動物霊園"}, "Scd0216": {"query": "八王子下柚木ペット霊園 八王子市", "name": "八王子下柚木ペット霊園"}, "S9370ff": {"query": "城南ペット霊園 品川区", "name": "城南ペット霊園"}, "S7bf45b": {"query": "東京ペット霊堂 大田区", "name": "東京ペット霊堂"}, "S9f181b": {"query": "大森ペット霊堂 大田区", "name": "大森ペット霊堂"}, "S4c6fc4": {"query": "慈恵院付属多摩犬猫霊園 府中市", "name": "慈恵院付属多摩犬猫霊園"}, "Sf45030": {"query": "真蔵院動物霊園 江戸川区", "name": "真蔵院動物霊園"}, "S948896": {"query": "寿量寺附属 真心動物霊園 町田市", "name": "寿量寺附属 真心動物霊園"}, "S3278da": {"query": "ペットメモリアルパーク南多摩 町田市", "name": "ペットメモリアルパーク南多摩"}, "S5818be": {"query": "観蔵院ペット霊園ニルバーナ 練馬区", "name": "観蔵院ペット霊園ニルバーナ"}, "S105757": {"query": "厚木動物メモリアルパーク 厚木市", "name": "厚木動物メモリアルパーク"}, "S606eea": {"query": "アニマルパークペット霊園 厚木市", "name": "アニマルパークペット霊園"}, "Sb2bece": {"query": "蓮昭寺 お寺のペット供養 平塚市", "name": "蓮昭寺 お寺のペット供養"}, "Sa3a602": {"query": "ポチたま霊園 横浜市戸塚区", "name": "ポチたま霊園"}, "S76a3f5": {"query": "よこはま動物葬儀センター 横浜市瀬谷区", "name": "よこはま動物葬儀センター"}, "S994039": {"query": "福泉寺動物霊園 横浜市緑区", "name": "福泉寺動物霊園"}, "S486255": {"query": "ペットエンジェルゲイト横浜青葉 横浜市青葉区", "name": "ペットエンジェルゲイト横浜青葉"}, "S3f9df6": {"query": "平和会ペットメモリアルパーク 横浜市青葉区・川崎市麻生区", "name": "平和会ペットメモリアルパーク"}, "S31d6ce": {"query": "横須賀ペット霊園 ハナオクリ 横須賀市", "name": "横須賀ペット霊園 ハナオクリ"}, "Scb4a2f": {"query": "ペット葬祭・霊園相模の園 相模原市南区", "name": "ペット葬祭・霊園相模の園"}, "S611d1d": {"query": "慈愛堂動物浄苑 上越市", "name": "慈愛堂動物浄苑"}, "S640953": {"query": "ペット葬祭センター 新潟市北区", "name": "ペット葬祭センター"}, "Sdcb9a8": {"query": "フジパーク ペット霊園 新潟市南区", "name": "フジパーク ペット霊園"}, "Sbcaec6": {"query": "北陸ペット葬儀社 富山市", "name": "北陸ペット葬儀社"}, "S08b96f": {"query": "富山動物霊苑 まごころペットセレモニー 射水市", "name": "富山動物霊苑 まごころペットセレモニー"}, "Sd4ef6b": {"query": "高岡ペット葬儀社 高岡市", "name": "高岡ペット葬儀社"}, "Sf259f2": {"query": "小松ペット霊園 小松市", "name": "小松ペット霊園"}, "S33db8a": {"query": "西部緑地動物霊苑 金沢市", "name": "西部緑地動物霊苑"}, "Sff49d6": {"query": "大乗寺山動物霊園 金沢市", "name": "大乗寺山動物霊園"}, "S1f8f5f": {"query": "福井動物霊苑 福井市", "name": "福井動物霊苑"}, "Sf408b4": {"query": "どうぶつセレモニーおおぞら 鯖江市", "name": "どうぶつセレモニーおおぞら"}, "S495b9e": {"query": "あやめの里ペット霊堂 南アルプス市", "name": "あやめの里ペット霊堂"}, "S347000": {"query": "ペット霊園 浄土の里 甲府市", "name": "ペット霊園 浄土の里"}, "S0a98c9": {"query": "長野ペット斎場やすらぎの杜 長野市", "name": "長野ペット斎場やすらぎの杜"}, "Saf555c": {"query": "ペットのあしあと 飯田市", "name": "ペットのあしあと"}, "S11b65d": {"query": "愛ペットセレモニーホール大垣 大垣市", "name": "愛ペットセレモニーホール大垣"}, "Se3d8b8": {"query": "ペットセレモニー岐阜 日野霊園 岐阜市", "name": "ペットセレモニー岐阜 日野霊園"}, "S9e0e34": {"query": "みどり霊園 PETなないろぷらす 浜松市中央区", "name": "みどり霊園 PETなないろぷらす"}, "S50a5de": {"query": "どうぶつの森霊園 静岡市葵区", "name": "どうぶつの森霊園"}, "S53ebbb": {"query": "平澤寺動物霊園 静岡市駿河区", "name": "平澤寺動物霊園"}, "Sd7f2f3": {"query": "一宮どうぶつ霊園 一宮市", "name": "一宮どうぶつ霊園"}, "Se1d99a": {"query": "名古屋ペット霊園 宝泉寺 名古屋市天白区", "name": "名古屋ペット霊園 宝泉寺"}, "S2102e1": {"query": "名古屋ペットセレモニー 眞如院 名古屋市瑞穂区", "name": "名古屋ペットセレモニー 眞如院"}, "S2edc19": {"query": "岡崎ペットセレモニーまんぷく寺 岡崎市", "name": "岡崎ペットセレモニーまんぷく寺"}, "Sbd2aea": {"query": "慈妙院動物霊園 春日井市", "name": "慈妙院動物霊園"}, "S298dd9": {"query": "豊橋動物霊苑 豊橋市", "name": "豊橋動物霊苑"}, "S1435ba": {"query": "ペットのやさしいお葬式 豊橋市", "name": "ペットのやさしいお葬式"}, "S829787": {"query": "三河動物愛護協会 豊田市", "name": "三河動物愛護協会"}, "Sc158a2": {"query": "四日市ペット斎場 四日市市", "name": "四日市ペット斎場"}, "S934111": {"query": "高西寺ペット霊園 津市", "name": "高西寺ペット霊園"}, "Sfb05bb": {"query": "国昌寺付属彦根動物霊園 彦根市", "name": "国昌寺付属彦根動物霊園"}, "S61877c": {"query": "草津・栗東セレモニーホール 栗東市", "name": "草津・栗東セレモニーホール"}, "Se470c1": {"query": "比叡平ペット霊園 京都市山科区", "name": "比叡平ペット霊園"}, "S8a7e14": {"query": "宇治動物霊園 宇治市", "name": "宇治動物霊園"}, "S51cb03": {"query": "大阪生駒ペット霊園 四條畷市", "name": "大阪生駒ペット霊園"}, "S4d3b06": {"query": "千手院動物霊園 堺市南区", "name": "千手院動物霊園"}, "S7d2886": {"query": "愛願院 ペット霊苑 堺市西区", "name": "愛願院 ペット霊苑"}, "S0801bc": {"query": "てんのうじペット霊園 大阪市天王寺区", "name": "てんのうじペット霊園"}, "S97b9b4": {"query": "平野動物霊園 大阪市平野区", "name": "平野動物霊園"}, "S55a861": {"query": "大阪ペット霊園社 大阪市旭区", "name": "大阪ペット霊園社"}, "S48f666": {"query": "大阪ペット斎場 大阪市西区", "name": "大阪ペット斎場"}, "Sf156a7": {"query": "東大阪動物霊園 東大阪市", "name": "東大阪動物霊園"}, "S07118b": {"query": "総合ペットセレモニー豊中・箕面会館 豊中市", "name": "総合ペットセレモニー豊中・箕面会館"}, "Sc72422": {"query": "ペットのお寺 千寿院 たかつき動物霊園 高槻市", "name": "ペットのお寺 千寿院 たかつき動物霊園"}, "S932ef2": {"query": "さんだ動物霊園 三田市", "name": "さんだ動物霊園"}, "S40d9e2": {"query": "犬友社動物霊園・加古川納骨堂 加古川市", "name": "犬友社動物霊園・加古川納骨堂"}, "S1fdf4b": {"query": "愛ペットセレモニー尼崎 尼崎市", "name": "愛ペットセレモニー尼崎"}, "S9388b0": {"query": "猪名川動物霊園 川辺郡猪名川町", "name": "猪名川動物霊園"}, "Sca0744": {"query": "明石動物霊園 明石市", "name": "明石動物霊園"}, "S181128": {"query": "六甲ペットメモリーズ 神戸市北区", "name": "六甲ペットメモリーズ"}, "Se0f92e": {"query": "神戸善光寺 ペット供養塔 神戸市灘区", "name": "神戸善光寺 ペット供養塔"}, "Sb00a5f": {"query": "神戸動物霊園 神戸市西区", "name": "神戸動物霊園"}, "S5175e2": {"query": "大塚山ペット霊園社 天理市", "name": "大塚山ペット霊園社"}, "S136c61": {"query": "ペットのお葬式＆思い出工房 奈良動物霊園 奈良市", "name": "ペットのお葬式＆思い出工房 奈良動物霊園"}, "S51aad1": {"query": "家族の杜 奈良動物霊園 奈良市", "name": "家族の杜 奈良動物霊園"}, "Sda5bf8": {"query": "日蓮宗安楽寺 和歌山市", "name": "日蓮宗安楽寺"}, "S2358f8": {"query": "アニマルレストガーデン 橋本市", "name": "アニマルレストガーデン"}, "S2a5368": {"query": "かけはし斎場 岩美郡岩美町", "name": "かけはし斎場"}, "S1fe8eb": {"query": "美保動物霊園 米子市", "name": "美保動物霊園"}, "S1b8c6d": {"query": "ペット葬祭ワンズハート 松江市", "name": "ペット葬祭ワンズハート"}, "S3536f9": {"query": "浜田ペット葬祭 ひまわりの丘 浜田市", "name": "浜田ペット葬祭 ひまわりの丘"}, "S6f6b42": {"query": "ペットピア 倉敷市", "name": "ペットピア"}, "S78992c": {"query": "愛ペットセレモニー ハロー 西大寺ホール 岡山市東区", "name": "愛ペットセレモニー ハロー 西大寺ホール"}, "S57a0db": {"query": "広島ペット霊苑 広島市南区", "name": "広島ペット霊苑"}, "Sb83f53": {"query": "逢の杜ペット霊園 東広島市", "name": "逢の杜ペット霊園"}, "S1c0622": {"query": "瀬戸動物霊園 福山市", "name": "瀬戸動物霊園"}, "S546706": {"query": "下関動物霊園 下関市", "name": "下関動物霊園"}, "S3ae7dc": {"query": "山口動物霊園 山口市", "name": "山口動物霊園"}, "S16e474": {"query": "徳島ペット供養苑 徳島市", "name": "徳島ペット供養苑"}, "S91417c": {"query": "心のふるさと 徳島霊園 徳島市", "name": "心のふるさと 徳島霊園"}, "S0b9ae7": {"query": "海岸寺ペット霊園やすらぎの里 仲多度郡多度津町", "name": "海岸寺ペット霊園やすらぎの里"}, "S80f803": {"query": "さぬき動物霊園 高松市", "name": "さぬき動物霊園"}, "Sfb31d7": {"query": "香川県ペットメモリアルパーク 御殿動物霊園葬斎場 高松市", "name": "香川県ペットメモリアルパーク 御殿動物霊園葬斎場"}, "Sb4f878": {"query": "ペット霊園松山 松山市", "name": "ペット霊園松山"}, "S43463b": {"query": "愛媛総合ペット霊園 西予市", "name": "愛媛総合ペット霊園"}, "S7edcb4": {"query": "四国ペットセレモニーオアシス 西条市", "name": "四国ペットセレモニーオアシス"}, "Sed9958": {"query": "公園墓地 鉢巻山動物霊園 吾川郡いの町", "name": "公園墓地 鉢巻山動物霊園"}, "S042315": {"query": "ペットのお葬式やさん。 高知市", "name": "ペットのお葬式やさん。"}, "Sbdecef": {"query": "ペットセレモニー 桜PREMIUM 北九州市小倉北区", "name": "ペットセレモニー 桜PREMIUM"}, "Sefe9bf": {"query": "おさゆき動物霊苑 北九州市小倉南区", "name": "おさゆき動物霊苑"}, "S27ad5e": {"query": "ペットメモリアルハーティー 大野城市", "name": "ペットメモリアルハーティー"}, "S8b5713": {"query": "太宰府ペットパーク 太宰府市", "name": "太宰府ペットパーク"}, "Scda797": {"query": "愛ペット・エデン 宮若市", "name": "愛ペット・エデン"}, "S65c821": {"query": "八大龍王寺ペットメモリアル斎場 福岡市東区", "name": "八大龍王寺ペットメモリアル斎場"}, "Se16301": {"query": "ばんれいパーク 福岡市西区", "name": "ばんれいパーク"}, "S1a0483": {"query": "やすらぎの森 ペット霊園むなかた 福津市", "name": "やすらぎの森 ペット霊園むなかた"}, "S28f707": {"query": "ハートランド福岡 筑紫野市", "name": "ハートランド福岡"}, "S5d4383": {"query": "杜の泉動物霊園 遠賀郡水巻町", "name": "杜の泉動物霊園"}, "Sd950b1": {"query": "ペット寺院エンゼルパーク 那珂川市", "name": "ペット寺院エンゼルパーク"}, "S5222d0": {"query": "慈光苑 佐賀市", "name": "慈光苑"}, "Sccf116": {"query": "メモリーランド 小城市", "name": "メモリーランド"}, "S643f2c": {"query": "ペット霊園アニマルへブン 長崎市", "name": "ペット霊園アニマルへブン"}, "S23e587": {"query": "森の中のペット霊園 ペットのおはか 長崎市", "name": "森の中のペット霊園 ペットのおはか"}, "S6940fc": {"query": "植木ペット霊園 熊本市北区", "name": "植木ペット霊園"}, "S461fc7": {"query": "ペット霊苑 蓮華乃郷 熊本市北区", "name": "ペット霊苑 蓮華乃郷"}, "S91ed90": {"query": "大分ペット葬儀社 大分市", "name": "大分ペット葬儀社"}, "S0393e3": {"query": "大分ペット斎場正雲寺 由布市", "name": "大分ペット斎場正雲寺"}, "S41c14a": {"query": "ペット霊園 ドリームランド 児湯郡新富町", "name": "ペット霊園 ドリームランド"}, "Sef3e12": {"query": "平塚ペットエンゼル 都城市", "name": "平塚ペットエンゼル"}, "S822672": {"query": "転法輪寺付属かじき動物霊園「にじの森」 姶良市", "name": "転法輪寺付属かじき動物霊園「にじの森」"}, "Sa2a9dd": {"query": "ペット総合葬祭 南郷の里 鹿児島市", "name": "ペット総合葬祭 南郷の里"}, "S56057f": {"query": "慈愛の丘 とそ動物霊園 鹿児島市", "name": "慈愛の丘 とそ動物霊園"}, "Se2b0db": {"query": "沖縄ペット葬祭 永遠の家まごころ 沖縄市", "name": "沖縄ペット葬祭 永遠の家まごころ"}, "S54fbcf": {"query": "ワンニャン・メモリアル 那覇市", "name": "ワンニャン・メモリアル"}};/*/EMG_REVIEWS*/

// 口コミの場所をどう探すか：提携先（SELECTION_FARES）・緊急タブ（EMG_REVIEWS）・候補カードに表示だけする会社（DISPLAY_COMPANIES）
// words があるときは、違う場所を拾わないよう、見つかった場所の名前にそのことばが全部入っているかを確かめる
function reviewTarget_(id) {
  var key = SELECTION_FARES && Object.keys(SELECTION_FARES).filter(function(k) { return SELECTION_FARES[k].partner_id === id; })[0];
  if (key && SELECTION_FARES[key].review_query) return {query:SELECTION_FARES[key].review_query, words:null, idKey:'PLACE_ID_' + id + '_' + SELECTION_FARES[key].review_query};
  var emg = EMG_REVIEWS[id];
  if (emg && emg.query) return {query:emg.query, words:[].concat(emg.name), idKey:'PLACE_ID_' + id + '_' + emg.query, emg:true};
  var dc = openDisplay_(id) || DISPLAY_COMPANIES.filter(function(c) { return c.id === id; })[0]; // 受け付けを始めた会社は、表示だけの会社と同じ場所で口コミを探す
  // 社内用の事業者一覧（dashPlace_）と同じ場所IDを使う
  // 地図の名前は「COCOタク 小平店」のように登録名と少し違うことが多いので、ブランド名＋支店名の中心のことばで照らし合わせる（loose）。
  // 前の厳しい照らし合わせで「見つからない」と覚えた会社も探し直すよう、覚える場所を D2 に変えた（2026-10-31）
  // 地図に同じ会社が2つあるときは、口コミのある方の正式な名前（review_exact）そのもので探す。（ペッタク 2026-11-09）
  // 住所を出していない（出張だけの）登録は名前の検索に出てこないので、場所のIDを決めておく（review_place。場所のIDは保存してよい）
  if (dc && dc.review_place) return {query:dc.review_q || dc.review_name, words:null, place:dc.review_place, idKey:'PLACE_ID_P_' + id + '_' + dc.review_place};
  if (dc && dc.review_exact) return {query:dc.review_exact, query2:dc.review_q, words:String(dc.review_name || dc.review_exact).split(/[\s、,]+/).filter(String), loose:true, exact:dc.review_exact, idKey:'PLACE_ID_D3_' + id + '_' + dc.review_exact};
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
  var ok = (found.places || []).filter(function(x) { return placeNameOk_(t, x); });
  // 同じ会社が地図に2つ登録されているときは、口コミのある方の正式な名前（review_exact）を先に選ぶ（ペッタク 2026-11-09）
  // 正式な名前が決まっている会社は、その名前と同じ候補だけを選ぶ（口コミのない方の登録を覚えてしまわないように、ほかの候補にはしない）
  var hit = t.exact ? ok.filter(function(x) { return placeNorm_((x.displayName || {}).text || '') === placeNorm_(t.exact); })[0] : ok[0];
  if (!hit || !hit.id) {
    if (keepTrying) return null; // もうひとつの探し方を試す
    log_('口コミ：場所が見つからない ' + id + ' ' + t.query + (found.error ? ' エラー：' + (found.error.status || '') + ' ' + String(found.error.message || '').slice(0, 200) : '') + ' 候補：' + (found.places || []).slice(0, 5).map(function(x) { return (x.displayName || {}).text || ''; }).join('／'));
    if (t.words && !t.exact) props.setProperty(t.idKey, '-'); // 正式な名前の会社は覚えずに次も探す
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
  if (!apiKey || !t) { log_('口コミ：' + (!apiKey ? 'キーがない ' : '探すことばがない ') + partnerId); return null; }
  var placeId = t.place || props.getProperty(t.idKey);
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
  if (used >= CONFIG.REVIEW_MONTHLY_LIMIT) { log_('口コミ：月の上限 ' + partnerId); return null; }
  if (t.emg) {
    var emgMonth = 'REVIEW_EMG_COUNT_' + ym, emgUsed = Number(props.getProperty(emgMonth)) || 0;
    if (emgUsed >= CONFIG.REVIEW_EMG_MONTHLY_LIMIT) { log_('口コミ：緊急タブ・病院の月の上限 ' + partnerId); return null; }
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
function selectionScores_(ids, demoId) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY'), out = {};
  if (!apiKey) return {ok:true, scores:out};
  var list = String(ids || '').split(',').filter(function(id, i, a) { return id && a.indexOf(id) === i && !EMG_REVIEWS[id] && !isAnon_(id, demoId); }).slice(0, 40)
    .map(function(id) { return {id:id, t:reviewTarget_(id)}; }).filter(function(x) { return x.t; });
  list.forEach(function(x) { x.place = x.t.place || props.getProperty(x.t.idKey); });
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
  if (list.length && used >= CONFIG.REVIEW_MONTHLY_LIMIT) log_('口コミ：今月の上限に達したので星を取り寄せない（' + used + '／' + CONFIG.REVIEW_MONTHLY_LIMIT + '）');
  list = list.slice(0, Math.max(0, CONFIG.REVIEW_MONTHLY_LIMIT - used));
  if (!list.length) return {ok:true, scores:out};
  props.setProperty(month, String(used + list.length));
  var got = UrlFetchApp.fetchAll(list.map(function(x) { return placeDetailsRequest_(x.place, apiKey, 'rating,userRatingCount'); }));
  list.forEach(function(x, i) {
    try {
      if (got[i].getResponseCode() !== 200) { log_('口コミ：取り寄せ失敗 ' + x.id + ' ' + got[i].getResponseCode()); return; }
      var v = JSON.parse(got[i].getContentText());
      if (v.rating > 0) out[x.id] = {rating:v.rating, count:Number(v.userRatingCount) || 0};
      else if (!isDisplayOnly_(x.id)) log_('口コミ：点数なし ' + x.id + ' ' + x.place); // 問い合わせできる会社だけ、星が出ない理由を残す
    } catch (e) { log_('口コミ：エラー ' + x.id + ' ' + e); }
  });
  return {ok:true, scores:out};
}

// 候補カードの「口コミを見る」：口コミ本文（地図サービスが関連度の高い順に返す最大5件）をサイトの中で見せる。
// 規約により、書いた人（名前・アイコン・プロフィールへのリンク）と、口コミそれぞれの元のページへのリンクを一緒に返す。保存はしない
function selectionReviews_(partnerId, demoId) {
  if (!reviewTarget_(partnerId) || isAnon_(partnerId, demoId)) return {ok:false,error:'unknown'};
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
  var out = {}, unknown = [];
  ids.split(',').filter(function(id, i, a) { if (!EMG_REVIEWS[id]) { unknown.push(id); return false; } return a.indexOf(id) === i; }).slice(0, 12).forEach(function(id) {
    var v = selectionReview_({id:id});
    if (v) out[id] = v;
  });
  if (unknown.length) log_('口コミ：EMG_REVIEWS にないID ' + unknown.join(',')); // 貼り直し前のコードでは新しい病院は黙って外れる
  return {ok:true, scores:out};
}

// 口コミの星が出ないときの切り分け（運営者がエディタから実行する。何も送らない・保存しない）。
// 例：reviewDebug_('V001') → 探すことば／覚えている場所ID／検索で返った名前と照合の結果／月の回数 を返す
function reviewDebug_(id) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY');
  var t = reviewTarget_(id), ym = Utilities.formatDate(new Date(), TZ, 'yyyyMM');
  var r = {id:id, inEmg:!!EMG_REVIEWS[id], target:t, hasKey:!!apiKey, saved:t ? props.getProperty(t.idKey) : null,
           used:props.getProperty('REVIEW_COUNT_' + ym), emgUsed:props.getProperty('REVIEW_EMG_COUNT_' + ym)};
  if (t && apiKey) {
    var q = placeSearchRequest_(t, apiKey), url = q.url; delete q.url;
    var res = UrlFetchApp.fetch(url, q), found = {};
    try { found = JSON.parse(res.getContentText()) || {}; } catch (e) {}
    r.searchStatus = res.getResponseCode();
    r.candidates = (found.places || []).map(function(x) { return {name:(x.displayName || {}).text || '', ok:placeNameOk_(t, x)}; });
    if (found.error) r.searchError = found.error;
  }
  if (t && apiKey && r.saved && r.saved !== '-') { // 覚えている場所の点数と件数（月の回数に数えずに1回だけ取り寄せる。点数がない場所は星を出さない仕様）
    var d = placeDetailsRequest_(r.saved, apiKey, 'rating,userRatingCount,displayName'), durl = d.url; delete d.url;
    var dres = UrlFetchApp.fetch(durl, d);
    r.detailsStatus = dres.getResponseCode();
    try { r.details = JSON.parse(dres.getContentText()); } catch (e) { r.details = dres.getContentText().slice(0, 300); }
  }
  r.logSheet = !!sheet_(SHEET_LOG); // ログの書き先（「ログ」タブ）があるか
  r.keysWithId = props.getKeys().filter(function(k) { return k.indexOf(id) >= 0; }); // そのIDに関わる覚えている値のキー
  Logger.log(JSON.stringify(r));
  return r;
}
// エディタの関数一覧から実行するための公開の名前（_ で終わる関数は一覧に出ない）。id を省くと V001
function reviewDebug(id) { return reviewDebug_(id || 'V001'); }
function reviewDebugV001() { Logger.log(JSON.stringify(reviewDebug_('V001'))); }

function validateSelection_(p) {
  var error = selectionValid_(p);
  if (error) return {ok:false,error:error};
  var expires = Number(p.quote_expires);
  if (!(expires > Date.now() && expires <= Date.now()+15*60000)) return {ok:false,error:'selection_expired'};
  if ((CONFIG.SHOW_ALL_CANDIDATES && !isOpen_(p.partner_id)) || isDisplayOnly_(p.partner_id)) return {ok:false,error:'selection_unavailable'}; // 全社準備中のあいだ・表示だけの会社には依頼できない
  var pt = selectionCandidates_(selectionRide_(p)).filter(function(x) { return x.id === p.partner_id && !isDisplayOnly_(x.id); })[0];
  if (!pt) return {ok:false,error:'selection_unavailable'};
  var price = selectionPrice_(pt,p);
  if (!price || p.quote_token !== quoteSignature_(p,pt.id,expires,price)) return {ok:false,error:'selection_changed'};
  return {ok:true,partner:pt,price:price};
}

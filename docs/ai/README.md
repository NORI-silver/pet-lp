# どのAIでも同じ作業をするための手順（Claude・ChatGPT・Gemini・Muse）

ペットのくらし窓口（pet.shiokonbu.com）の作業を、どのAIが受けても同じ決まり・同じやり方で進めるための入口です。
モデルが入れ替わっても、ここから読めば続きができるようにしています。Nori さんがやる設定は `docs/ai/setup.md`。

## 1. 作業の前に読む（この順）

1. `AGENTS.md`（このリポジトリ）：全部の決まり。とくに「いちばん上の決まり（4つのバランス）」と「品質の決まり」の一覧。
   - 仕事の進め方の型：`docs/ai/framework/README.md`（どの事業にも使える）と、このサイトの記入例 `docs/ai/pet-operating.md`。指摘の台帳は `docs/ai/feedback.json`。
2. pet-db（非公開）の `docs/ai-memory/MEMORY.md`：Nori さんの方針・戦略・進行中のこと・使わない言葉。必要な話題のファイルも読む。
3. `docs/ai/handoff.md`：ほかのAIの直近の引き継ぎ。
4. GitHub の開いているPRと、最近のコミット（同じところを二重に直さないため）。
5. SEO の作業なら、SHIOKONBU SEO の `get_playbook(site="pet.shiokonbu.com")` と `change_log`。

ほかのAIの会話は自動では伝わりません。決めたこと・分かったことは、GitHub（PR・この引き継ぎメモ・pet-db）に残したものだけが共有されます。

## 2. 作業のしかた（どのAIも同じ）

- 提案・PR・報告の最初に分類を書く：[A] 北極星／[B] 集客／[C] 内部DB＋管理画面／[D] 実データでの検証／[E] 空き状況・マッチング・AI対応／[F] マネタイズ／[G] AI前提の並列の進め方。
- 変更はブランチを作ってPR。ブランチ名はAIごとに分ける：`claude/…`・`chatgpt/…`（Codex は `codex/…`）・`gemini/…`・`muse/…`。`main` に直接書かない。マージは Nori さんの確認のあと。
- ページを変えたら：`python3 tools/gen_areas.py .` → `python3 tools/seo_check.py .` → `python3 tools/rules_check.py .`（新しい違反0件まで直す）→ `node tools/phone_check.cjs --changed`（スマホの写真を自分の目で見る）。生成したファイルも一緒にコミットする。
- コードを動かせないAI（チャットだけの ChatGPT・Gemini・Muse など）は、上の生成と点検ができません。その場合は「生成と点検はまだです」とPRに書き、ページのHTMLを手で直さない。生成は Claude・Codex・Jules・Gemini CLI など、コードを動かせるAIに回す。
- `booking/Code.gs` を変えたら「Apps Script への貼り直しが必要」とPRと報告に書く（貼り直しは手作業か、Mac の clasp）。
- 報告は Nori さんがやることを先に、短く、日本語でやさしく。数字（問い合わせ数・提携数・売上）があれば先頭に。

## 3. 止めていること・Nori さんの「やって」が要ること

- 会社への送信の再開（予約シート「設定」B1）は、Nori さんの「再開して」まで変えない。
- 元に戻せないこと（本番データの削除・外部への送信・お金のかかる設定）は勝手にしない。お金は使わない。
- お誘い・問い合わせのメール：`AGENTS.md` の「C. メール・下書き」と D5 のとおり。下書きは pettaxi.yoyaku の Gmail の下書きに保存し、`python3 tools/draft_check.py <ファイル>` を通す。送る直前にそのスレッドの最新（Nori さんの返信も）を読む。提携している会社には何もしない（Nori 2026-11-17）。
- 秘密（トークン・APIキー・パスワード・シートID・個人のメール）はリポジトリ・PR・チャットに書かない。pet-lp は公開です。

## 4. 道具（どこにつなぐと何ができるか）

| やること | つなぐ先 | 備考 |
|---|---|---|
| サイト・データ・生成スクリプト | GitHub `NORI-silver/pet-lp`（公開）・`NORI-silver/pet-db`（非公開） | 読む・ブランチ・PR |
| 検索の数字（Search Console・GA） | SHIOKONBU SEO（MCP）の `gsc_query`・`ga_report`（`site="pet.shiokonbu.com"`） | 作業の最初に `change_log`、最後に `handoff_note` |
| お誘い・返事のメール | Gmail（pettaxi.yoyaku） | 送るのは決まりどおりに |
| 予約シート・提携先シート | Google スプレッドシート（予約のしくみの持ち主のアカウント） | 読むだけを基本に。書くのは決まった列だけ |
| 予約のしくみ（Apps Script） | リポジトリの `booking/Code.gs` が控え | 本番への反映は貼り直し |

## 5. 終わるとき

- `docs/ai/handoff.md` のいちばん上に1行（日付・AI名・分類・やったこと・PR・残り）を足す（PRに入れる）。
- Nori さんに新しい決まりを言われたら、`AGENTS.md` の一覧と `tools/rules_check.py` と指摘の台帳 `docs/ai/feedback.json` に足す（`python3 tools/feedback_check.py .` を通す）。進行中のことは pet-db の `docs/ai-memory/` の話題のファイルに日付つきで足す。

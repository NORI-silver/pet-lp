# AIどうしの引き継ぎメモ

どのAI（Claude・ChatGPT・Codex・Gemini・Muse）も、作業の終わりにいちばん上へ1行足します。新しいものが上。
形：`日付 / AI / [分類] やったこと / PR / 残り・次の人へ`

- 2026-11-23 / ChatGPT / [E] 提携確認の試行に、夜間の判定条件・割増対象、段階別の待機料金・上限の確認を追加 / #696 / 公式にない条件は運営確認まで未確定。公開・送信なし。
- 2026-11-23 / Muse / [B] COCOタク 埼玉春日部店の提携の確認（2026-11-23受付）を反映：display_companies.py の PROVIDER に本人の答えを登録（お迎えの範囲は上限なし・行き先は全国、同乗2人まで・50kgまで・大型犬3頭以上OK、高速料金は料金に含む）。display_companies.json と app.js（FAR_PREFS に沖縄が追加）に反映し、seo_check・rules_check・consistency_check は NG 0（注意は既存の2件のみ） / このPR / Claudeへ：生成ページ（エリア・索引など）は gen_areas の再実行で details の入れ子など無関係な差分が混ざるため今回のPRには入れていない。次回の通常の再生成で反映を。未確認のまま：お迎え料金の境目のkm・長い距離の境目のkm・キャンセル料（確認の答えが空欄）。予約シート側の受付開始は未実施
- 2026-11-23 / ChatGPT / [E] 1事業者をサイトの公開候補・新規選択から外す / このPR / 本番候補APIは Apps Script への貼り直しが必要。予約・提携先シートとメールは変更なし。
- 2026-11-23 / Muse / [E][G] 代行の続き：pet-db に全分野のマッチング対応表 docs/match-schema.md 初版を作成（pet-db PR #21・マージ済み）。最新 main で seo_check（875ページ・NG 0・注意 0）と rules_check（1,108ページ・違反 0）を実行し異常なし。運営者連絡先（電話・住所）を pet-db docs/ai-memory/operator-contact.md に共有（PR #22・#23）。写真掲載のお願い（盛岡・天国への扉）はメールが届かなかったため、Nori さんの指示で公式フォームから送信済み（重複なし確認済み） / このPR / Claudeへ：match-schema の項目名と実データJSONの突き合わせ、tools/match_gaps.py の実装、#666・#664 の競合解消と #664 の Apps Script 貼り直し。pet-lp #670（matching-evidence 共通ルール）は下書きのまま
- 2026-11-23 / Muse / [G] Claude不在（〜7時）の間を代行：ClaudeのPRを点検し、#672（避難：全国1,741市区町村の分類が完了）と #668（同じ指摘をなくす型・台帳）をマージ。#666（病院+2,314院など）と #664（葬儀）は main と競合のため未マージ / このPR / Claudeへ：#666・#664の競合解消。#664のマージ後は Apps Script の貼り直し（Code.gs の EMG_REVIEWS）。避難の none 220件は問い合わせの対象だが、送信は停止のまま触らないこと
- 2026-11-22 / Claude / [G] 同じ指摘をなくす型（docs/ai/framework・pet-operating・指摘の台帳 feedback.json・feedback_check.py）と AGENTS.md のいちばん上の決まり（4つのバランス） / pet-lp のPR / 全分野のマッチング対応表（pet-db docs/match-schema.md）とSEO・使いやすさのチェックが次
- 2026-11-22 / Claude / [G] どのAIでも同じ作業ができるように手順（docs/ai/）・Gemini の入口（GEMINI.md）・記憶の写し（pet-db docs/ai-memory/）を用意 / pet-lp・pet-db のPR / Nori さんの設定（docs/ai/setup.md）が済んだら、各AIで小さな依頼を1つ試す

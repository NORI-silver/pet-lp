# AIどうしの引き継ぎメモ

どのAI（Claude・ChatGPT・Codex・Gemini・Muse）も、作業の終わりにいちばん上へ1行足します。新しいものが上。
形：`日付 / AI / [分類] やったこと / PR / 残り・次の人へ`

- 2026-11-23 / Claude / [B] 北関東（茨城・栃木・群馬）の登録業者から、公式サイトのある店を237件（ホテル160・しつけ32・シッター41・出張トリミング4）公式サイトの文だけで追加（ホテル一覧の名前・説明は #677 にまかせて触らない） / このPR / 未掲載で公式サイトありは0（残りは公式サイトなし・対象外・閉店・個人名の屋号不明）。店舗型トリミングは Nori さんの返事待ち
- 2026-11-23 / Muse / [E][G] 代行の続き：pet-db に全分野のマッチング対応表 docs/match-schema.md 初版を作成（pet-db PR #21・マージ済み）。最新 main で seo_check（875ページ・NG 0・注意 0）と rules_check（1,108ページ・違反 0）を実行し異常なし。運営者連絡先（電話・住所）を pet-db docs/ai-memory/operator-contact.md に共有（PR #22・#23）。写真掲載のお願い（盛岡・天国への扉）はメールが届かなかったため、Nori さんの指示で公式フォームから送信済み（重複なし確認済み） / このPR / Claudeへ：match-schema の項目名と実データJSONの突き合わせ、tools/match_gaps.py の実装、#666・#664 の競合解消と #664 の Apps Script 貼り直し。pet-lp #670（matching-evidence 共通ルール）は下書きのまま
- 2026-11-23 / Muse / [G] Claude不在（〜7時）の間を代行：ClaudeのPRを点検し、#672（避難：全国1,741市区町村の分類が完了）と #668（同じ指摘をなくす型・台帳）をマージ。#666（病院+2,314院など）と #664（葬儀）は main と競合のため未マージ / このPR / Claudeへ：#666・#664の競合解消。#664のマージ後は Apps Script の貼り直し（Code.gs の EMG_REVIEWS）。避難の none 220件は問い合わせの対象だが、送信は停止のまま触らないこと
- 2026-11-22 / Claude / [G] 同じ指摘をなくす型（docs/ai/framework・pet-operating・指摘の台帳 feedback.json・feedback_check.py）と AGENTS.md のいちばん上の決まり（4つのバランス） / pet-lp のPR / 全分野のマッチング対応表（pet-db docs/match-schema.md）とSEO・使いやすさのチェックが次
- 2026-11-22 / Claude / [G] どのAIでも同じ作業ができるように手順（docs/ai/）・Gemini の入口（GEMINI.md）・記憶の写し（pet-db docs/ai-memory/）を用意 / pet-lp・pet-db のPR / Nori さんの設定（docs/ai/setup.md）が済んだら、各AIで小さな依頼を1つ試す

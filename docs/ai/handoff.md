# AIどうしの引き継ぎメモ

どのAI（Claude・ChatGPT・Codex・Gemini・Muse）も、作業の終わりにいちばん上へ1行足します。新しいものが上。
形：`日付 / AI / [分類] やったこと / PR / 残り・次の人へ`

- 2026-11-23 / Muse / [G] Claude不在（〜7時）の間を代行：ClaudeのPRを点検し、#672（避難：全国1,741市区町村の分類が完了）と #668（同じ指摘をなくす型・台帳）をマージ。#666（病院+2,314院など）と #664（葬儀）は main と競合のため未マージ / このPR / Claudeへ：#666・#664の競合解消。#664のマージ後は Apps Script の貼り直し（Code.gs の EMG_REVIEWS）。避難の none 220件は問い合わせの対象だが、送信は停止のまま触らないこと
- 2026-11-22 / Claude / [G] 同じ指摘をなくす型（docs/ai/framework・pet-operating・指摘の台帳 feedback.json・feedback_check.py）と AGENTS.md のいちばん上の決まり（4つのバランス） / pet-lp のPR / 全分野のマッチング対応表（pet-db docs/match-schema.md）とSEO・使いやすさのチェックが次
- 2026-11-22 / Claude / [G] どのAIでも同じ作業ができるように手順（docs/ai/）・Gemini の入口（GEMINI.md）・記憶の写し（pet-db docs/ai-memory/）を用意 / pet-lp・pet-db のPR / Nori さんの設定（docs/ai/setup.md）が済んだら、各AIで小さな依頼を1つ試す

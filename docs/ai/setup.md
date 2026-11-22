# Nori さんがやる設定（ChatGPT・Gemini・Muse）

それぞれ最初に1回だけです。鍵やパスワードはチャットに貼らず、各サービスの設定画面に入れてください。お金のかかるプランへの変更は要りません（機能がプランで使えないときは、その道具だけ使わずに進めます）。

## 共通：どのAIにも最初に貼る文

> GitHub の NORI-silver/pet-lp の main にある AGENTS.md と docs/ai/README.md を読み、NORI-silver/pet-db の docs/ai-memory/MEMORY.md も読んでから作業してください。決まりはそこに書いてあるとおり。会社への送信は止めたまま、変更はブランチとPRで出し、マージは私の確認のあと。終わったら docs/ai/handoff.md に1行足してください。
> やってほしいこと：（ここに依頼）

## ChatGPT

いまお誘い用の Gmail（pettaxi.yoyaku）はつないであります。足りないのは次の3つです。

1. **GitHub**：設定 →「アプリ（コネクタ）」→ GitHub →「接続」。リポジトリは `pet-lp` と `pet-db` の2つを許可。
2. **コードを動かす作業は Codex**（chatgpt.com/codex）：同じ GitHub で pet-lp を選ぶ。Codex は `AGENTS.md` を自動で読みます。ページの生成・点検（gen_areas・rules_check）ができるのは Codex のほうです。
3. **SHIOKONBU SEO（検索の数字）**：前から ChatGPT につないであれば、そのまま使えます。新しく入れるときは https://chatgpt.com/plugins →「＋」→「Add custom MCP server」→ URL を入れる → 注意を読んで「続ける」→ インストール。チャットで `@` を打って選ぶと使えます。
4. （あれば）**プロジェクト**：ChatGPT の「プロジェクト」に「ペットのくらし窓口」を作り、上の「最初に貼る文」をプロジェクトの指示に入れておくと、毎回貼らなくて済みます。

## Gemini

1. **GitHub に書く作業は Jules**（jules.google）：Google のアカウントで入り、GitHub をつないで `pet-lp`・`pet-db` を選ぶ。Jules は `AGENTS.md` を読み、ブランチとPRを作ります。
2. **Gemini アプリ**（gemini.google.com）：
   - 「Gem」を1つ作り（名前「ペットのくらし窓口」）、指示に上の「最初に貼る文」を入れる。
   - Gmail・ドライブ・スプレッドシートは、設定 →「アプリ」で Google Workspace をオンにする（pettaxi.yoyaku のメールを見せるなら、そのアカウントで Gemini に入る）。
   - GitHub はチャットの「＋」→「コードをインポート」で pet-lp を読み込めます（読むだけ）。
3. **SHIOKONBU SEO**：Gemini アプリは「設定 → Gemini Apps Developer Mode」（gemini.google.com/devmode）→「＋ Create new」→ URL を入れて「Connect」。ただし Gemini アプリは OAuth のログインがあるサーバーだけつなげます。つながらなければ、SEO の数字は ChatGPT か Claude に頼みます。
4. パソコンで Gemini CLI を使う場合は、pet-lp のフォルダで動かせば `GEMINI.md`（＝`AGENTS.md` を読む）を自動で読みます。

## Muse（Meta）

Meta の Muse は、アプリかウェブ（muse.ai）で使うAIです。Nori さんのアカウントで使えることを確かめました（2026-11-22）。接続はリンクをタップして Nori さんが許可します。SHIOKONBU SEO の URL は、Claude の「設定 → コネクタ」か ChatGPT のアプリの設定にある SHIOKONBU SEO の画面で見られます。

1. **GitHub・Gmail**：設定 →「Connectors」→ GitHub と Gmail（pettaxi.yoyaku）をつなぐ。GitHub は pet-lp・pet-db を許可。
2. **承認の設定**：同じ画面で、送る・書きこむ動きは「毎回確認（require approval）」にしておく。
3. **SHIOKONBU SEO**：Muse には URL を入れる欄がないので、チャットで「このURLのMCPサーバー（streamable HTTP）をカスタムコネクタとしてつないで」と頼み、URL を渡す。鍵を聞かれたら、チャットではなく出てきた入力画面に入れる。最後に「スキルとして保存する」を選ぶ。
4. 上の「最初に貼る文」も、Muse に「スキルとして保存して」と頼んでおくと次から使えます。

## AIごとにできないこと（いまの時点）

- Claude のアーティファクト（運営ボードなど）は Claude の中だけで見られます。ほかのAIには数字をシートかリポジトリから読んでもらいます。
- Mac での作業（Gmail の送信の予約・clasp での Apps Script の貼り直し）は、いまは Claude だけがしています。ほかのAIで Apps Script を変えたときは、PRのあと Claude に「貼り直して」と頼んでください。
- ほかのAIの会話の中身は伝わりません。続きを頼むときは「docs/ai/handoff.md を読んで」と言えば、前のAIの引き継ぎを読みます。

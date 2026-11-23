# Claude も Codex も止まったときの予備（GitHub で動くAI）

GitHub の Issue（やることメモ）に頼みごとを書いて、ラベル「ai」を付けると、GitHub 上でAIが作業してPRを作ります。
スマホの GitHub アプリだけで使えます。AIは `AGENTS.md` のルールを読んで作業します。

- しくみ：`.github/workflows/ai-backup.yml`（GitHub Actions + Aider + OpenRouter）
- 料金：OpenRouter に入れたお金の分だけ（使った分だけ減ります）。GitHub Actions は公開リポジトリなら無料です。
- モデル：リポジトリの変数 `AI_MODEL` を書き換えるだけで替えられます（空なら `openrouter/anthropic/claude-sonnet-4.5`）。
- 他のリポジトリでも、このファイルと鍵を同じように入れれば使えます。

## 最初に1回だけ（Nori さんの操作）

1. **OpenRouter の鍵を作る**
   1. https://openrouter.ai にログインし、「Credits」でお金を入れる（まずは $10 くらいで十分です）。
   2. 「Keys」→「Create Key」。名前は `pet-lp` など。**「Credit limit」に上限（例：$10）を入れておく**と使いすぎを防げます。
   3. 表示された鍵（`sk-or-` で始まる文字）をコピーする。鍵は他の人やチャットに貼らないでください。
2. **鍵を GitHub に登録する**
   - https://github.com/NORI-silver/pet-lp/settings/secrets/actions を開き、「New repository secret」。
   - Name に `OPENROUTER_API_KEY`、Secret に鍵を貼って「Add secret」。
3. **AIがPRを作れるようにする**
   - https://github.com/NORI-silver/pet-lp/settings/actions を開き、下の「Workflow permissions」で
     「**Allow GitHub Actions to create and approve pull requests**」にチェックを入れて「Save」。
4. **ラベル「ai」を作る**
   - https://github.com/NORI-silver/pet-lp/labels で「New label」、名前 `ai` で作成。

（モデルを替えたいときは https://github.com/NORI-silver/pet-lp/settings/variables/actions で変数 `AI_MODEL` を作り、`openrouter/` + OpenRouter のモデル名 を入れます。）

## 頼むとき（毎回）

1. GitHub アプリで pet-lp を開き、「Issues」→「＋」（新しいIssue）。
2. タイトルに一言、本文にやってほしいことを具体的に書く。例：
   - タイトル「よくある質問にキャンセルの質問を足す」
   - 本文「トップのよくある質問に『キャンセルはできますか？』を足して。答えは、当サイトへのキャンセル料はなし、決定後は引き受けた会社の規定、という内容で。」
3. ラベル「ai」を付けて保存。数分〜10分ほどで、Issue に「PRを作りました」とリンクが付きます。
4. PR の中身を見て、よければ「Merge」。サイトに反映されます。
   - やり直したいときは、Issue の本文を直してからラベル「ai」を外して付け直します。
   - 「止まりました」と付いたら、鍵の残高を確かめてください。

## 注意

- ラベルを付けられるのはリポジトリの持ち主（Nori さん）だけなので、他の人が勝手に動かすことはできません。
- `booking/Code.gs` が変わったPRは、マージしても予約の仕組みには反映されません。PRにその旨が書かれるので、Claude が戻ってから貼り直します。
- 大きな作り替えより、文言の修正や小さな直しに向いています。

## 動作確認

最初は手順書の小さな追記を依頼して、PRが作られることを確認します。

2026-10-28 試運転で動作を確認しました。

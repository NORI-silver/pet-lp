# [F] 公開先を Cloudflare Pages へ移す手順（元に戻す方法つき）

2026-11-08 作成。まだ移していません。移す時期は「月5万PV」（2026-11-09 戦略担当「倍速」で10万PVから前倒し）か「手数料を始める日の前」の早いほう（戦略担当の判断）。Nori さんへの作業のお願いは、時期が来たら戦略担当がまとめて出す。

## なぜ移すか

- GitHub Pages は転送量の目安が月100GB。平均250KB/PVだと約40万PVで超えるので、余裕をみて5万PVで移す（手数料を始める前の商用の決まりにも早めに合わせる）。
- GitHub Pages は「オンラインの商売や取引を主にするサイト」には使えない決まり（[GitHub Pages の制限](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)）。手数料を始めたら当たるおそれがある。
- Cloudflare Pages は無料で商用に使え、静的なページの転送量に上限の記載がない。ファイルは2万まで（2026-11-08 で約630）、1ファイル25MiBまで、公開は月500回まで（[Cloudflare Pages の上限](https://developers.cloudflare.com/pages/platform/limits/)）。

URL（pet.shiokonbu.com）は変わらないので、検索の順位には響かない。

## 用意（Nori さん・1回だけ）

1. Cloudflare の無料アカウントを作る。
2. 「My Profile → API Tokens」で、権限「Account / Cloudflare Pages / Edit」だけの鍵を作る。
3. GitHub の pet-lp の Settings → Secrets and variables → Actions に、`CLOUDFLARE_API_TOKEN`（2の鍵）と `CLOUDFLARE_ACCOUNT_ID`（ダッシュボードの右に出るID）を入れる。鍵はリポジトリに書かない。

## 移し方（AIがやる。半日ほど）

1. **両方に公開する**：`.github/workflows/pages.yml` に、GitHub Pages の公開のあとに次のジョブを足す（GitHub Pages の公開はそのまま残す）。
   ```yaml
   cloudflare:
     needs: deploy
     runs-on: ubuntu-latest
     timeout-minutes: 10
     steps:
       - uses: actions/checkout@v4
       - uses: cloudflare/wrangler-action@v3
         with:
           apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
           accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
           command: pages deploy . --project-name=pet-shiokonbu --branch=main
   ```
   最初の1回で Cloudflare に `pet-shiokonbu` の公開先ができる。使うアクションの版は、足すときに最新の安定版を確かめる。
2. **pet-shiokonbu.pages.dev で確かめる**：トップ・地域ページ・病院／ドッグラン／葬儀のページ・ガイド・`/go/`・404 のページ・`sitemap.xml`・`robots.txt`・`llms.txt`・IndexNow の鍵のファイル。フォームで検索して候補カードが出るか（予約のしくみはどこから開いても動く）。
   - 場所の入力候補のブラウザ用キーは pet.shiokonbu.com からだけ動くように制限しているので、pages.dev では候補が出ない。これは正常。切りかえ後に確かめる。
   - Cloudflare は `/xxx.html` を `/xxx` にまとめる。このサイトはフォルダ（`/xxx/`）の形なので影響はないが、念のため `/go/` と `404.html` を見る。
3. **向き先を替える**：Cloudflare の pet-shiokonbu → Custom domains で `pet.shiokonbu.com` を足す。shiokonbu.com の DNS（いまの管理画面）で、`pet` の CNAME を GitHub（`nori-silver.github.io`）から `pet-shiokonbu.pages.dev` に替える。前の日に `pet` の TTL を300秒に下げておくと、切りかえも戻しも早い。ここだけ Nori さんの DNS の作業が要る。
4. **切りかえ後に確かめる**：https で開けるか、場所の入力候補、問い合わせの送信（見本の画面 `?demo=` で送らずに確かめる）、アクセス解析にPVが入るか、Search Console でエラーが増えていないか。

## 元に戻す

- `pet` の CNAME を `nori-silver.github.io` に戻すだけ。GitHub Pages の公開はつづけているので、中身は最新のまま。
- 戻したあと https の証明書が出なおすまで数分かかることがある。
- 1週間問題がなければ、`pages.yml` の GitHub Pages の公開を止めるかを戦略担当と決める（止めても `CNAME` と `.nojekyll` は消さない）。

## 費用

- Cloudflare Pages：0円（無料の範囲）。
- 移したあとに増えるもの：なし。口コミ・場所の入力候補の費用は公開先とは別（`booking/Code.gs` と地図サービスの側）。

const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const [root, kind, out] = process.argv.slice(2).map((v,i)=>i===1?v:path.resolve(v));
const origin = 'http://pet.test';
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml'};
const specs=kind==='photo'?[['/dog-trainer/kyoto/','.cs-ph[data-gph="T114"]'],['/dogrun/okayama/','.cs-ph:has(.cs-ph-c)'],['/rojin-home/','.cs-ph:has(.cs-ph-n)'],['/','.partner-card.qa-taxi']]:
  kind==='cta'?[['/','#seeBtn'],['/chiba/','#seeBtn']]:[['/jichitai/maigo/','#jcPro']];
(async()=>{
 fs.mkdirSync(out,{recursive:true}); const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||undefined});
 let failed=false;
 try {
 for (const width of (kind==='cta'?[320,375,390]:[375,390])) {
  const context=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1,serviceWorkers:'block'});
  await context.route('**/*', async r=>{
   const url=new URL(r.request().url());
   if(url.origin!==origin||r.request().method()!=='GET')return r.abort();
   try{
    const rel=decodeURIComponent(url.pathname).replace(/^\/+/, '');
    const file=path.resolve(root,rel)+(url.pathname.endsWith('/')?'/index.html':'');
    if (!file.startsWith(root+path.sep)) return r.abort();
    if(kind==='photo'&&url.pathname==='/') {
      const body=fs.readFileSync(file,'utf8').replace('function buildCard(card, leg){','window.__qaCard = buildCard; window.__qaPhotos = CO_PH; function buildCard(card, leg){');
      await r.fulfill({body,contentType:types['.html']});
    }else await r.fulfill({path:file,contentType:types[path.extname(file)]||'application/octet-stream'});
   }catch(e){await r.abort();}
  });
  for(const [p,selector] of specs){
   const page=await context.newPage(); const tag=p.replace(/[^a-z]+/g,'-')+'-'+width;
   try {
    await page.goto(origin+p,{waitUntil:'domcontentloaded'});
    await page.evaluate(()=>document.fonts.ready);
    if(kind==='photo'&&p==='/'){
     await page.evaluate(()=>{
      if(!window.__qaCard || !window.__qaPhotos?.D0ec95b6 || window.__qaPhotos.D0ec95b6[0].length<2)throw Error('missing exact two-photo taxi fixture');
      // First show actual candidate and actual authorized assets, then run an explicit stress-only localized synthetic credit in the same rendering path.
      function add(label,cls) {
       const card=window.__qaCard({id:'D0ec95b6',label,display_only:true,price:{text:'4,400円'},anon:true},'go');
       card.classList.add(cls);document.querySelector('main').prepend(card);
      }
      add('実画像・レイアウト確認（送信なし）','qa-taxi');
      window.__qaPhotos.D0ec95b6[1]='写真：公式サイト提供。表示確認用の架空の長いクレジット（折り返しテストのみ）';
      add('クレジット折り返しの合成検証','qa-credit');
     });
     for(const cls of ['.qa-taxi','.qa-credit']){
      const thumb=page.locator(cls+' .partner-thumb');
      const images=thumb.locator('img');
      assert.equal(await images.count(),2);
      await images.first().evaluate(im=>im.decode());
      const stats=await thumb.evaluate(el=>{
       const s=el.querySelector('.partner-photos'), img=s.querySelector('img'), dots=el.querySelector('.partner-photo-n'), c=el.querySelector('.partner-photo-credit');
       const a=s.getBoundingClientRect(), d=dots.getBoundingClientRect(), b=c?.getBoundingClientRect();
       return {contain:getComputedStyle(img).objectFit,swipe:s.scrollWidth>s.clientWidth+10,imgWidth:img.naturalWidth,dotsInside:d.top>=a.top-1&&d.bottom<=a.bottom+1,
        creditFit:!c||c.scrollWidth<=c.clientWidth+1,overlap:!!(b&&b.left<d.right&&d.left<b.right&&b.top<d.bottom&&d.top<b.bottom)};
      });
      assert.deepEqual([stats.contain,stats.swipe,stats.dotsInside,stats.creditFit,stats.overlap],['contain',true,true,true,false],JSON.stringify(stats));
      assert.ok(stats.imgWidth>0);
     }
    }
    const candidate=page.locator(selector).first();
    await candidate.waitFor({state:'visible',timeout:5000});
    await candidate.scrollIntoViewIfNeeded();
    if(kind==='photo'&&p!=='/') {
     await candidate.locator('img').first().evaluate(img=>img.decode()); 
     const stats=await candidate.evaluate(el=>{
      const s=el.querySelector('.cs-ph-s'), img=s.querySelector('img'), a=el.getBoundingClientRect(), credit=el.querySelector('.cs-ph-c'), mark=el.querySelector('.cs-ph-n');
      const within=(x)=>!x||[x.getBoundingClientRect()].every(b=>b.left>=a.left-1&&b.right<=a.right+1&&b.top>=a.top-1&&b.bottom<=a.bottom+1);
      const b=credit?.getBoundingClientRect(), m=mark?.getBoundingClientRect();
      return {fit:getComputedStyle(img).objectFit,loaded:img.naturalWidth>0,within:within(credit)&&within(mark),creditWrap:!credit||credit.scrollWidth<=credit.clientWidth+1,
        overlap:!!(b&&m&&b.left<m.right&&m.left<b.right&&b.top<m.bottom&&m.top<b.bottom),count:s.querySelectorAll('img').length,scroll:s.scrollWidth-s.clientWidth};
     });
     assert.deepEqual([stats.fit,stats.loaded,stats.within,stats.creditWrap,stats.overlap],['contain',true,true,true,false]);
     if(stats.count>1)assert.ok(stats.scroll>10,'multiple images must swipe');
    } else if(kind==='cta') {
     const b=page.getByRole('button',{name:'会社と料金を見る',exact:true});
     assert.equal(await b.count(),1,'accessible label must match exactly');
     assert.ok(await b.isVisible());
     const m=await candidate.evaluate(el=>{
      const label=el.textContent.trim(), a=el.getBoundingClientRect();
      const text=document.createRange();text.selectNodeContents(el);
      const rects=[...text.getClientRects()].filter(x=>x.width>0&&x.height>0);
      const described=el.getAttribute('aria-describedby');
      const help=document.getElementById(described), h=help?.getBoundingClientRect(), cs=help&&getComputedStyle(help);
      return {label,left:a.left,right:a.right,top:a.top,bottom:a.bottom,nativeFit:el.scrollWidth<=el.clientWidth+1,
       lines:new Set(rects.map(x=>Math.round(x.top))).size,glyphsWithin:rects.every(x=>x.left>=a.left-1&&x.right<=a.right+1),
       type:el.type,described,helpText:help?.textContent.trim(),separate:!!help&&!el.contains(help)&&el.nextElementSibling===help,
       helpVisible:!!h&&h.width>0&&h.height>0&&cs.visibility==='visible'&&cs.display!=='none',
       helpBelow:!!h&&h.top>=a.bottom-1,helpFits:!!h&&h.left>=-1&&h.right<=innerWidth+1&&help.scrollWidth<=help.clientWidth+1};
     });
     assert.deepEqual([m.label,m.lines,m.glyphsWithin,m.nativeFit,m.type,m.described,m.separate,m.helpVisible,m.helpBelow,m.helpFits],
      ['会社と料金を見る',1,true,true,'button','seeBtnHelp',true,true,true,true],JSON.stringify(m));
     assert.ok(m.left>=-1&&m.right<=width+1,JSON.stringify(m));
     assert.match(m.helpText,/料金の確認は無料です/);
     console.log('BOOKING_CTA',p,width,JSON.stringify(m));
    } else if(kind==='maigo') {
     const rows=await candidate.locator('tbody tr').count();
     assert.equal(rows,31);
     assert.ok(await candidate.locator('thead').first().isVisible());
    }
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+2),'viewport overflow');
    console.log('PASS',p,width,selector);
   }catch(e){failed=true;console.error('FAIL',p,width,selector,e.message);}
   try {
    await page.screenshot({path:path.join(out,tag+'.png')});
    if (kind==='photo'&&p==='/') await page.locator('.qa-credit').screenshot({path:path.join(out,tag+'-credit.png'),timeout:3000});
   }catch{}
   await page.close();
  }
  await context.close();
 }
 }finally{await browser.close();}
 if(failed)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});

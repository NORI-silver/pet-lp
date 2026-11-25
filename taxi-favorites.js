/* ペットタクシーのお気に入り。端末には公開一覧で引ける会社IDだけを残す。 */
(function(){
  "use strict";
  var KEY = "petTaxiFavorites:v1", LIMIT = 100;
  var owns = function(o, k){ return Object.prototype.hasOwnProperty.call(o, k); };
  function model(catalog, aliases, paused){
    function listing(id){
      if (typeof id !== "string" || !/^[PD][\da-f]+$/i.test(id) || paused.indexOf(id) >= 0) return null;
      var k = owns(aliases,id) ? aliases[id] : id;
      if (paused.indexOf(k) >= 0 || !owns(catalog,k) || !Array.isArray(catalog[k]) || !catalog[k][0]) return null;
      return {id:k, label:catalog[k][0]};
    }
    function read(raw){
      var input;
      try { input = JSON.parse(raw); } catch (e) { return []; }
      if (!Array.isArray(input)) return [];
      return input.slice(0,LIMIT).map(listing).filter(Boolean).map(function(x){ return x.id; }).filter(function(id,i,a){ return a.indexOf(id) === i; });
    }
    function offer(card){
      if (!card || card.demo || card.anonTag || (card.anon && !card.site)) return null;
      return listing(card.id);
    }
    return {listing:listing, read:read, offer:offer};
  }
  if (typeof module !== "undefined" && module.exports) { module.exports = {model:model}; return; }

  var active = null;
  function init(config){
    if (active || !config || !config.form || config.demo) return;
    var storage, api = model(config.catalog, config.aliases, config.paused), ids;
    try {
      storage = window.localStorage;
      ids = api.read(storage.getItem(KEY));
    } catch (e) { return; }
    var form = config.form, panel = document.createElement("details"), title = document.createElement("summary");
    var hint = document.createElement("p"), list = document.createElement("ul"), status = document.createElement("span");
    panel.className = "taxi-favorites";
    hint.textContent = "このブラウザに保存されます。料金や空き状況は、条件を入れてご確認ください。";
    status.className = "taxi-fav-sr"; status.setAttribute("role","status");
    panel.append(title,hint,list);
    form.prepend(panel,status); // フォームの先頭。緊急モードではフォームと一緒に隠れる。
    var atResults = document.getElementById("partnerTitle"), jump;
    if (atResults) {
      jump = document.createElement("button");
      jump.type = "button"; jump.className = "taxi-fav-jump";
      jump.addEventListener("click",function(){
        panel.open = true;
        title.focus({preventScroll:true});
        panel.scrollIntoView({block:"start"});
      });
      atResults.after(jump);
    }
    function reflect(button){
      var on = ids.indexOf(button.dataset.taxiFavorite) >= 0;
      button.firstChild.textContent = on ? "★" : "☆";
      button.setAttribute("aria-pressed",String(on));
    }
    function render(){
      panel.hidden = !ids.length;
      title.textContent = "お気に入り（" + ids.length + "件）";
      list.replaceChildren();
      ids.forEach(function(id){
        var item = api.listing(id), row = document.createElement("li"), label = document.createElement("span"), remove = document.createElement("button");
        label.textContent = item.label;
        remove.type = "button"; remove.textContent = "外す"; remove.setAttribute("aria-label",item.label + "をお気に入りから外す");
        remove.addEventListener("click",function(){
          var i = ids.indexOf(id);
          if (!change(item)) return;
          var next = list.children[Math.min(i,list.children.length-1)];
          if (next) next.querySelector("button").focus();
          else {
            panel.open = false;
            var toggle = Array.from(form.querySelectorAll("[data-taxi-favorite]")).find(function(b){ return b.dataset.taxiFavorite === id && b.getClientRects().length; });
            if (toggle) toggle.focus();
            else { var pickup = form.querySelector("#pickup"); if (pickup) pickup.focus(); }
          }
        });
        row.append(label,remove); list.appendChild(row);
      });
      if (jump) {
        jump.hidden = !ids.length;
        jump.textContent = "★ お気に入り（" + ids.length + "件）を見る";
      }
    }
    function redrawButtons(){ form.querySelectorAll("[data-taxi-favorite]").forEach(reflect); }
    function change(item, button){
      var prev;
      try { prev = api.read(storage.getItem(KEY)); }
      catch (e) { status.textContent = "このブラウザではお気に入りを保存できませんでした。"; return false; }
      // 表示中の状態に従う。他のタブの変更があっても、追加するつもりで外さない。
      var on = ids.indexOf(item.id) >= 0;
      var next = on ? prev.filter(function(id){ return id !== item.id; }) : [item.id].concat(prev.filter(function(id){ return id !== item.id; }));
      if (next.length > LIMIT) { status.textContent = "お気に入りがいっぱいです。使わない会社を外してください。"; return false; }
      try { if (next.length) storage.setItem(KEY,JSON.stringify(next)); else storage.removeItem(KEY); }
      catch (e) {
        status.textContent = "このブラウザではお気に入りを保存できませんでした。";
        if (button) button.title = status.textContent;
        return false;
      }
      ids = next;
      status.textContent = item.label + (on ? "をお気に入りから外しました。" : "をお気に入りに保存しました。");
      render(); redrawButtons();
      return true;
    }
    active = function(card){
      var item = api.offer(card);
      if (!item) return null;
      var button = document.createElement("button"), star = document.createElement("span");
      button.type = "button"; button.className = "taxi-fav-toggle"; button.dataset.taxiFavorite = item.id;
      button.setAttribute("aria-label",item.label + "のお気に入り");
      button.title = "お気に入り"; star.setAttribute("aria-hidden","true"); button.appendChild(star);
      reflect(button);
      button.addEventListener("click",function(event){ event.stopPropagation(); change(item,button); });
      return button;
    };
    render();
    window.addEventListener("storage",function(event){
      if (event.storageArea === storage && (event.key === KEY || event.key === null)) {
        ids = api.read(event.newValue); render(); redrawButtons();
      }
    });
  }
  window.PetTaxiFavorites = {init:init,button:function(card){ return active && active(card); }};
  if (window.PetTaxiFavoritesConfig) init(window.PetTaxiFavoritesConfig);
})();

import re
# --- CSS（tools/cardphoto.py）
p = "tools/cardphoto.py"
s = open(p, encoding="utf-8").read()
assert "cs-ph-w" not in s
anchor = "       '</style>')"
assert s.count(anchor) == 1
css = r"""       '.cs-ph-w{position:relative}'
       '.cs-ph-d{position:absolute;left:50%;bottom:7px;transform:translateX(-50%);display:flex;gap:5px;padding:3px 7px;border-radius:999px;background:rgba(0,0,0,.35);pointer-events:none}'
       '.cs-ph-d i{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.55)}'
       '.cs-ph-d i.on{background:#fff}'
       '.cs-ph-a{position:absolute;top:50%;width:28px;height:28px;margin-top:-14px;padding:0 0 3px;border:0;border-radius:50%;background:rgba(255,255,255,.78);color:#3d2f25;font-size:20px;line-height:28px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.25);cursor:pointer;opacity:.9}'
       '.cs-ph-a.l{left:6px}.cs-ph-a.r{right:6px}'
       '.cs-ph-w.f .cs-ph-a.l,.cs-ph-w.e .cs-ph-a.r{display:none}'
"""
s = s.replace(anchor, css + anchor)
open(p, "w", encoding="utf-8").write(s)
# --- JS（ga.js の先頭。どのカードのページにも入っている）
p = "ga.js"
s = open(p, encoding="utf-8").read()
assert "cs-ph-w" not in s
js = r"""// 写真が2枚以上のカードに、ドット（いま何枚目か）と左右の矢印（横にスワイプできる合図）を付ける。写真は全体のまま、切らない。
(function(){
  function dec(s){
    if (s.dataset.cd || s.children.length < 2) return;
    s.dataset.cd = 1;
    var w = document.createElement("div"), d = document.createElement("div"), n = s.children.length, i;
    w.className = "cs-ph-w"; s.parentNode.insertBefore(w, s); w.appendChild(s);
    d.className = "cs-ph-d"; d.setAttribute("aria-hidden", "true");
    for (i = 0; i < n; i++) d.appendChild(document.createElement("i"));
    function b(c, l, t){ var e = document.createElement("button"); e.type = "button"; e.className = "cs-ph-a " + c; e.setAttribute("aria-label", l); e.textContent = t;
      e.addEventListener("click", function(){ s.scrollBy({left: (c === "r" ? 1 : -1) * s.clientWidth, behavior: "smooth"}); }); return e; }
    w.appendChild(b("l", "前の写真", "‹")); w.appendChild(b("r", "次の写真", "›")); w.appendChild(d);
    function u(){ var k = Math.round(s.scrollLeft / s.clientWidth), j; for (j = 0; j < n; j++) d.children[j].className = j === k ? "on" : "";
      w.className = "cs-ph-w" + (k <= 0 ? " f" : "") + (k >= n - 1 ? " e" : ""); }
    s.addEventListener("scroll", u, {passive: true}); u();
  }
  function all(){ [].forEach.call(document.querySelectorAll(".cs-ph-s"), dec); }
  all();
  try { new MutationObserver(all).observe(document.documentElement, {childList: true, subtree: true}); } catch (x) {}
})();
"""
open(p, "w", encoding="utf-8").write(js + s)

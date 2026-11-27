(function(){
  'use strict';
  var form=document.getElementById('pd-filter');
  if(!form)return;
  var pref=document.getElementById('pd-pref'), animal=document.getElementById('pd-animal');
  var price=document.getElementById('pd-price'),eta=document.getElementById('pd-eta');
  var status=document.getElementById('pd-result'),empty=document.getElementById('pd-empty');
  var cards=Array.from(document.querySelectorAll('[data-pd]'));
  var qs=new URLSearchParams(location.search);
  var p=qs.get('pref'),a=qs.get('animal');
  if(Array.from(pref.options).some(function(o){return o.value===p;}))pref.value=p;
  if(Array.from(animal.options).some(function(o){return o.value===a;}))animal.value=a;
  function render(){
    var n=0;
    cards.forEach(function(card){
      var areas=card.dataset.area.split('|'), flags=card.dataset.pdFlags.split(' ');
      var ok=(!pref.value||areas.includes(pref.value)||areas.includes('全国')) &&
        (!animal.value||flags.includes(animal.value)) && (!price.checked||flags.includes('p')) &&
        (!eta.checked||flags.includes('eta'));
      card.hidden=!ok;if(ok)n++;
    });
    status.textContent=n+'件の候補';
    empty.hidden=n!==0;
  }
  form.addEventListener('change',render);
  form.addEventListener('submit',function(e){e.preventDefault();render();});
  render();
})();

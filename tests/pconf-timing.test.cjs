const fs=require('node:fs'),vm=require('node:vm'),a=require('node:assert/strict');
const ctx=vm.createContext({});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const wait=ctx.fareWaitTiered_, night=ctx.fareNightExact_;
const charge=(trigger,clock='component')=>({trigger,clock});
const only=(k,trigger,clock)=>({pickup:false,ride:false,wait:false,return:false,[k]:charge(trigger,clock)});
const rule=(components,round)=>({from:21*60,to:6*60,basisPoints:2000,components,round});
const t=(start,end)=>({start,end});
const same=(s,e)=>t('2026-11-27T'+s,'2026-11-27T'+e);

for (const [v,expected] of [['20:59',0],['21:00',60],['05:59',60],['06:00',0]]) {
  a.equal(night(rule(only('wait','start')),{wait:[300]},{wait:[same(v,v)]}),expected);
}
const overnight=t('2026-11-27T20:50','2026-11-28T06:10'), cross=same('20:50','21:20');
a.equal(night(rule(only('wait','start')),{wait:[300]},{wait:[cross]}),0);
a.equal(night(rule(only('wait','overlap')),{wait:[300]},{wait:[cross]}),60);
a.equal(night(rule(only('wait','prorate')),{wait:[300]},{wait:[cross]}),40);
a.equal(night(rule(only('wait','prorate'), 'floor_total'),{wait:[300]},{wait:[overnight]}),57);
a.equal(night(rule(only('wait','prorate')),{wait:[300]},{wait:[overnight]}),null); // unknown monetary rounding
a.equal(night(rule(only('wait','overlap','ride')),{wait:[300]},{wait:[cross],ride:[same('19:00','20:00')]}),0);
a.equal(night(rule(only('wait','prorate','ride')),{wait:[300]},{ride:[cross]}),null);
a.equal(night(rule(only('wait','overlap')),{wait:[300]},{}),null);
a.equal(night(rule({pickup:false,ride:false,wait:charge('overlap')}),{wait:[300]},{wait:[cross]}),null); // return unknown
a.equal(night(rule(only('wait','overlap')),{wait:[300]},{wait:[same('20:50','21:00')]}),0);
a.equal(night(rule(only('wait','overlap')),{wait:[300]},{wait:[same('06:00','06:10')]}),0);
a.equal(night(rule(only('wait','start'), 'ceil_total'),{wait:[1,1]},{wait:[same('21:00','21:00'),same('21:10','21:10')]}),1);
a.equal(night(rule(only('wait','start'), 'ceil_each'),{wait:[1,1]},{wait:[same('21:00','21:00'),same('21:10','21:10')]}),2);

// Public COCO Sara schedule, using only full units to avoid assuming its unpublished partial-increment rule.
// https://cocosara-pet.studio.site/service
const mk=(until,unit,yen,mode='ceil')=>({until,unit,yen,mode});
const sara={free:0,tiers:[mk(30,10,110),mk(60,15,330),mk(90,15,440),mk(null,15,550)]};
for(const [time,price] of [[30,330],[60,990],[90,1870],[120,2970]]) a.equal(wait(sara,time),price);

// Synthetic mixed thresholds: tier 4 uses its own unit, tier 5 is explicitly opted into instead of capped by absence.
const m={free:10,tiers:[mk(20,10,120),mk(30,10,220,'floor'),mk(45,15,330),mk(60,5,77),mk(null,20,12)]};
for(const [min,y] of [[9,0],[10,0],[11,120],[19,120],[20,120],[21,120],[30,340],[31,670],[45,670],[46,747],[50,747],[51,824],[60,901],[61,913]]) a.equal(wait(m,min),y);
a.equal(wait({...m,cap:750},60),750);
a.equal(wait({...m,cap:0},60),0);
a.equal(wait({...m,free:null},60),null);
a.equal(wait({...m,tiers:m.tiers.slice(0,4)},61),null);
a.equal(wait({free:0,tiers:[mk(null,10,0)]},40),0);
a.equal(wait({free:0,tiers:[mk(null,3,10,'exact')]},1),null);
a.equal(wait({free:0,tiers:[mk(null,3,10,'exact')],final:'floor'},1),3);
a.equal(wait({free:0,tiers:[mk(null,3,10,'exact')],final:'ceil'},1),4);
a.equal(wait({free:0,tiers:[mk(10,null,500,'flat'),mk(null,5,60)]},15),560);

// Strict timing can only be passed in from private server-side evidence checks.
const c=ctx.pconfFarePilot_('Dcb3b5a2'), f=ctx.pconfFareFixture_(c,10000,5000);
const draft={strategy:'one',waitMinutes:10,wait:{free:0,tiers:[mk(null,10,300)]},
  night:rule(only('wait','overlap')),schedule:{ride:[same('20:40','21:20')],wait:[same('20:55','21:05')]}};
const matching={...f.input,datetime:'2026-11-27T20:40'};
const good=ctx.displayPrice_(c,matching,f.lookup,draft);
a.equal(good.local.wait,300); a.equal(good.local.nightExtra,60); a.equal(good.local.amount,4560);
a.equal(ctx.displayPrice_(c,f.input,f.lookup).local.amount,4200); // same estimator, untouched legacy user-facing quote
a.equal(ctx.displayPrice_(c,matching,f.lookup,{...draft,schedule:{}}),null);
a.equal(ctx.displayPrice_(c,f.input,f.lookup,draft),null); // itinerary start inconsistent
a.equal(ctx.displayPrice_(c,matching,f.lookup,{...draft,schedule:{...draft.schedule,wait:[same('21:30','21:40')]}}),null);
a.equal(ctx.displayPrice_(c,matching,f.lookup,{...draft,waitMinutes:11}),null);
a.equal(ctx.displayPrice_(c,{...f.input, verifiedTiming:JSON.stringify(draft)},f.lookup).local.amount,4200);
const f2=ctx.pconfFareFixture_(c,10000,5000,'23:00');
const guarded=ctx.displayPrice_(c,f2.input,f2.lookup);
a.equal(guarded.local.amount,4200); a.equal(guarded.incompleteFees,true); a.match(guarded.text,/〜$/);
const before=ctx.pconfFareFixture_(c,1000,5000,'20:59');
a.equal(ctx.displayPrice_(c,before.input,before.lookup).incompleteFees,true);
const co=ctx.DISPLAY_COMPANIES.find(v=>v.id==='De5faaf3'), cf=ctx.pconfFareFixture_(co,10000,5000,'23:00');
a.equal(ctx.displayPrice_(co,cf.input,cf.lookup).local.nightExtra,3300); // different published legacy operator unchanged
const pub=ctx.pconfTimingDraft_({pf_w_1_unit:'10',pf_w_1_yen:'300',pf_n_return_trigger:'not_charged'});
a.equal(ctx.pconfFareDraft_(c,pub.answers),null);
a.equal(pub.wait,null); a.equal(pub.night,null); a.equal(pub.review,'timing_terms_incomplete');
const payload={pf_w_free:'0',pf_w_cap_mode:'none',pf_n_boundary:'from_in_to_out',
  pf_n_pickup_trigger:'start',pf_n_pickup_clock:'component',pf_n_ride_trigger:'overlap',
  pf_n_wait_trigger:'prorate',pf_n_wait_clock:'component',pf_n_return_trigger:'not_charged'};
sara.tiers.concat([mk(null,1,0)]).forEach((tier,i)=>{
  // Replace stage 4 with a finite end and test parser + review storage retaining stage 5.
  const end=i===3 ? 120 : tier.until;
  Object.assign(payload,{['pf_w_'+(i+1)+'_end']:end==null?'open':'until',['pf_w_'+(i+1)+'_until']:end==null?'':String(end),
    ['pf_w_'+(i+1)+'_mode']:tier.mode,['pf_w_'+(i+1)+'_unit']:String(tier.unit),['pf_w_'+(i+1)+'_yen']:String(tier.yen)});
});
const parsed=ctx.pconfTimingDraft_(payload);
a.equal(parsed.wait.tiers.length,5); a.equal(parsed.night.components.return,false);
a.equal(parsed.answers.pf_w_5_yen,'0'); a.equal(parsed.review,'independent_cases_needed');
a.equal(ctx.pconfFareDraft_(c,payload).check.ready,false);
console.log('PASS: private timing form, strict intervals and components, multi-tier waiting, known boundary totals, legacy parity');

/* JARVIS 9-scene cartoon animation panel. Read-only: never changes trade decisions or places orders. */
(function(root){
"use strict";
const PANEL_ID="jarvis-cartoon-panel", REFRESH_MS=2000;
const esc=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const obj=v=>v&&typeof v==="object"&&!Array.isArray(v)?v:{};
const arr=v=>Array.isArray(v)?v:[];
const value=(...xs)=>xs.find(x=>x!==undefined&&x!==null&&x!=="");
const statusOf=s=>String(value(s.decision_status,obj(s.decision).status,"WAIT")).toUpperCase().replace(/\s+/g,"_");
function hasEntryConfirmation(s){
 const one=obj(s.one_minute_analysis), mtf=obj(s.multi_timeframe);
 const candidates=[s.entry_confirmed,s.one_minute_confirmed,one.confirmed,one.entry_confirmed,one.status,one.signal,s.one_minute_direction,mtf.entry_confirmation];
 return candidates.some(v=>v===true||/ENTRY_CONFIRMED|CONFIRMED|BULLISH_BREAKOUT|BEARISH_BREAKDOWN|ENTRY_READY/i.test(String(v||"")));
}
function closedTrades(s){return arr(s.trade_history||s.trades||s.history).filter(t=>t&&(/CLOSED|TARGET|STOP_LOSS|SL_HIT|TARGET_HIT|WIN|LOSS/i.test(String(value(t.status,t.result,t.exit_reason,"")))));}
function sceneFor(s){
 const d=statusOf(s), trade=obj(value(s.active_trade,s.activeTrade,{})), hist=closedTrades(s);
 const rec=/BUY_CALL|BUY_PUT|TRADE_CANDIDATE/.test(d);
 const tg=obj(value(s.telegram_status,s.telegram,{})), telegram=String(value(tg.status,tg.state,typeof s.telegram_status==="string"?s.telegram_status:null,"")).toUpperCase();
 if(/SENT|SUCCESS|DELIVERED|OK/.test(telegram)) return 9;
 if(hist.length) {const last=hist[hist.length-1],r=String(value(last.result,last.exit_reason,last.status,"")).toUpperCase();if(/TARGET|WIN/.test(r))return 7;if(/STOP|SL_HIT|LOSS/.test(r))return 7;return 8;}
 if(Object.keys(trade).length) return 6;
 if(hasEntryConfirmation(s)) return 5;
 if(rec) return 4;
 if(arr(s.option_chain||s.options).length) return 3;
 if(Object.keys(obj(s.multi_timeframe)).length) return 2;
 return 1;
}
function sceneData(s){
 const d=statusOf(s),trade=obj(value(s.active_trade,s.activeTrade,{})),hist=closedTrades(s),last=hist[hist.length-1]||{};
 const symbol=value(trade.symbol,trade.tradingsymbol,s.symbol,last.symbol,last.tradingsymbol);
 const entry=value(trade.entry_price,trade.entry,last.entry_price,last.entry);
 const sl=value(trade.option_sl,trade.sl,last.option_sl,last.sl);
 const target=value(trade.option_target,trade.target,last.option_target,last.target);
 const score=value(s.entry_score,obj(s.decision).score,trade.score,trade.entry_score);
 const action=/BUY_CALL/.test(d)?"BUY CALL":/BUY_PUT/.test(d)?"BUY PUT":d.replace(/_/g," ");
 return {d,trade,hist,last,symbol,entry,sl,target,score,action,closed:hist.length>0,active:Object.keys(trade).length>0,confirmed:hasEntryConfirmation(s)};
}
const scenes=[
 {n:1,title:"Market Scan",desc:"Checking available live market snapshot",icon:"🔎"},
 {n:2,title:"15m → 5m → 1m Analysis",desc:"Reading published timeframe states",icon:"📊"},
 {n:3,title:"Strike Selection",desc:"Using available option-chain rows",icon:"🎯"},
 {n:4,title:"Trade Recommendation",desc:"Shows only a published BUY CALL / BUY PUT recommendation",icon:"💡"},
 {n:5,title:"Entry Confirmation",desc:"Reflects the existing 1-minute confirmation state",icon:"✅"},
 {n:6,title:"Trade in Progress",desc:"Reflects the published active trade",icon:"📈"},
 {n:7,title:"Exit Event",desc:"Target / stop-loss outcome only when recorded",icon:"🏁"},
 {n:8,title:"Result Summary",desc:"Uses recorded closed-trade details",icon:"🧾"},
 {n:9,title:"Telegram Alert",desc:"Shows success only when backend reports it",icon:"📲"}
];
const css=`
#${PANEL_ID}{margin:18px 0;color:var(--text,#263238);font-family:inherit}
#${PANEL_ID} .jc-shell{background:linear-gradient(135deg,#101c31,#172943 55%,#102a3a);color:#eef7ff;border:1px solid #2f536c;border-radius:16px;overflow:hidden;box-shadow:0 12px 30px rgba(20,40,65,.16)}
#${PANEL_ID} .jc-head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 18px;border-bottom:1px solid rgba(150,210,255,.2);flex-wrap:wrap}
#${PANEL_ID} .jc-title{font-weight:900;font-size:15px;letter-spacing:.04em}#${PANEL_ID} .jc-sub{color:#9ebbd2;font-size:12px;margin-top:4px}
#${PANEL_ID} .jc-state{font-size:11px;font-weight:800;border-radius:99px;padding:6px 10px;background:rgba(76,211,165,.14);color:#77f0c4;border:1px solid rgba(119,240,196,.35)}
#${PANEL_ID} .jc-hero{display:grid;grid-template-columns:170px minmax(0,1fr);gap:18px;padding:18px;align-items:center}
#${PANEL_ID} .jc-character{min-height:155px;display:grid;place-items:center;position:relative;border-radius:14px;background:radial-gradient(circle,rgba(35,200,255,.2),rgba(12,26,44,.05) 68%);overflow:hidden}
#${PANEL_ID} .jc-bot{font-size:74px;filter:drop-shadow(0 0 15px rgba(74,210,255,.55));animation:jc-float 2.4s ease-in-out infinite}
#${PANEL_ID} .jc-orbit{position:absolute;width:125px;height:125px;border:1px solid rgba(83,213,255,.5);border-radius:50%;animation:jc-spin 7s linear infinite}
#${PANEL_ID} .jc-orbit:before,#${PANEL_ID} .jc-orbit:after{content:"";position:absolute;width:8px;height:8px;border-radius:50%;background:#54e4ff;box-shadow:0 0 12px #54e4ff}
#${PANEL_ID} .jc-orbit:before{top:14px;left:20px}#${PANEL_ID} .jc-orbit:after{right:9px;bottom:20px}
#${PANEL_ID} .jc-speech{font-size:18px;font-weight:900;line-height:1.25;margin-bottom:8px}
#${PANEL_ID} .jc-detail{color:#bad0e2;font-size:12px;line-height:1.6}
#${PANEL_ID} .jc-facts{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
#${PANEL_ID} .jc-fact{border:1px solid rgba(145,193,224,.25);background:rgba(6,17,32,.45);border-radius:8px;padding:8px 10px;min-width:90px}
#${PANEL_ID} .jc-fact span{display:block;font-size:10px;color:#9ebbd2;text-transform:uppercase;letter-spacing:.07em}
#${PANEL_ID} .jc-fact b{display:block;margin-top:4px;font-size:13px;overflow-wrap:anywhere}
#${PANEL_ID} .jc-scenes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:0 18px 18px}
#${PANEL_ID} .jc-scene{min-width:0;border:1px solid rgba(145,193,224,.2);border-radius:11px;background:rgba(4,15,29,.46);padding:12px;transition:transform .25s,border-color .25s,background .25s}
#${PANEL_ID} .jc-scene.is-active{border-color:#5be1ff;background:rgba(17,105,143,.24);box-shadow:0 0 18px rgba(49,205,255,.18);transform:translateY(-2px);animation:jc-arrive .65s ease-out}
#${PANEL_ID} .jc-scene.is-done .jc-num{background:#1c8d68;color:white}
#${PANEL_ID} .jc-scene-top{display:flex;align-items:center;gap:8px;margin-bottom:8px}
#${PANEL_ID} .jc-num{width:25px;height:25px;display:grid;place-items:center;flex:0 0 25px;border-radius:8px;background:#263e57;color:#b8eaff;font-size:11px;font-weight:900}
#${PANEL_ID} .jc-icon{font-size:22px}#${PANEL_ID} .jc-scene h3{font-size:12px;margin:0 0 6px;color:#f2f8ff}
#${PANEL_ID} .jc-scene p{font-size:11px;color:#9ebbd2;line-height:1.45;margin:0;min-height:31px}
#${PANEL_ID} .jc-scene-status{font-size:10px;color:#65dfbd;font-weight:800;margin-top:9px;text-transform:uppercase;letter-spacing:.06em}
#${PANEL_ID} .jc-foot{padding:0 18px 15px;color:#8faec5;font-size:11px}
@keyframes jc-float{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-7px) rotate(2deg)}}
@keyframes jc-spin{to{transform:rotate(360deg)}}
@keyframes jc-arrive{0%{opacity:.45;transform:translateY(7px) scale(.98)}100%{opacity:1;transform:translateY(-2px) scale(1)}}
@media(max-width:760px){#${PANEL_ID} .jc-hero{grid-template-columns:100px minmax(0,1fr);gap:10px;padding:12px}#${PANEL_ID} .jc-bot{font-size:54px}#${PANEL_ID} .jc-orbit{width:90px;height:90px}#${PANEL_ID} .jc-scenes{grid-template-columns:repeat(2,minmax(0,1fr));padding:0 12px 12px}#${PANEL_ID} .jc-head{padding:12px}}
@media(prefers-reduced-motion:reduce){#${PANEL_ID} *{animation:none!important;transition:none!important}}
`;
function install(doc){
 if(!doc||doc.getElementById(PANEL_ID))return doc&&doc.getElementById(PANEL_ID);
 if(!doc.getElementById("jarvis-cartoon-style")){const st=doc.createElement("style");st.id="jarvis-cartoon-style";st.textContent=css;doc.head.appendChild(st);}
 const panel=doc.createElement("section");panel.id=PANEL_ID;panel.setAttribute("aria-label","JARVIS nine-scene cartoon animation");
 panel.innerHTML='<div class="jc-shell"><div class="jc-head"><div><div class="jc-title">🤖 JARVIS CARTOON ANIMATION</div><div class="jc-sub">Nine live-state scenes · read-only visual layer</div></div><span class="jc-state" id="jc-state">WAITING FOR LIVE DATA</span></div><div class="jc-hero"><div class="jc-character" aria-hidden="true"><div class="jc-orbit"></div><div class="jc-bot">🤖</div></div><div><div class="jc-speech" id="jc-speech">JARVIS is standing by.</div><div class="jc-detail" id="jc-detail">Live market state will determine the active scene. No example prices are pre-filled.</div><div class="jc-facts" id="jc-facts"></div></div></div><div class="jc-scenes" id="jc-scenes"></div><div class="jc-foot">Visual animation only. Trade decisions remain with the existing engine; orders are never placed by this panel.</div></div>';
 const main=doc.querySelector(".main"),phases=doc.getElementById("jarvis-phases-panel"),top=main&&main.querySelector(".topbar");
 if(phases)phases.insertAdjacentElement("afterend",panel);else if(top)top.insertAdjacentElement("afterend",panel);else if(main)main.prepend(panel);else doc.body.appendChild(panel);
 panel.querySelector("#jc-scenes").innerHTML=scenes.map(x=>'<article class="jc-scene" data-scene="'+x.n+'"><div class="jc-scene-top"><span class="jc-num">'+x.n+'</span><span class="jc-icon">'+x.icon+'</span></div><h3>'+esc(x.title)+'</h3><p>'+esc(x.desc)+'</p><div class="jc-scene-status" data-scene-status="'+x.n+'">Waiting</div></article>').join("");
 return panel;
}
function render(doc,s){
 const panel=doc&&doc.getElementById(PANEL_ID);if(!panel)return;
 const active=sceneFor(s),d=sceneData(s),status=panel.querySelector("#jc-state"),speech=panel.querySelector("#jc-speech"),detail=panel.querySelector("#jc-detail"),facts=panel.querySelector("#jc-facts");
 if(status)status.textContent="SCENE "+active+" / 9 · "+scenes[active-1].title.toUpperCase();
 if(speech)speech.textContent=active===4?"New trade recommendation detected":active===5?"1-minute entry confirmation detected":active===6?"Monitoring the published active trade":active===7?"Recorded trade exit detected":active===8?"Reviewing recorded trade result":active===9?"Telegram delivery status reported":active===3?"Checking live option-chain selection":active===2?"Reading multi-timeframe analysis":"Scanning available market data";
 if(detail)detail.textContent=active===4?"The existing decision engine published "+d.action+". Verify the live values below before any manual order.":active===5?"The existing 1-minute state indicates confirmation. This panel does not create or override confirmation.":active===6?"Active trade details are sourced from live_state.json. No order action is available here.":active>=7?"Closed-trade / notification details are displayed only when present in the live snapshot.":"Current scene follows available live data. Missing fields remain unavailable; no sample trade is inserted.";
 const factsList=[["Decision",d.action],["Symbol",d.symbol],["Entry",d.entry],["Stop Loss",d.sl],["Target",d.target],["Score",d.score]];
 if(facts)facts.innerHTML=factsList.map(([k,v])=>'<div class="jc-fact"><span>'+esc(k)+'</span><b>'+esc(v==null||v===""?"—":(typeof v==="number"?v.toLocaleString("en-IN",{maximumFractionDigits:2}):v))+'</b></div>').join("");
 panel.querySelectorAll(".jc-scene").forEach(el=>{const n=Number(el.getAttribute("data-scene"));el.classList.toggle("is-active",n===active);el.classList.toggle("is-done",n<active);const label=el.querySelector("[data-scene-status]");if(label)label.textContent=n===active?"ACTIVE SCENE":n<active?"STAGE PASSED":n===4&&/BUY_CALL|BUY_PUT|TRADE_CANDIDATE/.test(d.d)?"RECOMMENDATION AVAILABLE":n===5&&d.confirmed?"ENTRY CONFIRMED":n===6&&d.active?"ACTIVE TRADE":n===7&&d.closed?"EXIT RECORDED":n===8&&d.closed?"RESULT RECORDED":n===9&&/SENT|SUCCESS|DELIVERED|OK/.test(String(value(obj(s.telegram_status).status,s.telegram_status,""))).toUpperCase()?"DELIVERY REPORTED":"WAITING";});
}
async function refresh(root){
 try{const r=await root.fetch("live_state.json?ts="+Date.now(),{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);const data=await r.json();render(root.document,data);}
 catch(e){const status=root.document&&root.document.querySelector("#jc-state");if(status)status.textContent="LIVE DATA UNAVAILABLE";}
}
function start(root){install(root.document);refresh(root);root.setInterval(()=>refresh(root),REFRESH_MS);}
const api={sceneFor,hasEntryConfirmation,closedTrades,sceneData,scenes};
if(typeof module!=="undefined"&&module.exports)module.exports=api;
if(root&&root.document){if(root.document.readyState==="loading")root.document.addEventListener("DOMContentLoaded",()=>start(root),{once:true});else start(root);}
})(typeof window!=="undefined"?window:(typeof globalThis!=="undefined"?globalThis:this));

/* JARVIS nine-scene animation layer.
 * Read-only UI: consumes existing dashboard snapshots; never creates trades or sends orders.
 */
(() => {
  "use strict";
  if (window.__jarvisNineScenesLoaded) return;
  window.__jarvisNineScenesLoaded = true;

  const $ = (id) => document.getElementById(id);
  const safe = (v) => v === null || v === undefined || v === "" ? "—" : String(v);
  const num = (v) => {
    if (v === null || v === undefined || v === "" || !Number.isFinite(Number(v))) return null;
    return Number(v);
  };
  const first = (...values) => values.find(v => v !== null && v !== undefined && v !== "");
  const text = (v) => String(v ?? "").toUpperCase().replace(/_/g, " ");
  const money = (v) => { const n = num(v); return n === null ? "—" : "₹" + n.toFixed(2); };

  function installStyle() {
    if ($("jarvis-scenes-style")) return;
    const s = document.createElement("style");
    s.id = "jarvis-scenes-style";
    s.textContent = `
      #jarvis-scenes { margin:18px 0 22px; padding:18px; border-radius:16px; border:1px solid var(--border,#d8d0c4); background:var(--panel,#fffdf8); color:var(--text,#263238); box-shadow:var(--shadow,0 12px 35px rgba(55,65,81,.12)); overflow:hidden; }
      #jarvis-scenes * { box-sizing:border-box; }
      #jarvis-scenes .js-head { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; }
      #jarvis-scenes .js-title { font-size:17px; font-weight:850; letter-spacing:.3px; }
      #jarvis-scenes .js-sub { font-size:12px; color:var(--muted,#667085); margin-top:5px; }
      #jarvis-scenes .js-live { display:inline-flex; align-items:center; gap:7px; border:1px solid var(--border,#d8d0c4); border-radius:99px; padding:7px 10px; font-size:10px; font-weight:800; letter-spacing:.6px; }
      #jarvis-scenes .js-dot { width:7px; height:7px; border-radius:50%; background:#b7791f; }
      #jarvis-scenes .js-live.live .js-dot { background:#16803a; box-shadow:0 0 10px #16803a88; }
      #jarvis-scenes .js-hero { display:grid; grid-template-columns:150px minmax(0,1fr); gap:16px; align-items:center; margin:16px 0; padding:15px; border:1px solid var(--border,#d8d0c4); border-radius:13px; background:var(--panel2,#f7f1e6); }
      #jarvis-scenes .js-avatar-wrap { position:relative; width:124px; height:124px; margin:auto; display:grid; place-items:center; }
      #jarvis-scenes .js-ring { position:absolute; inset:5px; border:2px solid #5b7c9955; border-top-color:#16803a; border-right-color:#14b8a6; border-radius:50%; }
      #jarvis-scenes .js-ring.scanning { animation:jarvis-spin 2.8s linear infinite; }
      #jarvis-scenes .js-avatar { width:88px; height:88px; display:grid; place-items:center; font-size:55px; border-radius:50%; background:#dbeafe; border:2px solid #5b7c99; transform:rotateY(0deg); transition:transform .65s ease; box-shadow:0 5px 20px #5b7c9922; }
      #jarvis-scenes .js-avatar.scanning { transform:rotateY(180deg); }
      #jarvis-scenes .js-hero-title { font-size:15px; font-weight:850; }
      #jarvis-scenes .js-hero-status { margin-top:8px; font-size:12px; font-weight:800; }
      #jarvis-scenes .js-hero-detail { color:var(--muted,#667085); font-size:12px; margin-top:6px; line-height:1.5; }
      #jarvis-scenes .js-progress { height:4px; background:var(--border,#d8d0c4); border-radius:10px; overflow:hidden; margin-top:12px; }
      #jarvis-scenes .js-progress span { display:block; height:100%; width:0; background:linear-gradient(90deg,#5b7c99,#14b8a6,#16803a); transition:width .5s ease; }
      #jarvis-scenes .js-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
      #jarvis-scenes .js-scene { min-width:0; border:1px solid var(--border,#d8d0c4); border-radius:11px; padding:12px; background:var(--panel2,#f7f1e6); transition:border-color .25s, transform .25s, box-shadow .25s; }
      #jarvis-scenes .js-scene.active { border-color:#5b7c99; box-shadow:0 0 0 1px #5b7c9922; transform:translateY(-1px); }
      #jarvis-scenes .js-scene.ok { border-color:#16803a77; }
      #jarvis-scenes .js-scene.warn { border-color:#b7791f66; }
      #jarvis-scenes .js-scene-head { display:flex; align-items:flex-start; gap:9px; }
      #jarvis-scenes .js-num { flex:0 0 25px; height:25px; border-radius:8px; display:grid; place-items:center; font-size:11px; font-weight:900; background:var(--panel,#fffdf8); border:1px solid var(--border,#d8d0c4); }
      #jarvis-scenes .js-scene-title { font-size:12px; line-height:1.35; font-weight:850; }
      #jarvis-scenes .js-badge { display:inline-block; margin-top:8px; padding:4px 7px; border-radius:99px; font-size:9px; font-weight:900; letter-spacing:.5px; border:1px solid var(--border,#d8d0c4); }
      #jarvis-scenes .js-badge.ok { color:#16803a; } #jarvis-scenes .js-badge.warn { color:#b7791f; } #jarvis-scenes .js-badge.bad { color:#c0392b; }
      #jarvis-scenes .js-detail { font-size:11px; line-height:1.5; color:var(--muted,#667085); margin-top:8px; overflow-wrap:anywhere; }
      #jarvis-scenes .js-val { color:var(--text,#263238); font-weight:800; }
      #jarvis-scenes .js-scene.target { animation:jarvis-target-glow 1.5s ease-in-out 2; }
      #jarvis-scenes .js-scene.target .js-num { background:#dcfce7; color:#166534; }
      #jarvis-scenes .js-scene.stop .js-num { background:#fee2e2; color:#991b1b; }
      @keyframes jarvis-spin { to { transform:rotate(360deg); } }
      @keyframes jarvis-target-glow { 50% { box-shadow:0 0 18px #16a34a33; } }
      @media(max-width:800px) { #jarvis-scenes .js-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
      @media(max-width:560px) { #jarvis-scenes { padding:12px; } #jarvis-scenes .js-hero { grid-template-columns:1fr; text-align:center; } #jarvis-scenes .js-grid { grid-template-columns:1fr; } }
      @media(prefers-reduced-motion:reduce) { #jarvis-scenes *, #jarvis-scenes *::before, #jarvis-scenes *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; } }
    `;
    document.head.appendChild(s);
  }

  const sceneDefs = [
    ["Market Scan Started", "Scan", "Waiting for live market data"],
    ["Multi-Timeframe Analysis", "Analysis", "5-minute system; other timeframes are not assumed"],
    ["Strike Selection", "Strike", "Waiting for actual ATM and option contract data"],
    ["Trade Recommendation", "Recommendation", "Only the engine's real recommendation is shown"],
    ["Entry Confirmation", "Entry", "No confirmation means WAIT"],
    ["Trade in Progress", "Active trade", "No active trade is inferred"],
    ["Target Hit / Stop Loss", "Exit event", "Only confirmed exit events are shown"],
    ["Result & Summary", "Trade history", "Only recorded completed trades are shown"],
    ["Telegram Alert", "Telegram", "Only a recorded send status is shown"]
  ];

  function createPanel() {
    if ($("jarvis-scenes")) return;
    const panel = document.createElement("section");
    panel.id = "jarvis-scenes";
    panel.setAttribute("aria-live", "polite");
    panel.innerHTML = `
      <div class="js-head">
        <div><div class="js-title">JARVIS · Nine Scene Animations</div><div class="js-sub">Live read-only status · no automatic order placement</div></div>
        <span id="js-live" class="js-live"><i class="js-dot"></i><span id="js-live-label">WAITING FOR DATA</span></span>
      </div>
      <div class="js-hero">
        <div class="js-avatar-wrap"><div id="js-ring" class="js-ring"></div><div id="js-avatar" class="js-avatar" aria-label="Cartoon assistant">🤖</div></div>
        <div><div class="js-hero-title">MARKET SCAN STARTED</div><div id="js-hero-status" class="js-hero-status">Waiting for live market data…</div><div id="js-hero-detail" class="js-hero-detail">Scanner animation indicates UI activity only; it does not imply a trade signal.</div><div class="js-progress"><span id="js-progress-fill"></span></div></div>
      </div>
      <div class="js-grid">${sceneDefs.map((s,i)=>`<article id="js-scene-${i+1}" class="js-scene"><div class="js-scene-head"><span class="js-num">${String(i+1).padStart(2,"0")}</span><div class="js-scene-title">${s[0]}</div></div><span id="js-badge-${i+1}" class="js-badge warn">WAIT</span><div id="js-detail-${i+1}" class="js-detail">${s[2]}</div></article>`).join("")}</div>
    `;
    const main = document.querySelector("main.main");
    const sections = Array.from(document.querySelectorAll("main.main > .section"));
    const mtf = sections.find(el => (el.querySelector(".section-title h2")?.textContent || "").includes("5-Minute Analysis"));
    if (mtf) mtf.insertAdjacentElement("beforebegin", panel);
    else if (main) main.prepend(panel);
    else document.body.prepend(panel);
  }

  function scene(n, status, detail, tone="warn", active=false) {
    const card=$("js-scene-"+n), badge=$("js-badge-"+n), body=$("js-detail-"+n);
    if (!card || !badge || !body) return;
    card.classList.toggle("active", !!active);
    card.classList.toggle("ok", tone==="ok");
    card.classList.toggle("warn", tone==="warn");
    card.classList.toggle("target", tone==="target");
    card.classList.toggle("stop", tone==="bad");
    badge.className="js-badge "+(tone==="ok"||tone==="target"?"ok":tone==="bad"?"bad":"warn");
    badge.textContent=status;
    body.textContent=detail;
  }

  async function readJson(path) {
    try {
      const r=await fetch(path+"?ts="+Date.now(), {cache:"no-store"});
      if (!r.ok) return null;
      return await r.json();
    } catch (_) { return null; }
  }

  function render(live, stocks, review) {
    const hasLive = !!live && (num(first(live.spot,live.sensex_price,live.live_sensex?.last_price)) !== null);
    $("js-live")?.classList.toggle("live",hasLive);
    $("js-live-label").textContent=hasLive?"LIVE DATA CONNECTED":"WAITING FOR LIVE DATA";
    $("js-ring")?.classList.toggle("scanning",hasLive);
    $("js-avatar")?.classList.toggle("scanning",hasLive);
    $("js-hero-status").textContent=hasLive?"LIVE MARKET DATA RECEIVED":"Waiting for live market data…";
    $("js-hero-detail").textContent=hasLive
      ? "SENSEX "+money(first(live.spot,live.sensex_price,live.live_sensex?.last_price))+" · Snapshot "+safe(live.timestamp)
      : "Scanner is waiting for a real market price. No sample or placeholder prices are used.";
    $("js-progress-fill").style.width=hasLive?"100%":"8%";

    scene(1,hasLive?"LIVE DATA":"WAIT",hasLive?"SENSEX "+money(first(live.spot,live.sensex_price,live.live_sensex?.last_price))+" · "+safe(live.timestamp):"No live spot price in live_state.json",hasLive?"ok":"warn",true);

    const mtf=live?.multi_timeframe||review?.market_intelligence?.multi_timeframe||{};
    const d5=first(mtf.direction_5m,mtf["5m"],mtf.five_minute,live?.market_analysis?.direction,live?.market_analysis?.trend);
    const st5=first(mtf.status,mtf.confirmation_status,live?.decision_status);
    const d15=first(mtf.direction_15m,mtf["15m"],mtf.fifteen_minute);
    const d1=first(mtf.direction_1m,mtf["1m"],mtf.one_minute);
    const detailMtf="5M: "+safe(d5)+" · status: "+safe(st5)+" · 15M: "+safe(d15)+" · 1M: "+safe(d1);
    scene(2,d5?"SIGNAL FOUND":"WAIT",detailMtf,d5?"ok":"warn",false);

    const strike=first(live?.atm_strike,live?.option_data?.atm_strike,live?.live_option?.strike,live?.decision?.strike);
    const option=live?.live_option||live?.selected_option||{};
    const action=first(live?.decision?.action,live?.decision?.signal,live?.decision_status);
    scene(3,strike!==undefined?"STRIKE FOUND":"WAIT","Actual ATM strike: "+safe(strike)+" · contract: "+safe(first(option.symbol,option.tradingsymbol,option.instrument))+" · CE/PE: "+safe(first(live?.option_summary?.comparison,live?.ce_pe_comparison)),strike!==undefined?"ok":"warn",false);

    const dec=live?.decision||{};
    const side=text(first(dec.action,dec.signal,live?.decision_status,"WAIT"));
    const isTrade=["BUY CALL","BUY PUT","BUY_CALL","BUY_PUT"].includes(side);
    const entry=first(dec.entry,dec.entry_price,live?.entry,live?.recommendation?.entry);
    const sl=first(dec.option_sl,dec.stop_loss,dec.sl,live?.recommendation?.stop_loss);
    const target=first(dec.option_target,dec.target,live?.recommendation?.target);
    const score=first(dec.score,dec.entry_score,live?.entry_score);
    const recDetail="Signal: "+safe(action)+" · Entry: "+money(entry)+" · SL: "+money(sl)+" · Target: "+money(target)+" · Score: "+safe(score);
    scene(4,isTrade?"RECOMMENDATION":"WAIT",recDetail,isTrade?"ok":"warn",false);

    const entryStatus=text(first(live?.entry_confirmation?.status,dec.entry_confirmation,live?.entry_status));
    const confirmed=Boolean(live?.entry_confirmation?.confirmed===true || entryStatus==="ENTRY CONFIRMED" || entryStatus==="CONFIRMED");
    scene(5,confirmed?"ENTRY CONFIRMED":"WAIT",confirmed?"The engine reports entry confirmation. Manual order only.":"No verified entry confirmation in live snapshot; remain WAIT.",confirmed?"ok":"warn",false);

    const active=live?.active_trade;
    const activeExists=!!active && typeof active==="object" && Object.keys(active).length>0 && !["NONE","NO_TRADE","WAIT"].includes(text(active.status));
    const premium=first(live?.active_trade_ltp,active?.current_price,active?.last_price,active?.ltp);
    const pnl=first(active?.pnl,active?.pnl_points,live?.active_trade_pnl);
    scene(6,activeExists?"ACTIVE TRADE":"NO ACTIVE TRADE",activeExists?"Symbol: "+safe(first(active.symbol,active.tradingsymbol))+" · Entry: "+money(first(active.entry,active.entry_price))+" · Live premium: "+money(premium)+" · P&L: "+safe(pnl):"No active trade recorded. No P&L is invented.",activeExists?"ok":"warn",false);

    const history=Array.isArray(live?.trade_history)?live.trade_history:[];
    const last=history.length?history[history.length-1]:null;
    const exitReason=text(first(last?.exit_reason,last?.result,last?.reason));
    const targetHit=!!last && (exitReason==="TARGET"||text(last.result)==="WIN"&&text(last.exit_reason).includes("TARGET"));
    const slHit=!!last && ["STOP LOSS","STOP_LOSS"].includes(exitReason);
    scene(7,targetHit?"TARGET HIT":slHit?"STOP LOSS": "NO EXIT EVENT",last?"Last recorded exit: "+safe(first(last.exit_reason,last.result))+" · Exit: "+money(first(last.exit_price,last.exit)):"No confirmed exit in recorded trade history",targetHit?"target":slHit?"bad":"warn",false);

    const closed=history.length;
    const lastSummary=last?"Last: "+safe(first(last.symbol,last.tradingsymbol))+" · "+safe(first(last.result,last.status))+" · Entry "+money(first(last.entry,last.entry_price))+" → Exit "+money(first(last.exit_price,last.exit))+" · P&L "+safe(first(last.pnl_points,last.pnl)):"No completed trades recorded";
    scene(8,closed?closed+" RECORDED":"NO HISTORY",lastSummary,closed?"ok":"warn",false);

    const telegramText=String(first(live?.telegram_status,live?.telegram?.status,live?.last_telegram_status,review?.telegram_status,"")).toUpperCase();
    const telegramSent=telegramText.includes("SENT")||telegramText==="SUCCESS";
    const telegramFailed=telegramText.includes("ERROR")||telegramText.includes("FAILED");
    scene(9,telegramSent?"SENT":telegramFailed?"FAILED":"STATUS UNAVAILABLE",telegramText?"Recorded status: "+telegramText:"Snapshot does not publish a Telegram delivery status. This panel will not assume a message was sent.",telegramSent?"ok":telegramFailed?"bad":"warn",false);
  }

  async function refresh() {
    const [live,stocks,review]=await Promise.all([
      readJson("live_state.json"),readJson("live_sensex30.json"),readJson("agentic_review.json")
    ]);
    render(live,stocks,review);
  }
  function start(){installStyle();createPanel();refresh();window.setInterval(refresh,2000);}
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",start,{once:true});
  else start();
})();
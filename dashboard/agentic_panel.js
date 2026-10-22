/* JARVIS / Agentic AI read-only dashboard panel.
 * Reads the advisory snapshot published by AgenticAI.agent_orchestrator.
 * It never creates, changes, or submits trade decisions.
 */
(() => {
    "use strict";

    const STYLE_ID = "jarvis-agentic-panel-style";
    const PANEL_ID = "jarvis-agentic-panel";

    function installStyles() {
        if (document.getElementById(STYLE_ID)) return;
        const style = document.createElement("style");
        style.id = STYLE_ID;
        style.textContent = `
            #${PANEL_ID} { background: var(--panel, #fffdf8); border: 1px solid var(--border, #d8d0c4); border-radius: 12px; padding: 18px; margin: 20px 0; box-shadow: var(--shadow, 0 12px 35px rgba(55,65,81,.12)); }
            #${PANEL_ID} .jarvis-head { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
            #${PANEL_ID} .jarvis-brand { display:flex; align-items:center; gap:14px; min-width:0; }
            #${PANEL_ID} .jarvis-core { --core-accent:#38bdf8; position:relative; width:76px; height:76px; flex:0 0 76px; display:grid; place-items:center; border-radius:50%; isolation:isolate; }
            #${PANEL_ID} .jarvis-core[data-bias="bullish"] { --core-accent:#34d399; }
            #${PANEL_ID} .jarvis-core[data-bias="bearish"] { --core-accent:#fb7185; }
            #${PANEL_ID} .jarvis-core[data-bias="unknown"] { --core-accent:#38bdf8; }
            #${PANEL_ID} .jarvis-core-ring { position:absolute; inset:5px; border:1px solid color-mix(in srgb,var(--core-accent) 75%,transparent); border-radius:50%; box-shadow:0 0 10px color-mix(in srgb,var(--core-accent) 25%,transparent),inset 0 0 10px color-mix(in srgb,var(--core-accent) 18%,transparent); animation:jarvis-core-spin 9s linear infinite; }
            #${PANEL_ID} .jarvis-core-ring::before, #${PANEL_ID} .jarvis-core-ring::after { content:""; position:absolute; inset:8px -3px; border:1px dashed color-mix(in srgb,var(--core-accent) 70%,transparent); border-radius:50%; transform:rotate(55deg); }
            #${PANEL_ID} .jarvis-core-ring::after { inset:13px -1px; transform:rotate(-55deg); }
            #${PANEL_ID} .jarvis-core-orb { width:29px; height:29px; border-radius:50%; background:radial-gradient(circle at 32% 28%,#e0f2fe 0 6%,var(--core-accent) 28%,#0b1e35 76%); box-shadow:0 0 13px var(--core-accent),0 0 28px color-mix(in srgb,var(--core-accent) 45%,transparent); animation:jarvis-core-pulse 2.4s ease-in-out infinite; }
            #${PANEL_ID} .jarvis-core-caption { position:absolute; bottom:-3px; left:50%; transform:translateX(-50%); white-space:nowrap; font-size:8px; font-weight:800; letter-spacing:1.2px; color:var(--muted,#667085); }
            @keyframes jarvis-core-spin { to { transform:rotate(360deg); } }
            @keyframes jarvis-core-pulse { 0%,100% { transform:scale(.92); opacity:.86; } 50% { transform:scale(1.08); opacity:1; } }
            @media (prefers-reduced-motion:reduce) { #${PANEL_ID} .jarvis-core-ring, #${PANEL_ID} .jarvis-core-orb { animation:none; } }
            #${PANEL_ID} .jarvis-title { font-size:16px; font-weight:800; letter-spacing:.2px; }
            #${PANEL_ID} .jarvis-subtitle { color:var(--muted,#667085); font-size:12px; margin-top:4px; }
            #${PANEL_ID} .jarvis-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
            #${PANEL_ID} .jarvis-card { border:1px solid var(--border,#d8d0c4); background:var(--panel2,#f7f1e6); border-radius:10px; padding:13px; min-width:0; }
            #${PANEL_ID} .jarvis-label { font-size:11px; color:var(--muted,#667085); text-transform:uppercase; letter-spacing:.8px; margin-bottom:7px; }
            #${PANEL_ID} .jarvis-value { font-size:14px; font-weight:750; overflow-wrap:anywhere; }
            #${PANEL_ID} .jarvis-detail { color:var(--muted,#667085); font-size:12px; line-height:1.5; margin-top:6px; overflow-wrap:anywhere; }
            #${PANEL_ID} .jarvis-pill { display:inline-block; border:1px solid var(--border,#d8d0c4); border-radius:999px; padding:5px 9px; font-size:10px; font-weight:800; letter-spacing:.6px; }
            #${PANEL_ID} .jarvis-pill.ok { color:#16803a; }
            #${PANEL_ID} .jarvis-pill.warn { color:#b7791f; }
            #${PANEL_ID} .jarvis-pill.error { color:#c0392b; }
            #${PANEL_ID} .jarvis-lower { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }
            #${PANEL_ID} .jarvis-list { margin:6px 0 0; padding-left:18px; color:var(--text,#263238); font-size:12px; line-height:1.6; overflow-wrap:anywhere; }
            #${PANEL_ID} .jarvis-empty { color:var(--muted,#667085); font-size:12px; }
            @media (max-width:900px) { #${PANEL_ID} .jarvis-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
            @media (max-width:600px) { #${PANEL_ID} { padding:12px; } #${PANEL_ID} .jarvis-grid, #${PANEL_ID} .jarvis-lower { grid-template-columns:1fr; } }
        `;
        document.head.appendChild(style);
    }

    function createPanel() {
        if (document.getElementById(PANEL_ID)) return;
        const panel = document.createElement("section");
        panel.id = PANEL_ID;
        panel.className = "section";
        panel.setAttribute("aria-live", "polite");
        panel.innerHTML = `
            <div class="jarvis-head">
                <div class="jarvis-brand">
                    <div class="jarvis-core" id="jarvis-holographic-core" data-bias="unknown" role="img" aria-label="JARVIS holographic core, market bias unknown">
                        <span class="jarvis-core-ring" aria-hidden="true"></span>
                        <span class="jarvis-core-orb" aria-hidden="true"></span>
                        <span class="jarvis-core-caption" id="jarvis-core-caption">CORE · IDLE</span>
                    </div>
                    <div>
                        <div class="jarvis-title">JARVIS · Agentic AI Review</div>
                        <div class="jarvis-subtitle">Independent diagnostics · advisory only · never places broker orders</div>
                    </div>
                </div>
                <span id="jarvis-status" class="jarvis-pill warn">WAITING FOR REVIEW</span>
            </div>
            <div class="jarvis-grid">
                <div class="jarvis-card">
                    <div class="jarvis-label">Decision audit</div>
                    <div id="jarvis-decision" class="jarvis-value">Waiting for first review</div>
                    <div id="jarvis-score" class="jarvis-detail">Score: —</div>
                    <div id="jarvis-candidate" class="jarvis-detail">Candidate: —</div>
                </div>
                <div class="jarvis-card">
                    <div class="jarvis-label">Market intelligence</div>
                    <div id="jarvis-trend" class="jarvis-value">Trend: —</div>
                    <div id="jarvis-mtf" class="jarvis-detail">MTF: —</div>
                    <div id="jarvis-pa" class="jarvis-detail">Price action: —</div>
                </div>
                <div class="jarvis-card">
                    <div class="jarvis-label">Risk review</div>
                    <div id="jarvis-risk" class="jarvis-value">Risk review: —</div>
                    <div id="jarvis-risk-limit" class="jarvis-detail">Risk limit: —</div>
                    <div id="jarvis-order-mode" class="jarvis-detail">Orders: disabled</div>
                </div>
            </div>
            <div class="jarvis-lower">
                <div class="jarvis-card">
                    <div class="jarvis-label">Diagnostic flags</div>
                    <ul id="jarvis-flags" class="jarvis-list"><li class="jarvis-empty">Waiting for review data</li></ul>
                </div>
                <div class="jarvis-card">
                    <div class="jarvis-label">JARVIS explanation</div>
                    <div id="jarvis-headline" class="jarvis-value">Waiting for review</div>
                    <div id="jarvis-explanation" class="jarvis-detail">No review snapshot has been published yet.</div>
                    <div id="jarvis-llm" class="jarvis-detail">Local LLM: —</div>
                    <div id="jarvis-timestamp" class="jarvis-detail">Last review: —</div>
                </div>
            </div>
        `;

        const sections = Array.from(document.querySelectorAll("main.main > .section"));
        const mtf = sections.find(section =>
            (section.querySelector(".section-title h2")?.textContent || "").includes("Multi-Timeframe Analysis")
        );
        const market = sections.find(section =>
            (section.querySelector(".section-title h2")?.textContent || "").includes("Market Intelligence")
        );
        // Place JARVIS review above Multi-Timeframe Analysis, not below it.
        if (mtf) mtf.insertAdjacentElement("beforebegin", panel);
        else if (market) market.insertAdjacentElement("beforebegin", panel);
        else document.querySelector("main.main")?.appendChild(panel);
    }

    function text(id, value, fallback = "—") {
        const node = document.getElementById(id);
        if (node) node.textContent = value === null || value === undefined || value === "" ? fallback : String(value);
    }

    function list(id, values) {
        const node = document.getElementById(id);
        if (!node) return;
        node.replaceChildren();
        const items = Array.isArray(values) && values.length ? values : ["No diagnostic flags reported"];
        for (const value of items) {
            const item = document.createElement("li");
            item.textContent = String(value);
            node.appendChild(item);
        }
    }

    function updateHolographicCore(market = {}, audit = {}) {
        const core = document.getElementById("jarvis-holographic-core");
        const caption = document.getElementById("jarvis-core-caption");
        if (!core || !caption) return;

        const rawBias = String(
            market.market_trend || market.candidate_direction || market.price_action || ""
        ).toLowerCase();
        let bias = "unknown";
        if (/bull|uptrend|buy.call|long/.test(rawBias)) bias = "bullish";
        else if (/bear|downtrend|buy.put|short/.test(rawBias)) bias = "bearish";

        const score = Number(audit.entry_score);
        const scoreText = Number.isFinite(score) ? " · " + Math.round(score) : "";
        const label = bias === "bullish" ? "BULLISH" : bias === "bearish" ? "BEARISH" : "BIAS UNKNOWN";
        core.dataset.bias = bias;
        core.setAttribute("aria-label", "JARVIS holographic core, " + label.toLowerCase() + (Number.isFinite(score) ? ", entry score " + Math.round(score) : ""));
        caption.textContent = (bias === "unknown" ? "CORE · STANDBY" : "CORE · " + label) + scoreText;
    }

    function statusPill(value) {
        const node = document.getElementById("jarvis-status");
        if (!node) return;
        const state = String(value || "UNKNOWN").toUpperCase();
        node.textContent = state.replace(/_/g, " ");
        node.classList.remove("ok", "warn", "error");
        if (["OK", "COMPLETE", "TRADE_CANDIDATE"].includes(state)) node.classList.add("ok");
        else if (["ERROR", "UNAVAILABLE", "FAILED"].includes(state)) node.classList.add("error");
        else node.classList.add("warn");
    }

    async function refreshReview() {
        try {
            const response = await fetch("agentic_review.json?ts=" + Date.now(), { cache: "no-store" });
            if (!response.ok) {
                updateHolographicCore({}, {});
                statusPill(response.status === 404 ? "WAITING FOR REVIEW" : "SNAPSHOT UNAVAILABLE");
                text("jarvis-explanation", "Dashboard snapshot is not available yet. Confirm the trading engine is running and has dispatched an Agentic AI review.");
                return;
            }
            const review = await response.json();
            const market = review.market_intelligence || {};
            const mtf = market.multi_timeframe || {};
            const audit = review.decision_audit || {};
            const risk = review.risk_review || {};
            const explanation = review.explanation || {};
            const llm = review.local_llm || {};

            updateHolographicCore(market, audit);
            statusPill(audit.decision_status || review.mode || "REVIEW READY");
            text("jarvis-decision", audit.decision_status, "UNKNOWN");
            text("jarvis-score", "Score: " + (audit.entry_score ?? "—") + " / " + (audit.minimum_score ?? 80));
            text("jarvis-candidate", "Candidate: " + (market.candidate_direction ?? (audit.candidate_present ? "PRESENT" : "—")));
            text("jarvis-trend", "Trend: " + (market.market_trend ?? "UNKNOWN"));
            text("jarvis-mtf", "MTF: " + (mtf.direction ?? "UNKNOWN") + " · " + (mtf.status ?? "UNKNOWN"));
            text("jarvis-pa", "Price action: " + (market.price_action ?? "UNKNOWN"));
            text("jarvis-risk", "Active trade: " + (risk.active_trade ? "YES — lock must hold" : "NO"));
            text("jarvis-risk-limit", "Risk limit: ₹" + (risk.risk_limit_inr ?? "—"));
            text("jarvis-order-mode", "Broker orders: " + (risk.broker_orders_enabled ? "ENABLED" : "DISABLED") + " · Recommendations only");
            list("jarvis-flags", [
                ...(Array.isArray(audit.diagnostic_flags) ? audit.diagnostic_flags : []),
                ...(Array.isArray(risk.risk_flags) ? risk.risk_flags : [])
            ]);
            text("jarvis-headline", explanation.headline ?? "JARVIS diagnostic review");
            text("jarvis-explanation", [
                explanation.market_summary,
                explanation.decision_summary,
                explanation.safety
            ].filter(Boolean).join(" · "), "No explanation returned.");
            text("jarvis-llm", "Local LLM: " + (llm.status || (llm.enabled ? "UNKNOWN" : "DISABLED")) + (llm.text ? " · " + llm.text : ""));
            text("jarvis-timestamp", "Last review: " + (review.timestamp || "—"));
        } catch (error) {
            updateHolographicCore({}, {});
            statusPill("UPDATE ERROR");
            console.warn("JARVIS_AGENTIC_PANEL_ERROR:", error);
        }
    }

    function start() {
        installStyles();
        createPanel();
        refreshReview();
        window.setInterval(refreshReview, 3000);
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
    else start();
})();

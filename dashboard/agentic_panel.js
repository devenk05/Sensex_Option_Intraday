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
            #${PANEL_ID} { background:linear-gradient(135deg,rgba(7,20,38,.98),rgba(10,31,53,.97)); border:1px solid #1e5274; border-radius:16px; padding:20px; margin:20px 0; box-shadow:0 16px 44px rgba(0,0,0,.25),inset 0 1px rgba(80,220,255,.06); color:#e6f4ff; }
            #${PANEL_ID} .jarvis-head { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
            #${PANEL_ID} .jarvis-title { font-size:19px; font-weight:850; letter-spacing:.2px; color:#effbff; }
            #${PANEL_ID} .jarvis-subtitle { color:#9abbd4; font-size:12px; margin-top:5px; line-height:1.5; }
            #${PANEL_ID} .jarvis-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
            #${PANEL_ID} .jarvis-card { border:1px solid #214765; background:linear-gradient(145deg,rgba(14,35,59,.96),rgba(8,23,41,.98)); border-radius:12px; padding:15px; min-width:0; }
            #${PANEL_ID} .jarvis-label { font-size:11px; color:#8eb4d0; text-transform:uppercase; letter-spacing:1px; margin-bottom:9px; }
            #${PANEL_ID} .jarvis-value { font-size:14px; font-weight:750; color:#e9f8ff; overflow-wrap:anywhere; line-height:1.45; }
            #${PANEL_ID} .jarvis-detail { color:#a0bad0; font-size:12px; line-height:1.6; margin-top:7px; overflow-wrap:anywhere; }
            #${PANEL_ID} .jarvis-pill { display:inline-block; border:1px solid var(--border,#d8d0c4); border-radius:999px; padding:5px 9px; font-size:10px; font-weight:800; letter-spacing:.6px; }
            #${PANEL_ID} .jarvis-pill.ok { color:#50e3a4; border-color:#176c58; background:rgba(0,208,132,.08); }
            #${PANEL_ID} .jarvis-pill.warn { color:#ffd078; border-color:#775a23; background:rgba(255,190,70,.08); }
            #${PANEL_ID} .jarvis-pill.error { color:#ff8b98; border-color:#783b4a; background:rgba(255,83,104,.08); }
            #${PANEL_ID} .jarvis-lower { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }
            #${PANEL_ID} .jarvis-list { margin:6px 0 0; padding-left:18px; color:#d2e7f6; font-size:12px; line-height:1.7; overflow-wrap:anywhere; }
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
                <div>
                    <div class="jarvis-title">JARVIS · Trade Review Assistant</div>
                    <div class="jarvis-subtitle">A second opinion on the engine’s analysis · advice only · broker orders stay disabled</div>
                </div>
                <span id="jarvis-status" class="jarvis-pill warn">WAITING FOR REVIEW</span>
            </div>
            <div class="jarvis-intro" style="display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:start;padding:14px 15px;margin:0 0 13px;border:1px solid #235577;border-radius:12px;background:linear-gradient(100deg,rgba(0,190,255,.10),rgba(11,30,51,.6));">
                <div aria-hidden="true" style="font-size:24px;line-height:1">◈</div>
                <div><div id="jarvis-plain-status" style="font-size:14px;font-weight:800;color:#eafaff">Review not received yet</div><div id="jarvis-plain-help" style="font-size:12px;line-height:1.6;color:#a4c0d6;margin-top:5px">This panel explains the engine’s review. It does not generate a trade signal or place orders. Start the trading engine that publishes dashboard/agentic_review.json to populate it.</div></div>
            </div>
            <div class="jarvis-grid">
                <div class="jarvis-card">
                    <div class="jarvis-label">1 · Decision check</div>
                    <div id="jarvis-decision" class="jarvis-value">Waiting for first review</div>
                    <div id="jarvis-score" class="jarvis-detail">Score: —</div>
                    <div id="jarvis-candidate" class="jarvis-detail">Candidate: —</div>
                </div>
                <div class="jarvis-card">
                    <div class="jarvis-label">2 · Market direction</div>
                    <div id="jarvis-trend" class="jarvis-value">Trend: —</div>
                    <div id="jarvis-mtf" class="jarvis-detail">5M direction: —</div>
                    <div id="jarvis-pa" class="jarvis-detail">Price action: —</div>
                </div>
                <div class="jarvis-card">
                    <div class="jarvis-label">3 · Risk & safety</div>
                    <div id="jarvis-risk" class="jarvis-value">Risk review: —</div>
                    <div id="jarvis-risk-limit" class="jarvis-detail">Risk limit: —</div>
                    <div id="jarvis-order-mode" class="jarvis-detail">Orders: disabled</div>
                </div>
            </div>
            <div class="jarvis-lower">
                <div class="jarvis-card">
                    <div class="jarvis-label">Checks that need attention</div>
                    <ul id="jarvis-flags" class="jarvis-list"><li class="jarvis-empty">Waiting for review data</li></ul>
                </div>
                <div class="jarvis-card">
                    <div class="jarvis-label">Plain-English explanation</div>
                    <div id="jarvis-headline" class="jarvis-value">Waiting for review</div>
                    <div id="jarvis-explanation" class="jarvis-detail">No review snapshot has been published yet.</div>
                    <div id="jarvis-llm" class="jarvis-detail">Local LLM: —</div>
                    <div id="jarvis-timestamp" class="jarvis-detail">Last review: —</div>
                </div>
            </div>
        `;

        const sections = Array.from(document.querySelectorAll("main.main > .section"));
        const mtf = sections.find(section =>
            (section.querySelector(".section-title h2")?.textContent || "").includes("5-Minute Analysis")
        );
        const market = sections.find(section =>
            (section.querySelector(".section-title h2")?.textContent || "").includes("Market Intelligence")
        );
        // Place JARVIS review above the 5-Minute Analysis section.
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
            const [response, liveResponse] = await Promise.all([
                fetch("agentic_review.json?ts=" + Date.now(), { cache: "no-store" }),
                fetch("live_state.json?ts=" + Date.now(), { cache: "no-store" }).catch(() => null)
            ]);
            if (!response.ok) {
                statusPill(response.status === 404 ? "WAITING FOR REVIEW" : "SNAPSHOT UNAVAILABLE");
                text("jarvis-plain-status", "JARVIS has not received a review yet");
                text("jarvis-plain-help", "This is a data-availability message, not a market signal. The dashboard is looking for dashboard/agentic_review.json. Start the project process that publishes the Agentic AI review; do not interpret this panel as BUY or SELL.");
                text("jarvis-headline", "No review available");
                text("jarvis-explanation", "The panel will fill in after the review snapshot is published.");
                return;
            }
            const review = await response.json();
            let liveState = {};
            if (liveResponse && liveResponse.ok) {
                try { liveState = await liveResponse.json(); } catch (_) { liveState = {}; }
            }
            const market = review.market_intelligence || {};
            const mtf = market.multi_timeframe || {};
            const audit = review.decision_audit || {};
            const risk = review.risk_review || {};
            const explanation = review.explanation || {};
            const llm = review.local_llm || {};

            // The main trading engine score is authoritative. JARVIS is advisory;
            // its separate review score must never override the live eligibility gate.
            const canonicalScore = liveState.entry_score !== null
                && liveState.entry_score !== undefined
                && Number.isFinite(Number(liveState.entry_score))
                ? Number(liveState.entry_score) : null;
            const minimumScore = Number(audit.minimum_score ?? 80);
            const reportedDecision = String(audit.decision_status || review.mode || "REVIEW READY").toUpperCase();
            const reportsCandidate = ["TRADE_CANDIDATE", "BUY_CALL", "BUY_PUT", "CONFIRMED"].includes(reportedDecision);
            const scoreGateBlocked = reportsCandidate
                && (canonicalScore === null || canonicalScore < minimumScore);
            const displayDecision = scoreGateBlocked ? "WAIT — SCORE GATE" : reportedDecision;
            statusPill(scoreGateBlocked ? "WAIT" : reportedDecision);
            text("jarvis-decision", displayDecision, "UNKNOWN");
            text("jarvis-score", canonicalScore === null
                ? "Official score: unavailable · JARVIS review: " + (audit.entry_score ?? "—") + " / " + minimumScore
                : "Official score: " + canonicalScore.toFixed(2) + " / " + minimumScore);
            text("jarvis-candidate", scoreGateBlocked
                ? (canonicalScore === null
                    ? "Candidate blocked: official live score unavailable"
                    : "Candidate rejected: score " + canonicalScore.toFixed(2) + " is below " + minimumScore)
                : "Candidate: " + (market.candidate_direction ?? (audit.candidate_present ? "PRESENT" : "—")));
            text("jarvis-trend", "Trend: " + (market.market_trend ?? "UNKNOWN"));
            text("jarvis-mtf", "5M direction: " + (mtf.direction_5m ?? "UNKNOWN") + " · " + (mtf.status ?? "UNKNOWN"));
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

const test = require("node:test");
const assert = require("node:assert/strict");
const { getOptions, riskSummary, healthSummary, heatmapCell, LIMIT_INR } = require("../dashboard/jarvis_phases.js");

test("option-chain rows normalize live price and bid/ask depth", () => {
  const rows = getOptions({ option_chain: [{ strike: 73200, option_type: "CE", ltp: 100, bid: 99, ask: 101, total_bid_quantity: 20, total_ask_quantity: 10 }] });
  assert.equal(rows.length, 1);
  assert.equal(rows[0].price, 100);
  assert.equal(rows[0].bidQty, 20);
  assert.equal(rows[0].askQty, 10);
});

test("risk estimate respects the configured INR cap and never invents missing values", () => {
  const r = riskSummary({ active_trade: { entry_price: 200, option_sl: 150, option_target: 300, lot_size: 20 }, entry_score: 88 });
  assert.equal(r.riskInr, 1000);
  assert.equal(r.rr, 2);
  assert.equal(r.cap, LIMIT_INR);
  const missing = riskSummary({});
  assert.equal(missing.riskInr, null);
  assert.equal(missing.rr, null);
});

test("health uses snapshot age and reports stale data", () => {
  const now = Date.parse("2026-10-22T10:00:30Z");
  const fresh = healthSummary({ live_update: "2026-10-22T10:00:25Z", active_trade: { symbol: "X" } }, {}, now);
  assert.equal(fresh.live, true);
  assert.equal(fresh.tradeLocked, true);
  const stale = healthSummary({ live_update: "2026-10-22T09:00:00Z" }, {}, now);
  assert.equal(stale.live, false);
});

test("heatmap direction is based on actual premium change", () => {
  assert.equal(heatmapCell({ premium_change_percent: 12 }, 20).color, "up");
  assert.equal(heatmapCell({ premium_change_percent: -4 }, 20).color, "down");
  assert.equal(heatmapCell({}, 20).color, "neutral");
});

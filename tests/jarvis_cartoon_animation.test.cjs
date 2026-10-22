const test = require("node:test");
const assert = require("node:assert/strict");
const { sceneFor, hasEntryConfirmation, closedTrades, sceneData, scenes } = require("../dashboard/jarvis_cartoon_animation.js");

test("all nine cartoon scenes are defined", () => {
  assert.equal(scenes.length, 9);
  assert.deepEqual(scenes.map(s => s.n), [1,2,3,4,5,6,7,8,9]);
});

test("scene 1 is the neutral fallback and option-chain data advances to strike selection", () => {
  assert.equal(sceneFor({}), 1);
  assert.equal(sceneFor({ options: [{ strike: 73000, type: "CE" }] }), 3);
});

test("published BUY CALL and BUY PUT recommendation trigger scene 4", () => {
  assert.equal(sceneFor({ decision_status: "BUY_CALL" }), 4);
  assert.equal(sceneFor({ decision_status: "BUY_PUT" }), 4);
});

test("entry confirmation triggers scene 5 but WAIT/NOT_CONFIRMED does not", () => {
  assert.equal(hasEntryConfirmation({ one_minute_analysis: { status: "ENTRY_CONFIRMED" } }), true);
  assert.equal(hasEntryConfirmation({ one_minute_analysis: { status: "NOT_CONFIRMED" } }), false);
  assert.equal(hasEntryConfirmation({ one_minute_analysis: { status: "WAIT" } }), false);
  assert.equal(sceneFor({ one_minute_analysis: { status: "ENTRY_CONFIRMED" } }), 5);
});

test("active trade takes precedence and triggers scene 6", () => {
  assert.equal(sceneFor({ active_trade: { symbol: "SENSEX_OPTION" }, trade_history: [{ status: "CLOSED", result: "TARGET" }] }), 6);
});

test("recorded target/stop-loss outcome triggers exit scene; missing history stays empty", () => {
  assert.equal(closedTrades({ trade_history: [{ status: "CLOSED", result: "TARGET_HIT" }] }).length, 1);
  assert.equal(sceneFor({ trade_history: [{ status: "CLOSED", result: "TARGET_HIT" }] }), 7);
  assert.equal(sceneFor({ trade_history: [{ status: "CLOSED", result: "CLOSED" }] }), 8);
});

test("telegram scene is used only when backend reports delivery and no active decision dominates", () => {
  assert.equal(sceneFor({ telegram_status: "SENT" }), 9);
  assert.equal(sceneFor({ telegram_status: "UNKNOWN" }), 1);
});

test("missing trade fields remain unavailable rather than using example prices", () => {
  const d = sceneData({ decision_status: "BUY_CALL" });
  assert.equal(d.entry, undefined);
  assert.equal(d.sl, undefined);
  assert.equal(d.target, undefined);
  assert.equal(d.score, undefined);
});

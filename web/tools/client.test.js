// Client, route table, and app.js consistency.  Run: node --test web/tools
const test = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");
const ROUTES = require("../routes.js");
const Client = require("../client.js");
const Mock = require("../mock.js");

function read(name) { return fs.readFileSync(path.join(__dirname, "..", name), "utf8"); }

test("route table is well formed", () => {
  const seen = new Set();
  for (const [key, spec] of Object.entries(ROUTES)) {
    assert.match(key, /^[a-z]+\.[a-zA-Z]+$/, key);
    assert.ok(["GET", "POST", "PUT", "DELETE"].includes(spec[0]), key);
    assert.ok(spec[1].startsWith("/api/"), key);
    assert.ok(Array.isArray(spec[3]), key);
    const placeholders = [...spec[1].matchAll(/\{(\w+)\}/g)].map((m) => m[1]);
    placeholders.forEach((p) => assert.ok(spec[3].includes(p), `${key}: {${p}} not in params`));
    const id = spec[0] + " " + spec[1];
    assert.ok(!seen.has(id), "duplicate " + id);
    seen.add(id);
  }
});

test("every route handler exists in the mock", () => {
  const missing = Object.values(ROUTES).map((s) => s[2]).filter((h) => typeof Mock[h] !== "function");
  assert.deepStrictEqual(missing, []);
});

test("app.js only uses Api calls that exist in the route table", () => {
  const app = read("app.js");
  const used = new Set([...app.matchAll(/Api\.([a-z]+)\.([a-zA-Z]+)\(/g)].map((m) => m[1] + "." + m[2]));
  assert.ok(used.size > 40, "expected many Api calls, found " + used.size);
  const missing = [...used].filter((k) => !ROUTES[k]);
  assert.deepStrictEqual(missing, [], "unknown Api calls: " + missing.join(", "));
  assert.ok(!/window\.pywebview\.api/.test(app), "app.js must not call the bridge directly");
  assert.ok(!/fetch\(/.test(app), "app.js must not call fetch directly");
});

test("HttpTransport builds URLs, query strings, and JSON bodies", async () => {
  const calls = [];
  const fakeFetch = (url, options) => { calls.push({ url, options }); return Promise.resolve({ status: 200, json: () => Promise.resolve({ ok: true, url }) }); };
  const api = Client.build(new Client.HttpTransport("http://h", "tok", fakeFetch));
  await api.ledger.list({ search: "rent & co", year: "2025" });
  assert.strictEqual(calls[0].url, "http://h/api/ledger?search=rent%20%26%20co&year=2025");
  assert.strictEqual(calls[0].options.method, "GET");
  assert.strictEqual(calls[0].options.headers["X-Iceberg-Token"], "tok");
  assert.strictEqual(calls[0].options.body, undefined);
  await api.transactions.update({ transaction_id: 7, fields: { name: "x" } });
  assert.strictEqual(calls[1].url, "http://h/api/transactions/7");
  assert.strictEqual(calls[1].options.method, "PUT");
  assert.deepStrictEqual(JSON.parse(calls[1].options.body), { fields: { name: "x" } });
  await api.databases.save();
  assert.strictEqual(calls[2].options.body, "{}");
  const failing = Client.build(new Client.HttpTransport("", "t", () => Promise.reject(new Error("down"))));
  const r = await failing.app.status();
  assert.strictEqual(r.ok, false);
  assert.match(r.message, /did not respond/);
});

test("MockTransport maps named args to the mock's positional signature", async () => {
  const api = Client.build(new Client.MockTransport(Mock));
  await Mock.open_database();
  const ledger = await api.ledger.list({ search: "rent", year: "" });
  assert.strictEqual(ledger.rows.length, 3);
  const one = await api.transactions.get({ transaction_id: 5 });
  assert.strictEqual(one.transaction.name, "Consulting fee");
  const dup = await api.transactions.create({ fields: { name: "Owner investment", date: "2025-01-02", amount: "10000", debit_account: "10002", credit_account: "14001" }, confirm_warnings: false });
  assert.ok(dup.needs_confirmation);
  const byKey = await api.call("app.status");
  assert.ok("database_loaded" in byKey);
});

test("HttpTransport can be built the way the page builds it (global fetch)", () => {
  const transport = new Client.HttpTransport("", "tok");   // no fetch injected: must find the global one
  assert.strictEqual(typeof transport.fetch, "function");
  const api = Client.build(transport);
  assert.strictEqual(typeof api.app.status, "function");
});

test("token is read from the page URL", () => {
  assert.strictEqual(Client.tokenFromLocation({ search: "?token=abc%20d" }), "abc d");
  assert.strictEqual(Client.tokenFromLocation({ search: "" }), "");
  assert.deepStrictEqual(Client.fillPath("/api/x/{id}/y", { id: "a/b" }), { path: "/api/x/a%2Fb/y", used: { id: true } });
});

// Loads the real index.html in jsdom against a real server started by the Python
// side (ICEBERG_URL/ICEBERG_TOKEN from tests/test_server.py), runs every script the
// page ships, and checks that the landing page actually paints.  Requires jsdom
// (npm install jsdom); skipped when it is not installed.
const test = require("node:test");
const assert = require("node:assert");
let JSDOM;
try { JSDOM = require("jsdom").JSDOM; } catch (e) { JSDOM = null; }

function waitFor(check, timeoutMs) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    (function poll() {
      if (check()) { return resolve(); }
      if (Date.now() - started > timeoutMs) { return reject(new Error("timed out waiting for the page")); }
      setTimeout(poll, 100);
    })();
  });
}

test("index.html boots to the Welcome screen over HTTP", { skip: !JSDOM ? "jsdom not installed" : (!process.env.ICEBERG_URL ? "no server" : false) }, async () => {
  const url = process.env.ICEBERG_URL + "/?token=" + process.env.ICEBERG_TOKEN;
  const dom = await JSDOM.fromURL(url, { runScripts: "dangerously", resources: "usable", pretendToBeVisual: true,
    beforeParse(window) { window.fetch = (u, o) => fetch(new URL(u, url).toString(), o); } });
  const { window } = dom;
  const content = () => window.document.getElementById("content").innerHTML;
  try {
    const status = await (await fetch(process.env.ICEBERG_URL + "/api/status", { headers: { "X-Iceberg-Token": process.env.ICEBERG_TOKEN } })).json();
    await waitFor(() => content().length > 0, 15000);
    assert.ok(!content().includes("could not start"), "startup error shown: " + content().slice(0, 300));
    if (status.database_loaded) {
      assert.ok(content().includes("Chart of accounts"), "dashboard not painted: " + content().slice(0, 300));
      assert.ok(window.document.getElementById("status-bar").innerHTML.includes(status.db_name));
      window.document.querySelector('[data-action="go"][data-screen="ledger"]').click();
      await waitFor(() => content().includes('data-action="new-transaction"') && content().includes("Ledger<span"), 5000);
    } else {
      assert.ok(content().includes("Create New Database"), "welcome screen not painted: " + content().slice(0, 300));
      assert.ok(window.document.getElementById("status-bar").innerHTML.includes("No database open"));
      window.document.querySelector('[data-action="go"][data-screen="create"]').click();
      await waitFor(() => content().includes("Create New Database</h1>"), 5000);
    }
  } finally {
    window.close();   // stops the page's timers so Node can exit even when an assertion failed
  }
});

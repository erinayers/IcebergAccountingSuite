// End-to-end: the real client against a running server.  Used by tests/test_server.py.
//   ICEBERG_URL=http://127.0.0.1:PORT ICEBERG_TOKEN=... ICEBERG_KEYS=/folder node web/tools/e2e.js
const Client = require("../client.js");
const api = Client.build(new Client.HttpTransport(process.env.ICEBERG_URL, process.env.ICEBERG_TOKEN, fetch));
function must(r, what) { if (!r.ok) { throw new Error(what + ": " + JSON.stringify(r)); } return r; }
(async () => {
  const before = await api.app.status();
  if (before.database_loaded) { throw new Error("expected no database"); }
  must(await api.databases.create({ fields: { business_name: "E2E Books", address: "1 Main", sales_tax: "6.25", save_location: process.env.ICEBERG_KEYS, receipts_location: process.env.ICEBERG_KEYS } }), "create");
  const bad = await api.transactions.create({ fields: { name: "", date: "2025-01-01", amount: "x", debit_account: "10002", credit_account: "10002" } });
  if (bad.ok || bad.errors.map((e) => e.field).join() !== "name,amount,credit_account") { throw new Error("validation: " + JSON.stringify(bad)); }
  const added = must(await api.transactions.create({ fields: { name: "Owner investment", date: "2025-01-02", amount: "10,000", debit_account: "10002", credit_account: "14001" } }), "add");
  const customer = must(await api.customers.save({ fields: { company: "Globex", first_name: "Hank", last_name: "Scorpio", address: "1 Volcano Ln" } }), "customer");
  const service = must(await api.services.save({ fields: { description: "Consulting hour", price: "150", taxable: "True" } }), "service");
  const item = must(await api.invoices.lineItem({ sku: service.id, quantity: "2" }), "line item").line_item;
  const totals = must(await api.invoices.totals({ line_items: [item], tax_rate: "0.0625" }), "totals");
  if (totals.total !== 31875) { throw new Error("totals " + JSON.stringify(totals)); }
  const invoice = must(await api.invoices.create({ fields: { customer_id: customer.id, status: "Due", due_date: "2025-02-01" }, line_items: [item] }), "invoice");
  const paid = must(await api.invoices.changeStatus({ invoice_id: invoice.id, status: "Paid", account: "10002" }), "pay");
  const detail = must(await api.invoices.get({ invoice_id: invoice.id }), "invoice detail");
  if (detail.history.length !== 2 || detail.invoice.status !== "Paid") { throw new Error("history " + JSON.stringify(detail.history)); }
  const dash = must(await api.dashboard.get({ type_prefix: "10", year: "" }), "dashboard");
  const checking = dash.accounts.find((a) => a.id === "10002");
  if (checking.balance !== 1000000 + 31875) { throw new Error("checking balance " + checking.balance); }
  const recon = must(await api.reconcile.start({ account_id: "10002", statement_date: "2099-12-31", statement_balance: "10,318.75" }), "reconcile start");
  const summary = must(await api.reconcile.summary({ cleared_ids: recon.candidates.map((c) => c.Transaction_ID) }), "summary");
  if (!summary.summary.balanced) { throw new Error("not balanced " + JSON.stringify(summary.summary)); }
  must(await api.reconcile.finish({ cleared_ids: summary.cleared_ids }), "finish");
  const report = must(await api.reports.run({ report_type: "Balance Sheet", start: "2025-01-01", end: "2025-12-31" }), "report");
  if (!report.report.balanced) { throw new Error("balance sheet not balanced"); }
  must(await api.databases.save(), "save");
  const backups = must(await api.backups.list(), "backups");
  if (backups.backups.length < 1) { throw new Error("no backups"); }
  const status = await api.app.status();
  if (status.unsaved) { throw new Error("still unsaved after save"); }
  const unauthorised = await Client.build(new Client.HttpTransport(process.env.ICEBERG_URL, "wrong", fetch)).app.status();
  if (unauthorised.ok !== false) { throw new Error("token not enforced"); }
  console.log(JSON.stringify({ transaction: added.id, invoice: invoice.id, paid: paid.status, checking: checking.balance, backups: backups.backups.length }));
})().catch((error) => { console.error(error.message); process.exit(1); });

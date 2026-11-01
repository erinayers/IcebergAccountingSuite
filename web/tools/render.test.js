// Run with: node --test web/tools
const test = require("node:test");
const assert = require("node:assert");
const R = require("../render_tools.js");
const Mock = require("../mock.js");

test("money formats cents like the Python helper", () => {
  assert.strictEqual(R.money(0), "$0.00");
  assert.strictEqual(R.money(5), "$0.05");
  assert.strictEqual(R.money(123456), "$1,234.56");
  assert.strictEqual(R.money(-104218), "($1,042.18)");
  assert.strictEqual(R.money(100000000), "$1,000,000.00");
});

test("esc neutralises markup in user data", () => {
  assert.strictEqual(R.esc('<b onclick="x">&'), "&lt;b onclick=&quot;x&quot;&gt;&amp;");
  const html = R.ledger({ status: {}, screen: "ledger", ledger: { rows: [{ id: 1, date: "2025-01-01", name: "<script>alert(1)</script>", amount: 1, debit: "10002", debit_name: "", credit: "14001", credit_name: "", notes: "", reconciled: "" }] } });
  assert.ok(!html.includes("<script>alert"));
  assert.ok(html.includes("&lt;script&gt;"));
});

test("field marks errors and required", () => {
  const html = R.field({ name: "amount", label: "Amount", required: true, value: "x", errors: [{ field: "amount", message: "Not a number" }] });
  assert.ok(html.includes('class="field invalid"'));
  assert.ok(html.includes("Not a number"));
  assert.ok(html.includes('<span class="req">*</span>'));
  const clean = R.field({ name: "amount", label: "Amount", value: "1", errors: [], hint: "Dollars" });
  assert.ok(!clean.includes("invalid"));
  assert.ok(clean.includes("Dollars"));
});

test("icons render as labelled spans from the design sheet", () => {
  const html = R.icon("check", "Reconciled", "sm");
  assert.strictEqual(html, '<span class="icon icon-check icon-sm" role="img" aria-label="Reconciled" title="Reconciled"></span>');
  assert.ok(R.icon("back").includes("icon-mono"));
  assert.ok(!R.icon("check").includes("icon-mono"));
  const fs = require("fs"), path = require("path");
  Object.keys(R.ICONS).forEach((name) => assert.ok(fs.existsSync(path.join(__dirname, "..", "icons", name + ".png")), name + ".png missing"));
  const views = fs.readFileSync(path.join(__dirname, "..", "render.js"), "utf8") + fs.readFileSync(path.join(__dirname, "..", "render_records.js"), "utf8") + fs.readFileSync(path.join(__dirname, "..", "render_tools.js"), "utf8");
  assert.ok(!/[\u2713\u2716\u2190\u2715\u2630\u26a0]|&#128213;|&#128190;|&#9776;/.test(views), "views still contain glyphs that should be icons");
});

test("welcome shows the database count link only when there are databases", () => {
  assert.ok(!R.welcome({ databases: [] }).includes("View them"));
  assert.ok(R.welcome({ databases: [{}, {}] }).includes("You have 2 databases"));
  assert.ok(R.welcome({ databases: [{}] }).includes("You have 1 database in"));
});

test("workspace highlights the active tab and the save state", () => {
  const html = R.workspace({ screen: "ledger", status: { business_name: "Alpha", db_name: "Alpha.icb", unsaved: true } }, "<p>body</p>");
  assert.ok(html.includes('class="nav-tab active" data-action="go" data-screen="ledger"'));
  assert.ok(html.includes("Unsaved changes"));
  assert.ok(html.includes("<p>body</p>"));
  assert.strictEqual(R.NAV.length, 8);
});

test("status bar countdown and messages", () => {
  assert.strictEqual(R.countdown(245), "4:05");
  assert.strictEqual(R.countdown(-3), "0:00");
  const bar = R.statusBar({ status: { database_loaded: true, db_name: "A.icb", unsaved: true, autosave_in: 61 }, message: { text: "Saved", kind: "ok" } });
  assert.ok(bar.includes("autosave in 1:01"));
  assert.ok(bar.includes('class="message ok"><span class="icon icon-check"'));
  assert.ok(bar.includes("Saved"));
  assert.ok(R.statusBar({ status: { database_loaded: false } }).includes("No database open"));
});

test("dashboard renders tiles, filters and balance state from the API shape", async () => {
  const data = await Mock.dashboard("", "");
  const html = R.dashboard({ screen: "dashboard", status: { business_name: "Alpha" }, dashboard: data });
  assert.ok(html.includes("Chart of accounts"));
  assert.ok(html.includes("In balance"));
  assert.ok(html.includes('data-action="open-account" data-account="10002"'));
  assert.ok(html.includes("Business income"));
  const expenses = await Mock.dashboard("11", "");
  assert.ok(expenses.accounts.every((a) => a.id.startsWith("11")));
});

test("ledger renders rows, selection, and the empty state", async () => {
  const data = await Mock.ledger("rent", "");
  assert.strictEqual(data.rows.length, 3);
  const html = R.ledger({ screen: "ledger", status: {}, ledger: data, selected: data.rows[0] });
  assert.ok(html.includes('class="clickable selected"'));
  assert.ok(html.includes("Office rent March"));
  const empty = R.ledger({ screen: "ledger", status: {}, ledger: { rows: [], filters: { search: "zzz" } } });
  assert.ok(empty.includes("No transactions match"));
});

test("transaction modal shows field errors and the confirmation prompt", async () => {
  const form = await Mock.transaction_form();
  const bad = await Mock.add_transaction({ name: "", amount: "x", debit_account: "10002", credit_account: "10002" });
  const html = R.transactionModal({ form, fields: {}, errors: bad.errors, message: bad.message });
  assert.ok(html.includes("Transaction name is required."));
  assert.ok(html.includes("must be different"));
  assert.ok(html.includes('id="f-debit_account"'));
  const dup = await Mock.add_transaction({ name: "Owner investment", date: "2025-01-02", amount: "10000", debit_account: "10002", credit_account: "14001" });
  assert.ok(dup.needs_confirmation);
  const confirm = R.transactionModal({ form, fields: {}, errors: [], warnings: dup.warnings });
  assert.ok(confirm.includes("Save anyway"));
});

test("register shows running balances newest first", async () => {
  const data = await Mock.account_register("10002");
  assert.strictEqual(data.rows[data.rows.length - 1].running_balance, 1000000);
  const html = R.register({ screen: "account", status: {}, register: data });
  assert.ok(html.includes("Back to chart of accounts"));
  assert.ok(html.includes("Register"));
});

const fs = require("fs");
const path = require("path");

function read(name) { return fs.readFileSync(path.join(__dirname, "..", name), "utf8"); }

test("every data-action emitted by a view has a handler in app.js", () => {
  const views = read("render.js") + read("render_records.js") + read("render_tools.js");
  const emitted = new Set([...views.matchAll(/data-action="([a-z-]+)"/g)].map((m) => m[1]));
  const app = read("app.js");
  const handled = new Set([...app.matchAll(/^\s*"([a-z-]+)": function/gm)].map((m) => m[1]));
  const missing = [...emitted].filter((a) => !handled.has(a));
  assert.deepStrictEqual(missing, [], "unhandled actions: " + missing.join(", "));
});

test("invoices screen shows list, details, history and status form", async () => {
  await Mock.open_database();
  const list = await Mock.invoices("");
  const detail = await Mock.invoice(10002);
  const html = R.invoices({ screen: "invoices", status: {}, invoices: list, selectedInvoice: detail });
  assert.ok(html.includes("Globex Corporation"));
  assert.ok(html.includes("Invoice 10002"));
  assert.ok(html.includes("Network installation"));
  assert.ok(html.includes('data-action="change-invoice-status"'));
  assert.ok(html.includes('<option value="Paid">'));
  const paid = R.invoices({ screen: "invoices", status: {}, invoices: list, selectedInvoice: await Mock.invoice(10001) });
  assert.ok(paid.includes('<option value="Refunded">'));
  const empty = R.invoices({ screen: "invoices", status: {}, invoices: { invoices: [] } });
  assert.ok(empty.includes("No invoices yet"));
});

test("invoice modal renders line items, totals and field errors", async () => {
  const form = await Mock.invoice_form();
  const item = (await Mock.invoice_line_item("10002", "2")).line_item;
  const totals = await Mock.invoice_totals([item], "0.0625");
  assert.strictEqual(totals.total, 255000);
  const bad = await Mock.create_invoice({ customer_id: "", status: "Paid", due_date: "2025-05-01" }, []);
  const html = R.invoiceModal({ invoiceForm: form, invoiceFields: { status: "Paid" }, lineItems: [item], invoiceTotals: totals, errors: bad.errors, message: bad.message });
  assert.ok(html.includes("Select a customer from the list."));
  assert.ok(html.includes("Add at least one line item."));
  assert.ok(html.includes("Deposit account is required."));
  assert.ok(html.includes("$2,550.00"));
  assert.ok(html.includes('data-action="remove-line-item" data-index="0"'));
});

test("customers, vendors and services screens and modals", async () => {
  const customers = await Mock.customers("");
  const detail = await Mock.customer("1");
  let html = R.customers({ screen: "customers", status: {}, customers: customers, selectedCustomer: detail });
  assert.ok(html.includes("Balance due"));
  assert.ok(html.includes("$6,903.63"));
  assert.ok(html.includes('data-action="edit-customer"'));
  const badCustomer = await Mock.save_customer({});
  html = R.customerModal({ fields: {}, errors: badCustomer.errors, message: badCustomer.message });
  assert.ok(html.includes("Customer address is required"));
  const vendors = await Mock.vendors("office");
  assert.strictEqual(vendors.vendors.length, 1);
  html = R.vendors({ screen: "vendors", status: {}, vendors: vendors, selectedVendor: vendors.vendors[0] });
  assert.ok(html.includes("officedepot.example"));
  html = R.vendorModal({ fields: { name: "" }, errors: (await Mock.save_vendor({ name: "" })).errors });
  assert.ok(html.includes("Vendor name is required."));
  const services = await Mock.services("");
  html = R.services({ screen: "services", status: {}, services: services, selectedService: services.services[1] });
  assert.ok(html.includes("Taxable"));
  assert.ok(html.includes("$1,200.00"));
  html = R.serviceModal({ fields: { price: "abc" }, errors: (await Mock.save_service({ description: "x", price: "abc" })).errors });
  assert.ok(html.includes("is not a number"));
});

test("reconcile screen: setup, candidates, summary and finish state", async () => {
  const accounts = (await Mock.accounts()).accounts;
  let html = R.reconcile({ screen: "reconcile", status: {}, accountList: accounts, reconcile: { fields: {}, errors: [], data: null } });
  assert.ok(html.includes("Load transactions"));
  const started = await Mock.reconcile_start("10002", "2025-02-28", "10,057.82");
  const all = await Mock.reconcile_summary(started.candidates.map((c) => c.Transaction_ID));
  assert.ok(all.summary.balanced);
  html = R.reconcile({ screen: "reconcile", status: {}, accountList: accounts, reconcile: { fields: { account: "10002" }, errors: [], data: all } });
  assert.ok(html.includes("Balanced"));
  assert.ok(html.includes('data-action="reconcile-finish">'));
  assert.ok(!html.includes('data-action="reconcile-finish" disabled'));
  assert.strictEqual((html.match(/type="checkbox" checked/g) || []).length, 2);
  const none = await Mock.reconcile_summary([]);
  html = R.reconcile({ screen: "reconcile", status: {}, accountList: accounts, reconcile: { fields: {}, errors: [], data: none } });
  assert.ok(html.includes('data-action="reconcile-finish" disabled'));
  const bad = await Mock.reconcile_start("", "", "x");
  html = R.reconcile({ screen: "reconcile", status: {}, accountList: accounts, reconcile: { fields: {}, errors: bad.errors, data: null } });
  assert.ok(html.includes("Select an account."));
});

test("properties, account modal, tools menu and dialogs", async () => {
  const props = await Mock.properties_summary();
  let html = R.properties({ screen: "properties", status: {}, properties: props });
  assert.ok(html.includes('value="6.25"'));
  assert.ok(html.includes("tbl_ledger_Alpha_Corporation_CY2025"));
  assert.strictEqual(R.percent("0.0625"), "6.25");
  html = R.accountModal({ accountForm: await Mock.account_form(), fields: {}, errors: [{ field: "name", message: "Account name is required." }] });
  assert.ok(html.includes("Account name is required."));
  assert.ok(html.includes('name="type_prefix"'));
  html = R.toolsMenu({ status: { database_loaded: false } });
  assert.ok(html.includes('data-action="show-backups" disabled'));
  html = R.toolsMenu({ status: { database_loaded: true, db_name: "A.icb" } });
  assert.ok(!html.includes('data-action="show-backups" disabled'));
  html = R.backupsModal(await Mock.backups());
  assert.ok(html.includes("Restore"));
  html = R.importPreviewModal("/x/t.csv", await Mock.import_transactions("/x/t.csv", false));
  assert.ok(html.includes("Import 4 transaction(s)?"));
  html = R.importProblemsModal(await Mock.import_transactions("/x/bad.csv", false));
  assert.ok(html.includes("Line 3: Amount"));
  html = R.preferencesModal(await Mock.preferences());
  assert.ok(html.includes("High contrast"));
  assert.ok(R.shortcutsModal().includes("Ctrl+N"));
  assert.ok(R.consoleModal(["a", "<b>"]).includes("&lt;b&gt;"));
});

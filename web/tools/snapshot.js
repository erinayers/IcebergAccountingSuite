// Renders every screen with the sample data to static HTML (build/screens/*.html)
// so they can be rasterised without a webview: node web/tools/snapshot.js
const fs = require("fs");
const path = require("path");
const R = require("../render_tools.js");
const Mock = require("../mock.js");

const out = path.join(__dirname, "..", "..", "build", "screens");
fs.mkdirSync(out, { recursive: true });
const iconBase = "file://" + path.join(__dirname, "..") + "/";
const css = fs.readFileSync(path.join(__dirname, "..", "app.css"), "utf8").replace(/url\(icons\/([a-z]+\.png)\)/g, (m, f) => "url(\"" + iconBase + "icons/" + f + "\")");

function page(name, contentHtml, statusHtml, modalHtml) {
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>${css}
  body { width: 1260px; height: 820px; }</style></head><body>
  <div class="titlebar"><div class="brand"><div class="badge">IC</div><span>Iceberg Accounting Suite</span></div><div class="clock">Saturday, 10/31/2026  -  14:52 (UTC-04:00)</div></div>
  <div class="content" id="content">${contentHtml}</div>
  <div class="run-status-bar" id="status-bar">${statusHtml}</div>
  <div class="modal-overlay${modalHtml ? " open" : ""}" id="modal">${modalHtml || ""}</div></body></html>`;
  fs.writeFileSync(path.join(out, name + ".html"), html);
  console.log("wrote", name);
}

(async () => {
  const databases = await Mock.recent_databases();
  const closed = await Mock.status();
  page("01-welcome", R.welcome({ databases, version: closed.version }), R.statusBar({ status: closed, message: { text: "", kind: "" } }));
  page("02-databases", R.databases({ databases, status: closed }), R.statusBar({ status: closed }));
  const createBad = await Mock.create_database({ business_name: "" });
  page("03-create", R.createForm({ fields: { address: "488 E Main St\nAnytown", sales_tax: "six", save_location: "E:\\Keys", receipts_location: "C:\\Users\\you\\Receipts" }, errors: createBad.errors }),
    R.statusBar({ status: closed, message: { text: createBad.message, kind: "bad" } }));
  await Mock.open_database();
  const open = await Mock.status();
  const dash = await Mock.dashboard("", "");
  page("04-dashboard", R.dashboard({ screen: "dashboard", status: open, dashboard: dash }), R.statusBar({ status: open, message: { text: "Opened Alpha_Corporation.icb.", kind: "ok" } }));
  const ledger = await Mock.ledger("", "");
  const selected = (await Mock.transaction(5)).transaction;
  page("05-ledger", R.ledger({ screen: "ledger", status: open, ledger: ledger, selected }), R.statusBar({ status: open, message: { text: "", kind: "" } }));
  const form = await Mock.transaction_form();
  const bad = await Mock.add_transaction({ name: "", date: "2025-04-02", amount: "abc", debit_account: "11010", credit_account: "11010" });
  page("06-new-transaction", R.ledger({ screen: "ledger", status: open, ledger: ledger, selected }), R.statusBar({ status: open, message: { text: bad.message, kind: "bad" } }),
    R.transactionModal({ form, fields: { date: "2025-04-02", amount: "abc", debit_account: "11010", credit_account: "11010", notes: "Check 1043" }, errors: bad.errors, message: bad.message }));
  const added = await Mock.add_transaction({ name: "Office rent April", date: "2025-04-02", amount: "1200", debit_account: "11010", credit_account: "10002", notes: "Check 1043" });
  const dirty = await Mock.status();
  const ledger2 = await Mock.ledger("", "");
  page("07-ledger-unsaved", R.ledger({ screen: "ledger", status: dirty, ledger: ledger2, selected: (await Mock.transaction(added.id)).transaction }), R.statusBar({ status: dirty, message: { text: added.message, kind: "ok" } }));
  const register = await Mock.account_register("10002");
  page("08-register", R.register({ screen: "account", status: dirty, register }), R.statusBar({ status: dirty }));
  const periods = await Mock.report_periods();
  const report = await Mock.report("Income Statement", "2025-01-01", "2025-03-31");
  page("09-reports", R.reports({ screen: "reports", status: dirty, periods, reportSelection: { type: "Income Statement", preset: "Last Quarter", start: "2025-01-01", end: "2025-03-31" }, report }), R.statusBar({ status: dirty, message: { text: "Income Statement ready.", kind: "ok" } }));
  const invoiceList = await Mock.invoices("");
  page("10-invoices", R.invoices({ screen: "invoices", status: dirty, invoices: invoiceList, selectedInvoice: await Mock.invoice(10002) }), R.statusBar({ status: dirty }));
  const invForm = await Mock.invoice_form();
  const li1 = (await Mock.invoice_line_item("10001", "8")).line_item, li2 = (await Mock.invoice_line_item("10002", "1")).line_item;
  page("11-new-invoice", R.invoices({ screen: "invoices", status: dirty, invoices: invoiceList }), R.statusBar({ status: dirty }),
    R.invoiceModal({ invoiceForm: invForm, invoiceFields: { customer_id: "1", status: "Due", due_date: "2025-05-02", sales_tax_rate: "0.0625" }, lineItems: [li1, li2], invoiceTotals: await Mock.invoice_totals([li1, li2], "0.0625"), errors: [] }));
  const customerList = await Mock.customers("");
  page("12-customers", R.customers({ screen: "customers", status: dirty, customers: customerList, selectedCustomer: await Mock.customer("1") }), R.statusBar({ status: dirty }));
  const vendorList = await Mock.vendors("");
  page("13-vendors", R.vendors({ screen: "vendors", status: dirty, vendors: vendorList, selectedVendor: vendorList.vendors[0] }), R.statusBar({ status: dirty }),
    R.vendorModal({ fields: { name: "", email: "not-an-email" }, errors: [{ field: "name", message: "Vendor name is required." }, { field: "email", message: "Email 'not-an-email' does not look like an email address." }], message: "Please fix the highlighted fields." }));
  const serviceList = await Mock.services("");
  page("14-services", R.services({ screen: "services", status: dirty, services: serviceList, selectedService: serviceList.services[1] }), R.statusBar({ status: dirty }));
  const accounts = (await Mock.accounts()).accounts;
  const started = await Mock.reconcile_start("10002", "2025-02-28", "10,057.82");
  const partial = await Mock.reconcile_summary([4]);
  page("15-reconcile", R.reconcile({ screen: "reconcile", status: dirty, accountList: accounts, reconcile: { fields: { account: "10002", statement_date: "2025-02-28", statement_balance: "10,057.82" }, errors: [], data: partial } }), R.statusBar({ status: dirty }));
  page("16-properties", R.properties({ screen: "properties", status: dirty, properties: await Mock.properties_summary() }), R.statusBar({ status: dirty }));
  page("17-tools", R.dashboard({ screen: "dashboard", status: dirty, dashboard: dash }), R.statusBar({ status: dirty }), R.toolsMenu({ status: dirty }));
  page("18-backups", R.dashboard({ screen: "dashboard", status: dirty, dashboard: dash }), R.statusBar({ status: dirty }), R.backupsModal(await Mock.backups()));
})();

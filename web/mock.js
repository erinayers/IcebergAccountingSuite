/* Mock API with sample data so the interface can be previewed in a browser
   (open web/index.html) and rendered by the screenshot tool.  Mirrors api.py. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) { module.exports = factory(); } else { root.MockApi = factory(); }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var accounts = [["10001", "Fixed Asset Real Estate"], ["10002", "Fixed Asset Bank Account Checking"], ["10004", "Cash"], ["10006", "Accounts Receivable"],
    ["11001", "Office Supplies and Postage"], ["11010", "Rent or Lease of Real Property"], ["12001", "Owner Equity Withdrawals"],
    ["13002", "Accounts Payable"], ["13003", "Sales Tax Payable"], ["14001", "Owner Equity Deposits"], ["15001", "Sales"]];
  var names = {}; accounts.forEach(function (a) { names[a[0]] = a[1]; });
  var types = { "0": "Assets", "1": "Expenses", "2": "Equity Withdrawals", "3": "Liabilities", "4": "Owner Equity", "5": "Revenue" };
  var txs = [
    [1, "2025-01-02", "Owner investment", 1000000, "10002", "14001", "Seed money", "", "2025-01-31"],
    [2, "2025-01-05", "Office rent January", 120000, "11010", "10002", "Check 1041", "3 - Main St Properties", "2025-01-31"],
    [3, "2025-01-10", "Printer paper", 4218, "11001", "10002", "", "5 - Office Depot", "2025-01-31"],
    [4, "2025-02-01", "Office rent February", 120000, "11010", "10002", "Check 1042", "3 - Main St Properties", ""],
    [5, "2025-02-14", "Consulting fee", 250000, "10002", "15001", "Invoice 10003 paid by transfer", "", ""],
    [6, "2025-03-01", "Office rent March", 120000, "11010", "10002", "", "3 - Main St Properties", ""],
    [7, "2025-03-15", "Cash sale", 30000, "10004", "15001", "", "", ""],
    [8, "2025-03-20", "Owner draw", 50000, "12001", "10002", "", "", ""],
    [9, "2025-03-25", "Bought land", 500000, "10001", "10002", "Parcel 12-B", "", ""],
    [10, "2025-03-28", "Supplier on credit", 20000, "11001", "13002", "Net 30", "5 - Office Depot", ""]
  ].map(function (t) { return { id: t[0], date: t[1], name: t[2], amount: t[3], debit: t[4], debit_name: names[t[4]], credit: t[5], credit_name: names[t[5]],
    notes: t[6], vendor: t[7], customer: "", record_image: "", reconciled: t[8], created: "Sunday, 12/21/2025  -  17:47 (UTC-05:00)", edited: "Sunday, 12/21/2025  -  17:47 (UTC-05:00)" }; });
  var loaded = false, unsaved = false, lastSaved = "14:52 (UTC-05:00)", recon = null, prefs = { theme: "light", text_scale: 1, compact: false };
  var vendors = [
    { id: "3", name: "Main St Properties", category: "Landlord", first_name: "Dana", last_name: "Reyes", preferred_name: "", phone: "555-0101", phone_type: "Office", address: "12 Main St", email: "dana@mainst.example", website: "", notes: "Rent due on the 1st", created: "Sunday, 12/21/2025  -  17:52 (UTC-05:00)", edited: "Sunday, 12/21/2025  -  17:52 (UTC-05:00)" },
    { id: "5", name: "Office Depot", category: "Supplies", first_name: "", last_name: "", preferred_name: "", phone: "555-0199", phone_type: "Office", address: "", email: "", website: "officedepot.example", notes: "", created: "Sunday, 12/21/2025  -  17:53 (UTC-05:00)", edited: "Sunday, 12/21/2025  -  17:53 (UTC-05:00)" }
  ];
  var customers = [
    { id: "1", company: "Globex Corporation", first_name: "Hank", last_name: "Scorpio", preferred_name: "Hank", phone: "555-0110", phone_type: "Mobile", address: "1 Volcano Lane\nCypress Creek", email: "hank@globex.example", notes: "", display_name: "Globex Corporation", contact: "Hank Scorpio", balance: 690363, created: "Sunday, 12/21/2025  -  17:51 (UTC-05:00)", edited: "Sunday, 12/21/2025  -  17:51 (UTC-05:00)" },
    { id: "2", company: "", first_name: "Pauli", last_name: "Portabello", preferred_name: "", phone: "555-0120", phone_type: "Home", address: "9 Fungus Way", email: "pauli@example.com", notes: "Prefers email", display_name: "Pauli Portabello", contact: "Pauli Portabello", balance: 0, created: "Monday, 12/22/2025  -  09:10 (UTC-05:00)", edited: "Monday, 12/22/2025  -  09:10 (UTC-05:00)" }
  ];
  var services = [
    { sku: "10001", description: "Consulting hour", long_description: "Hourly consulting", price: 15000, taxable: false, created: "Sunday, 12/21/2025  -  17:55 (UTC-05:00)", edited: "Sunday, 12/21/2025  -  17:55 (UTC-05:00)" },
    { sku: "10002", description: "Network installation", long_description: "Per site", price: 120000, taxable: true, created: "Sunday, 12/21/2025  -  17:56 (UTC-05:00)", edited: "Sunday, 12/21/2025  -  17:56 (UTC-05:00)" }
  ];
  var invoices = [
    { id: 10001, customer_id: "1", customer_name: "Globex Corporation", customer_contact: "Hank Scorpio", customer_phone: "555-0110", customer_email: "hank@globex.example", tracking_code: "Q7V2KD0P4MZ1", line_items: [["10002", "Network installation", "$1,200.00", "1", "$1,200.00"]], due_date: "2025-01-21", subtotal: 120000, sales_tax: 7500, total: 127500, status: "Paid", location: "/receipts/Invoices/10001/10001.pdf", created: "Sunday, 12/21/2025  -  18:09 (UTC-05:00)", created_date: "2025-12-21", edited: "Monday, 12/22/2025  -  09:00 (UTC-05:00)", allowed_transitions: ["Refunded"] },
    { id: 10002, customer_id: "1", customer_name: "Globex Corporation", customer_contact: "Hank Scorpio", customer_phone: "555-0110", customer_email: "hank@globex.example", tracking_code: "A1B2C3D4E5F6", line_items: [["10001", "Consulting hour", "$150.00", "40", "$6,000.00"], ["10002", "Network installation", "$1,200.00", "0.5", "$600.00"]], due_date: "2026-01-20", subtotal: 660000, sales_tax: 3750, total: 663750, status: "Due", location: "", created: "Sunday, 12/21/2025  -  18:30 (UTC-05:00)", created_date: "2025-12-21", edited: "Sunday, 12/21/2025  -  18:30 (UTC-05:00)", allowed_transitions: ["Canceled", "Overdue", "Paid"] },
    { id: 10003, customer_id: "2", customer_name: "Pauli Portabello", customer_contact: "Pauli Portabello", customer_phone: "555-0120", customer_email: "pauli@example.com", tracking_code: "ZZ9PLURAL7", line_items: [["10001", "Consulting hour", "$150.00", "2", "$300.00"]], due_date: "2025-12-01", subtotal: 30000, sales_tax: 0, total: 30000, status: "Overdue", location: "", created: "Monday, 12/22/2025  -  09:12 (UTC-05:00)", created_date: "2025-12-22", edited: "Tuesday, 12/30/2025  -  08:00 (UTC-05:00)", allowed_transitions: ["Canceled", "Paid"] }
  ];
  function money(c) { var n = Math.abs(Math.round(c)); var t = "$" + Math.floor(n / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") + "." + ("0" + (n % 100)).slice(-2); return c < 0 ? "(" + t + ")" : t; }
  function ok(extra) { var o = { ok: true, message: "", errors: [] }; Object.keys(extra || {}).forEach(function (k) { o[k] = extra[k]; }); return Promise.resolve(o); }
  function balances() {
    var b = {}; accounts.forEach(function (a) { b[a[0]] = { debits: 0, credits: 0 }; });
    txs.forEach(function (t) { b[t.debit].debits += t.amount; b[t.credit].credits += t.amount; });
    return b;
  }
  function chart(prefix, year) {
    var b = balances();
    return accounts.filter(function (a) { return !prefix || a[0].indexOf(prefix) === 0; }).map(function (a) {
      var d = b[a[0]].debits, c = b[a[0]].credits, debitNormal = "012".indexOf(a[0][1]) >= 0;
      return { id: a[0], name: a[1], type: types[a[0][1]], debits: d, credits: c, balance: debitNormal ? d - c : c - d, institution: a[0] === "10002" ? "First Community Bank" : "" };
    });
  }
  function summary() {
    var by = { "0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 };
    chart().forEach(function (a) { by[a.id[1]] += a.balance; });
    var total = txs.reduce(function (s, t) { return s + t.amount; }, 0);
    return { total_debits: total, total_credits: total, in_balance: true, assets: by["0"], expenses: by["1"], withdrawals: by["2"], liabilities: by["3"], owner_equity: by["4"], revenue: by["5"],
      net_assets: by["0"] - by["3"], total_equity: by["4"] + by["5"] - by["1"] - by["2"], retained_earnings: by["5"] - by["1"] - by["2"], business_income: by["5"] - by["1"], transaction_count: txs.length };
  }
  return {
    status: function () { return Promise.resolve({ version: "2.0 (web preview, sample data)", database_loaded: loaded, db_name: loaded ? "Alpha_Corporation.icb" : "", business_name: loaded ? "Alpha Corporation" : "", unsaved: unsaved, last_saved: lastSaved, autosave_in: 221, clock: "Saturday, 10/31/2026  -  14:52 (UTC-04:00)", console: [] }); },
    recent_databases: function () { return Promise.resolve([{ db_name: "Alpha_Corporation.icb", label: "Alpha Corporation", modified: "Saturday, 10/31/2026  -  14:52 (UTC-04:00)", size: 103864, backups: 12 }, { db_name: "Basile_Kemp_House.icb", label: "Basile Kemp House", modified: "Friday, 10/24/2026  -  09:10 (UTC-04:00)", size: 88211, backups: 3 }]); },
    pick_key_file: function () { return Promise.resolve("/keys/Alpha_Corporation.icbkey"); },
    pick_folder: function () { return Promise.resolve("/home/you/Documents/Iceberg"); },
    pick_file: function () { return Promise.resolve("/home/you/Receipts/2025/receipt.png"); },
    open_path: function () { return ok(); },
    open_database: function () { loaded = true; return ok({ message: "Opened Alpha_Corporation.icb." }); },
    create_database: function (f) {
      if (!f.business_name) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: [{ field: "business_name", message: "Business name is required." }, { field: "sales_tax", message: "Sales tax 'six' is not a number. Enter the percentage, e.g. 6.25 (or 0 if you do not collect it)." }] }); }
      loaded = true; return ok({ message: "Created " + f.business_name + ".icb. Keep the filekey safe." });
    },
    save: function () { unsaved = false; return ok({ message: "Manual save: saved Alpha_Corporation.icb and wrote a backup." }); },
    autosave_if_due: function () { return ok(); },
    shutdown: function () { return ok(); },
    dashboard: function (prefix, year) { return ok({ summary: summary(), accounts: chart(prefix, year), years: ["2025"], business: { business_name: "Alpha Corporation", address: "488 E Main St, Anytown", owner_name: "Joseph Basile" }, filters: { type_prefix: prefix || "", year: year || "" } }); },
    accounts: function () { return ok({ accounts: accounts.map(function (a) { return { id: a[0], name: a[1], type: types[a[0][1]] }; }) }); },
    account_register: function (id) {
      var bal = 0, rows = [];
      txs.forEach(function (t) { if (t.debit !== id && t.credit !== id) { return; } var dn = "012".indexOf(id[1]) >= 0; var e = (t.debit === id ? t.amount : -t.amount) * (dn ? 1 : -1); bal += e; var r = Object.assign({}, t, { effect: e, running_balance: bal }); rows.push(r); });
      rows.reverse();
      return ok({ account: { id: id, name: names[id], type: types[id[1]], institution: id === "10002" ? "First Community Bank" : "", notes: "", balance: bal }, rows: rows });
    },
    ledger: function (search, year) {
      var term = (search || "").toLowerCase();
      var rows = txs.filter(function (t) { return (!year || t.date.indexOf(year) === 0) && (!term || (t.name + t.notes + t.debit + t.credit + t.vendor).toLowerCase().indexOf(term) >= 0); });
      rows = rows.slice().sort(function (a, b) { return b.date.localeCompare(a.date) || b.id - a.id; });
      return ok({ rows: rows, years: ["2025"], total: txs.length, filters: { search: search || "", year: year || "" } });
    },
    transaction: function (id) { var t = txs.filter(function (x) { return x.id === Number(id); })[0]; return t ? ok({ transaction: t }) : Promise.resolve({ ok: false, message: "Not found", errors: [] }); },
    transaction_form: function () { return ok({ next_id: txs.length + 1, today: "2025-04-02", accounts: accounts.map(function (a) { return { id: a[0], name: a[1] }; }), vendors: [{ id: "3", name: "Main St Properties" }, { id: "5", name: "Office Depot" }] }); },
    add_transaction: function (f, confirm) {
      var errors = [];
      if (!f.name) { errors.push({ field: "name", message: "Transaction name is required." }); }
      if (!f.amount || isNaN(Number(String(f.amount).replace(/[$,]/g, "")))) { errors.push({ field: "amount", message: "Amount '" + f.amount + "' is not a number. Use digits with an optional decimal point, e.g. 125.00." }); }
      if (!f.debit_account) { errors.push({ field: "debit_account", message: "Debit account is required." }); }
      if (f.debit_account && f.debit_account === f.credit_account) { errors.push({ field: "credit_account", message: "Debit and credit accounts must be different." }); }
      if (errors.length) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: errors, warnings: [] }); }
      var dup = txs.filter(function (t) { return t.name === f.name && t.date === f.date; })[0];
      if (dup && !confirm) { return Promise.resolve({ ok: false, message: "Please confirm before saving.", errors: [], warnings: ["A transaction with the same name, date, amount, and accounts already exists (Transaction " + dup.id + ")."], needs_confirmation: true }); }
      var id = txs.length + 1;
      txs.push({ id: id, date: f.date, name: f.name, amount: Math.round(Number(String(f.amount).replace(/[$,]/g, "")) * 100), debit: f.debit_account, debit_name: names[f.debit_account], credit: f.credit_account, credit_name: names[f.credit_account], notes: f.notes || "", vendor: f.vendor || "", customer: "", record_image: f.record_image || "", reconciled: "", created: "now", edited: "now" });
      unsaved = true;
      return ok({ message: "Transaction " + id + " '" + f.name + "' recorded.", id: id });
    },
    update_transaction: function (id, f) { unsaved = true; return ok({ message: "Transaction " + id + " updated.", id: Number(id) }); },
    report_periods: function () { return ok({ presets: [{ name: "This Year", start: "2025-01-01", end: "2025-12-31" }, { name: "Year to Date", start: "2025-01-01", end: "2025-04-02" }, { name: "Last Quarter", start: "2025-01-01", end: "2025-03-31" }], types: ["Income Statement", "Income Statement by Month", "Balance Sheet", "Cash Flow"] }); },
    pick_save_file: function (name) { return Promise.resolve("/home/you/Documents/" + name); },
    open_docs: function () { return ok(); },
    open_data_folder: function () { return ok(); },
    paths: function () { return ok({ paths: { mode: "user", root: "C:\\Users\\you\\AppData\\Local\\Iceberg", databases: "C:\\Users\\you\\AppData\\Local\\Iceberg\\databases", backups: "C:\\Users\\you\\AppData\\Local\\Iceberg\\backups", logs: "C:\\Users\\you\\AppData\\Local\\Iceberg\\logs", log_file: "C:\\Users\\you\\AppData\\Local\\Iceberg\\logs\\iceberg.log", preferences: "C:\\Users\\you\\AppData\\Local\\Iceberg\\preferences.json", program: "C:\\Program Files\\Iceberg" }, portable: false }); },
    /* ---- accounts */
    account_form: function () { return ok({ types: [["10", "Assets"], ["11", "Expenses"], ["12", "Equity Withdrawals"], ["13", "Liabilities"], ["14", "Owner Equity"], ["15", "Revenue"]].map(function (t) { return { prefix: t[0], label: t[1] }; }), bank_account_types: ["", "Checking", "Savings", "Passbook", "Certificate of Deposit"] }); },
    account: function (id) { return names[id] ? ok({ account: { id: id, name: names[id], type: types[id[1]], type_prefix: id.slice(0, 2), notes: "", institution: id === "10002" ? "First Community Bank" : "", bank_account_type: id === "10002" ? "Checking" : "", routing_number: "", account_number: "" } }) : Promise.resolve({ ok: false, message: "Account " + id + " does not exist.", errors: [] }); },
    add_account: function (f) { if (!f.name) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: [{ field: "name", message: "Account name is required." }] }); } var id = f.type_prefix + "099"; accounts.push([id, f.name]); names[id] = f.name; unsaved = true; return ok({ message: "Account " + id + " '" + f.name + "' added.", id: id }); },
    update_account: function (id, f) { names[id] = f.name; unsaved = true; return ok({ message: "Account " + id + " updated.", id: id }); },
    /* ---- vendors / customers / services */
    vendors: function (search) { var list = vendors.filter(function (v) { return !search || (v.name + v.category).toLowerCase().indexOf(search.toLowerCase()) >= 0; }); return ok({ vendors: list, phone_types: ["Mobile", "Home", "Office", "Work", "Other"], filters: { search: search || "" } }); },
    vendor: function (id) { var v = vendors.filter(function (x) { return x.id === String(id); })[0]; return v ? ok({ vendor: v }) : Promise.resolve({ ok: false, message: "Vendor not found", errors: [] }); },
    save_vendor: function (f, id) { if (!f.name) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: [{ field: "name", message: "Vendor name is required." }] }); } if (id) { var v = vendors.filter(function (x) { return x.id === String(id); })[0]; Object.assign(v, f); return ok({ message: "Vendor '" + f.name + "' updated.", id: id }); } var nid = String(vendors.length + 1); vendors.push(Object.assign({ id: nid, created: "now", edited: "now" }, f)); unsaved = true; return ok({ message: "Vendor '" + f.name + "' added.", id: nid }); },
    customers: function (search) { var list = customers.filter(function (c) { return !search || (c.display_name + c.contact + c.email).toLowerCase().indexOf(search.toLowerCase()) >= 0; }); return ok({ customers: list, phone_types: ["Mobile", "Home", "Office", "Work", "Other"], filters: { search: search || "" } }); },
    customer: function (id) { var c = customers.filter(function (x) { return x.id === String(id); })[0]; return c ? ok({ customer: c, invoices: invoices.filter(function (i) { return i.customer_id === c.id; }) }) : Promise.resolve({ ok: false, message: "Customer not found", errors: [] }); },
    save_customer: function (f, id) {
      var errors = []; if (!f.company && !f.first_name && !f.last_name) { errors.push({ field: "company", message: "Enter a company name or a contact first/last name." }); } if (!f.address) { errors.push({ field: "address", message: "Customer address is required (it is printed on invoices)." }); }
      if (errors.length) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: errors }); }
      var rec = Object.assign({ display_name: f.company || (f.first_name + " " + f.last_name).trim(), contact: ((f.first_name || "") + " " + (f.last_name || "")).trim(), balance: 0, created: "now", edited: "now" }, f);
      if (id) { Object.assign(customers.filter(function (x) { return x.id === String(id); })[0], rec); return ok({ message: "Customer updated.", id: id }); }
      rec.id = String(customers.length + 1); customers.push(rec); unsaved = true; return ok({ message: "Customer added.", id: rec.id });
    },
    services: function (search) { var list = services.filter(function (s) { return !search || (s.sku + s.description).toLowerCase().indexOf(search.toLowerCase()) >= 0; }); return ok({ services: list, filters: { search: search || "" } }); },
    save_service: function (f, sku) {
      var errors = []; if (!f.description) { errors.push({ field: "description", message: "Service description is required." }); } if (isNaN(Number(String(f.price).replace(/[$,]/g, "")))) { errors.push({ field: "price", message: "Price '" + f.price + "' is not a number." }); }
      if (errors.length) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: errors }); }
      var rec = { description: f.description, long_description: f.long_description || "", price: Math.round(Number(String(f.price).replace(/[$,]/g, "")) * 100), taxable: String(f.taxable) === "True", created: "now", edited: "now" };
      if (sku) { Object.assign(services.filter(function (x) { return x.sku === String(sku); })[0], rec); return ok({ message: "Service '" + f.description + "' updated.", id: sku }); }
      rec.sku = String(10000 + services.length + 1); services.push(rec); unsaved = true; return ok({ message: "Service '" + f.description + "' added.", id: rec.sku });
    },
    /* ---- invoices */
    invoices: function (search) { var list = invoices.filter(function (i) { return !search || (String(i.id) + i.customer_name + i.status).toLowerCase().indexOf(search.toLowerCase()) >= 0; }); return ok({ invoices: list.slice().reverse(), filters: { search: search || "" } }); },
    invoice: function (id) {
      var inv = invoices.filter(function (i) { return i.id === Number(id); })[0];
      if (!inv) { return Promise.resolve({ ok: false, message: "Invoice " + id + " was not found.", errors: [] }); }
      var hist = [["Sunday, 12/21/2025  -  18:30 (UTC-05:00)", "Invoice created", inv.status === "Paid" ? "Due" : inv.status, money(inv.total), "10006 Accounts Receivable", "13, 14"]];
      if (inv.status === "Paid") { hist.push(["Monday, 12/22/2025  -  09:00 (UTC-05:00)", "Payment received", "Due -> Paid", money(inv.total), "10002 Fixed Asset Bank Account Checking", "15, 16"]); }
      return ok({ invoice: inv, history: hist, asset_accounts: accounts.filter(function (a) { return a[0][1] === "0" && a[0] !== "10006"; }).map(function (a) { return { id: a[0], name: a[1] }; }) });
    },
    invoice_form: function () { return ok({ next_id: 10000 + invoices.length + 1, today: "2025-04-02", sales_tax_rate: "0.0625", customers: customers, services: services, asset_accounts: accounts.filter(function (a) { return a[0][1] === "0" && a[0] !== "10006"; }).map(function (a) { return { id: a[0], name: a[1] }; }), statuses: ["Due", "Overdue", "Paid"], max_line_items: 10 }); },
    invoice_totals: function (items, rate) {
      var sub = 0, tax = 0, r = Number(rate === undefined || rate === "" ? 0.0625 : rate);
      (items || []).forEach(function (li) { var c = Math.round(Number(String(li[4]).replace(/[$,]/g, "")) * 100); sub += c; var svc = services.filter(function (s) { return s.sku === li[0]; })[0]; if (svc && svc.taxable) { tax += Math.round(c * r); } });
      return ok({ subtotal: sub, sales_tax: tax, total: sub + tax });
    },
    invoice_line_item: function (sku, qty) {
      var svc = services.filter(function (s) { return s.sku === String(sku); })[0]; var q = Number(qty);
      var errors = []; if (!svc) { errors.push({ field: "sku", message: "Select a service from the search results before adding a line item." }); } if (!(q > 0)) { errors.push({ field: "quantity", message: "Quantity must be greater than zero." }); }
      if (errors.length) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: errors }); }
      return ok({ line_item: [svc.sku, svc.description, money(svc.price), String(q), money(Math.round(q * svc.price))] });
    },
    create_invoice: function (f, items) {
      var errors = []; if (!f.customer_id) { errors.push({ field: "customer", message: "Select a customer from the list." }); } if (!items.length) { errors.push({ field: "line_items", message: "Add at least one line item." }); }
      if (f.status === "Paid" && !f.deposit_account) { errors.push({ field: "deposit_account", message: "Deposit account is required." }); }
      if (errors.length) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: errors }); }
      var c = customers.filter(function (x) { return x.id === String(f.customer_id); })[0];
      var sub = 0; items.forEach(function (li) { sub += Math.round(Number(String(li[4]).replace(/[$,]/g, "")) * 100); });
      var id = 10000 + invoices.length + 1;
      invoices.push({ id: id, customer_id: c.id, customer_name: c.display_name, customer_contact: c.contact, customer_phone: c.phone, customer_email: c.email, tracking_code: "MOCK" + id, line_items: items, due_date: f.due_date, subtotal: sub, sales_tax: 0, total: sub, status: f.status, location: "", created: "now", created_date: "2025-04-02", edited: "now", allowed_transitions: f.status === "Paid" ? ["Refunded"] : ["Canceled", "Overdue", "Paid"] });
      unsaved = true; return ok({ message: "Invoice " + id + " created. PDF saved to /receipts/Invoices/" + id + "/" + id + ".pdf.", id: id, pdf: "/receipts/Invoices/" + id + "/" + id + ".pdf", ledger_entries: [txs.length + 1] });
    },
    change_invoice_status: function (id, status, account) {
      var inv = invoices.filter(function (i) { return i.id === Number(id); })[0];
      if ((status === "Paid" || status === "Refunded") && !account) { return Promise.resolve({ ok: false, message: "Select the " + (status === "Paid" ? "deposit" : "refund source") + " account.", errors: [] }); }
      inv.status = status; inv.allowed_transitions = status === "Paid" ? ["Refunded"] : status === "Overdue" ? ["Canceled", "Paid"] : []; unsaved = true;
      return ok({ message: "Invoice " + id + ": " + status + ". Ledger entries: 21, 22. PDF saved.", id: Number(id), status: status, pdf: "" });
    },
    invoice_pdf_path: function (id) { return ok({ path: "/receipts/Invoices/" + id + "/" + id + ".pdf" }); },
    /* ---- reconcile */
    reconcile_start: function (account, date, balance) {
      var errors = []; if (!account) { errors.push({ field: "account", message: "Select an account." }); } if (!date) { errors.push({ field: "statement_date", message: "Statement date is required." }); } if (!balance || isNaN(Number(String(balance).replace(/[$,]/g, "")))) { errors.push({ field: "statement_balance", message: "Statement balance '" + balance + "' is not a number." }); }
      if (errors.length) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: errors }); }
      recon = { account: account, date: date, balance: Math.round(Number(String(balance).replace(/[$,]/g, "")) * 100), cleared: [] };
      return this.reconcile_summary([]);
    },
    reconcile_summary: function (ids) {
      if (!recon) { return Promise.resolve({ ok: false, message: "Load the statement first.", errors: [] }); }
      var dn = "012".indexOf(recon.account[1]) >= 0;
      var candidates = txs.filter(function (t) { return (t.debit === recon.account || t.credit === recon.account) && t.date <= recon.date && !t.reconciled; }).map(function (t) { return { Transaction_ID: t.id, Transaction_Date: t.date, Name: t.name, Amount: (t.debit === recon.account ? t.amount : -t.amount) * (dn ? 1 : -1), Counter_Account: t.debit === recon.account ? t.credit : t.debit }; });
      var reconciled = txs.filter(function (t) { return (t.debit === recon.account || t.credit === recon.account) && t.reconciled; });
      var reconciledBalance = reconciled.reduce(function (s, t) { return s + (t.debit === recon.account ? t.amount : -t.amount) * (dn ? 1 : -1); }, 0);
      var cleared = candidates.filter(function (c) { return ids.indexOf(c.Transaction_ID) >= 0; }), unmatched = candidates.filter(function (c) { return ids.indexOf(c.Transaction_ID) < 0; });
      var clearedTotal = cleared.reduce(function (s, c) { return s + c.Amount; }, 0);
      var summary = { statement_balance: recon.balance, reconciled_balance: reconciledBalance, cleared_total: clearedTotal, cleared_count: cleared.length, cleared_balance: reconciledBalance + clearedTotal, difference: recon.balance - reconciledBalance - clearedTotal, cleared: cleared, unmatched: unmatched, unmatched_total: unmatched.reduce(function (s, c) { return s + c.Amount; }, 0) };
      summary.balanced = summary.difference === 0;
      return ok({ session: { account_id: recon.account, statement_date: recon.date, reconciled_count: reconciled.length, later_reconciled: 0 }, candidates: candidates, summary: summary, cleared_ids: ids });
    },
    reconcile_finish: function (ids) { ids.forEach(function (id) { txs.filter(function (t) { return t.id === id; })[0].reconciled = recon.date; }); var n = ids.length; recon = null; return ok({ message: "Reconciled: " + n + " transactions cleared.", cleared_count: n }); },
    reconcile_history: function () { return ok({ history: [{ id: 1, account_id: "10002", statement_date: "2025-01-31", statement_balance: 875782, cleared_count: 3, recorded: "Saturday, 02/01/2025  -  10:12 (UTC-05:00)" }] }); },
    reconcile_undo: function () { return ok({ message: "Undid the reconciliation for statement 2025-01-31." }); },
    /* ---- properties / backups / exchange / prefs */
    properties_summary: function () { return Promise.resolve({ business_name: "Alpha Corporation", address: "488 E Main St\nAnytown", owner_name: "Joseph Basile", owner_title: "Owner", phone: "555-0100", email: "joe@alpha.example", notes: "", ein: "", receipts_location: "C:\\Users\\you\\Receipts", ledger_name: "tbl_ledger_Alpha_Corporation_CY2025", sales_tax: "0.0625" }); },
    update_properties: function (f) { if (!f.business_name) { return Promise.resolve({ ok: false, message: "Please fix the highlighted fields.", errors: [{ field: "business_name", message: "Business name is required." }] }); } return ok({ message: "Database properties saved.", properties: Object.assign({ ledger_name: "tbl_ledger_Alpha_Corporation_CY2025", sales_tax: "0.0625" }, f) }); },
    backups: function () { return ok({ folder: "C:\\Iceberg\\backups\\Alpha_Corporation", backups: [{ path: "/b/Alpha_Corporation_20261031T185220Z.icb", label: "Saturday, 10/31/2026  -  14:52:20 (UTC-04:00)", name: "Alpha_Corporation_20261031T185220Z.icb", size: 103864 }, { path: "/b/Alpha_Corporation_20261031T184703Z.icb", label: "Saturday, 10/31/2026  -  14:47:03 (UTC-04:00)", name: "Alpha_Corporation_20261031T184703Z.icb", size: 103112 }] }); },
    restore_backup: function (p) { return ok({ message: "Restored from " + p.split("/").pop() + ". The previous file was kept as a backup.", safety_copy: "/b/safety.icb" }); },
    export_ledger: function (p) { return ok({ message: "Exported " + txs.length + " transactions to " + p + ".", count: txs.length, path: p }); },
    export_all: function (f) { return ok({ message: "Exported 7 files to " + f + ".", files: {} }); },
    export_report: function (p) { return ok({ message: "Report exported to " + p + ".", path: p }); },
    import_transactions: function (p, confirm) { if (/bad/.test(p)) { return Promise.resolve({ ok: false, message: "2 problem(s) found; nothing was imported.", errors: [], problems: ["Line 3: Amount 'abc' is not a number.", "Line 5: Debit account 19999 does not exist in the chart of accounts."] }); } if (!confirm) { return ok({ message: "4 transaction(s) are ready to import.", preview: 4, warnings: ["Line 2: A transaction with the same name, date, amount, and accounts already exists (Transaction 3)."], needs_confirmation: true }); } unsaved = true; return ok({ message: "Imported 4 transactions.", imported: 4, transaction_ids: [11, 12, 13, 14] }); },
    import_template: function (p) { return ok({ message: "Template written to " + p + ".", path: p }); },
    preferences: function () { return ok({ preferences: prefs, themes: ["light", "dark", "high-contrast"], text_scales: [{ value: 0.85, label: "Smaller" }, { value: 1, label: "Default" }, { value: 1.15, label: "Larger" }, { value: 1.3, label: "Large" }, { value: 1.5, label: "Extra large" }] }); },
    save_preferences: function (p) { prefs = { theme: p.theme || "light", text_scale: Number(p.text_scale) || 1, compact: !!p.compact }; return ok({ message: "Preferences saved.", preferences: prefs }); },
    console: function () { return ok({ lines: ["Console (Saturday, 10/31/2026  -  14:52:08 (UTC-04:00)): Database opened: Alpha_Corporation.icb", "Console (Saturday, 10/31/2026  -  14:52:05 (UTC-04:00)): Welcome to Iceberg Accounting Suite! Create or open a database to get started."] }); },
    report: function (type, start, end) {
      return ok({ report: { title: type, period: start + " to " + end }, text: type + "\nPeriod: " + start + " to " + end + "\n\nREVENUE\n    15001 Sales                                    $2,800.00\n  Total Revenue                                    $2,800.00\n\nEXPENSES\n    11001 Office Supplies and Postage                $242.18\n    11010 Rent or Lease of Real Property           $3,600.00\n  Total Expenses                                   $3,842.18\n\nNet Loss                                        ($1,042.18)" });
    }
  };
});

/* Pure view functions: (data) -> HTML string.  No DOM access, no API calls,
   so the same file runs in the webview, in Node for unit tests, and in the
   screenshot tool.  All user data passes through esc(). */
(function (root, factory) {
  if (typeof module === "object" && module.exports) { module.exports = factory(); }
  else { root.Render = factory(); }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var NAV = [
    { id: "dashboard", label: "Dashboard", key: "1" },
    { id: "ledger", label: "Ledger", key: "2" },
    { id: "invoices", label: "Invoices", key: "3" },
    { id: "customers", label: "Customers", key: "4" },
    { id: "vendors", label: "Vendors", key: "5" },
    { id: "services", label: "Services", key: "6" },
    { id: "reports", label: "Reports", key: "7" },
    { id: "reconcile", label: "Reconcile", key: "8" }
  ];
  var WORKSPACES = ["dashboard", "ledger", "invoices", "customers", "vendors", "services", "reports", "reconcile", "account", "properties"];
  var TYPE_FILTERS = [["", "All accounts"], ["10", "Assets"], ["11", "Expenses"], ["12", "Withdrawals"], ["13", "Liabilities"], ["14", "Owner equity"], ["15", "Revenue"]];

  function esc(value) {
    return String(value === null || value === undefined ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function money(cents, symbol) {
    symbol = symbol === undefined ? "$" : symbol;
    var n = Math.round(Number(cents) || 0);
    var negative = n < 0;
    n = Math.abs(n);
    var dollars = Math.floor(n / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    var text = symbol + dollars + "." + ("0" + (n % 100)).slice(-2);
    return negative ? "(" + text + ")" : text;
  }

  function moneyCell(cents, extraClass) {
    var cls = "num" + (Number(cents) < 0 ? " negative" : "") + (extraClass ? " " + extraClass : "");
    return '<td class="' + cls + '">' + money(cents) + "</td>";
  }

  function pill(text, kind) { return '<span class="pill ' + esc(kind || "neutral") + '">' + esc(text) + "</span>"; }

  var ICONS = { check: "Success", cross: "Error", warning: "Warning", back: "Back", forward: "Open", play: "Run", terminal: "Console", screen: "Database", tools: "Tools" };
  var MONO_ICONS = { back: true, forward: true, play: true, terminal: true, screen: true, tools: true };

  /* An icon from web/icons (the design's icon sheet).  Decorative unless a label is given. */
  function icon(name, label, size) {
    var cls = "icon icon-" + name + (MONO_ICONS[name] ? " icon-mono" : "") + (size ? " icon-" + size : "");
    var text = label === undefined ? ICONS[name] || name : label;
    return '<span class="' + cls + '" role="img" aria-label="' + esc(text) + '" title="' + esc(text) + '"></span>';
  }
  var KIND_ICON = { ok: "check", bad: "cross", warn: "warning" };

  function errorFor(errors, field) {
    if (!errors) { return ""; }
    for (var i = 0; i < errors.length; i++) { if (errors[i].field === field) { return errors[i].message; } }
    return "";
  }

  function field(opts) {
    var err = errorFor(opts.errors, opts.name);
    var html = '<div class="field' + (err ? " invalid" : "") + (opts.narrow ? " narrow" : "") + '">';
    html += '<label for="f-' + esc(opts.name) + '">' + esc(opts.label) + (opts.required ? '<span class="req">*</span>' : "") + "</label>";
    var attrs = ' id="f-' + esc(opts.name) + '" name="' + esc(opts.name) + '"' + (opts.placeholder ? ' placeholder="' + esc(opts.placeholder) + '"' : "") + (opts.autofocus ? " autofocus" : "");
    if (opts.type === "select") {
      html += "<select" + attrs + ">";
      (opts.options || []).forEach(function (o) {
        var v = Array.isArray(o) ? o[0] : o.value, l = Array.isArray(o) ? o[1] : o.label;
        html += '<option value="' + esc(v) + '"' + (String(v) === String(opts.value || "") ? " selected" : "") + ">" + esc(l) + "</option>";
      });
      html += "</select>";
    } else if (opts.type === "textarea") {
      html += "<textarea" + attrs + ' rows="' + (opts.rows || 3) + '">' + esc(opts.value || "") + "</textarea>";
    } else if (opts.browse) {
      html += '<div class="input-group"><input type="text"' + attrs + ' value="' + esc(opts.value || "") + '" />' +
        '<button type="button" class="btn btn-secondary btn-sm" data-action="' + esc(opts.browse) + '" data-target="' + esc(opts.name) + '">Browse…</button></div>';
    } else {
      html += '<input type="' + esc(opts.type || "text") + '"' + attrs + ' value="' + esc(opts.value || "") + '" />';
    }
    if (err) { html += '<div class="error">' + icon("cross", "", "sm") + " " + esc(err) + "</div>"; }
    else if (opts.hint) { html += '<div class="hint">' + esc(opts.hint) + "</div>"; }
    return html + "</div>";
  }

  function alertBox(kind, title, items) {
    if (!title && !(items && items.length)) { return ""; }
    var html = '<div class="form-alert ' + esc(kind) + '">' + (KIND_ICON[kind] ? icon(KIND_ICON[kind], "") + " " : "") + esc(title || "");
    if (items && items.length) { html += "<ul>" + items.map(function (i) { return "<li>" + esc(i) + "</li>"; }).join("") + "</ul>"; }
    return html + "</div>";
  }

  function accountOptions(accounts, selected) {
    return [["", "Select an account…"]].concat((accounts || []).map(function (a) { return [a.id, a.id + " · " + a.name]; }));
  }

  /* ---------------------------------------------------------------- welcome */

  function welcome(state) {
    var count = (state.databases || []).length;
    return '<section class="screen" id="screen-welcome"><div class="hero">' +
      "<h1>Iceberg</h1>" +
      '<p class="sub">Books and invoicing for individuals and small businesses. Your records stay in one encrypted file on this computer.</p>' +
      '<div class="cta-row"><button class="btn btn-primary" data-action="go" data-screen="create">Create New Database</button>' +
      '<button class="btn btn-secondary" data-action="open-database">Open Database…</button></div>' +
      (count ? '<button class="welcome-link" data-action="go" data-screen="databases">You have ' + count + " database" + (count === 1 ? "" : "s") + " in this folder · View them →</button>" : "") +
      '</div><div class="footer-note">Iceberg Accounting Suite ' + esc(state.version || "") + " · encrypted with your filekey</div></section>";
  }

  function databases(state) {
    var list = state.databases || [];
    var cards = list.map(function (d) {
      var isOpen = state.status && state.status.database_loaded && state.status.db_name === d.db_name;
      return '<div class="card"><div class="card-top"><div class="card-id"><div class="card-icon">' + icon("screen", "", "lg") + '</div><div>' +
        '<div class="card-name">' + esc(d.label) + '</div><div class="card-meta">' + esc(d.db_name) + " · " + (d.backups || 0) + " backup" + (d.backups === 1 ? "" : "s") + "</div></div></div>" +
        pill(isOpen ? "● Open" : "● Closed", isOpen ? "ok" : "neutral") + "</div>" +
        '<div class="card-foot"><span class="card-time">Saved ' + esc(d.modified) + "</span><div class=\"card-buttons\">" +
        (isOpen ? '<button class="btn btn-primary btn-sm" data-action="go" data-screen="dashboard">Continue ' + icon("forward", "", "sm") + '</button>'
                : '<button class="btn btn-primary btn-sm" data-action="open-database" data-db="' + esc(d.db_name) + '">Open ' + icon("forward", "", "sm") + '</button>') +
        "</div></div></div>";
    }).join("");
    return '<section class="screen" id="screen-databases"><div class="page"><div class="dash-header"><div><h1>Your Databases</h1>' +
      "<p>Open a set of books with its filekey, or start a new one.</p></div>" +
      '<div class="dash-actions"><button class="btn btn-secondary" data-action="open-database">Open Database…</button>' +
      '<button class="btn btn-primary" data-action="go" data-screen="create">+ Create New Database</button></div></div>' +
      '<div class="card-grid">' + (cards || '<div class="empty">No databases in the Iceberg folder yet.</div>') + "</div></div>" +
      '<div class="footer-note">Databases (.icb) live in the Iceberg folder; filekeys (.icbkey) live wherever you saved them.</div></section>';
  }

  /* ---------------------------------------------------------------- create */

  function createForm(state) {
    var f = state.fields || {}, errors = state.errors || [];
    return '<section class="screen" id="screen-create"><div class="page">' +
      '<button class="back-link" data-action="go" data-screen="welcome">' + icon("back", "") + ' Back</button>' +
      '<div class="page-head"><h1>Create New Database</h1><p>Tell Iceberg about the business. You can change everything later under Database Properties.</p></div>' +
      '<div class="workspace-scroll">' + alertBox("bad", state.message, []) +
      '<div class="form-columns"><div class="panel"><div class="panel-head"><h3>Business</h3><span class="form-legend"><span class="req">*</span> required</span></div><div class="panel-body">' +
      field({ name: "business_name", label: "Business name", required: true, value: f.business_name, errors: errors, autofocus: true, hint: "Also used as the database file name." }) +
      field({ name: "address", label: "Address", required: true, type: "textarea", rows: 2, value: f.address, errors: errors, hint: "Printed on invoices." }) +
      '<div class="field-row">' + field({ name: "owner_name", label: "Owner or financial officer", value: f.owner_name, errors: errors }) +
      field({ name: "owner_title", label: "Title", value: f.owner_title, errors: errors }) + "</div>" +
      '<div class="field-row">' + field({ name: "phone", label: "Phone", value: f.phone, errors: errors }) +
      field({ name: "email", label: "Email", value: f.email, errors: errors }) + "</div>" +
      field({ name: "ein", label: "EIN or SSN", value: f.ein, errors: errors }) +
      field({ name: "notes", label: "Notes", type: "textarea", rows: 2, value: f.notes, errors: errors }) +
      "</div></div>" +
      '<div class="panel"><div class="panel-head"><h3>Files and tax</h3></div><div class="panel-body">' +
      field({ name: "save_location", label: "Filekey folder", required: true, value: f.save_location, errors: errors, browse: "pick-folder", hint: "The .icbkey is the key to your books. A thumb drive or a backed-up folder is ideal." }) +
      field({ name: "receipts_location", label: "Receipts folder", required: true, value: f.receipts_location, errors: errors, browse: "pick-folder", hint: "Receipt images and invoices are saved here." }) +
      field({ name: "sales_tax", label: "Sales tax %", required: true, value: f.sales_tax === undefined ? "0.00" : f.sales_tax, errors: errors, hint: "Enter 6.25 for 6.25%. Leave 0.00 if you do not collect sales tax." }) +
      "</div></div></div></div></div>" +
      '<div class="bottom-bar"><div class="status-pill"><span class="dot off"></span> The database is encrypted the moment it is created.</div>' +
      '<div style="display:flex;gap:10px;"><button class="btn btn-secondary" data-action="go" data-screen="welcome">Cancel</button>' +
      '<button class="btn btn-primary" data-action="create-database">Create Database</button></div></div></section>';
  }

  /* ---------------------------------------------------------------- workspace shell */

  function workspace(state, body) {
    var s = state.status || {};
    var tabs = NAV.map(function (n) {
      return '<button class="nav-tab' + (state.screen === n.id ? " active" : "") + '" data-action="go" data-screen="' + n.id + '" title="Ctrl+' + n.key + '">' + esc(n.label) + "</button>";
    }).join("");
    var saved = s.unsaved ? pill("● Unsaved changes", "warn") : pill("● Saved", "ok");
    return '<section class="screen" id="screen-' + esc(state.screen) + '">' +
      '<div class="run-top"><div class="run-title-group">' +
      '<button class="back-link" data-action="go" data-screen="databases" title="Your databases">' + icon("back", "Your databases", "lg") + '</button>' +
      "<div><h2>" + esc(s.business_name || s.db_name || "Iceberg") + '</h2><div class="meta">' + esc(s.db_name || "") + "</div></div>" + saved + "</div>" +
      '<div class="run-actions"><button class="btn btn-secondary btn-sm" data-action="show-tools" title="Ctrl+M">' + icon("tools", "", "sm") + ' Tools</button>' +
      '<button class="btn btn-secondary btn-sm" data-action="save" title="Ctrl+S">Save</button>' +
      '<button class="btn btn-primary btn-sm" data-action="new-transaction" title="Ctrl+N">+ New Transaction</button></div></div>' +
      '<div class="nav-tabs">' + tabs + "</div>" +
      '<div class="workspace">' + body + "</div></section>";
  }

  function statusBar(state) {
    var s = state.status || {}, m = state.message || {};
    var left = s.database_loaded
      ? '<span><span class="dot"></span> ' + esc(s.db_name) + "</span>"
      : '<span><span class="dot off"></span> No database open</span>';
    var right = !s.database_loaded ? "" : s.unsaved
      ? "Unsaved changes · autosave in " + countdown(s.autosave_in) + " · Ctrl+S to save now"
      : (s.last_saved ? "All changes saved " + esc(s.last_saved) : "No unsaved changes");
    var badge = m.text && KIND_ICON[m.kind] ? icon(KIND_ICON[m.kind], "") + " " : "";
    return '<div class="left">' + left + "</div>" +
      '<div class="message ' + esc(m.kind || "") + '">' + badge + esc(m.text || "") + "</div>" +
      "<div>" + right + "</div>";
  }

  function countdown(seconds) {
    seconds = Math.max(0, Math.floor(Number(seconds) || 0));
    return Math.floor(seconds / 60) + ":" + ("0" + (seconds % 60)).slice(-2);
  }

  /* ---------------------------------------------------------------- dashboard */

  function dashboard(state) {
    var d = state.dashboard || {}, sum = d.summary || {}, business = d.business || {}, filters = d.filters || {};
    var tiles = [
      ["Assets", sum.assets], ["Liabilities", sum.liabilities], ["Revenue", sum.revenue], ["Expenses", sum.expenses],
      ["Business income", sum.business_income], ["Net assets", sum.net_assets], ["Owner equity", sum.owner_equity], ["Retained earnings", sum.retained_earnings]
    ].map(function (t) {
      return '<div class="stat-tile"><div class="label">' + esc(t[0]) + '</div><div class="value' + (t[1] < 0 ? " negative" : "") + '">' + money(t[1]) + "</div></div>";
    }).join("");
    var years = [["", "All years"]].concat((d.years || []).map(function (y) { return [y, y]; }));
    var rows = (d.accounts || []).map(function (a) {
      return '<tr class="clickable" data-action="open-account" data-account="' + esc(a.id) + '">' +
        '<td class="mono">' + esc(a.id) + '</td><td class="name">' + esc(a.name) + (a.institution ? '<span class="sub">' + esc(a.institution) + "</span>" : "") + "</td>" +
        "<td>" + esc(a.type) + "</td>" + moneyCell(a.debits) + moneyCell(a.credits) + moneyCell(a.balance) + "</tr>";
    }).join("");
    var balance = sum.in_balance
      ? '<span class="status-pill"><span class="dot"></span> In balance · debits ' + money(sum.total_debits) + " = credits " + money(sum.total_credits) + "</span>"
      : '<span class="status-pill"><span class="dot bad"></span> Out of balance · debits ' + money(sum.total_debits) + " ≠ credits " + money(sum.total_credits) + "</span>";
    var body = '<div class="stat-row">' + tiles + "</div>" +
      '<div class="panel" style="flex:1;min-height:0;"><div class="panel-head"><h3>Chart of accounts<span class="count-badge">' + (d.accounts || []).length + "</span></h3>" +
      '<div class="tools toolbar">' + balance +
      '<select data-action="dashboard-filter" name="type_prefix">' + TYPE_FILTERS.map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === (filters.type_prefix || "") ? " selected" : "") + ">" + o[1] + "</option>"; }).join("") + "</select>" +
      '<select data-action="dashboard-filter" name="year">' + years.map(function (o) { return '<option value="' + esc(o[0]) + '"' + (String(o[0]) === String(filters.year || "") ? " selected" : "") + ">" + esc(o[1]) + "</option>"; }).join("") + "</select>" +
      '<button class="btn btn-secondary btn-sm" data-action="new-account">+ New account</button></div></div>' +
      '<div class="table-wrap" style="flex:1;min-height:0;margin-top:12px;"><table class="data"><thead><tr>' +
      '<th data-sort="id">Account</th><th data-sort="name">Name</th><th data-sort="type">Type</th><th class="num" data-sort="debits">Debits</th><th class="num" data-sort="credits">Credits</th><th class="num" data-sort="balance">Balance</th>' +
      "</tr></thead><tbody>" + (rows || '<tr><td colspan="6" class="empty">No accounts.</td></tr>') + "</tbody></table></div></div>" +
      '<p class="footer-note" style="padding:10px 0 0;">' + esc(business.address || "") + (business.owner_name ? " · " + esc(business.owner_name) : "") + "</p>";
    return workspace(state, body);
  }

  /* ---------------------------------------------------------------- ledger */

  function ledger(state) {
    var l = state.ledger || {}, rows = l.rows || [], filters = l.filters || {}, selected = state.selected || null;
    var years = [["", "All years"]].concat((l.years || []).map(function (y) { return [y, y]; }));
    var body_rows = rows.map(function (r) {
      return '<tr class="clickable' + (selected && selected.id === r.id ? " selected" : "") + '" data-action="select-transaction" data-id="' + r.id + '">' +
        '<td class="mono">' + r.id + '</td><td class="mono">' + esc(r.date) + '</td><td class="name">' + esc(r.name) + (r.notes ? '<span class="sub">' + esc(r.notes) + "</span>" : "") + "</td>" +
        "<td>" + esc(r.debit) + '<span class="sub">' + esc(r.debit_name) + "</span></td><td>" + esc(r.credit) + '<span class="sub">' + esc(r.credit_name) + "</span></td>" +
        moneyCell(r.amount) + "<td>" + (r.reconciled ? '<span class="pill ok">' + icon("check", "Reconciled", "sm") + " " + esc(r.reconciled) + "</span>" : "") + "</td></tr>";
    }).join("");
    var main = '<div class="panel" style="flex:1;min-height:0;"><div class="panel-head"><h3>Ledger<span class="count-badge">' + rows.length + (l.total !== undefined && l.total !== rows.length ? " of " + l.total : "") + "</span></h3>" +
      '<div class="tools toolbar"><input type="text" name="search" data-action="ledger-search" placeholder="Search name, notes, account, amount… (Ctrl+F)" value="' + esc(filters.search || "") + '" />' +
      '<select name="year" data-action="ledger-filter">' + years.map(function (o) { return '<option value="' + esc(o[0]) + '"' + (String(o[0]) === String(filters.year || "") ? " selected" : "") + ">" + esc(o[1]) + "</option>"; }).join("") + "</select>" +
      '<button class="btn btn-primary btn-sm" data-action="new-transaction">+ New Transaction</button></div></div>' +
      '<div class="table-wrap" style="flex:1;min-height:0;margin-top:12px;"><table class="data"><thead><tr>' +
      '<th data-sort="id">#</th><th data-sort="date">Date</th><th data-sort="name">Name</th><th data-sort="debit">Debit (to)</th><th data-sort="credit">Credit (from)</th><th class="num" data-sort="amount">Amount</th><th>Reconciled</th>' +
      "</tr></thead><tbody>" + (body_rows || '<tr><td colspan="7" class="empty">' + (filters.search ? "No transactions match your search." : "No transactions yet. Record the first one with New Transaction.") + "</td></tr>") + "</tbody></table></div></div>";
    var side = '<div class="panel"><div class="panel-head"><h3>' + (selected ? "Transaction " + selected.id : "Transaction") + "</h3>" +
      (selected ? '<button class="btn btn-secondary btn-sm" data-action="edit-transaction" data-id="' + selected.id + '">Edit</button>' : "") + "</div>" +
      '<div class="panel-body">' + (selected ? transactionDetails(selected) : '<div class="empty">Select a transaction to see its details.</div>') + "</div></div>";
    return workspace(state, '<div class="columns" style="flex:1;min-height:0;"><div class="main">' + main + '</div><div class="side">' + side + "</div></div>");
  }

  function transactionDetails(t) {
    var rows = [
      ["Name", t.name], ["Date", t.date, "mono"], ["Amount", money(t.amount), "mono"],
      ["Debit (to)", t.debit + " · " + t.debit_name], ["Credit (from)", t.credit + " · " + t.credit_name],
      ["Vendor", t.vendor || "—"], ["Customer", t.customer || "—"], ["Notes", t.notes || "—"],
      ["Reconciled", t.reconciled || "Not yet"], ["Recorded", t.created], ["Edited", t.edited]
    ];
    return '<div class="detail-list">' + rows.map(function (r) {
      return '<div class="detail-row"><span class="k">' + esc(r[0]) + '</span><span class="v' + (r[2] ? " " + r[2] : "") + '">' + esc(r[1]) + "</span></div>";
    }).join("") + "</div>" + (t.record_image ? '<p class="hint" style="margin-top:10px;"><button class="btn btn-secondary btn-sm" data-action="open-file" data-path="' + esc(t.record_image) + '">View receipt</button></p>' : "");
  }

  function transactionModal(state) {
    var form = state.form || {}, f = state.fields || {}, errors = state.errors || [], editing = !!state.editing;
    var title = editing ? "Edit transaction " + esc(state.editing) : "Record transaction " + esc(form.next_id || "");
    var confirm = state.warnings && state.warnings.length
      ? alertBox("warn", "Please confirm before saving:", state.warnings) + '<div class="modal-actions" style="margin-top:0;margin-bottom:12px;"><button class="btn btn-secondary btn-sm" data-action="submit-transaction" data-confirm="1">Save anyway</button></div>'
      : "";
    return '<div class="modal-box wide"><h3>' + title + '</h3><p class="modal-sub">Fields marked <span class="req">*</span> are required. Amounts are positive; swap the accounts to reverse a transaction.</p>' +
      alertBox("bad", state.message && errors.length ? state.message : "", []) + confirm +
      '<form id="transaction-form" data-action="submit-transaction">' +
      '<div class="section"><h4>Details</h4>' +
      '<div class="field-row">' + field({ name: "name", label: "Transaction name", required: true, value: f.name, errors: errors, autofocus: true, placeholder: "What was it for?" }) +
      field({ name: "date", label: "Date", required: true, type: "date", value: f.date || form.today, errors: errors, narrow: true }) +
      field({ name: "amount", label: "Amount ($)", required: true, value: f.amount, errors: errors, narrow: true, placeholder: "0.00" }) + "</div></div>" +
      '<div class="section"><h4>Accounts</h4><div class="field-row">' +
      field({ name: "debit_account", label: "Debit — money goes to", required: true, type: "select", options: accountOptions(form.accounts), value: f.debit_account, errors: errors }) +
      field({ name: "credit_account", label: "Credit — money comes from", required: true, type: "select", options: accountOptions(form.accounts), value: f.credit_account, errors: errors }) + "</div>" +
      field({ name: "vendor", label: "Vendor", type: "select", options: [["", "—"]].concat((form.vendors || []).map(function (v) { return [v.id + " - " + v.name, v.id + " · " + v.name]; })), value: f.vendor, errors: errors }) + "</div>" +
      '<div class="section"><h4>Notes and receipt</h4>' + field({ name: "notes", label: "Notes", type: "textarea", rows: 2, value: f.notes, errors: errors }) +
      field({ name: "record_image", label: "Receipt image or PDF", value: f.record_image, errors: errors, browse: "pick-file" }) + "</div>" +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button>' +
      '<button type="submit" class="btn btn-primary">' + (editing ? "Save changes" : "Record transaction") + "</button></div></form></div>";
  }

  /* ---------------------------------------------------------------- account register */

  function register(state) {
    var r = state.register || {}, a = r.account || {}, rows = r.rows || [];
    var body_rows = rows.map(function (t) {
      return '<tr class="clickable" data-action="select-transaction" data-id="' + t.id + '" data-screen="ledger">' +
        '<td class="mono">' + t.id + '</td><td class="mono">' + esc(t.date) + '</td><td class="name">' + esc(t.name) + "</td>" +
        "<td>" + esc(t.effect > 0 ? (t.credit + " · " + t.credit_name) : (t.debit + " · " + t.debit_name)) + "</td>" +
        moneyCell(t.effect) + moneyCell(t.running_balance) + "</tr>";
    }).join("");
    var body = '<button class="back-link" data-action="go" data-screen="dashboard">' + icon("back", "") + ' Back to chart of accounts</button>' +
      '<div class="page-head" style="margin:8px 0 14px;"><div style="display:flex;align-items:center;gap:10px;"><h1 style="font-size:22px;">' + esc(a.id) + " · " + esc(a.name) + "</h1>" + pill(a.type || "", "info") + "</div>" +
      "<p>" + (a.institution ? esc(a.institution) + " · " : "") + "Balance " + money(a.balance) + " · " + rows.length + " transactions</p></div>" +
      '<div class="panel" style="flex:1;min-height:0;"><div class="panel-head"><h3>Register</h3><div class="tools"><button class="btn btn-secondary btn-sm" data-action="edit-account" data-account="' + esc(a.id) + '">Edit account</button>' +
      '<button class="btn btn-secondary btn-sm" data-action="reconcile-account" data-account="' + esc(a.id) + '">Reconcile</button></div></div>' +
      '<div class="table-wrap" style="flex:1;min-height:0;margin-top:12px;"><table class="data"><thead><tr><th>#</th><th>Date</th><th>Name</th><th>Other account</th><th class="num">Change</th><th class="num">Balance</th></tr></thead><tbody>' +
      (body_rows || '<tr><td colspan="6" class="empty">No transactions for this account.</td></tr>') + "</tbody></table></div></div>";
    return workspace(state, body);
  }

  /* ---------------------------------------------------------------- reports */

  function reportsScreen(state) {
    var p = state.periods || {}, sel = state.reportSelection || {}, result = state.report || null;
    var types = (p.types || []).map(function (t) { return [t, t]; });
    var presets = (p.presets || []).map(function (x) { return [x.name, x.name]; }).concat([["Custom", "Custom"]]);
    var body = '<div class="panel" style="flex:1;min-height:0;"><div class="panel-head"><h3>Financial reports</h3>' +
      '<form class="tools toolbar" id="report-form" data-action="run-report">' +
      '<select name="type">' + types.map(function (o) { return '<option value="' + esc(o[0]) + '"' + (o[0] === sel.type ? " selected" : "") + ">" + esc(o[1]) + "</option>"; }).join("") + "</select>" +
      '<select name="preset" data-action="report-preset">' + presets.map(function (o) { return '<option value="' + esc(o[0]) + '"' + (o[0] === (sel.preset || "This Year") ? " selected" : "") + ">" + esc(o[1]) + "</option>"; }).join("") + "</select>" +
      '<input type="date" name="start" value="' + esc(sel.start || "") + '" /><input type="date" name="end" value="' + esc(sel.end || "") + '" />' +
      '<button type="submit" class="btn btn-primary btn-sm">' + icon("play", "", "sm") + ' Run report</button>' +
      '<button type="button" class="btn btn-secondary btn-sm" data-action="export-report"' + (result ? "" : " disabled") + ">Export CSV</button></form></div>" +
      '<div class="workspace-scroll">' + (result ? '<pre class="report">' + esc(result.text) + "</pre>" : '<div class="empty">Choose a report and period, then select Run report.</div>') + "</div></div>";
    return workspace(state, body);
  }

  function consoleLog(lines) {
    return '<div class="console">' + (lines || []).slice(0, 12).map(esc).join("\n") + "</div>";
  }

  return {
    NAV: NAV, WORKSPACES: WORKSPACES, ICONS: ICONS, esc: esc, money: money, moneyCell: moneyCell, pill: pill, icon: icon, field: field, alertBox: alertBox, countdown: countdown,
    welcome: welcome, databases: databases, createForm: createForm, workspace: workspace, statusBar: statusBar,
    dashboard: dashboard, ledger: ledger, transactionDetails: transactionDetails, transactionModal: transactionModal,
    register: register, reports: reportsScreen, consoleLog: consoleLog
  };
});

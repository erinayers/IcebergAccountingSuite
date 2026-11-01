/* Views for reconciliation, database properties, accounts, the tools menu,
   backups, import/export, preferences, console, shortcuts.  Extends Render. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) { module.exports = factory(require("./render_records.js")); }
  else { factory(root.Render); }
})(typeof self !== "undefined" ? self : this, function (R) {
  "use strict";
  var esc = R.esc, money = R.money, pill = R.pill, field = R.field, alertBox = R.alertBox;

  var SHORTCUTS = [
    ["Ctrl+1 … Ctrl+8", "Dashboard, Ledger, Invoices, Customers, Vendors, Services, Reports, Reconcile"],
    ["Ctrl+N", "New transaction"], ["Ctrl+I", "New invoice"], ["Ctrl+S", "Save database"], ["Ctrl+O", "Open database"],
    ["Ctrl+F", "Search on the current screen"], ["Ctrl+,", "Preferences"], ["Ctrl+M", "Tools menu"],
    ["Esc", "Close a dialog"], ["Enter", "Submit the open form"], ["Tab / Shift+Tab", "Move between fields"]
  ];

  /* --------------------------------------------------------------- reconcile */

  function reconcileScreen(state) {
    var r = state.reconcile || {}, f = r.fields || {}, errors = r.errors || [], data = r.data || null;
    var accounts = [["", "Select an account…"]].concat((state.accountList || []).map(function (a) { return [a.id, a.id + " · " + a.name]; }));
    var setup = '<div class="panel"><div class="panel-head"><h3>Statement</h3><div class="tools">' +
      '<button class="btn btn-secondary btn-sm" data-action="reconcile-history">History</button><button class="btn btn-secondary btn-sm" data-action="reconcile-undo">Undo last</button></div></div>' +
      '<div class="panel-body"><form id="reconcile-form" data-action="reconcile-start"><div class="field-row">' +
      field({ name: "account", label: "Account", required: true, type: "select", options: accounts, value: f.account, errors: errors }) +
      field({ name: "statement_date", label: "Statement date", required: true, type: "date", value: f.statement_date, errors: errors, narrow: true }) +
      field({ name: "statement_balance", label: "Ending balance ($)", required: true, value: f.statement_balance, errors: errors, narrow: true, hint: "As printed on the statement" }) +
      '<div class="field narrow" style="justify-content:flex-end;"><button type="submit" class="btn btn-primary">Load transactions</button></div></div></form></div></div>';
    if (!data) {
      return R.workspace(state, setup + '<div class="panel" style="margin-top:16px;"><div class="placeholder"><h3>Reconcile an account against its statement</h3><p>Enter the statement date and ending balance, load the transactions, then tick each one that appears on the statement. When the difference is zero, finish.</p></div></div>');
    }
    var s = data.summary, cleared = {};
    (data.cleared_ids || []).forEach(function (id) { cleared[id] = true; });
    var rows = data.candidates.map(function (c) {
      var on = !!cleared[c.Transaction_ID];
      return '<tr class="clickable' + (on ? " selected" : "") + '" data-action="toggle-cleared" data-id="' + c.Transaction_ID + '">' +
        '<td><input type="checkbox" ' + (on ? "checked" : "") + ' tabindex="-1" /></td><td class="mono">' + c.Transaction_ID + '</td><td class="mono">' + esc(c.Transaction_Date) + '</td><td class="name">' + esc(c.Name) + "</td>" +
        "<td>" + esc(c.Counter_Account) + "</td>" + R.moneyCell(c.Amount) + "</tr>";
    }).join("");
    var summary = '<div class="panel"><div class="panel-head"><h3>' + (s.balanced ? R.icon("check", "") + ' Balanced' : R.icon("warning", "") + ' Not balanced yet') + "</h3></div>" +
      '<div class="panel-body">' + R.details([["Previously reconciled", money(s.reconciled_balance) + " (" + data.session.reconciled_count + ")", "mono"], ["Cleared on this statement", money(s.cleared_total) + " (" + s.cleared_count + ")", "mono"],
        ["Cleared balance", money(s.cleared_balance), "mono"], ["Statement balance", money(s.statement_balance), "mono"], ["Difference", money(s.difference), "mono"], ["Unmatched", money(s.unmatched_total) + " (" + s.unmatched.length + ")", "mono"]]) +
      (data.session.later_reconciled ? '<p class="hint" style="margin-top:8px;color:var(--amber-ink);font-size:11.5px;">' + data.session.later_reconciled + " transaction(s) dated after this statement were reconciled on a later statement.</p>" : "") +
      '<div class="modal-actions" style="margin-top:14px;"><button class="btn btn-secondary btn-sm" data-action="reconcile-select-all">Select all</button><button class="btn btn-secondary btn-sm" data-action="reconcile-clear-all">Clear</button>' +
      '<button class="btn btn-primary" data-action="reconcile-finish"' + (s.balanced ? "" : " disabled") + ">" + R.icon("check", "", "sm") + " Finish reconciliation</button></div></div></div>";
    var table = '<div class="panel" style="flex:1;min-height:0;"><div class="panel-head"><h3>Transactions through ' + esc(data.session.statement_date) + '<span class="count-badge">' + data.candidates.length + "</span></h3><span class=\"form-legend\">Click a row to mark it cleared</span></div>" +
      '<div class="table-wrap" style="flex:1;min-height:0;margin-top:12px;"><table class="data"><thead><tr><th></th><th>#</th><th>Date</th><th>Name</th><th>Other account</th><th class="num">Amount</th></tr></thead><tbody>' +
      (rows || '<tr><td colspan="6" class="empty">Nothing left to reconcile through this date.</td></tr>') + "</tbody></table></div></div>";
    return R.workspace(state, setup + '<div class="columns" style="flex:1;min-height:0;margin-top:16px;"><div class="main">' + table + '</div><div class="side">' + summary + "</div></div>");
  }

  function reconcileHistoryModal(rows) {
    var body = (rows || []).map(function (h) { return '<tr><td class="mono">' + esc(h.statement_date) + '</td><td class="mono">' + esc(h.account_id) + "</td>" + R.moneyCell(h.statement_balance) + '<td class="num">' + h.cleared_count + "</td><td>" + esc(h.recorded) + "</td></tr>"; }).join("");
    return '<div class="modal-box wide"><h3>Reconciliation history</h3><p class="modal-sub">Completed statements, newest first.</p><table class="data"><thead><tr><th>Statement</th><th>Account</th><th class="num">Ending balance</th><th class="num">Cleared</th><th>Recorded</th></tr></thead><tbody>' +
      (body || '<tr><td colspan="5" class="empty">No reconciliations yet.</td></tr>') + '</tbody></table><div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  /* -------------------------------------------------------------- properties */

  function propertiesScreen(state) {
    var p = state.propertyFields || state.properties || {}, errors = state.propertyErrors || [];
    var body = '<form id="properties-form" data-action="save-properties" class="workspace-scroll">' + alertBox("bad", state.propertyMessage || "", []) +
      '<div class="form-columns"><div class="panel"><div class="panel-head"><h3>Business</h3><span class="form-legend"><span class="req">*</span> required</span></div><div class="panel-body">' +
      field({ name: "business_name", label: "Business name", required: true, value: p.business_name, errors: errors, hint: "Changing the name does not rename the database file." }) +
      field({ name: "address", label: "Address", required: true, type: "textarea", rows: 2, value: p.address, errors: errors }) +
      '<div class="field-row">' + field({ name: "owner_name", label: "Owner or financial officer", value: p.owner_name, errors: errors }) + field({ name: "owner_title", label: "Title", value: p.owner_title, errors: errors }) + "</div>" +
      '<div class="field-row">' + field({ name: "phone", label: "Phone", value: p.phone, errors: errors }) + field({ name: "email", label: "Email", value: p.email, errors: errors }) + "</div>" +
      field({ name: "ein", label: "EIN or SSN", value: p.ein, errors: errors }) + field({ name: "notes", label: "Notes", type: "textarea", rows: 2, value: p.notes, errors: errors }) + "</div></div>" +
      '<div class="panel"><div class="panel-head"><h3>Files and tax</h3></div><div class="panel-body">' +
      field({ name: "receipts_location", label: "Receipts folder", required: true, value: p.receipts_location, errors: errors, browse: "pick-folder", hint: "Receipt images and invoice PDFs are saved here." }) +
      field({ name: "sales_tax", label: "Sales tax %", required: true, value: p.sales_tax_percent !== undefined ? p.sales_tax_percent : percent(p.sales_tax), errors: errors, hint: "Enter 6.25 for 6.25%." }) +
      R.details([["Ledger table", p.ledger_name, "mono"]]) + "</div></div></div>" +
      '<div class="modal-actions"><button type="submit" class="btn btn-primary">Save properties</button></div></form>';
    return R.workspace(state, '<div class="page-head" style="margin:0 0 14px;"><h1 style="font-size:22px;">Database properties</h1><p>Details printed on invoices and used for sales tax.</p></div>' + body);
  }

  function percent(fraction) {
    var n = Number(fraction);
    if (isNaN(n)) { return fraction || "0.00"; }
    return (Math.round(n * 10000) / 100).toFixed(2);
  }

  /* ---------------------------------------------------------------- accounts */

  function accountModal(state) {
    var f = state.fields || {}, errors = state.errors || [], form = state.accountForm || {}, editing = state.editing;
    var types = (form.types || []).map(function (t) { return [t.prefix, t.prefix + " " + t.label]; });
    var bank = (form.bank_account_types || [""]).map(function (b) { return [b, b || "—"]; });
    return '<div class="modal-box"><h3>' + (editing ? "Edit account " + esc(editing) : "New account") + '</h3><p class="modal-sub">' + (editing ? "The account number and type cannot change." : "The number is assigned from the type's block (for example 11019 for an expense).") + "</p>" +
      alertBox("bad", state.message && errors.length ? state.message : "", []) + '<form id="account-form" data-action="submit-account">' +
      field({ name: "name", label: "Account name", required: true, value: f.name, errors: errors, autofocus: true }) +
      (editing ? "" : field({ name: "type_prefix", label: "Type", required: true, type: "select", options: types, value: f.type_prefix || "10", errors: errors.map(function (e) { return e.field === "type" ? { field: "type_prefix", message: e.message } : e; }) })) +
      '<div class="section"><h4>Bank details (optional)</h4>' + field({ name: "institution", label: "Bank or credit union", value: f.institution, errors: errors, hint: "Accounts with a bank count as cash on the cash-flow report." }) +
      '<div class="field-row">' + field({ name: "bank_account_type", label: "Account type", type: "select", options: bank, value: f.bank_account_type, errors: errors }) +
      field({ name: "routing_number", label: "Routing number", value: f.routing_number, errors: errors }) + field({ name: "account_number", label: "Account number", value: f.account_number, errors: errors }) + "</div></div>" +
      field({ name: "notes", label: "Notes", type: "textarea", rows: 2, value: f.notes, errors: errors }) +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">' + (editing ? "Save changes" : "Add account") + "</button></div></form></div>";
  }

  /* ------------------------------------------------------------------- tools */

  function toolsMenu(state) {
    var s = state.status || {}, loaded = !!s.database_loaded;
    var iconFor = { "go-databases": "screen", "show-backups": "back", "show-console": "terminal", "show-docs": "forward", "save": "check", "go-properties": "tools" };
    function item(action, label, description, disabled) {
      return '<button class="menu-item" data-action="' + action + '"' + (disabled ? " disabled" : "") + '><span class="menu-label">' + (iconFor[action] ? R.icon(iconFor[action], "", "sm") + " " : "") + esc(label) + '</span><span class="menu-desc">' + esc(description) + "</span></button>";
    }
    return '<div class="modal-box wide"><h3>Tools</h3><p class="modal-sub">' + (loaded ? esc(s.db_name) : "No database open") + '</p><div class="menu-grid">' +
      item("go-databases", "Your databases", "Open or create a set of books") +
      item("go-properties", "Database properties", "Business details, receipts folder, sales tax", !loaded) +
      item("save", "Save now", "Ctrl+S · also happens automatically", !loaded) +
      item("show-backups", "Restore from backup", "Roll back to a previous save", !loaded) +
      item("export-ledger", "Export ledger to CSV", "All transactions with account names", !loaded) +
      item("export-all", "Export all data to CSV", "One file per table, into a folder", !loaded) +
      item("import-transactions", "Import transactions from CSV", "Checked line by line before anything is written", !loaded) +
      item("import-template", "Save an import template", "A sample CSV in the expected layout", false) +
      item("show-preferences", "Preferences", "Appearance and text size (Ctrl+,)", false) +
      item("show-shortcuts", "Keyboard shortcuts", "Everything reachable without the mouse", false) +
      item("show-console", "Console log", "Everything Iceberg did this session", false) +
      item("show-paths", "Where are my files", "Databases, backups, logs, preferences", false) +
      item("show-docs", "Documentation", "Open the docs folder", false) +
      '</div><div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  function backupsModal(data) {
    var rows = (data.backups || []).map(function (b) { return '<tr><td class="name">' + esc(b.label) + '<span class="sub">' + esc(b.name) + '</span></td><td class="num">' + Math.round(b.size / 1024) + ' KB</td><td><button class="btn btn-secondary btn-sm" data-action="restore-backup" data-path="' + esc(b.path) + '">Restore</button></td></tr>'; }).join("");
    return '<div class="modal-box wide"><h3>Restore from backup</h3><p class="modal-sub">A backup is written after every save. Restoring keeps the current file as a new backup first. Folder: <span class="kbd">' + esc(data.folder || "") + '</span></p>' +
      '<table class="data"><thead><tr><th>Backup</th><th class="num">Size</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="3" class="empty">No backups yet. Save the database to create one.</td></tr>') + "</tbody></table>" +
      '<div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  function confirmModal(opts) {
    return '<div class="modal-box"><h3>' + esc(opts.title) + '</h3><p class="modal-sub">' + esc(opts.message) + "</p>" + (opts.extra || "") +
      '<div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Cancel</button><button class="btn ' + (opts.danger ? "btn-danger" : "btn-primary") + '" data-action="' + esc(opts.action) + '"' + (opts.attrs || "") + ">" + esc(opts.confirmLabel || "Confirm") + "</button></div></div>";
  }

  function importPreviewModal(path, result) {
    var warnings = (result.warnings || []).length ? alertBox("warn", "Please review:", result.warnings.slice(0, 15)) : "";
    return confirmModal({ title: "Import " + result.preview + " transaction(s)?", message: path, extra: warnings, action: "import-transactions-confirm", attrs: ' data-path="' + esc(path) + '"', confirmLabel: "Import" });
  }

  function importProblemsModal(result) {
    return '<div class="modal-box wide"><h3>The file cannot be imported</h3><p class="modal-sub">' + esc(result.message) + " Nothing was written.</p>" +
      alertBox("bad", "", (result.problems || []).slice(0, 30)) + '<div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  function preferencesModal(data) {
    var p = data.preferences || {};
    var themes = [["light", "Light"], ["dark", "Dark"], ["high-contrast", "High contrast"]];
    return '<div class="modal-box"><h3>Preferences</h3><p class="modal-sub">Changes apply immediately and are remembered.</p><form id="preferences-form" data-action="save-preferences">' +
      field({ name: "theme", label: "Appearance", type: "select", options: themes, value: p.theme || "light" }) +
      field({ name: "text_scale", label: "Text size", type: "select", options: (data.text_scales || []).map(function (t) { return [String(t.value), t.label]; }), value: String(p.text_scale || 1) }) +
      '<div class="field"><label><input type="checkbox" name="compact" ' + (p.compact ? "checked" : "") + ' /> Compact rows in tables</label></div>' +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">Save</button></div></form></div>';
  }

  function pathsModal(data) {
    var p = data.paths || {};
    var rows = [["Mode", p.mode === "portable" ? "Portable - files stay next to the program" : (p.mode === "custom" ? "Custom data folder (--data-dir)" : "Per-user data folder")],
                ["Databases (.icb)", p.databases], ["Backups", p.backups], ["Log file", p.log_file], ["Preferences", p.preferences], ["Program", p.program]];
    return '<div class="modal-box wide"><h3>Where are my files</h3><p class="modal-sub">Filekeys (.icbkey) and the receipts folder are wherever you chose when creating the database.</p>' +
      R.details(rows.map(function (r) { return [r[0], r[1], r[0] === "Mode" ? "" : "mono"]; })) +
      '<div class="modal-actions"><button class="btn btn-secondary" data-action="open-data-folder">Open data folder</button><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  function consoleModal(lines) {
    return '<div class="modal-box wide"><h3>' + R.icon("terminal", "") + ' Console log</h3><p class="modal-sub">Newest first. The log is also stored in the database.</p><div class="console" style="max-height:420px;">' + (lines || []).map(esc).join("\n") + '</div><div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  function shortcutsModal() {
    var rows = SHORTCUTS.map(function (s) { return "<tr><td><span class=\"kbd\">" + esc(s[0]) + "</span></td><td>" + esc(s[1]) + "</td></tr>"; }).join("");
    return '<div class="modal-box"><h3>Keyboard shortcuts</h3><table class="data"><tbody>' + rows + '</tbody></table><div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Close</button></div></div>';
  }

  function aboutText(version) {
    return "Iceberg Accounting Suite " + version + " · Timestamps are stored in UTC and shown in your local time · Backups are written on every save";
  }

  R.SHORTCUTS = SHORTCUTS; R.percent = percent;
  R.reconcile = reconcileScreen; R.reconcileHistoryModal = reconcileHistoryModal;
  R.properties = propertiesScreen; R.accountModal = accountModal; R.toolsMenu = toolsMenu; R.backupsModal = backupsModal;
  R.confirmModal = confirmModal; R.importPreviewModal = importPreviewModal; R.importProblemsModal = importProblemsModal;
  R.preferencesModal = preferencesModal; R.consoleModal = consoleModal; R.pathsModal = pathsModal; R.shortcutsModal = shortcutsModal; R.aboutText = aboutText;
  return R;
});

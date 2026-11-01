/* Runtime: state, screens, actions.  Views come from render*.js; all data
   goes through Api (client.js), which hides whether the transport is the
   local HTTP server or the sample-data mock. */
(function () {
  "use strict";
  var R = window.Render;
  var Api = null;
  var state = {
    screen: "welcome", status: {}, databases: [], message: null, version: "", modal: null, editing: null,
    filters: { dashboard: { type_prefix: "", year: "" }, ledger: { search: "", year: "" }, invoices: { search: "" }, customers: { search: "" }, vendors: { search: "" }, services: { search: "" } },
    selected: { transaction: null, invoice: null, customer: null, vendor: null, service: null },
    reportSelection: { type: "Income Statement", preset: "This Year" },
    reconcile: { fields: {}, errors: [], data: null }
  };

  /* ---------------------------------------------------------------- feedback */
  function notify(text, kind) { state.message = { text: text, kind: kind || "" }; paintStatus(); }
  function report(r, okKind) { notify(r.message, r.ok ? (okKind || "ok") : (r.needs_confirmation ? "warn" : "bad")); return r; }
  function paintStatus() {
    document.getElementById("status-bar").innerHTML = R.statusBar(state);
    var clock = document.getElementById("clock");
    if (clock && state.status.clock) { clock.textContent = state.status.clock; }
  }
  function refreshStatus() { return Api.app.status().then(function (s) { state.status = s; state.version = s.version; paintStatus(); return s; }); }
  function applyPreferences(p) {
    document.body.className = (p.theme && p.theme !== "light" ? "theme-" + p.theme : "") + (p.compact ? " compact" : "");
    document.documentElement.style.fontSize = (16 * (Number(p.text_scale) || 1)) + "px";
  }

  /* ---------------------------------------------------------------- screens */
  function paint(html) {
    document.getElementById("content").innerHTML = html;
    var first = document.querySelector("#content [autofocus]");
    if (first) { first.focus(); }
  }

  var SCREENS = {
    welcome:    { load: function () { return Api.databases.list().then(function (l) { state.databases = l; }); }, view: function () { return R.welcome(state); } },
    databases:  { load: function () { return Api.databases.list().then(function (l) { state.databases = l; }); }, view: function () { return R.databases(state); } },
    create:     { load: function () { state.createFields = state.createFields || { sales_tax: "0.00" }; }, view: function () { return R.createForm({ fields: state.createFields, errors: state.createErrors || [], message: state.createMessage }); } },
    dashboard:  { db: true, load: function () { return Api.dashboard.get(state.filters.dashboard).then(function (d) { state.dashboard = d; }); }, view: function () { return R.dashboard(state); } },
    account:    { db: true, load: function (p) { return Api.accounts.register({ account_id: p.account }).then(function (r) { if (!r.ok) { throw r; } state.register = r; }); }, view: function () { return R.register(state); } },
    ledger:     { db: true, load: function (p) {
                    return Api.ledger.list(state.filters.ledger).then(function (l) { state.ledger = l; if (p.select) { return selectTransaction(p.select); } });
                  }, view: function () { return R.ledger({ screen: "ledger", status: state.status, ledger: state.ledger, selected: state.selected.transaction }); } },
    reports:    { db: true, load: function () {
                    return Api.reports.periods().then(function (p) {
                      state.periods = p;
                      if (!state.reportSelection.start) { var preset = p.presets[0]; state.reportSelection.start = preset.start; state.reportSelection.end = preset.end; state.reportSelection.preset = preset.name; }
                    });
                  }, view: function () { return R.reports(state); } },
    invoices:   { db: true, load: function (p) {
                    return Api.invoices.list(state.filters.invoices).then(function (d) { state.invoices = d; if (p.select) { return selectInvoice(p.select); } });
                  }, view: function () { return R.invoices({ screen: "invoices", status: state.status, invoices: state.invoices, selectedInvoice: state.selected.invoice }); } },
    customers:  { db: true, load: function () { return Api.customers.list(state.filters.customers).then(function (d) { state.customers = d; }); },
                  view: function () { return R.customers({ screen: "customers", status: state.status, customers: state.customers, selectedCustomer: state.selected.customer }); } },
    vendors:    { db: true, load: function () { return Api.vendors.list(state.filters.vendors).then(function (d) { state.vendors = d; }); },
                  view: function () { return R.vendors({ screen: "vendors", status: state.status, vendors: state.vendors, selectedVendor: state.selected.vendor }); } },
    services:   { db: true, load: function () { return Api.services.list(state.filters.services).then(function (d) { state.services = d; }); },
                  view: function () { return R.services({ screen: "services", status: state.status, services: state.services, selectedService: state.selected.service }); } },
    reconcile:  { db: true, load: function (p) {
                    return Api.accounts.list().then(function (d) {
                      state.accountList = d.accounts || [];
                      if (p.account) { state.reconcile.fields.account = p.account; }
                      if (!state.reconcile.fields.statement_date) { state.reconcile.fields.statement_date = new Date().toISOString().slice(0, 10); }
                    });
                  }, view: function () { return R.reconcile(state); } },
    properties: { db: true, load: function () { return Api.properties.get().then(function (p) { state.properties = p; state.propertyFields = null; state.propertyErrors = []; state.propertyMessage = ""; }); }, view: function () { return R.properties(state); } }
  };

  function go(screen, params) {
    var spec = SCREENS[screen] || SCREENS.welcome;
    if (spec.db && !state.status.database_loaded) { notify("Open or create a database first.", "warn"); return Promise.resolve(); }
    state.screen = screen;
    return Promise.resolve(spec.load(params || {})).then(function () { paint(spec.view()); }).catch(function (error) {
      if (error && error.message !== undefined) { return report(error); }
      throw error;
    });
  }
  function repaint() { paint(SCREENS[state.screen].view()); }

  /* ---------------------------------------------------------------- modals */
  function openModal(html) { state.modal = html; var m = document.getElementById("modal"); m.innerHTML = html; m.classList.add("open"); var f = m.querySelector("[autofocus]"); if (f) { f.focus(); } }
  function closeModal() { state.modal = null; state.editing = null; var m = document.getElementById("modal"); m.classList.remove("open"); m.innerHTML = ""; }
  function formValues(form) {
    var out = {};
    Array.prototype.forEach.call(form.querySelectorAll("input, select, textarea"), function (el) { if (el.name) { out[el.name] = el.type === "checkbox" ? el.checked : el.value; } });
    return out;
  }
  function modalForm(id) { return document.getElementById(id); }
  function pickPath(dialog, args) { return dialog(args).then(function (r) { if (!r.ok) { report(r); } return r.path || null; }); }

  /* ----------------------------------------------------------- selections */
  function selectTransaction(id) { return Api.transactions.get({ transaction_id: id }).then(function (t) { state.selected.transaction = t.ok ? t.transaction : null; }); }
  function selectInvoice(id) { return Api.invoices.get({ invoice_id: id }).then(function (d) { state.selected.invoice = d.ok ? d : null; if (!d.ok) { report(d); } }); }

  /* ---------------------------------------------------------- transactions */
  function openTransactionModal(existing) {
    return Api.transactions.form().then(function (form) {
      if (!form.ok) { return report(form); }
      state.form = form;
      state.editing = existing ? existing.id : null;
      var fields = existing ? { name: existing.name, date: existing.date, amount: (existing.amount / 100).toFixed(2), debit_account: existing.debit, credit_account: existing.credit, vendor: existing.vendor, notes: existing.notes, record_image: existing.record_image } : { date: form.today };
      openModal(R.transactionModal({ form: form, fields: fields, errors: [], editing: state.editing }));
    });
  }
  function submitTransaction(confirm) {
    var fields = formValues(modalForm("transaction-form"));
    var call = state.editing ? Api.transactions.update({ transaction_id: state.editing, fields: fields }) : Api.transactions.create({ fields: fields, confirm_warnings: !!confirm });
    return call.then(function (r) {
      if (!r.ok) { openModal(R.transactionModal({ form: state.form, fields: fields, errors: r.errors, warnings: r.warnings, message: r.message, editing: state.editing })); return report(r); }
      closeModal(); report(r);
      return refreshStatus().then(function () { return go("ledger", { select: r.id }); });
    });
  }

  /* -------------------------------------------------------------- invoices */
  function recalcInvoice() {
    var form = modalForm("invoice-form");
    var fields = form ? formValues(form) : (state.invoiceFields || {});
    state.invoiceFields = fields;
    return Api.invoices.totals({ line_items: state.lineItems, tax_rate: fields.sales_tax_rate }).then(function (t) {
      state.invoiceTotals = t.ok ? t : { subtotal: 0, sales_tax: 0, total: 0 };
      openModal(R.invoiceModal({ invoiceForm: state.invoiceForm, invoiceFields: fields, lineItems: state.lineItems, invoiceTotals: state.invoiceTotals, errors: state.invoiceErrors || [], message: state.invoiceMessage }));
    });
  }
  function openInvoiceModal() {
    return Api.invoices.form().then(function (form) {
      if (!form.ok) { return report(form); }
      state.invoiceForm = form; state.lineItems = []; state.invoiceErrors = []; state.invoiceMessage = "";
      state.invoiceFields = { status: "Due", due_date: form.today, sales_tax_rate: form.sales_tax_rate };
      return recalcInvoice();
    });
  }

  /* --------------------------------------------------------------- records */
  var RECORDS = {
    customer: { modal: R.customerModal, formId: "customer-form", screen: "customers", idKey: "customer_id", save: function (fields, id) { return Api.customers.save({ fields: fields, customer_id: id }); },
                toFields: function (c) { return c; }, afterSave: function (id) { return actions["select-customer"]({ dataset: { id: id } }); } },
    vendor:   { modal: R.vendorModal, formId: "vendor-form", screen: "vendors", save: function (fields, id) { return Api.vendors.save({ fields: fields, vendor_id: id }); },
                toFields: function (v) { return v; }, afterSave: function (id) { return actions["select-vendor"]({ dataset: { id: id } }); } },
    service:  { modal: R.serviceModal, formId: "service-form", screen: "services", save: function (fields, sku) { return Api.services.save({ fields: fields, sku: sku }); },
                toFields: function (s) { return { description: s.description, price: (s.price / 100).toFixed(2), taxable: s.taxable ? "True" : "False", long_description: s.long_description }; },
                afterSave: function (sku) { return actions["select-service"]({ dataset: { id: sku } }); } }
  };
  function openRecordModal(kind, existing) {
    var spec = RECORDS[kind];
    state.editing = existing ? (existing.id || existing.sku) : null;
    openModal(spec.modal({ fields: existing ? spec.toFields(existing) : {}, errors: [], editing: state.editing }));
  }
  function submitRecord(kind) {
    var spec = RECORDS[kind], fields = formValues(modalForm(spec.formId)), editing = state.editing;
    return spec.save(fields, editing).then(function (r) {
      if (!r.ok) { openModal(spec.modal({ fields: fields, errors: r.errors, message: r.message, editing: editing })); return report(r); }
      closeModal(); report(r);
      return refreshStatus().then(function () { return go(spec.screen); }).then(function () { return spec.afterSave(r.id); });
    });
  }

  /* ------------------------------------------------------------- reconcile */
  function reconcileSummary(ids) {
    return Api.reconcile.summary({ cleared_ids: ids }).then(function (r) { if (!r.ok) { return report(r); } state.reconcile.data = r; repaint(); });
  }
  function currentReconcileAccount() { return (document.getElementById("f-account") || {}).value || state.reconcile.fields.account || ""; }

  /* ---------------------------------------------------------------- actions */
  var actions = {
    "go": function (el) { return go(el.dataset.screen, el.dataset); },
    "go-databases": function () { closeModal(); return go("databases"); },
    "go-properties": function () { closeModal(); return go("properties"); },
    "open-database": function () {
      return pickPath(Api.dialogs.keyFile).then(function (path) {
        if (!path) { return; }
        notify("Opening…", "");
        return Api.databases.open({ key_path: path }).then(function (r) { report(r); if (r.ok) { return refreshStatus().then(function () { return go("dashboard"); }); } });
      });
    },
    "pick-folder": function (el) { return pickPath(Api.dialogs.folder).then(function (p) { if (p) { document.getElementById("f-" + el.dataset.target).value = p; } }); },
    "pick-file": function (el) { return pickPath(Api.dialogs.file).then(function (p) { if (p) { document.getElementById("f-" + el.dataset.target).value = p; } }); },
    "create-database": function () {
      var fields = formValues(document.getElementById("content"));
      state.createFields = fields; notify("Creating database…", "");
      return Api.databases.create({ fields: fields }).then(function (r) {
        if (!r.ok) { state.createErrors = r.errors; state.createMessage = r.errors.length ? "" : r.message; repaint(); return report(r); }
        state.createErrors = []; state.createMessage = ""; report(r);
        return refreshStatus().then(function () { return go("dashboard"); });
      });
    },
    "save": function () { closeModal(); notify("Saving…", ""); return Api.databases.save().then(function (r) { report(r); return refreshStatus(); }); },
    "close-modal": function () { closeModal(); },
    /* ledger */
    "new-transaction": function () { return openTransactionModal(null); },
    "edit-transaction": function () { return openTransactionModal(state.selected.transaction); },
    "submit-transaction": function (el) { return submitTransaction(el.dataset.confirm === "1"); },
    "select-transaction": function (el) {
      var id = Number(el.dataset.id);
      if (el.dataset.screen === "ledger" && state.screen !== "ledger") { return go("ledger", { select: id }); }
      return selectTransaction(id).then(repaint);
    },
    "ledger-filter": function (el) { state.filters.ledger[el.name] = el.value; return go("ledger"); },
    "ledger-search": function (el) { state.filters.ledger.search = el.value; return go("ledger").then(refocusSearch); },
    /* dashboard / accounts */
    "dashboard-filter": function (el) { state.filters.dashboard[el.name] = el.value; return go("dashboard"); },
    "open-account": function (el) { return go("account", { account: el.dataset.account }); },
    "new-account": function () { return Api.accounts.form().then(function (form) { state.accountForm = form; state.editing = null; openModal(R.accountModal({ accountForm: form, fields: {}, errors: [] })); }); },
    "edit-account": function (el) {
      return Promise.all([Api.accounts.form(), Api.accounts.get({ account_id: el.dataset.account })]).then(function (results) {
        if (!results[1].ok) { return report(results[1]); }
        state.accountForm = results[0]; state.editing = results[1].account.id;
        openModal(R.accountModal({ accountForm: results[0], fields: results[1].account, errors: [], editing: state.editing }));
      });
    },
    "submit-account": function () {
      var fields = formValues(modalForm("account-form")), editing = state.editing;
      var call = editing ? Api.accounts.update({ account_id: editing, fields: fields }) : Api.accounts.create({ fields: fields });
      return call.then(function (r) {
        if (!r.ok) { openModal(R.accountModal({ accountForm: state.accountForm, fields: fields, errors: r.errors, message: r.message, editing: editing })); return report(r); }
        closeModal(); report(r);
        return refreshStatus().then(function () { return editing ? go("account", { account: editing }) : go("dashboard"); });
      });
    },
    /* reports */
    "report-preset": function (el) {
      var sel = state.reportSelection; sel.preset = el.value;
      var p = (state.periods.presets || []).filter(function (x) { return x.name === el.value; })[0];
      if (p) { sel.start = p.start; sel.end = p.end; repaint(); }
    },
    "run-report": function (el) {
      var v = formValues(el); state.reportSelection = { type: v.type, preset: v.preset, start: v.start, end: v.end };
      notify("Building report…", "");
      return Api.reports.run({ report_type: v.type, start: v.start, end: v.end }).then(function (r) { if (!r.ok) { return report(r); } state.report = r; repaint(); notify(r.report.title + " ready.", "ok"); });
    },
    "export-report": function () {
      var name = ((state.report && state.report.report.type) || "report").replace(/ /g, "_") + ".csv";
      return pickPath(Api.dialogs.saveFile, { filename: name }).then(function (path) { if (path) { return Api.reports.export({ path: path }).then(report); } });
    },
    "open-file": function (el) { return Api.app.openPath({ path: el.dataset.path }).then(function (r) { if (!r.ok) { report(r); } }); },
    /* invoices */
    "invoice-search": function (el) { state.filters.invoices.search = el.value; return go("invoices").then(refocusSearch); },
    "select-invoice": function (el) {
      if (el.dataset.screen === "invoices" && state.screen !== "invoices") { return go("invoices", { select: Number(el.dataset.id) }); }
      return selectInvoice(Number(el.dataset.id)).then(repaint);
    },
    "new-invoice": function () { return openInvoiceModal(); },
    "add-line-item": function () {
      var v = formValues(modalForm("invoice-form")); state.invoiceFields = v;
      return Api.invoices.lineItem({ sku: v.service, quantity: v.quantity }).then(function (r) {
        state.invoiceErrors = r.ok ? [] : r.errors; state.invoiceMessage = r.ok ? "" : r.message;
        if (r.ok) { state.lineItems.push(r.line_item); } else { report(r); }
        return recalcInvoice();
      });
    },
    "remove-line-item": function (el) { state.lineItems.splice(Number(el.dataset.index), 1); return recalcInvoice(); },
    "invoice-recalc": function () { return recalcInvoice(); },
    "submit-invoice": function () {
      var fields = formValues(modalForm("invoice-form")); state.invoiceFields = fields; notify("Creating invoice…", "");
      return Api.invoices.create({ fields: fields, line_items: state.lineItems }).then(function (r) {
        if (!r.ok) { state.invoiceErrors = r.errors; state.invoiceMessage = r.message; report(r); return recalcInvoice(); }
        closeModal(); report(r);
        return refreshStatus().then(function () { return go("invoices", { select: r.id }); });
      });
    },
    "change-invoice-status": function (el) {
      var v = formValues(el), id = Number(el.dataset.id);
      return Api.invoices.changeStatus({ invoice_id: id, status: v.status, account: v.account }).then(function (r) {
        report(r);
        if (r.ok) { return refreshStatus().then(function () { return go("invoices", { select: id }); }); }
      });
    },
    "open-invoice-pdf": function (el) {
      return Api.invoices.pdf({ invoice_id: Number(el.dataset.id) }).then(function (r) { if (!r.ok) { return report(r); } return Api.app.openPath({ path: r.path }); });
    },
    /* customers / vendors / services */
    "customer-search": function (el) { state.filters.customers.search = el.value; return go("customers").then(refocusSearch); },
    "vendor-search": function (el) { state.filters.vendors.search = el.value; return go("vendors").then(refocusSearch); },
    "service-search": function (el) { state.filters.services.search = el.value; return go("services").then(refocusSearch); },
    "select-customer": function (el) { return Api.customers.get({ customer_id: el.dataset.id }).then(function (d) { state.selected.customer = d.ok ? d : null; repaint(); }); },
    "select-vendor": function (el) { return Api.vendors.get({ vendor_id: el.dataset.id }).then(function (d) { state.selected.vendor = d.ok ? d.vendor : null; repaint(); }); },
    "select-service": function (el) {
      var sku = String(el.dataset.id);
      state.selected.service = ((state.services || {}).services || []).filter(function (s) { return s.sku === sku; })[0] || null;
      repaint();
    },
    "new-customer": function () { openRecordModal("customer", null); },
    "edit-customer": function () { openRecordModal("customer", state.selected.customer && state.selected.customer.customer); },
    "submit-customer": function () { return submitRecord("customer"); },
    "new-vendor": function () { openRecordModal("vendor", null); },
    "edit-vendor": function () { openRecordModal("vendor", state.selected.vendor); },
    "submit-vendor": function () { return submitRecord("vendor"); },
    "new-service": function () { openRecordModal("service", null); },
    "edit-service": function () { openRecordModal("service", state.selected.service); },
    "submit-service": function () { return submitRecord("service"); },
    /* reconcile */
    "reconcile-account": function (el) { return go("reconcile", { account: el.dataset.account }); },
    "reconcile-start": function (el) {
      var v = formValues(el); state.reconcile.fields = v;
      return Api.reconcile.start({ account_id: v.account, statement_date: v.statement_date, statement_balance: v.statement_balance }).then(function (r) {
        state.reconcile.errors = r.ok ? [] : (r.errors || []); state.reconcile.data = r.ok ? r : null;
        if (!r.ok) { report(r); }
        repaint();
      });
    },
    "toggle-cleared": function (el) {
      var id = Number(el.dataset.id), ids = state.reconcile.data.cleared_ids.slice(), at = ids.indexOf(id);
      if (at >= 0) { ids.splice(at, 1); } else { ids.push(id); }
      return reconcileSummary(ids);
    },
    "reconcile-select-all": function () { return reconcileSummary(state.reconcile.data.candidates.map(function (c) { return c.Transaction_ID; })); },
    "reconcile-clear-all": function () { return reconcileSummary([]); },
    "reconcile-finish": function () {
      return Api.reconcile.finish({ cleared_ids: state.reconcile.data.cleared_ids }).then(function (r) {
        report(r);
        if (r.ok) { state.reconcile.data = null; return refreshStatus().then(function () { return go("reconcile"); }); }
      });
    },
    "reconcile-history": function () { return Api.reconcile.history({ account_id: currentReconcileAccount() }).then(function (r) { openModal(R.reconcileHistoryModal(r.history)); }); },
    "reconcile-undo": function () {
      var account = currentReconcileAccount();
      if (!account) { return notify("Select an account first.", "warn"); }
      openModal(R.confirmModal({ title: "Undo the last reconciliation?", message: "Account " + account + ": its most recent statement is removed and the transactions become unreconciled again.", action: "reconcile-undo-confirm", attrs: ' data-account="' + R.esc(account) + '"', confirmLabel: "Undo", danger: true }));
    },
    "reconcile-undo-confirm": function (el) { closeModal(); return Api.reconcile.undo({ account_id: el.dataset.account }).then(function (r) { report(r); state.reconcile.data = null; return go("reconcile"); }); },
    /* properties */
    "save-properties": function (el) {
      var fields = formValues(el); state.propertyFields = fields;
      return Api.properties.save({ fields: fields }).then(function (r) {
        if (!r.ok) { state.propertyErrors = r.errors; state.propertyMessage = r.errors.length ? "" : r.message; repaint(); return report(r); }
        state.properties = r.properties; state.propertyFields = null; state.propertyErrors = []; report(r);
        return refreshStatus().then(repaint);
      });
    },
    /* tools */
    "show-tools": function () { openModal(R.toolsMenu(state)); },
    "show-backups": function () { return Api.backups.list().then(function (r) { if (!r.ok) { return report(r); } openModal(R.backupsModal(r)); }); },
    "restore-backup": function (el) {
      openModal(R.confirmModal({ title: "Restore this backup?", message: "The current database file is preserved as a new backup first. Unsaved changes will be discarded.", action: "restore-backup-confirm", attrs: ' data-path="' + R.esc(el.dataset.path) + '"', confirmLabel: "Restore", danger: true }));
    },
    "restore-backup-confirm": function (el) { closeModal(); notify("Restoring…", ""); return Api.backups.restore({ path: el.dataset.path }).then(function (r) { report(r); return refreshStatus().then(function () { return go("dashboard"); }); }); },
    "export-ledger": function () { closeModal(); return pickPath(Api.dialogs.saveFile, { filename: "ledger.csv" }).then(function (p) { if (p) { return Api.exchange.exportLedger({ path: p }).then(report); } }); },
    "export-all": function () { closeModal(); return pickPath(Api.dialogs.folder).then(function (p) { if (p) { return Api.exchange.exportAll({ folder: p }).then(report); } }); },
    "import-template": function () { closeModal(); return pickPath(Api.dialogs.saveFile, { filename: "transactions_import_template.csv" }).then(function (p) { if (p) { return Api.exchange.template({ path: p }).then(report); } }); },
    "import-transactions": function () {
      closeModal();
      return pickPath(Api.dialogs.file).then(function (path) {
        if (!path) { return; }
        return Api.exchange.import({ path: path, confirm: false }).then(function (r) {
          if (!r.ok) { openModal(R.importProblemsModal(r)); return report(r); }
          openModal(R.importPreviewModal(path, r));
        });
      });
    },
    "import-transactions-confirm": function (el) { closeModal(); notify("Importing…", ""); return Api.exchange.import({ path: el.dataset.path, confirm: true }).then(function (r) { report(r); return refreshStatus().then(function () { return go("ledger"); }); }); },
    "show-preferences": function () { return Api.preferences.get().then(function (r) { openModal(R.preferencesModal(r)); }); },
    "save-preferences": function (el) {
      var v = formValues(el); v.text_scale = Number(v.text_scale);
      return Api.preferences.save({ prefs: v }).then(function (r) { if (r.ok) { applyPreferences(r.preferences); closeModal(); } report(r); });
    },
    "show-shortcuts": function () { openModal(R.shortcutsModal()); },
    "show-paths": function () { return Api.app.paths().then(function (r) { openModal(R.pathsModal(r)); }); },
    "open-data-folder": function () { return Api.app.openDataFolder().then(function (r) { if (!r.ok) { report(r); } }); },
    "show-console": function () { return Api.app.console().then(function (r) { openModal(R.consoleModal(r.lines)); }); },
    "show-docs": function () { closeModal(); return Api.app.openDocs().then(function (r) { if (!r.ok) { report(r); } }); }
  };

  function refocusSearch() { var s = document.querySelector('[name="search"]'); if (s) { s.focus(); s.setSelectionRange(s.value.length, s.value.length); } }

  function dispatch(el, event) {
    var handler = actions[el.dataset.action];
    if (!handler) { return; }
    if (event) { event.preventDefault(); }
    Promise.resolve(handler(el)).catch(function (error) { console.error(error); notify("Something went wrong: " + (error && error.message ? error.message : error), "bad"); });
  }

  /* ------------------------------------------------------------ event wiring */
  document.addEventListener("click", function (event) {
    var el = event.target.closest("[data-action]");
    if (!el || el.tagName === "SELECT" || el.tagName === "INPUT" || el.tagName === "FORM") { return; }
    dispatch(el, event);
  });
  document.addEventListener("change", function (event) {
    var el = event.target;
    if (el.dataset && el.dataset.action && el.tagName === "SELECT") { dispatch(el); return; }
    if (el.name === "sales_tax_rate" && modalForm("invoice-form")) { dispatch({ dataset: { action: "invoice-recalc" } }); }
  });
  var searchTimer = null;
  document.addEventListener("input", function (event) {
    var el = event.target;
    if (el.dataset && /-search$/.test(el.dataset.action || "")) { clearTimeout(searchTimer); searchTimer = setTimeout(function () { dispatch(el); }, 250); }
  });
  document.addEventListener("submit", function (event) { if (event.target.dataset && event.target.dataset.action) { dispatch(event.target, event); } });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && state.modal) { closeModal(); return; }
    if (!(event.ctrlKey || event.metaKey)) { return; }
    var key = event.key.toLowerCase();
    var nav = R.NAV.filter(function (n) { return n.key === key; })[0];
    if (nav) { event.preventDefault(); go(nav.id); return; }
    var map = { s: "save", n: "new-transaction", o: "open-database", i: "new-invoice", m: "show-tools", ",": "show-preferences" };
    if (map[key]) {
      event.preventDefault();
      if (!state.status.database_loaded && ["o", "m", ","].indexOf(key) < 0) { notify("Open or create a database first.", "warn"); return; }
      dispatch({ dataset: { action: map[key] } });
    }
    if (key === "f") { var s = document.querySelector('[name="search"]'); if (s) { event.preventDefault(); s.focus(); s.select(); } }
  });

  /* ----------------------------------------------------------------- start */
  function showFatal(title, detail) {
    document.getElementById("content").innerHTML = '<div class="placeholder"><h3>' + R.esc(title) + "</h3><p>" + R.esc(detail) +
      '</p><p style="margin-top:10px;">Start Iceberg with <span class="kbd">python webapp.py</span>; if this keeps happening, send the text above with your report.</p></div>';
  }

  function start() {
    try {
      var token = window.ApiClient.tokenFromLocation(window.location);
      if (token) { Api = window.ApiClient.build(new window.ApiClient.HttpTransport("", token)); }
      else if (window.MockApi) { Api = window.ApiClient.build(new window.ApiClient.MockTransport(window.MockApi)); }
      else { showFatal("No API available", "The page was opened without a session token and without the preview data."); return; }
    } catch (error) {
      showFatal("The interface could not start", String(error && error.message ? error.message : error));
      return;
    }
    Api.preferences.get().then(function (r) { if (r.ok) { applyPreferences(r.preferences); } });
    refreshStatus().then(function (s) {
      if (s.ok === false) { showFatal("Iceberg's local service did not answer", s.message); return; }
      return go(s.database_loaded ? "dashboard" : "welcome");
    }).catch(function (error) { showFatal("The interface could not start", String(error && error.message ? error.message : error)); });
    setInterval(function () { Api.app.autosave().then(function (r) { if (r && r.message) { report(r); } return refreshStatus(); }); }, 5000);
    window.addEventListener("beforeunload", function () { Api.app.shutdown(); });
  }
  window.addEventListener("error", function (event) {
    var content = document.getElementById("content");
    if (content && !content.firstChild) { showFatal("A script error stopped the interface", String(event.message || event.error)); }
  });
  document.addEventListener("DOMContentLoaded", start);
  window.IcebergApp = { state: state, go: go, notify: notify, actions: actions, api: function () { return Api; } };
})();

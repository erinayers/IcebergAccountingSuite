/* Views for invoices, customers, vendors, and services.  Extends Render. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) { module.exports = factory(require("./render.js")); }
  else { factory(root.Render); }
})(typeof self !== "undefined" ? self : this, function (R) {
  "use strict";
  var esc = R.esc, money = R.money, pill = R.pill, field = R.field, alertBox = R.alertBox;

  var STATUS_KIND = { Due: "info", Overdue: "warn", Paid: "ok", Refunded: "neutral", Canceled: "bad" };

  function statusPill(status) { return pill(status, STATUS_KIND[status] || "neutral"); }

  function listPanel(opts) {
    /* opts: title, count, search(action,value,placeholder), newAction, newLabel, headings[], rows(html), empty */
    return '<div class="panel" style="flex:1;min-height:0;"><div class="panel-head"><h3>' + esc(opts.title) + '<span class="count-badge">' + opts.count + "</span></h3>" +
      '<div class="tools toolbar"><input type="text" name="search" data-action="' + esc(opts.searchAction) + '" placeholder="' + esc(opts.placeholder || "Search…") + '" value="' + esc(opts.search || "") + '" />' +
      (opts.newAction ? '<button class="btn btn-primary btn-sm" data-action="' + esc(opts.newAction) + '">' + esc(opts.newLabel) + "</button>" : "") + "</div></div>" +
      '<div class="table-wrap" style="flex:1;min-height:0;margin-top:12px;"><table class="data"><thead><tr>' +
      opts.headings.map(function (h) { return "<th" + (h.num ? ' class="num"' : "") + ">" + esc(h.label || h) + "</th>"; }).join("") +
      "</tr></thead><tbody>" + (opts.rows || '<tr><td colspan="' + opts.headings.length + '" class="empty">' + esc(opts.empty) + "</td></tr>") + "</tbody></table></div></div>";
  }

  function detailPanel(title, actionsHtml, bodyHtml) {
    return '<div class="panel"><div class="panel-head"><h3>' + title + '</h3><div class="tools">' + (actionsHtml || "") + "</div></div>" +
      '<div class="panel-body">' + bodyHtml + "</div></div>";
  }

  function details(rows) {
    return '<div class="detail-list">' + rows.filter(function (r) { return r; }).map(function (r) {
      return '<div class="detail-row"><span class="k">' + esc(r[0]) + '</span><span class="v' + (r[2] ? " " + r[2] : "") + '">' + (r[3] ? r[1] : esc(r[1] || "—")) + "</span></div>";
    }).join("") + "</div>";
  }

  /* ---------------------------------------------------------------- invoices */

  function invoicesScreen(state) {
    var data = state.invoices || {}, list = data.invoices || [], sel = state.selectedInvoice || null;
    var rows = list.map(function (i) {
      return '<tr class="clickable' + (sel && sel.invoice.id === i.id ? " selected" : "") + '" data-action="select-invoice" data-id="' + i.id + '">' +
        '<td class="mono">' + i.id + '</td><td class="name">' + esc(i.customer_name) + '<span class="sub">' + esc(i.customer_contact) + "</span></td>" +
        '<td class="mono">' + esc(i.created_date) + '</td><td class="mono">' + esc(i.due_date) + "</td>" + R.moneyCell(i.total) + "<td>" + statusPill(i.status) + "</td></tr>";
    }).join("");
    var main = listPanel({ title: "Invoices", count: list.length, searchAction: "invoice-search", search: (data.filters || {}).search, placeholder: "Search number, customer, status…",
      newAction: "new-invoice", newLabel: "+ New Invoice", headings: ["Invoice", "Customer", "Created", "Due", { label: "Total", num: true }, "Status"], rows: rows,
      empty: "No invoices yet. Add a customer and a service, then create the first invoice." });
    var side;
    if (sel) {
      var inv = sel.invoice;
      var items = inv.line_items.map(function (li) { return '<tr><td class="mono">' + esc(li[0]) + "</td><td>" + esc(li[1]) + '</td><td class="num">' + esc(li[3]) + '</td><td class="num">' + esc(li[4]) + "</td></tr>"; }).join("");
      var history = (sel.history || []).map(function (h) { return "<tr><td>" + esc(h[0]) + "</td><td>" + esc(h[1]) + (h[2] ? '<span class="sub">' + esc(h[2]) + "</span>" : "") + '</td><td class="num">' + esc(h[3]) + '</td><td class="mono">' + esc(h[5]) + "</td></tr>"; }).join("");
      var transitions = inv.allowed_transitions || [];
      var statusForm = transitions.length
        ? '<form class="toolbar" data-action="change-invoice-status" data-id="' + inv.id + '" style="margin-top:10px;"><select name="status">' +
          transitions.map(function (t) { return '<option value="' + esc(t) + '">' + esc(t) + "</option>"; }).join("") + "</select>" +
          '<select name="account" title="Deposit / refund account"><option value="">Account (for Paid/Refunded)…</option>' +
          (sel.asset_accounts || []).map(function (a) { return '<option value="' + esc(a.id) + '">' + esc(a.id + " · " + a.name) + "</option>"; }).join("") + "</select>" +
          '<button type="submit" class="btn btn-secondary btn-sm">Change status</button></form>'
        : '<p class="hint" style="margin-top:10px;color:var(--muted-2);font-size:11.5px;">This invoice is ' + esc(inv.status.toLowerCase()) + "; no further changes are possible.</p>";
      side = detailPanel("Invoice " + inv.id + " " + statusPill(inv.status),
        '<button class="btn btn-secondary btn-sm" data-action="open-invoice-pdf" data-id="' + inv.id + '">View PDF</button>',
        details([["Customer", inv.customer_name], ["Contact", inv.customer_contact], ["Email", inv.customer_email], ["Phone", inv.customer_phone],
                 ["Created", inv.created_date, "mono"], ["Due", inv.due_date, "mono"], ["Subtotal", money(inv.subtotal), "mono"], ["Sales tax", money(inv.sales_tax), "mono"],
                 ["Total", money(inv.total), "mono"], ["Tracking code", inv.tracking_code, "mono"]]) +
        '<h4 style="margin:14px 0 6px;font-size:12.5px;">Line items</h4><table class="data"><thead><tr><th>SKU</th><th>Description</th><th class="num">Qty</th><th class="num">Total</th></tr></thead><tbody>' + items + "</tbody></table>" +
        '<h4 style="margin:14px 0 6px;font-size:12.5px;">History</h4><table class="data"><thead><tr><th>When</th><th>Event</th><th class="num">Amount</th><th>Ledger #</th></tr></thead><tbody>' + (history || '<tr><td colspan="4" class="empty">No history.</td></tr>') + "</tbody></table>" + statusForm);
    } else {
      side = detailPanel("Invoice", "", '<div class="empty">Select an invoice to see its details, line items, and history.</div>');
    }
    return R.workspace(state, '<div class="columns" style="flex:1;min-height:0;"><div class="main">' + main + '</div><div class="side" style="flex-basis:420px;">' + side + "</div></div>");
  }

  function invoiceModal(state) {
    var form = state.invoiceForm || {}, f = state.invoiceFields || {}, errors = state.errors || [], items = state.lineItems || [], totals = state.invoiceTotals || { subtotal: 0, sales_tax: 0, total: 0 };
    var customers = [["", "Select a customer…"]].concat((form.customers || []).map(function (c) { return [c.id, c.display_name + (c.contact && c.company ? " · " + c.contact : "")]; }));
    var services = [["", "Select a service…"]].concat((form.services || []).map(function (s) { return [s.sku, s.sku + " · " + s.description + " · " + money(s.price) + (s.taxable ? " (taxable)" : "")]; }));
    var accounts = [["", "Select the deposit account…"]].concat((form.asset_accounts || []).map(function (a) { return [a.id, a.id + " · " + a.name]; }));
    var itemRows = items.map(function (li, index) {
      return '<tr><td class="mono">' + esc(li[0]) + "</td><td>" + esc(li[1]) + '</td><td class="num">' + esc(li[2]) + '</td><td class="num">' + esc(li[3]) + '</td><td class="num">' + esc(li[4]) + "</td>" +
        '<td><button type="button" class="btn btn-ghost btn-sm" data-action="remove-line-item" data-index="' + index + '" title="Remove">' + R.icon("cross", "Remove", "sm") + '</button></td></tr>';
    }).join("");
    var lineError = R.esc((errors.filter(function (e) { return e.field === "line_items"; })[0] || {}).message || "");
    return '<div class="modal-box wide"><h3>New invoice ' + esc(form.next_id || "") + '</h3><p class="modal-sub">Pick the customer, add line items, then create the invoice. The PDF is generated and saved in the receipts folder.</p>' +
      alertBox("bad", state.message && errors.length ? state.message : "", []) +
      '<form id="invoice-form" data-action="submit-invoice">' +
      '<div class="section"><h4>Customer and terms</h4><div class="field-row">' +
      field({ name: "customer_id", label: "Customer", required: true, type: "select", options: customers, value: f.customer_id, errors: errors.map(function (e) { return e.field === "customer" ? { field: "customer_id", message: e.message } : e; }), autofocus: true }) +
      field({ name: "status", label: "Status", required: true, type: "select", options: (form.statuses || ["Due", "Overdue", "Paid"]).map(function (s) { return [s, s]; }), value: f.status || "Due", errors: errors, narrow: true }) +
      field({ name: "due_date", label: "Due date", required: true, type: "date", value: f.due_date || form.today, errors: errors, narrow: true }) + "</div>" +
      '<div class="field-row">' + field({ name: "deposit_account", label: "Deposit account (when already paid)", type: "select", options: accounts, value: f.deposit_account, errors: errors }) +
      field({ name: "sales_tax_rate", label: "Sales tax rate (fraction)", value: f.sales_tax_rate === undefined ? form.sales_tax_rate : f.sales_tax_rate, errors: errors, narrow: true, hint: "0.0625 = 6.25%" }) + "</div></div>" +
      '<div class="section"><h4>Line items <span class="count-badge">' + items.length + " of " + (form.max_line_items || 10) + "</span></h4>" +
      '<div class="field-row"><div class="field" style="flex:3;"><label for="f-service">Service</label><select id="f-service" name="service">' + services.map(function (o) { return '<option value="' + esc(o[0]) + '">' + esc(o[1]) + "</option>"; }).join("") + "</select></div>" +
      '<div class="field narrow"><label for="f-quantity">Qty</label><input type="text" id="f-quantity" name="quantity" value="1" /></div>' +
      '<div class="field narrow" style="justify-content:flex-end;"><button type="button" class="btn btn-secondary" data-action="add-line-item">+ Add line item</button></div></div>' +
      (lineError ? '<div class="form-alert bad">' + lineError + "</div>" : "") +
      '<table class="data"><thead><tr><th>SKU</th><th>Description</th><th class="num">Price</th><th class="num">Qty</th><th class="num">Total</th><th></th></tr></thead><tbody>' +
      (itemRows || '<tr><td colspan="6" class="empty">No line items yet.</td></tr>') + "</tbody></table>" +
      '<div class="stat-row" style="margin:12px 0 0;"><div class="stat-tile"><div class="label">Subtotal</div><div class="value">' + money(totals.subtotal) + '</div></div>' +
      '<div class="stat-tile"><div class="label">Sales tax</div><div class="value">' + money(totals.sales_tax) + '</div></div><div class="stat-tile"><div class="label">Total</div><div class="value">' + money(totals.total) + "</div></div></div></div>" +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">Create invoice</button></div></form></div>';
  }

  /* --------------------------------------------------------------- customers */

  function personFields(f, errors, kind) {
    var phoneTypes = ["Mobile", "Home", "Office", "Work", "Other"].map(function (p) { return [p, p]; });
    var nameField = kind === "vendor"
      ? field({ name: "name", label: "Business name", required: true, value: f.name, errors: errors, autofocus: true })
      : field({ name: "company", label: "Company", value: f.company, errors: errors, autofocus: true, hint: "Company or contact name is required." });
    return '<div class="section"><h4>' + (kind === "vendor" ? "Business" : "Customer") + "</h4>" + nameField +
      (kind === "vendor" ? field({ name: "category", label: "Merchant category", value: f.category, errors: errors }) : "") +
      '<div class="field-row">' + field({ name: "first_name", label: "Contact first name", value: f.first_name, errors: errors }) + field({ name: "last_name", label: "Contact last name", value: f.last_name, errors: errors }) + "</div>" +
      field({ name: "preferred_name", label: "Preferred name", value: f.preferred_name, errors: errors }) + "</div>" +
      '<div class="section"><h4>Contact details</h4><div class="field-row">' + field({ name: "phone", label: "Phone", value: f.phone, errors: errors }) +
      field({ name: "phone_type", label: "Phone type", type: "select", options: phoneTypes, value: f.phone_type || "Mobile", errors: errors, narrow: true }) + "</div>" +
      field({ name: "address", label: "Address", required: kind !== "vendor", type: "textarea", rows: 2, value: f.address, errors: errors, hint: kind === "vendor" ? "" : "Printed on invoices." }) +
      '<div class="field-row">' + field({ name: "email", label: "Email", value: f.email, errors: errors }) + (kind === "vendor" ? field({ name: "website", label: "Website", value: f.website, errors: errors }) : "") + "</div>" +
      field({ name: "notes", label: "Notes", type: "textarea", rows: 2, value: f.notes, errors: errors }) + "</div>";
  }

  function customersScreen(state) {
    var data = state.customers || {}, list = data.customers || [], sel = state.selectedCustomer || null;
    var rows = list.map(function (c) {
      return '<tr class="clickable' + (sel && sel.customer.id === c.id ? " selected" : "") + '" data-action="select-customer" data-id="' + esc(c.id) + '">' +
        '<td class="mono">' + esc(c.id) + '</td><td class="name">' + esc(c.display_name) + (c.company ? '<span class="sub">' + esc(c.contact) + "</span>" : "") + "</td><td>" + esc(c.phone) + "</td><td>" + esc(c.email) + "</td>" + R.moneyCell(c.balance) + "</tr>";
    }).join("");
    var main = listPanel({ title: "Customers", count: list.length, searchAction: "customer-search", search: (data.filters || {}).search, placeholder: "Search name, phone, email…",
      newAction: "new-customer", newLabel: "+ New Customer", headings: ["#", "Customer", "Phone", "Email", { label: "Balance due", num: true }], rows: rows, empty: "No customers yet." });
    var side;
    if (sel) {
      var c = sel.customer;
      var invRows = (sel.invoices || []).map(function (i) { return '<tr class="clickable" data-action="select-invoice" data-id="' + i.id + '" data-screen="invoices"><td class="mono">' + i.id + '</td><td class="mono">' + esc(i.due_date) + "</td>" + R.moneyCell(i.total) + "<td>" + statusPill(i.status) + "</td></tr>"; }).join("");
      side = detailPanel(esc(c.display_name), '<button class="btn btn-secondary btn-sm" data-action="edit-customer" data-id="' + esc(c.id) + '">Edit</button>',
        details([["Customer #", c.id, "mono"], ["Company", c.company], ["Contact", c.contact], ["Preferred name", c.preferred_name], ["Phone", c.phone + (c.phone_type ? " (" + c.phone_type + ")" : "")],
                 ["Email", c.email], ["Address", c.address], ["Notes", c.notes], ["Balance due", money(c.balance), "mono"], ["Added", c.created], ["Edited", c.edited]]) +
        '<h4 style="margin:14px 0 6px;font-size:12.5px;">Invoices</h4><table class="data"><thead><tr><th>#</th><th>Due</th><th class="num">Total</th><th>Status</th></tr></thead><tbody>' + (invRows || '<tr><td colspan="4" class="empty">No invoices.</td></tr>') + "</tbody></table>");
    } else {
      side = detailPanel("Customer", "", '<div class="empty">Select a customer to see details and invoices.</div>');
    }
    return R.workspace(state, '<div class="columns" style="flex:1;min-height:0;"><div class="main">' + main + '</div><div class="side" style="flex-basis:380px;">' + side + "</div></div>");
  }

  function customerModal(state) {
    var f = state.fields || {}, errors = state.errors || [], editing = state.editing;
    return '<div class="modal-box wide"><h3>' + (editing ? "Edit customer " + esc(editing) : "New customer") + '</h3><p class="modal-sub">Customer details appear on invoices.</p>' +
      alertBox("bad", state.message && errors.length ? state.message : "", []) + '<form id="customer-form" data-action="submit-customer">' + personFields(f, errors, "customer") +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">' + (editing ? "Save changes" : "Add customer") + "</button></div></form></div>";
  }

  /* ----------------------------------------------------------------- vendors */

  function vendorsScreen(state) {
    var data = state.vendors || {}, list = data.vendors || [], sel = state.selectedVendor || null;
    var rows = list.map(function (v) {
      return '<tr class="clickable' + (sel && sel.id === v.id ? " selected" : "") + '" data-action="select-vendor" data-id="' + esc(v.id) + '">' +
        '<td class="mono">' + esc(v.id) + '</td><td class="name">' + esc(v.name) + (v.category ? '<span class="sub">' + esc(v.category) + "</span>" : "") + "</td><td>" + esc((v.first_name + " " + v.last_name).trim()) + "</td><td>" + esc(v.phone) + "</td><td>" + esc(v.email) + "</td></tr>";
    }).join("");
    var main = listPanel({ title: "Vendors", count: list.length, searchAction: "vendor-search", search: (data.filters || {}).search, placeholder: "Search name, category, contact…",
      newAction: "new-vendor", newLabel: "+ New Vendor", headings: ["#", "Vendor", "Contact", "Phone", "Email"], rows: rows, empty: "No vendors yet." });
    var side = sel
      ? detailPanel(esc(sel.name), '<button class="btn btn-secondary btn-sm" data-action="edit-vendor" data-id="' + esc(sel.id) + '">Edit</button>',
          details([["Vendor #", sel.id, "mono"], ["Category", sel.category], ["Contact", (sel.first_name + " " + sel.last_name).trim()], ["Preferred name", sel.preferred_name],
                   ["Phone", sel.phone + (sel.phone_type ? " (" + sel.phone_type + ")" : "")], ["Email", sel.email], ["Website", sel.website], ["Address", sel.address], ["Notes", sel.notes], ["Added", sel.created], ["Edited", sel.edited]]))
      : detailPanel("Vendor", "", '<div class="empty">Select a vendor to see details.</div>');
    return R.workspace(state, '<div class="columns" style="flex:1;min-height:0;"><div class="main">' + main + '</div><div class="side">' + side + "</div></div>");
  }

  function vendorModal(state) {
    var f = state.fields || {}, errors = state.errors || [], editing = state.editing;
    return '<div class="modal-box wide"><h3>' + (editing ? "Edit vendor " + esc(editing) : "New vendor") + '</h3><p class="modal-sub">Vendors can be attached to transactions.</p>' +
      alertBox("bad", state.message && errors.length ? state.message : "", []) + '<form id="vendor-form" data-action="submit-vendor">' + personFields(f, errors, "vendor") +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">' + (editing ? "Save changes" : "Add vendor") + "</button></div></form></div>";
  }

  /* ---------------------------------------------------------------- services */

  function servicesScreen(state) {
    var data = state.services || {}, list = data.services || [], sel = state.selectedService || null;
    var rows = list.map(function (s) {
      return '<tr class="clickable' + (sel && sel.sku === s.sku ? " selected" : "") + '" data-action="select-service" data-id="' + esc(s.sku) + '">' +
        '<td class="mono">' + esc(s.sku) + '</td><td class="name">' + esc(s.description) + (s.long_description ? '<span class="sub">' + esc(s.long_description) + "</span>" : "") + "</td>" + R.moneyCell(s.price) + "<td>" + (s.taxable ? pill("Taxable", "info") : pill("Not taxable", "neutral")) + "</td></tr>";
    }).join("");
    var main = listPanel({ title: "Services", count: list.length, searchAction: "service-search", search: (data.filters || {}).search, placeholder: "Search SKU or description…",
      newAction: "new-service", newLabel: "+ New Service", headings: ["SKU", "Description", { label: "Price", num: true }, "Tax"], rows: rows, empty: "No services yet. Services are the line items on invoices." });
    var side = sel
      ? detailPanel(esc(sel.description), '<button class="btn btn-secondary btn-sm" data-action="edit-service" data-id="' + esc(sel.sku) + '">Edit</button>',
          details([["SKU", sel.sku, "mono"], ["Price", money(sel.price), "mono"], ["Taxable", sel.taxable ? "Yes" : "No"], ["Notes", sel.long_description], ["Added", sel.created], ["Edited", sel.edited]]))
      : detailPanel("Service", "", '<div class="empty">Select a service to see details.</div>');
    return R.workspace(state, '<div class="columns" style="flex:1;min-height:0;"><div class="main">' + main + '</div><div class="side">' + side + "</div></div>");
  }

  function serviceModal(state) {
    var f = state.fields || {}, errors = state.errors || [], editing = state.editing;
    return '<div class="modal-box"><h3>' + (editing ? "Edit service " + esc(editing) : "New service") + '</h3><p class="modal-sub">A service is something you sell by the unit or the hour.</p>' +
      alertBox("bad", state.message && errors.length ? state.message : "", []) + '<form id="service-form" data-action="submit-service">' +
      field({ name: "description", label: "Description", required: true, value: f.description, errors: errors, autofocus: true }) +
      '<div class="field-row">' + field({ name: "price", label: "Price ($)", required: true, value: f.price, errors: errors, placeholder: "0.00" }) +
      field({ name: "taxable", label: "Sales tax", required: true, type: "select", options: [["False", "Not taxable"], ["True", "Taxable"]], value: f.taxable === true ? "True" : (f.taxable === false ? "False" : (f.taxable || "False")), errors: errors }) + "</div>" +
      field({ name: "long_description", label: "Notes", type: "textarea", rows: 2, value: f.long_description, errors: errors }) +
      '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">' + (editing ? "Save changes" : "Add service") + "</button></div></form></div>";
  }

  R.statusPill = statusPill; R.listPanel = listPanel; R.detailPanel = detailPanel; R.details = details;
  R.invoices = invoicesScreen; R.invoiceModal = invoiceModal;
  R.customers = customersScreen; R.customerModal = customerModal;
  R.vendors = vendorsScreen; R.vendorModal = vendorModal;
  R.services = servicesScreen; R.serviceModal = serviceModal;
  return R;
});

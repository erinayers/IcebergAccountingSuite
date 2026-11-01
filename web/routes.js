/* The API route table: the single source of truth for every operation the
   interface can perform.  Each entry is
     "group.name": [HTTP method, path, Python handler, [parameter names]]
   Path segments in {braces} are filled from the named parameters; on GET
   the remaining parameters travel as query strings, otherwise as a JSON
   body.  server.py reads this file to build its routes, client.js builds
   Api.group.name(args) from it, and mock.js must implement every handler. */
var API_ROUTES = {
  "app.status":            ["GET",  "/api/status",                   "status",              []],
  "app.console":           ["GET",  "/api/console",                  "console",             []],
  "app.autosave":          ["POST", "/api/autosave",                 "autosave_if_due",     []],
  "app.shutdown":          ["POST", "/api/shutdown",                 "shutdown",            []],
  "app.openPath":          ["POST", "/api/open-path",                "open_path",           ["path"]],
  "app.openDocs":          ["POST", "/api/open-docs",                "open_docs",           []],
  "app.paths":             ["GET",  "/api/paths",                    "paths",               []],
  "app.openDataFolder":    ["POST", "/api/open-data-folder",         "open_data_folder",    []],
  "preferences.get":       ["GET",  "/api/preferences",              "preferences",         []],
  "preferences.save":      ["PUT",  "/api/preferences",              "save_preferences",    ["prefs"]],
  "dialogs.keyFile":       ["POST", "/api/dialogs/key-file",         "pick_key_file",       []],
  "dialogs.file":          ["POST", "/api/dialogs/file",             "pick_file",           []],
  "dialogs.folder":        ["POST", "/api/dialogs/folder",           "pick_folder",         []],
  "dialogs.saveFile":      ["POST", "/api/dialogs/save-file",        "pick_save_file",      ["filename"]],

  "databases.list":        ["GET",  "/api/databases",                "recent_databases",    []],
  "databases.create":      ["POST", "/api/databases",                "create_database",     ["fields"]],
  "databases.open":        ["POST", "/api/databases/open",           "open_database",       ["key_path"]],
  "databases.save":        ["POST", "/api/databases/save",           "save",                []],
  "properties.get":        ["GET",  "/api/properties",               "properties_summary",  []],
  "properties.save":       ["PUT",  "/api/properties",               "update_properties",   ["fields"]],
  "backups.list":          ["GET",  "/api/backups",                  "backups",             []],
  "backups.restore":       ["POST", "/api/backups/restore",          "restore_backup",      ["path"]],

  "dashboard.get":         ["GET",  "/api/dashboard",                "dashboard",           ["type_prefix", "year"]],
  "accounts.list":         ["GET",  "/api/accounts",                 "accounts",            []],
  "accounts.form":         ["GET",  "/api/accounts/form",            "account_form",        []],
  "accounts.get":          ["GET",  "/api/accounts/{account_id}",    "account",             ["account_id"]],
  "accounts.register":     ["GET",  "/api/accounts/{account_id}/register", "account_register", ["account_id"]],
  "accounts.create":       ["POST", "/api/accounts",                 "add_account",         ["fields"]],
  "accounts.update":       ["PUT",  "/api/accounts/{account_id}",    "update_account",      ["account_id", "fields"]],

  "ledger.list":           ["GET",  "/api/ledger",                   "ledger",              ["search", "year"]],
  "transactions.form":     ["GET",  "/api/transactions/form",        "transaction_form",    []],
  "transactions.get":      ["GET",  "/api/transactions/{transaction_id}", "transaction",    ["transaction_id"]],
  "transactions.create":   ["POST", "/api/transactions",             "add_transaction",     ["fields", "confirm_warnings"]],
  "transactions.update":   ["PUT",  "/api/transactions/{transaction_id}", "update_transaction", ["transaction_id", "fields"]],

  "invoices.list":         ["GET",  "/api/invoices",                 "invoices",            ["search"]],
  "invoices.form":         ["GET",  "/api/invoices/form",            "invoice_form",        []],
  "invoices.get":          ["GET",  "/api/invoices/{invoice_id}",    "invoice",             ["invoice_id"]],
  "invoices.totals":       ["POST", "/api/invoices/totals",          "invoice_totals",      ["line_items", "tax_rate"]],
  "invoices.lineItem":     ["POST", "/api/invoices/line-item",       "invoice_line_item",   ["sku", "quantity"]],
  "invoices.create":       ["POST", "/api/invoices",                 "create_invoice",      ["fields", "line_items"]],
  "invoices.changeStatus": ["POST", "/api/invoices/{invoice_id}/status", "change_invoice_status", ["invoice_id", "status", "account"]],
  "invoices.pdf":          ["GET",  "/api/invoices/{invoice_id}/pdf", "invoice_pdf_path",   ["invoice_id"]],

  "customers.list":        ["GET",  "/api/customers",                "customers",           ["search"]],
  "customers.get":         ["GET",  "/api/customers/{customer_id}",  "customer",            ["customer_id"]],
  "customers.save":        ["POST", "/api/customers",                "save_customer",       ["fields", "customer_id"]],
  "vendors.list":          ["GET",  "/api/vendors",                  "vendors",             ["search"]],
  "vendors.get":           ["GET",  "/api/vendors/{vendor_id}",      "vendor",              ["vendor_id"]],
  "vendors.save":          ["POST", "/api/vendors",                  "save_vendor",         ["fields", "vendor_id"]],
  "services.list":         ["GET",  "/api/services",                 "services",            ["search"]],
  "services.save":         ["POST", "/api/services",                 "save_service",        ["fields", "sku"]],

  "reports.periods":       ["GET",  "/api/reports/periods",          "report_periods",      []],
  "reports.run":           ["POST", "/api/reports/run",              "report",              ["report_type", "start", "end"]],
  "reports.export":        ["POST", "/api/reports/export",           "export_report",       ["path"]],

  "reconcile.start":       ["POST", "/api/reconcile/start",          "reconcile_start",     ["account_id", "statement_date", "statement_balance"]],
  "reconcile.summary":     ["POST", "/api/reconcile/summary",        "reconcile_summary",   ["cleared_ids"]],
  "reconcile.finish":      ["POST", "/api/reconcile/finish",         "reconcile_finish",    ["cleared_ids"]],
  "reconcile.history":     ["GET",  "/api/reconcile/history",        "reconcile_history",   ["account_id"]],
  "reconcile.undo":        ["POST", "/api/reconcile/undo",           "reconcile_undo",      ["account_id"]],

  "exchange.exportLedger": ["POST", "/api/exchange/export-ledger",   "export_ledger",       ["path"]],
  "exchange.exportAll":    ["POST", "/api/exchange/export-all",      "export_all",          ["folder"]],
  "exchange.import":       ["POST", "/api/exchange/import",          "import_transactions", ["path", "confirm"]],
  "exchange.template":     ["POST", "/api/exchange/template",        "import_template",     ["path"]]
};
if (typeof module === "object" && module.exports) { module.exports = API_ROUTES; }

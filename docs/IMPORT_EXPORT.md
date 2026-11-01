# Importing and Exporting Data

## Exporting

| Menu item | What you get |
|-----------|--------------|
| *Tools → Export ledger to CSV* | Every transaction with account names, notes, vendor, customer, reconciled date, and local timestamps. |
| *Tools → Export all data to CSV* | A folder of files: `ledger_*.csv`, `accounts_*.csv`, `vendors_*.csv`, `customers_*.csv`, `services_*.csv`, `invoices_*.csv`, plus `invoice_history_*.csv` and `reconciliations_*.csv` when those tables exist. |
| *Export CSV* on the Reports tab | The report currently displayed. |

Files are UTF-8 CSV with a header row. Money columns are in dollars with two decimals
(`1200.00`); dates are `YYYY-MM-DD`; timestamps are shown in your local timezone with
the offset, e.g. `Sunday, 12/21/2025  -  17:52:20 (UTC-05:00)`. File names carry a UTC
stamp so repeated exports never overwrite each other.

These exports are for sharing with an accountant or loading into a spreadsheet. To move
your books to another computer, copy the encrypted `.icb`, its `.icbkey`, and the
`backups` folder instead (see [BACKUP_AND_RESTORE.md](BACKUP_AND_RESTORE.md)).

## Importing transactions

*Tools → Import transactions from CSV* reads a file of journal transactions, checks
every row, shows you what it found, and only then writes them to the ledger.

### File format

A header row followed by one transaction per line. A sample is provided in
[`samples/transactions_import_sample.csv`](samples/transactions_import_sample.csv), and
*Tools → Save an import template* writes one for you.

| Column | Required | Accepted values |
|--------|----------|-----------------|
| `Date` | yes | `YYYY-MM-DD`, `MM/DD/YYYY`, `YYYY/MM/DD`, or `YYYYMMDD`. Day-first dates are rejected rather than guessed. |
| `Name` | yes | Description of the transaction (up to 200 characters). |
| `Amount` | yes | Positive dollars, e.g. `42.18`, `$1,234.50`. Swap the accounts instead of using a negative number. |
| `Debit_Account` | yes | Five-digit account number, optionally followed by the name (`11001 - Office Supplies`). |
| `Credit_Account` | yes | As above; must differ from the debit account. |
| `Notes` | no | Free text. |
| `Vendor` | no | Vendor number or name as you want it stored. |

Column names are matched case-insensitively and a few aliases are understood
(`description`/`payee` for Name, `debit`/`credit`, `memo`). A UTF-8 byte-order mark from
Excel is ignored. Extra columns are ignored.

### What is checked

Each row is validated with the same rules as the New Transaction form: required fields,
a parseable date and amount, accounts that exist in your chart of accounts, and
different debit/credit accounts. Two kinds of outcome:

- **Errors** stop the import. A dialog lists each problem with its line number
  (`Line 7: Debit account 19999 does not exist in the chart of accounts.`). Nothing is
  written until every line passes — you never end up with half a file in the books.
- **Warnings** do not stop it but are shown for confirmation: a row that duplicates a
  transaction already in the ledger (same name, date, amount, and accounts) or another
  row in the same file, or a date more than a year in the future.

After you confirm, the rows are written in one database transaction, the database is
saved (which also creates a backup), and the Ledger tab shows the new entries.

Receipt images cannot be attached by import; add them afterwards with *Edit*.

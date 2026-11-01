# Financial Reports

Open the **Reports** tab (Ctrl+7). Choose the report type, pick a period preset (This Year, Year to Date, Last Year, This/Last
Quarter, This/Last Month, All Time) or type custom *From*/*To* dates, then select
**Run report**. **Export CSV** saves the report you are looking at.

All reports are built from the ledger; nothing is cached, so they always reflect the
transactions currently in the books.

## Income Statement (Profit and Loss)

Revenue (accounts 15xxx) minus expenses (11xxx) for the period, listed by account with
totals and the resulting net income or net loss. Equity withdrawals (12xxx) are not
expenses and are not included.

## Income Statement by Month

The same figures broken into one column per month of the period plus a total column.
Useful for spotting seasonal patterns or a month where an expense was booked twice.

## Balance Sheet

The financial position *as of the To date*: assets (10xxx), liabilities (13xxx), and
equity. Equity is owner equity deposits (14xxx) plus retained earnings, where retained
earnings are all-time revenue minus expenses minus withdrawals through that date.
The report checks that assets equal liabilities plus equity and prints a warning if
they do not (which can only happen if transactions were edited inconsistently).

## Statement of Cash Flows

Shows where cash came from and went during the period, using the direct method.
"Cash" means the default checking (10002) and cash (10004) accounts plus any asset
account that has a bank or credit union entered in its *Institution* field. Each
transaction that moves cash is classified by the other account involved:

| Other account | Activity |
|---------------|----------|
| Revenue, expenses, accounts receivable, accounts payable, sales tax payable, inventory | Operating |
| Other assets (equipment, property, investments) | Investing |
| Liabilities (loans), owner equity deposits, owner withdrawals | Financing |

Transfers between two cash accounts cancel out and are not shown. The summary lists the
net change in cash and the cash balance at the beginning and end of the period.

## Exporting

*Export CSV* on the Reports tab writes the current report as `Section,Line,Amount` rows
(or one column per month for the monthly statement). Amounts are in dollars. See
[IMPORT_EXPORT.md](IMPORT_EXPORT.md) for exporting the underlying data.

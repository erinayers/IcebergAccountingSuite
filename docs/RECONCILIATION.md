# Reconciling an Account

Reconciliation confirms that the transactions in Iceberg for a bank, cash, or credit
card account match the statement the institution sent you. When the two agree, the
balance in your books is proven; when they do not, the unmatched transactions tell you
what to look for.

## Before you start

Have the statement in front of you. You need its **closing date** and **ending balance**.
Every transaction on the statement should already be recorded in Iceberg; if some are
missing (bank fees, interest, a deposit you forgot), record them first from
*Ledger → New Transaction*.

## Steps

1. Open the **Reconcile** tab (Ctrl+8) and pick the account - or click the account on the
   Dashboard and select **Reconcile** on its register.
2. Enter the **Statement date** and the
   **Ending balance** exactly as printed on the statement. For a credit card, enter the
   amount you owe as a positive number.
3. Select **Load transactions**. Iceberg lists every transaction for that account dated on
   or before the statement date that has not been reconciled on a previous statement.
   Amounts are shown from the account's point of view: deposits to a bank account and
   charges to a credit card are positive; withdrawals and card payments are negative.
4. Click each transaction that appears on the statement to tick it as *cleared*; click
   again to untick (*Select all* / *Clear* are available). The summary panel updates as you go:

   | Line | Meaning |
   |------|---------|
   | Previously reconciled balance | Sum of transactions cleared on earlier statements. |
   | Cleared on this statement | Sum of the rows you have selected. |
   | Cleared balance | The two lines above added together. |
   | Statement ending balance | What you typed in step 2. |
   | Difference | Statement balance minus cleared balance. **Zero means you are done.** |
   | Unmatched | Rows you have not selected: transactions in your books that are not on the statement. |

5. When the difference is zero, **Finish reconciliation** becomes available. Selecting it
   marks the cleared transactions with the statement date, records the statement in the
   reconciliation history, and saves the database.

## When the difference is not zero

- **A transaction is on the statement but not in the list.** It has not been recorded in
  Iceberg. Record it (Ctrl+N), then select *Load transactions* again.
- **A transaction is in the list but not on the statement.** Leave it unselected. It is an
  outstanding check or a pending deposit and will appear on a later statement.
- **An amount differs.** Open the transaction on the Ledger tab, correct it with *Edit*,
  and reload.
- **The difference equals one transaction.** You probably missed or double-clicked that row.

Iceberg will not finish an unbalanced reconciliation; the difference must be explained,
not forced.

## History and undo

- **History** lists every completed statement for the selected account with
  its date, ending balance, and the number of transactions cleared.
- **Undo last** removes the most recent statement for the account and makes
  its transactions available to clear again. Use this if you entered the wrong date or
  balance.

## What is stored

- Each cleared transaction gets a `Reconciled_Date` (the statement date) in the ledger.
  The ledger export includes this column so your accountant can see which transactions
  are proven.
- Each finished statement is a row in `tbl_Reconciliations` (account, statement date,
  statement balance, cleared balance, count and IDs of cleared transactions, and when it
  was recorded).

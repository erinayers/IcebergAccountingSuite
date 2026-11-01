# ST-037 — Multi-currency accounts and transactions

- **Status:** Proposed, not started — needs its own design review before estimation
- **Priority:** P3
- **Area:** Multi-Currency

## User story

As a business owner who transacts in more than one currency, I want to record
transactions in a foreign currency with an exchange rate captured at entry time, so my
books reflect true cost and revenue in my home currency.

## Acceptance criteria

- [ ] An account can be designated as denominated in a specific currency, with one
      clearly defined home/reporting currency for the business as a whole.
- [ ] A transaction in a foreign-currency account captures the exchange rate at entry
      time and stores both the foreign-currency amount and the home-currency
      equivalent (not just a single converted number with the original rate lost).
- [ ] `accounting.py`'s balance and signed-effect logic correctly nets
      foreign-currency and home-currency amounts without mixing them incorrectly.
- [ ] `iceberg_utils.py`'s currency formatting displays amounts with the correct
      currency symbol/code per account, not a single hard-coded symbol.
- [ ] Every report (income statement, balance sheet, cash flow) reconciles correctly
      when multi-currency accounts are present, with realized/unrealized exchange gain
      or loss handled explicitly (not silently absorbed into another account).
- [ ] Existing single-currency books continue to work with zero behavior change (this
      must be additive, not a breaking migration).
- [ ] A written design doc covering schema changes, rounding/precision rules, and
      exchange-gain/loss treatment exists and has been reviewed before implementation
      begins.

## Scope notes

Largest and riskiest story in the roadmap: touches `accounting.py`, ledger schema, PDF
rendering, and every report. Do not start implementation before the design review.

# BUG-010 — Creating a database crashed on a non-numeric sales tax and left a partial file

- **Status:** Resolved in 1.3 (ST-009)
- **Priority:** P0
- **Area:** New Database / Database Properties
- **Affected environment:** Windows 10, Python 3.13.0 (reported); all platforms

## Description

The New Database form only checked that fields were non-empty. The sales tax field was
parsed with `Decimal(value) / 100`, so an entry such as `6.25%`, `six`, or a stray
character raised `decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]` and
ended the session:

```
File "iceberg.py", line 1320, in create_database
    icb_session.sales_tax = dec(values[f'-Business_SalesTax_{num}-'])/100
decimal.InvalidOperation
```

Because the tables and default accounts had already been written to `./<Business>.icb`
on disk (unencrypted) before that line ran, the next attempt was refused with
"DATABASE ALREADY EXISTS" in the console and no dialog. The Database Properties editor had
the same parsing problem.

## Resolution

- `validation.validate_database_properties()` checks the form before anything is written:
  business name (and that it makes a valid file name and does not already exist), address,
  sales tax percentage (`6.25` or `6.25%`; blank means 0; must be 0-100), and that the
  filekey and receipts folders exist. Problems are listed in a dialog and the form stays open.
- `create_database` now builds the database inside a try/except; on any failure the
  connection is closed, the partial `.icb` is deleted, and the reason is shown in a dialog.
- An existing database of the same name is reported in a dialog instead of only the console.
- Tests: `tests/test_validation.py::TestOtherRecords::test_parse_percent` and
  `test_database_properties`.

## If you hit this before the fix

Delete the partially created `<Business>.icb` from the Iceberg folder (it contains only the
default chart of accounts) and create the database again.

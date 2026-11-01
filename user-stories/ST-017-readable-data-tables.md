# ST-017 — Readable data tables

- **Status:** Implemented
- **Priority:** P2
- **Area:** Tables

## User story

As a bookkeeper, I want sortable, resizable tables with clearer column headings, row
selection, and legible financial values so I can review records quickly.

## Acceptance criteria

- [x] Every main table supports click-to-sort with value-aware comparisons (dates,
      money including parenthesized negatives, plain numbers) — not naive string sort.
- [x] Sort direction is indicated visually (e.g. ▲/▼) on the active column.
- [x] Sorting preserves any side-panel/detail-view selection mapping (the selected
      row's identity, not its position, is preserved).
- [x] Money columns are right-aligned; rows alternate shading for scan-ability.
- [x] Covered by the table-sorting test suite (`TestTables`).

## Implementation evidence

`web/render_tools.js`, table-sorting tests (`TestTables`).

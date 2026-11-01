# ST-045 — Local LLM plugin for forecasting and reporting narration

- **Status:** Proposed, not started — lowest priority in the roadmap, deliberately last
- **Priority:** P5
- **Area:** AI / Forecasting

## User story

As a business owner, I want an optional plugin that attaches a locally-running LLM to
generate cash-flow/revenue forecasts and plain-language narrative summaries of my
reports, so I can get forward-looking insight and easier-to-read reports without
sending my financial data anywhere off my own machine.

## Acceptance criteria

- [ ] The feature is fully opt-in: disabled by default, with a dedicated Preferences/
      Tools toggle that clearly explains what it does, what data it uses, and what it
      requires (local model download size, disk space, RAM) before the user turns it
      on.
- [ ] A local LLM can be attached via a narrow, swappable provider interface (e.g.
      pointing at a local Ollama server, or an embedded llama.cpp-style runtime) —
      the accounting core has zero new dependencies and zero behavior change when the
      feature is disabled or not installed.
- [ ] **No ledger data, account names, vendor/customer PII, or any other business data
      is ever sent off-device.** This is the non-negotiable constraint given the
      product's existing "local only" privacy positioning (`docs/ARCHITECTURE.md`,
      the website's privacy page per
      [ST-030](ST-030-project-transparency.md)); it must hold even with the feature
      enabled, and should be independently testable by running with outbound network
      access blocked and confirming the feature still works unless a user has
      explicitly pointed it at a non-local endpoint they control.
- [ ] A forecasting capability projects cash flow, revenue, and/or expenses for a
      future period from existing ledger/report data, and every forecast is visibly
      labeled as an estimate (not a guarantee), separate from the authoritative
      numeric reports.
- [ ] A reporting-narration capability generates a plain-language summary of an
      existing report (income statement, balance sheet, cash flow) without altering
      or replacing the underlying numeric report, which remains the source of truth.
- [ ] Only already-computed aggregate figures (the same numbers already shown in
      `reports.py` output) are passed to the model — never raw transaction-level
      detail, names, or notes — to keep the data-exposure surface minimal even though
      everything stays on-device.
- [ ] If the local model is unavailable, unconfigured, or fails to load, the app
      degrades gracefully: all existing reports and bookkeeping functionality
      continue to work unaffected, with a clear status message explaining that the AI
      feature specifically is unavailable and why.
- [ ] Documented in a new `docs/LOCAL_AI.md` (or similar) covering supported local
      runtimes, model/hardware requirements, exactly what data is used, the privacy
      guarantee above, and current limitations.
- [ ] Covered by tests that stub/mock the LLM provider boundary, so the existing
      accounting-core test suite continues to run headless, offline, and without
      requiring an actual model or GPU.

## Scope notes

Deliberately the last story in the roadmap. This introduces a fundamentally different
kind of dependency (a local model runtime, potentially gigabytes of model weights,
meaningful RAM/compute requirements) than anything else in this project, and must not
compromise the "nothing leaves your machine" guarantee that is core to the product's
identity. Before implementation:

- Confirm there's validated user demand — this is a large, optional investment for a
  small-business bookkeeping tool.
- Decide the supported local runtime(s) explicitly (e.g. Ollama as the primary
  integration target, since it already handles model management and runs a local
  HTTP API, which fits this app's existing local-HTTP-server architecture in
  `server.py`) rather than bundling model-serving code directly into Iceberg.
- Consider pairing with [ST-044](ST-044-extension-points-for-reports-transitions-and-shortcuts.md)'s
  extension-point work, since a plugin boundary makes this cleaner to implement and
  keep optional — but ST-044 is not a hard prerequisite.
- Revisit `docs/ARCHITECTURE.md`'s "accounting and persistence modules never import a
  GUI toolkit or pywebview" rule to decide where this plugin's boundary should live so
  it doesn't entangle the accounting core.

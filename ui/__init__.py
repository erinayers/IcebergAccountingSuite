"""User-interface building blocks for Iceberg (P2 stories ST-011 to ST-020).

The modules here hold everything about *how* the application looks and is
navigated, separately from accounting rules (``accounting``, ``reports``,
``reconciliation``, ``invoice_lifecycle``, ``validation``) and persistence
(``db_calls``, ``backups``, ``repository``).  Functions that build widgets take
the PySimpleGUI module as a parameter so the logic can be unit tested without
a display.
"""

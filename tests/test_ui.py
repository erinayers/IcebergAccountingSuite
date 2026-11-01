import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import accessibility, feedback, forms, navigation, preferences, tables, theme
import validation


def keyed_window():
    """A window mock whose window[key] returns a distinct element mock per key."""
    window = MagicMock()
    elements = {}
    window.__getitem__.side_effect = lambda key: elements.setdefault(key, MagicMock())
    return window


class TestTheme(unittest.TestCase):
    def test_every_palette_meets_wcag_aa(self):
        for name, palette in theme.PALETTES.items():
            report = theme.contrast_report(palette)
            failing = {pair: round(ratio, 2) for pair, ratio in report.items() if ratio < 4.5}
            self.assertEqual(failing, {}, f"{name}: {failing}")

    def test_contrast_ratio_reference_values(self):
        self.assertAlmostEqual(theme.contrast_ratio("#000000", "#ffffff"), 21.0, places=1)
        self.assertAlmostEqual(theme.contrast_ratio("#ffffff", "#ffffff"), 1.0, places=3)

    def test_text_scale_changes_every_size(self):
        base = theme.Theme("light", 1.0)
        large = theme.Theme("light", 1.5)
        for key in theme.BASE_SIZES:
            self.assertGreater(large.sizes[key], base.sizes[key])
        self.assertEqual(base.font("medium"), (theme.FONT_FAMILY, 11))
        self.assertEqual(base.font("large", bold=True), (theme.FONT_FAMILY, 15, "bold"))
        self.assertEqual(base.font("medium", mono=True)[0], theme.MONO_FAMILY)

    def test_compact_reduces_rows_and_padding(self):
        self.assertLess(theme.Theme("light", compact=True).row_height, theme.Theme("light").row_height)
        self.assertLess(theme.Theme("light", compact=True).pad["md"], theme.Theme("light").pad["md"])

    def test_unknown_theme_falls_back_to_light(self):
        self.assertEqual(theme.Theme("neon").name, "light")
        self.assertEqual(theme.from_preferences({"theme": "dark", "text_scale": 1.15}).name, "dark")

    def test_window_size_fits_screen(self):
        t = theme.Theme()
        self.assertEqual(t.window_size((1920, 1080)), (1280, 972))
        self.assertEqual(t.window_size((1366, 768)), (1280, 720))   # clamped to the minimum height
        self.assertEqual(t.window_size((800, 600)), (1024, 720))    # never below minimum
        self.assertEqual(t.window_size(None), (1280, 980))          # unknown screen: use the preferred size
        self.assertEqual(t.window_size((0, 0)), (1280, 980))

    def test_apply_sets_pysimplegui_options(self):
        sg = MagicMock()
        theme.Theme("dark").apply(sg)
        sg.theme.assert_called_once_with("DarkGrey13")
        sg.set_options.assert_called_once()


class TestPreferences(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_defaults_when_missing(self):
        self.assertEqual(preferences.load(self.temp), preferences.DEFAULTS)

    def test_round_trip(self):
        saved = preferences.save({"theme": "dark", "text_scale": 1.3, "compact": True}, self.temp)
        self.assertEqual(saved, {"theme": "dark", "text_scale": 1.3, "compact": True})
        self.assertEqual(preferences.load(self.temp), saved)
        self.assertTrue(os.path.isfile(os.path.join(self.temp, "preferences.json")))

    def test_invalid_values_are_normalized(self):
        self.assertEqual(preferences.normalize({"theme": "neon", "text_scale": "huge", "compact": 1}), {"theme": "light", "text_scale": 1.0, "compact": True})
        self.assertEqual(preferences.normalize({"text_scale": 1.2})["text_scale"], 1.15)
        self.assertEqual(preferences.normalize("garbage"), preferences.DEFAULTS)

    def test_damaged_file_does_not_raise(self):
        with open(os.path.join(self.temp, "preferences.json"), "w") as handle:
            handle.write("{not json")
        self.assertEqual(preferences.load(self.temp), preferences.DEFAULTS)

    def test_scale_labels(self):
        self.assertEqual(preferences.scale_label(1.0), "Default")
        self.assertEqual(preferences.scale_from_label("Extra large"), 1.5)
        self.assertEqual(preferences.scale_from_label("nonsense"), 1.0)


class TestNavigation(unittest.TestCase):
    def test_tab_registry_is_consistent(self):
        self.assertEqual(len(navigation.TAB_KEYS), 13)
        self.assertEqual(navigation.TAB_INDEX["-Reconcile_Tab-"], 12)
        self.assertEqual(navigation.TAB_INDEX["-Reports_Tab-"], 2)
        for _, _, index, _ in navigation.NAV_ITEMS:
            self.assertLess(index, len(navigation.TAB_KEYS))

    def test_nav_key_translation(self):
        self.assertEqual(navigation.event_for_nav_key(navigation.nav_key("Ledger")), "View Ledger")
        self.assertEqual(navigation.event_for_nav_key("Something else"), "Something else")
        self.assertEqual(navigation.index_for_event("Point of Sale"), 5)
        self.assertEqual(navigation.active_item_for_tab(12), "Reconcile")
        self.assertIsNone(navigation.active_item_for_tab(8))

    def test_build_nav_bar_and_highlight(self):
        sg = MagicMock()
        t = theme.Theme()
        row = navigation.build_nav_bar(sg, t)
        self.assertEqual(sg.Button.call_count, len(navigation.NAV_ITEMS))
        self.assertTrue(all(c.kwargs["disabled"] for c in sg.Button.call_args_list))
        window = keyed_window()
        navigation.show_tab(window, t, 1)
        window["-Ledger_Tab-"].update.assert_any_call(visible=True)
        window["-Ledger_Tab-"].select.assert_called()
        window["-Dashboard_Tab-"].update.assert_any_call(visible=False)
        active = window[navigation.nav_key("Ledger")].update.call_args.kwargs["button_color"]
        inactive = window[navigation.nav_key("Dashboard")].update.call_args.kwargs["button_color"]
        self.assertEqual(active, (t.color("nav_active_text"), t.color("nav_active")))
        self.assertEqual(inactive, (t.color("nav_inactive_text"), t.color("nav_inactive")))
        window["-Nav_Location-"].update.assert_called_with("View Ledger")
        navigation.set_enabled(window, True)
        window[navigation.nav_key("Reports")].update.assert_called_with(disabled=False)


class TestTables(unittest.TestCase):
    def test_sort_key_orders_money_dates_and_text(self):
        self.assertLess(tables.sort_key("($1,200.00)"), tables.sort_key("$0.05"))
        self.assertLess(tables.sort_key("$999.99"), tables.sort_key("$1,000.00"))
        self.assertLess(tables.sort_key("2025-01-31"), tables.sort_key("2025-02-01"))
        self.assertLess(tables.sort_key("apple"), tables.sort_key("Banana"))
        self.assertLess(tables.sort_key(""), tables.sort_key("2025-01-01"))
        self.assertLess(tables.sort_key("10002"), tables.sort_key("10010"))

    def test_sort_rows_keeps_backing_aligned(self):
        rows = [["2", "b", "$5.00"], ["1", "a", "$10.00"], ["3", "c", "($1.00)"]]
        backing = ["two", "one", "three"]
        sorted_rows, sorted_backing = tables.sort_rows(rows, 2, False, backing)
        self.assertEqual([r[0] for r in sorted_rows], ["3", "2", "1"])
        self.assertEqual(sorted_backing, ["three", "two", "one"])

    def test_sorter_toggles_and_sorts_in_place(self):
        sorter = tables.TableSorter()
        rows = [["2", "b"], ["1", "a"], ["3", "c"]]
        sorter.register("-T-", rows, headings=["Id", "Name"])
        result_rows, backing, descending = sorter.sort("-T-", 0)
        self.assertFalse(descending)
        self.assertEqual([r[0] for r in rows], ["1", "2", "3"])      # the caller's list was reordered
        self.assertIs(result_rows, rows)
        self.assertIs(backing, rows)
        _, _, descending = sorter.sort("-T-", 0)
        self.assertTrue(descending)
        self.assertEqual([r[0] for r in rows], ["3", "2", "1"])
        self.assertEqual(sorter.headings_with_indicator("-T-"), ["Id \u25bc", "Name"])
        self.assertIsNone(sorter.sort("-T-", 9))
        self.assertIsNone(sorter.sort("-missing-", 0))

    def test_sorter_with_separate_backing(self):
        sorter = tables.TableSorter()
        rows = [["b"], ["a"]]
        backing = [{"id": 2}, {"id": 1}]
        sorter.register("-T-", rows, backing)
        sorter.sort("-T-", 0)
        self.assertEqual([b["id"] for b in backing], [1, 2])
        self.assertIs(sorter.backing("-T-"), backing)

    def test_parse_click_event(self):
        self.assertEqual(tables.parse_click_event(("-T-", "+CLICKED+", (-1, 2))), ("-T-", -1, 2))
        self.assertIsNone(tables.parse_click_event("-T-"))
        self.assertIsNone(tables.parse_click_event(("-T-", "+CLICKED+", (None, None))))
        self.assertIsNone(tables.parse_click_event(("-T-", "other", (1, 1))))

    def test_money_columns_right_aligned(self):
        self.assertEqual(tables.money_column_justification(["Transaction", "Name", "Amount", "Date"]), ["c", "l", "r", "c"])
        kwargs = tables.table_kwargs(theme.Theme(), ["Invoice", "Total"])
        self.assertTrue(kwargs["enable_click_events"])
        self.assertEqual(kwargs["cols_justification"], ["c", "r"])


class TestFeedback(unittest.TestCase):
    def test_save_state_text(self):
        self.assertEqual(feedback.save_state_text(False, False, "", 0), "No database open")
        self.assertIn("autosave in 4:05", feedback.save_state_text(True, True, "", 245))
        self.assertEqual(feedback.save_state_text(True, False, "14:52 (UTC-04:00)", 0), "All changes saved 14:52 (UTC-04:00)")
        self.assertEqual(feedback.save_state_text(True, False, "", 0), "No unsaved changes")
        self.assertEqual(feedback.format_countdown(-5), "0:00")

    def test_notify_colours_by_level(self):
        window, t = keyed_window(), theme.Theme()
        text = feedback.notify(window, t, "Saved", "success")
        self.assertTrue(text.endswith("Saved"))
        window["-Status_Message-"].update.assert_called_with(text, text_color=t.color("success"))
        feedback.notify(window, t, "Working", "working")
        window.refresh.assert_called()
        feedback.notify(window, t, "x", "bogus-level")
        window["-Status_Message-"].update.assert_called_with("\u2139 x", text_color=t.color("info"))
        feedback.update_save_state(window, t, "Unsaved", True)
        window["-Save_State-"].update.assert_called_with("Unsaved", text_color=t.color("warning"))

    def test_build_status_bar(self):
        sg = MagicMock()
        row = feedback.build_status_bar(sg, theme.Theme())
        self.assertEqual(len(row), 2)
        keys = [c.kwargs["key"] for c in sg.Text.call_args_list]
        self.assertEqual(keys, ["-Status_Message-", "-Save_State-"])


class TestForms(unittest.TestCase):
    def test_show_errors_marks_fields_and_writes_message(self):
        window, t = keyed_window(), theme.Theme()
        result = validation.validate_transaction({"name": "", "date": "x", "amount": "5", "debit_account": "10002", "credit_account": "10002"}, ["10002"])
        field_map = {"name": "-N-", "date": "-D-", "amount": "-A-"}
        ok = forms.show_errors(window, t, "-Msg-", result, field_map)
        self.assertFalse(ok)
        message = window["-Msg-"].update.call_args.args[0]
        self.assertIn("Transaction name is required.", message)
        window["-N-"].update.assert_any_call(background_color=t.color("field_error_bg"))
        window["-D-"].update.assert_any_call(background_color=t.color("field_error_bg"))
        window["-A-"].update.assert_called_with(background_color=t.color("field_bg"))  # cleared, not marked

    def test_show_errors_clears_when_valid(self):
        window, t = keyed_window(), theme.Theme()
        result = validation.validate_transaction({"name": "Rent", "date": "2025-01-01", "amount": "5", "debit_account": "11001", "credit_account": "10002"}, ["10002", "11001"])
        self.assertTrue(forms.show_errors(window, t, "-Msg-", result, {"name": "-N-"}))
        window["-Msg-"].update.assert_called_with("", text_color=t.color("warning"))

    def test_builders(self):
        sg, t = MagicMock(), theme.Theme()
        forms.label(sg, t, "Amount", required=True)
        self.assertEqual(sg.Text.call_args.args[0], "Amount *")
        forms.section(sg, t, "Details", [[]])
        sg.Frame.assert_called_once()
        self.assertEqual(len(forms.message_row(sg, t, "-M-")), 1)


class TestAccessibility(unittest.TestCase):
    def test_shortcuts_unique_and_cover_navigation(self):
        sequences = [seq for seq, _, _, _ in accessibility.SHORTCUTS]
        self.assertEqual(len(sequences), len(set(sequences)))
        events = {event for _, event, _, _ in accessibility.SHORTCUTS}
        for _, event, _, shortcut in navigation.NAV_ITEMS:
            self.assertIn(event, events, f"{event} has no shortcut")
            self.assertIn(shortcut, [label for _, _, label, _ in accessibility.SHORTCUTS])

    def test_bind_shortcuts(self):
        window = MagicMock()
        self.assertEqual(accessibility.bind_shortcuts(window), len(accessibility.SHORTCUTS))
        window.bind.assert_any_call("<Control-s>", "Save Database")

    def test_help_text_lists_every_shortcut(self):
        text = accessibility.shortcut_help_text()
        for _, _, label, description in accessibility.SHORTCUTS:
            self.assertIn(label, text)
            self.assertIn(description, text)

    def test_focus_helper(self):
        window = MagicMock()
        self.assertTrue(accessibility.focus_first_input(window, "-X-"))
        window["-X-"].set_focus.assert_called_once()
        broken = MagicMock()
        broken.__getitem__.side_effect = KeyError
        self.assertFalse(accessibility.focus_first_input(broken, "-X-"))


if __name__ == "__main__":
    unittest.main()

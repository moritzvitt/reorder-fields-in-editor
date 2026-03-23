from __future__ import annotations

from aqt import dialogs, mw
from aqt.utils import showInfo

_LAST_BROWSER = None


def register_browser_instance(browser) -> None:
    global _LAST_BROWSER
    _LAST_BROWSER = browser

    def _clear() -> None:
        global _LAST_BROWSER
        if _LAST_BROWSER is browser:
            _LAST_BROWSER = None

    try:
        browser.form.destroyed.connect(_clear)
    except Exception:
        pass


def current_browser():
    if _LAST_BROWSER is not None:
        return _LAST_BROWSER
    dialog = dialogs._dialogs.get("Browser")
    if not dialog:
        return None
    if isinstance(dialog, type):
        return None
    if isinstance(dialog, list):
        for candidate in reversed(dialog):
            if candidate is not None:
                return candidate
    if isinstance(dialog, tuple):
        browser = dialog[1] if dialog[1] is not None else dialog[0]
    else:
        browser = dialog
    return browser


def browser_selected_note_ids(browser) -> list[int]:
    if browser is None or isinstance(browser, type):
        return []
    if hasattr(browser, "selected_notes"):
        try:
            return list(browser.selected_notes())
        except (TypeError, RuntimeError):
            return []
    if hasattr(browser, "selectedNotes"):
        try:
            return list(browser.selectedNotes())
        except (TypeError, RuntimeError):
            return []
    if hasattr(browser, "selected_cards"):
        try:
            card_ids = browser.selected_cards()
            return list({mw.col.get_card(cid).note_id for cid in card_ids})
        except (TypeError, RuntimeError):
            return []
    if hasattr(browser, "selectedCards"):
        try:
            card_ids = browser.selectedCards()
            return list({mw.col.get_card(cid).note_id for cid in card_ids})
        except (TypeError, RuntimeError):
            return []
    return []


def get_selected_notes(n: int) -> list[int]:
    browser = current_browser()
    if browser is None:
        showInfo("ChatGPT Helper: Open the Browser and select notes.")
        return []
    note_ids = browser_selected_note_ids(browser)
    if not note_ids:
        try:
            editor = getattr(browser, "editor", None)
            note = getattr(editor, "note", None) if editor is not None else None
            if note is not None and getattr(note, "id", None):
                note_ids = [int(note.id)]
        except Exception:
            note_ids = []
    if not note_ids:
        showInfo("ChatGPT Helper: No notes selected or focused.")
        return []
    return list(note_ids[:n])


def refresh_browser_note(note) -> None:
    note_id = getattr(note, "id", None)
    if not note_id:
        return
    browser = current_browser()
    if browser is None:
        return
    try:
        if hasattr(browser, "refresh"):
            browser.refresh()
        browser.model.reset()
    except Exception:
        try:
            if hasattr(browser, "onReset"):
                browser.onReset()
            browser.model().reset()
        except Exception:
            pass
    try:
        editor = getattr(browser, "editor", None)
        current = getattr(editor, "note", None) if editor is not None else None
        if (
            current is not None
            and getattr(current, "id", None) == note_id
            and hasattr(editor, "tags")
        ):
            if hasattr(editor, "set_note"):
                editor.set_note(note)
            elif hasattr(editor, "setNote"):
                editor.setNote(note)
            else:
                editor.loadNote()
    except Exception:
        pass


def unwrap_editor(editor):
    return getattr(editor, "editor", editor)


def resolve_editor_note(editor):
    note = getattr(editor, "note", None)
    if callable(note):
        try:
            note = note()
        except Exception:
            note = None
    if note is None and hasattr(editor, "currentNote"):
        try:
            note = editor.currentNote()
        except Exception:
            note = None
    if note is not None and getattr(note, "id", None):
        return note
    browser = current_browser()
    if browser is not None:
        note_ids = browser_selected_note_ids(browser)
        if note_ids:
            return mw.col.get_note(note_ids[0])
    reviewer = getattr(mw, "reviewer", None)
    card = getattr(reviewer, "card", None) if reviewer is not None else None
    if card is not None:
        try:
            return card.note()
        except Exception:
            return None
    return None

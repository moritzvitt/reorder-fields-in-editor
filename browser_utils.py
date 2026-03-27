from __future__ import annotations

from aqt import dialogs

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

from __future__ import annotations

import sys

from aqt import dialogs, gui_hooks, mw, qconnect
from aqt.qt import (
    QAction,
    QActionGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequence,
    QLineEdit,
    QMenu,
    QTimer,
    Qt,
)
from aqt.utils import askUser, showInfo, tooltip

from .utils.chatgpt_helper import (
    build_batch_prompt,
    build_prompt_for_note,
    parse_batch_response,
)

CHATGPT_MODE_OFF = "OFF"
CHATGPT_MODE_SINGLE = "SINGLE"
CHATGPT_MODE_BATCH = "BATCH"

CHATGPT_CONFIG_MODE = "chatgpt_helper_mode"
CHATGPT_CONFIG_SHORTCUT = "chatgpt_helper_shortcut"
CHATGPT_CONFIG_LEMMA_FIELD = "chatgpt_field_lemma"
CHATGPT_CONFIG_SUBTITLE_FIELD = "chatgpt_field_subtitle"
CHATGPT_CONFIG_QUESTION_FIELD = "chatgpt_field_question"
CHATGPT_CONFIG_GRAMMAR_FIELD = "chatgpt_field_grammar"

CHATGPT_DEFAULT_SHORTCUT = (
    "Meta+Shift+G" if sys.platform == "darwin" else "Ctrl+Shift+G"
)

_CHATGPT_SHORTCUT_ACTION: QAction | None = None
_CHATGPT_WAIT_TIMER: QTimer | None = None
_CHATGPT_PENDING: dict[str, object] | None = None
_LAST_BROWSER = None

_CHATGPT_MODE_ACTIONS: dict[str, QAction] = {}


def _get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(__name__) or {}
    if CHATGPT_CONFIG_MODE not in config:
        config[CHATGPT_CONFIG_MODE] = CHATGPT_MODE_SINGLE
    if CHATGPT_CONFIG_SHORTCUT not in config or not str(
        config.get(CHATGPT_CONFIG_SHORTCUT) or ""
    ).strip():
        config[CHATGPT_CONFIG_SHORTCUT] = CHATGPT_DEFAULT_SHORTCUT
    if CHATGPT_CONFIG_LEMMA_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_LEMMA_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_LEMMA_FIELD] = "Lemma"
    if CHATGPT_CONFIG_SUBTITLE_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_SUBTITLE_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_SUBTITLE_FIELD] = "Subtitle"
    if CHATGPT_CONFIG_QUESTION_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_QUESTION_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_QUESTION_FIELD] = "Question"
    if CHATGPT_CONFIG_GRAMMAR_FIELD not in config or not str(
        config.get(CHATGPT_CONFIG_GRAMMAR_FIELD) or ""
    ).strip():
        config[CHATGPT_CONFIG_GRAMMAR_FIELD] = "Grammar"
    return config


def _save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(__name__, config)


def _run_open_config() -> None:
    config = _get_addon_config()
    dialog = QDialog(mw)
    dialog.setWindowTitle("Prompt Addon Configuration")
    layout = QFormLayout(dialog)
    layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    chatgpt_shortcut_edit = QLineEdit()
    chatgpt_shortcut_edit.setText(str(config.get(CHATGPT_CONFIG_SHORTCUT, "")))
    layout.addRow("Shortcut:", chatgpt_shortcut_edit)

    chatgpt_lemma_edit = QLineEdit()
    chatgpt_lemma_edit.setText(str(config.get(CHATGPT_CONFIG_LEMMA_FIELD, "Lemma")))
    layout.addRow("Lemma Field:", chatgpt_lemma_edit)

    chatgpt_subtitle_edit = QLineEdit()
    chatgpt_subtitle_edit.setText(
        str(config.get(CHATGPT_CONFIG_SUBTITLE_FIELD, "Subtitle"))
    )
    layout.addRow("Subtitle Field:", chatgpt_subtitle_edit)

    chatgpt_question_edit = QLineEdit()
    chatgpt_question_edit.setText(
        str(config.get(CHATGPT_CONFIG_QUESTION_FIELD, "Question"))
    )
    layout.addRow("Question Field (optional):", chatgpt_question_edit)

    chatgpt_grammar_edit = QLineEdit()
    chatgpt_grammar_edit.setText(
        str(config.get(CHATGPT_CONFIG_GRAMMAR_FIELD, "Grammar"))
    )
    layout.addRow("Grammar Field:", chatgpt_grammar_edit)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    shortcut_value = chatgpt_shortcut_edit.text().strip()
    config[CHATGPT_CONFIG_SHORTCUT] = shortcut_value or CHATGPT_DEFAULT_SHORTCUT
    config[CHATGPT_CONFIG_LEMMA_FIELD] = chatgpt_lemma_edit.text().strip() or "Lemma"
    config[CHATGPT_CONFIG_SUBTITLE_FIELD] = (
        chatgpt_subtitle_edit.text().strip() or "Subtitle"
    )
    config[CHATGPT_CONFIG_QUESTION_FIELD] = (
        chatgpt_question_edit.text().strip() or "Question"
    )
    config[CHATGPT_CONFIG_GRAMMAR_FIELD] = (
        chatgpt_grammar_edit.text().strip() or "Grammar"
    )
    _save_addon_config(config)
    _refresh_chatgpt_shortcut()
    showInfo("Configuration saved.")


def _refresh_chatgpt_shortcut() -> None:
    global _CHATGPT_SHORTCUT_ACTION
    config = _get_addon_config()
    sequence = str(config.get(CHATGPT_CONFIG_SHORTCUT) or CHATGPT_DEFAULT_SHORTCUT)
    sequences = [sequence]
    if sys.platform == "darwin":
        normalized = sequence.replace("Command", "Meta").replace("Cmd", "Meta")
        if "Ctrl" in normalized and "Meta" not in normalized:
            sequences.append(normalized.replace("Ctrl", "Meta"))
    if _CHATGPT_SHORTCUT_ACTION is None:
        action = QAction("ChatGPT Helper Trigger", mw)
        action.setShortcuts([QKeySequence(s) for s in sequences])
        action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        qconnect(action.triggered, _run_chatgpt_helper)
        mw.addAction(action)
        _CHATGPT_SHORTCUT_ACTION = action
    else:
        _CHATGPT_SHORTCUT_ACTION.setShortcuts([QKeySequence(s) for s in sequences])


def _register_browser_instance(browser) -> None:
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


def _current_browser():
    if _LAST_BROWSER is not None:
        return _LAST_BROWSER
    dialog = dialogs._dialogs.get("Browser")
    if not dialog:
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


def _browser_selected_note_ids(browser) -> list[int]:
    if hasattr(browser, "selected_notes"):
        return list(browser.selected_notes())
    if hasattr(browser, "selectedNotes"):
        return list(browser.selectedNotes())
    if hasattr(browser, "selected_cards"):
        card_ids = browser.selected_cards()
        return list({mw.col.get_card(cid).note_id for cid in card_ids})
    if hasattr(browser, "selectedCards"):
        card_ids = browser.selectedCards()
        return list({mw.col.get_card(cid).note_id for cid in card_ids})
    return []


def get_selected_notes(n: int) -> list[int]:
    browser = _current_browser()
    if browser is None:
        showInfo("ChatGPT Helper: Open the Browser and select notes.")
        return []
    note_ids = _browser_selected_note_ids(browser)
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


def copy_to_clipboard(text: str) -> None:
    mw.app.clipboard().setText(text)


def wait_for_clipboard_change(old_text: str) -> None:
    global _CHATGPT_WAIT_TIMER
    if _CHATGPT_WAIT_TIMER is not None:
        _CHATGPT_WAIT_TIMER.stop()
    timer = QTimer(mw)
    timer.setInterval(500)
    timer.timeout.connect(lambda: _poll_clipboard(old_text))
    timer.start()
    _CHATGPT_WAIT_TIMER = timer


def _read_clipboard_payload() -> tuple[str, str]:
    clipboard = mw.app.clipboard()
    mime = clipboard.mimeData()
    if mime is None:
        return "", ""
    plain = mime.text() or ""
    html = mime.html() or ""
    rtf = ""
    if mime.hasFormat("text/rtf"):
        try:
            rtf = bytes(mime.data("text/rtf")).decode("utf-8", "replace")
        except Exception:
            rtf = ""
    if rtf:
        content = rtf
        compare = plain or rtf
    elif mime.hasHtml():
        content = html
        compare = plain or html
    else:
        content = plain
        compare = plain
    if not content:
        content = clipboard.text() or ""
    if not compare:
        compare = content
    return content, compare


def write_to_field(note, field_name: str, content: str) -> None:
    note[field_name] = (content or "").strip()
    mw.col.update_note(note)
    try:
        note.flush()
    except Exception:
        pass
    _refresh_browser_note(note)


def _refresh_browser_note(note) -> None:
    note_id = getattr(note, "id", None)
    if not note_id:
        return
    browser = _current_browser()
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
        if current is not None and getattr(current, "id", None) == note_id:
            if hasattr(editor, "set_note"):
                editor.set_note(note)
            elif hasattr(editor, "setNote"):
                editor.setNote(note)
            else:
                editor.loadNote()
    except Exception:
        pass


def _poll_clipboard(old_text: str) -> None:
    if _CHATGPT_WAIT_TIMER is None or _CHATGPT_PENDING is None:
        return
    content, compare = _read_clipboard_payload()
    if not compare or compare.strip() == (old_text or "").strip():
        return
    _CHATGPT_WAIT_TIMER.stop()
    _handle_chatgpt_response(content)


def _handle_chatgpt_response(text: str) -> None:
    global _CHATGPT_PENDING, _CHATGPT_WAIT_TIMER
    pending = _CHATGPT_PENDING or {}
    mode = pending.get("mode")
    note_ids = list(pending.get("note_ids", []))
    grammar_field = str(pending.get("grammar_field", "Grammar"))
    _CHATGPT_PENDING = None
    _CHATGPT_WAIT_TIMER = None

    if not note_ids:
        showInfo("ChatGPT Helper: No pending notes to update.")
        return

    if mode == CHATGPT_MODE_BATCH:
        try:
            mapping = parse_batch_response(text, note_ids)
        except ValueError as exc:
            showInfo(f"ChatGPT Helper: Failed to parse response. {exc}")
            return
        for nid, content in mapping.items():
            note = mw.col.get_note(nid)
            write_to_field(note, grammar_field, content)
        tooltip(f"ChatGPT Helper: Updated {len(mapping)} notes.")
        return

    note = mw.col.get_note(note_ids[0])
    write_to_field(note, grammar_field, text)
    tooltip("ChatGPT Helper: Updated 1 note.")


def _chatgpt_required_fields(config: dict[str, str]) -> dict[str, str]:
    return {
        "lemma": str(config.get(CHATGPT_CONFIG_LEMMA_FIELD, "Lemma")),
        "subtitle": str(config.get(CHATGPT_CONFIG_SUBTITLE_FIELD, "Subtitle")),
        "question": str(config.get(CHATGPT_CONFIG_QUESTION_FIELD, "Question")),
        "grammar": str(config.get(CHATGPT_CONFIG_GRAMMAR_FIELD, "Grammar")),
    }


def _run_chatgpt_helper() -> None:
    global _CHATGPT_PENDING, _CHATGPT_WAIT_TIMER
    config = _get_addon_config()
    mode = str(config.get(CHATGPT_CONFIG_MODE) or CHATGPT_MODE_OFF)
    if mode == CHATGPT_MODE_OFF:
        for candidate in (CHATGPT_MODE_SINGLE, CHATGPT_MODE_BATCH):
            action = _CHATGPT_MODE_ACTIONS.get(candidate)
            if action is not None and action.isChecked():
                mode = candidate
                config[CHATGPT_CONFIG_MODE] = candidate
                _save_addon_config(config)
                break
        if mode == CHATGPT_MODE_OFF:
            tooltip("ChatGPT Helper is OFF.")
            return

    if _CHATGPT_WAIT_TIMER is not None and _CHATGPT_WAIT_TIMER.isActive():
        if not askUser(
            "ChatGPT Helper is already waiting for clipboard change. Cancel and restart?"
        ):
            return
        _CHATGPT_WAIT_TIMER.stop()
        _CHATGPT_PENDING = None
        _CHATGPT_WAIT_TIMER = None

    limit = 1 if mode == CHATGPT_MODE_SINGLE else 5
    note_ids = get_selected_notes(limit)
    if not note_ids:
        return

    fields = _chatgpt_required_fields(config)
    required = [fields["lemma"], fields["subtitle"], fields["grammar"]]
    if fields["question"]:
        required.append(fields["question"])

    notes = []
    missing: list[int] = []
    for nid in note_ids:
        note = mw.col.get_note(nid)
        if any(field not in note for field in required):
            missing.append(nid)
            continue
        notes.append(note)
    if missing:
        showInfo(
            "ChatGPT Helper: Missing required fields in selected notes. "
            f"Missing in {len(missing)} notes."
        )
        return

    if mode == CHATGPT_MODE_SINGLE:
        prompt = build_prompt_for_note(
            notes[0],
            lemma_field=fields["lemma"],
            subtitle_field=fields["subtitle"],
            question_field=fields["question"],
        )
    else:
        prompt, note_ids = build_batch_prompt(
            notes,
            lemma_field=fields["lemma"],
            subtitle_field=fields["subtitle"],
            question_field=fields["question"],
        )

    copy_to_clipboard(prompt)
    _CHATGPT_PENDING = {
        "mode": mode,
        "note_ids": note_ids,
        "grammar_field": fields["grammar"],
    }
    wait_for_clipboard_change(prompt)
    tooltip("ChatGPT Helper: Prompt copied. Waiting for clipboard response.")


def _set_chatgpt_mode(mode: str) -> None:
    config = _get_addon_config()
    config[CHATGPT_CONFIG_MODE] = mode
    _save_addon_config(config)
    for key, action in _CHATGPT_MODE_ACTIONS.items():
        action.setChecked(key == mode)
    tooltip(f"ChatGPT Helper mode: {mode}")


def _add_chatgpt_menu() -> None:
    menu = QMenu("Prompt Generation", mw)
    group = QActionGroup(menu)
    group.setExclusive(True)
    options = [
        ("Off", CHATGPT_MODE_OFF),
        ("On (Individual Prompt)", CHATGPT_MODE_SINGLE),
        ("On (Bulk: 5 notes)", CHATGPT_MODE_BATCH),
    ]
    for label, mode in options:
        action = QAction(label, menu)
        action.setCheckable(True)
        group.addAction(action)
        menu.addAction(action)
        _CHATGPT_MODE_ACTIONS[mode] = action
        qconnect(action.triggered, lambda _checked=False, m=mode: _set_chatgpt_mode(m))
    current = str(_get_addon_config().get(CHATGPT_CONFIG_MODE) or CHATGPT_MODE_OFF)
    if current in _CHATGPT_MODE_ACTIONS:
        _CHATGPT_MODE_ACTIONS[current].setChecked(True)
    mw.form.menuTools.addMenu(menu)


action = QAction("Prompt Addon Configuration", mw)
qconnect(action.triggered, _run_open_config)
mw.form.menuTools.addAction(action)

_add_chatgpt_menu()
_refresh_chatgpt_shortcut()

if hasattr(gui_hooks, "browser_menus"):
    gui_hooks.browser_menus.append(_register_browser_instance)
elif hasattr(gui_hooks, "browser_will_show"):
    gui_hooks.browser_will_show.append(_register_browser_instance)

from __future__ import annotations

import sys

from aqt import mw, qconnect
from aqt.qt import (
    QAction,
    QActionGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequence,
    QLineEdit,
    QMenu,
    Qt,
)
from aqt.utils import showInfo, tooltip

from .config import (
    CHATGPT_CONFIG_GRAMMAR_FIELD,
    CHATGPT_CONFIG_LEMMA_FIELD,
    CHATGPT_CONFIG_MODE,
    CHATGPT_CONFIG_QUESTION_FIELD,
    CHATGPT_CONFIG_SHORTCUT,
    CHATGPT_CONFIG_SUBTITLE_FIELD,
    CHATGPT_DEFAULT_SHORTCUT,
    CHATGPT_MODE_BATCH,
    CHATGPT_MODE_OFF,
    CHATGPT_MODE_SINGLE,
    get_addon_config,
    save_addon_config,
)
from .flow import run_chatgpt_helper, run_chatgpt_helper_from_editor

_CHATGPT_SHORTCUT_ACTION: QAction | None = None
_CHATGPT_MODE_ACTIONS: dict[str, QAction] = {}


def get_mode_actions() -> dict[str, QAction]:
    return _CHATGPT_MODE_ACTIONS


def run_open_config() -> None:
    config = get_addon_config()
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
    save_addon_config(config)
    refresh_chatgpt_shortcut()
    showInfo("Configuration saved.")


def refresh_chatgpt_shortcut() -> None:
    global _CHATGPT_SHORTCUT_ACTION
    config = get_addon_config()
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
        qconnect(action.triggered, run_chatgpt_helper)
        mw.addAction(action)
        _CHATGPT_SHORTCUT_ACTION = action
    else:
        _CHATGPT_SHORTCUT_ACTION.setShortcuts([QKeySequence(s) for s in sequences])


def set_chatgpt_mode(mode: str) -> None:
    config = get_addon_config()
    config[CHATGPT_CONFIG_MODE] = mode
    save_addon_config(config)
    for key, action in _CHATGPT_MODE_ACTIONS.items():
        action.setChecked(key == mode)
    tooltip(f"ChatGPT Helper mode: {mode}")


def add_chatgpt_menu() -> None:
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
        qconnect(action.triggered, lambda _checked=False, m=mode: set_chatgpt_mode(m))
    current = str(get_addon_config().get(CHATGPT_CONFIG_MODE) or CHATGPT_MODE_OFF)
    if current in _CHATGPT_MODE_ACTIONS:
        _CHATGPT_MODE_ACTIONS[current].setChecked(True)
    mw.form.menuTools.addMenu(menu)


def on_editor_context_menu(editor, menu) -> None:
    action = QAction("Ask ChatGPT", menu)
    qconnect(action.triggered, lambda _checked=False, e=editor: run_chatgpt_helper_from_editor(e))
    menu.addAction(action)

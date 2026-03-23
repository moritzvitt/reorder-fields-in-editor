from __future__ import annotations

from aqt import mw
from aqt.qt import QTimer
from aqt.utils import askUser, showInfo, tooltip

from .browser_utils import (
    current_browser,
    get_selected_notes,
    refresh_browser_note,
    refresh_other_editors,
    unwrap_editor,
)
from .chatgpt_app import focus_and_paste_chatgpt
from .clipboard_utils import copy_to_clipboard, normalize_response_text, read_clipboard_payload
from .config import (
    CHATGPT_MODE_BATCH,
    CHATGPT_MODE_OFF,
    CHATGPT_MODE_SINGLE,
    chatgpt_required_fields,
    get_addon_config,
)
from .utils.chatgpt_helper import (
    build_batch_prompt,
    build_prompt_for_note,
    parse_batch_response,
)

_CHATGPT_WAIT_TIMER: QTimer | None = None
_CHATGPT_PENDING: dict[str, object] | None = None
_ACTIVE_FIELD_CONTEXT: dict[str, object] | None = None


def run_chatgpt_helper() -> None:
    global _CHATGPT_PENDING, _CHATGPT_WAIT_TIMER
    browser = current_browser()
    if browser is not None and getattr(browser, "editor", None) is not None:
        run_chatgpt_helper_from_editor(browser.editor)
        return
    ctx = _ACTIVE_FIELD_CONTEXT or {}
    note_id = ctx.get("note_id")
    field_name = ctx.get("field_name")
    if field_name and not note_id:
        showInfo("ChatGPT Helper: Current note is not saved yet.")
        return
    if note_id and field_name:
        note = mw.col.get_note(int(note_id))
        _start_prompt_for_note(note, str(field_name))
        return
    config = get_addon_config()
    mode = str(config.get("chatgpt_helper_mode") or CHATGPT_MODE_OFF)
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

    fields = chatgpt_required_fields(config)
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

    _start_prompt_for_notes(notes, note_ids, fields, mode)


def run_chatgpt_helper_from_editor(editor) -> None:
    global _CHATGPT_PENDING, _CHATGPT_WAIT_TIMER
    editor_obj = unwrap_editor(editor)
    note = getattr(editor_obj, "note", None)
    if callable(note):
        try:
            note = note()
        except Exception:
            note = None
    if note is None and hasattr(editor_obj, "currentNote"):
        try:
            note = editor_obj.currentNote()
        except Exception:
            note = None
    if note is None or not getattr(note, "id", None):
        showInfo("ChatGPT Helper: No note selected.")
        return
    field_index = getattr(editor_obj, "currentField", None)
    if callable(field_index):
        try:
            field_index = field_index()
        except Exception:
            field_index = None
    if field_index is None or field_index < 0:
        field_index = getattr(editor_obj, "last_field_index", None)
    if field_index is None or field_index < 0:
        field_index = getattr(editor_obj, "currentFieldIndex", None)
        if callable(field_index):
            try:
                field_index = field_index()
            except Exception:
                field_index = None
    if field_index is None or field_index < 0:
        field_index = getattr(editor_obj, "_currentField", None)
    if field_index is None or field_index < 0:
        try:
            total_fields = len(note.fields)
        except Exception:
            total_fields = 0
        if total_fields == 1:
            field_index = 0
    if field_index is None or field_index < 0:
        showInfo("ChatGPT Helper: No field selected.")
        return
    try:
        field_name = note.model()["flds"][field_index]["name"]
    except Exception:
        showInfo("ChatGPT Helper: Failed to resolve field name.")
        return
    _start_prompt_for_note(note, field_name)


def on_editor_did_focus_field(note, field_idx) -> None:
    global _ACTIVE_FIELD_CONTEXT
    field_name = None
    try:
        field_name = note.model()["flds"][field_idx]["name"]
    except Exception:
        field_name = None
    note_id = getattr(note, "id", None)
    _ACTIVE_FIELD_CONTEXT = {
        "note_id": int(note_id) if note_id else None,
        "field_index": field_idx,
        "field_name": field_name,
    }


def _start_prompt_for_note(note, field_name: str) -> None:
    global _CHATGPT_PENDING, _CHATGPT_WAIT_TIMER
    config = get_addon_config()
    fields = chatgpt_required_fields(config)
    required = [fields["lemma"], fields["subtitle"]]
    if fields["question"]:
        required.append(fields["question"])
    if any(field not in note for field in required):
        showInfo("ChatGPT Helper: Missing required fields in selected note.")
        return
    if _CHATGPT_WAIT_TIMER is not None and _CHATGPT_WAIT_TIMER.isActive():
        if not askUser(
            "ChatGPT Helper is already waiting for clipboard change. Cancel and restart?"
        ):
            return
        _CHATGPT_WAIT_TIMER.stop()
        _CHATGPT_PENDING = None
        _CHATGPT_WAIT_TIMER = None
    prompt = build_prompt_for_note(
        note,
        lemma_field=fields["lemma"],
        subtitle_field=fields["subtitle"],
        question_field=fields["question"],
        target_field=field_name,
    )
    copy_to_clipboard(prompt)
    QTimer.singleShot(300, focus_and_paste_chatgpt)
    _CHATGPT_PENDING = {
        "mode": CHATGPT_MODE_SINGLE,
        "note_ids": [int(note.id)],
        "grammar_field": field_name,
    }
    wait_for_clipboard_change(prompt)
    tooltip("ChatGPT Helper: Prompt copied. Waiting for clipboard response.")


def _start_prompt_for_notes(notes, note_ids, fields, mode) -> None:
    global _CHATGPT_PENDING
    if mode == CHATGPT_MODE_SINGLE:
        prompt = build_prompt_for_note(
            notes[0],
            lemma_field=fields["lemma"],
            subtitle_field=fields["subtitle"],
            question_field=fields["question"],
            target_field=fields["grammar"],
        )
    else:
        prompt, note_ids = build_batch_prompt(
            notes,
            lemma_field=fields["lemma"],
            subtitle_field=fields["subtitle"],
            question_field=fields["question"],
            target_field=fields["grammar"],
        )

    copy_to_clipboard(prompt)
    QTimer.singleShot(300, focus_and_paste_chatgpt)
    _CHATGPT_PENDING = {
        "mode": mode,
        "note_ids": note_ids,
        "grammar_field": fields["grammar"],
    }
    wait_for_clipboard_change(prompt)
    tooltip("ChatGPT Helper: Prompt copied. Waiting for clipboard response.")


def wait_for_clipboard_change(old_text: str) -> None:
    global _CHATGPT_WAIT_TIMER
    if _CHATGPT_WAIT_TIMER is not None:
        _CHATGPT_WAIT_TIMER.stop()
    timer = QTimer(mw)
    timer.setInterval(500)
    timer.timeout.connect(lambda: _poll_clipboard(old_text))
    timer.start()
    _CHATGPT_WAIT_TIMER = timer


def _poll_clipboard(old_text: str) -> None:
    if _CHATGPT_WAIT_TIMER is None or _CHATGPT_PENDING is None:
        return
    content, compare = read_clipboard_payload()
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
        pending["response_mapping"] = mapping
    else:
        pending["response_text"] = text
    pending["captured"] = True
    pending["grammar_field"] = grammar_field
    _CHATGPT_PENDING = pending
    _apply_captured_response()


def _apply_captured_response() -> None:
    global _CHATGPT_PENDING
    pending = _CHATGPT_PENDING or {}
    mode = pending.get("mode")
    note_ids = list(pending.get("note_ids", []))
    grammar_field = str(pending.get("grammar_field", "Grammar"))
    if not note_ids:
        showInfo("ChatGPT Helper: No pending notes to update.")
        _CHATGPT_PENDING = None
        return
    if mode == CHATGPT_MODE_BATCH:
        mapping = pending.get("response_mapping", {})
        if not isinstance(mapping, dict) or not mapping:
            showInfo("ChatGPT Helper: No response captured to paste.")
            return
        for nid, content in mapping.items():
            note = mw.col.get_note(nid)
            _write_to_field(note, grammar_field, normalize_response_text(content))
        tooltip(f"ChatGPT Helper: Updated {len(mapping)} notes.")
    else:
        text = pending.get("response_text", "")
        if not text:
            showInfo("ChatGPT Helper: No response captured to paste.")
            return
        note = mw.col.get_note(note_ids[0])
        _write_to_field(note, grammar_field, normalize_response_text(str(text)))
        tooltip("ChatGPT Helper: Updated 1 note.")
    _CHATGPT_PENDING = None


def _write_to_field(note, field_name: str, content: str) -> None:
    note[field_name] = (content or "").strip()
    mw.col.update_note(note)
    try:
        note.flush()
    except Exception:
        pass
    refresh_browser_note(note)
    refresh_other_editors(note)

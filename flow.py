from __future__ import annotations

from aqt.utils import showInfo, tooltip

from .browser_utils import get_selected_notes, unwrap_editor
from .clipboard_utils import copy_to_clipboard
from .config import (
    CHATGPT_MODE_BATCH,
    CHATGPT_MODE_OFF,
    CHATGPT_MODE_SINGLE,
    chatgpt_required_fields,
    get_addon_config,
)

_ACTIVE_FIELD_CONTEXT: dict[str, object] | None = None
_BATCH_LIMIT = 5


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


def run_chatgpt_helper() -> None:
    config = get_addon_config()
    mode = str(config.get("chatgpt_helper_mode") or CHATGPT_MODE_SINGLE)
    if mode == CHATGPT_MODE_OFF:
        tooltip("Prompt Generation is turned off.")
        return
    if mode == CHATGPT_MODE_BATCH:
        _run_batch_prompt(config)
        return
    _run_single_prompt(None, config)


def run_chatgpt_helper_from_editor(editor) -> None:
    config = get_addon_config()
    mode = str(config.get("chatgpt_helper_mode") or CHATGPT_MODE_SINGLE)
    if mode == CHATGPT_MODE_OFF:
        tooltip("Prompt Generation is turned off.")
        return
    if mode == CHATGPT_MODE_BATCH:
        _run_batch_prompt(config)
        return
    _run_single_prompt(editor, config)


def _run_single_prompt(editor, config: dict[str, object]) -> None:
    note = _resolve_note_from_editor(editor)
    if note is None:
        note_ids = get_selected_notes(1)
        note = _get_note(note_ids[0]) if note_ids else None
    if note is None:
        showInfo("Prompt Generation: no focused or selected note.")
        return

    prompt = _build_prompt_for_note(note, config)
    if not prompt:
        showInfo("Prompt Generation: unable to build a prompt for the current note.")
        return

    copy_to_clipboard(prompt)
    tooltip("Prompt copied to clipboard.")


def _run_batch_prompt(config: dict[str, object]) -> None:
    note_ids = get_selected_notes(_BATCH_LIMIT)
    if not note_ids:
        return

    notes = [_get_note(note_id) for note_id in note_ids]
    valid_notes = [note for note in notes if note is not None]
    if not valid_notes:
        showInfo("Prompt Generation: unable to load the selected notes.")
        return

    prompt = _build_batch_prompt(valid_notes, config)
    copy_to_clipboard(prompt)
    tooltip(f"Batch prompt for {len(valid_notes)} notes copied to clipboard.")


def _resolve_note_from_editor(editor):
    if editor is not None:
        resolved = unwrap_editor(editor)
        note = getattr(resolved, "note", None)
        if note is not None:
            return note

    active_note_id = _active_note_id()
    if active_note_id is not None:
        return _get_note(active_note_id)
    return None


def _active_note_id() -> int | None:
    if not _ACTIVE_FIELD_CONTEXT:
        return None
    note_id = _ACTIVE_FIELD_CONTEXT.get("note_id")
    return int(note_id) if isinstance(note_id, int) else None


def _get_note(note_id: int):
    try:
        return _mw().col.get_note(int(note_id))
    except Exception:
        return None


def _mw():
    from aqt import mw

    return mw


def _build_prompt_for_note(note, config: dict[str, object]) -> str:
    fields = chatgpt_required_fields(config)
    note_name = _note_type_name(note)
    note_fields = _note_field_map(note)
    field_lines = [
        f"- {label}: {note_fields.get(field_name, '').strip() or '[missing]'}"
        for label, field_name in (
            ("Lemma", fields["lemma"]),
            ("Subtitle", fields["subtitle"]),
            ("Question", fields["question"]),
            ("Grammar", fields["grammar"]),
        )
    ]
    return "\n".join(
        [
            "Use the note data below to generate the requested prompt content.",
            f"Note type: {note_name}",
            "Fields:",
            *field_lines,
        ]
    ).strip()


def _build_batch_prompt(notes: list[object], config: dict[str, object]) -> str:
    sections = []
    for index, note in enumerate(notes, start=1):
        sections.append(f"Note {index}")
        sections.append(_build_prompt_for_note(note, config))
        sections.append("")
    return "\n".join(sections).strip()


def _note_type_name(note) -> str:
    try:
        return str(note.model().get("name") or "Unknown")
    except Exception:
        return "Unknown"


def _note_field_map(note) -> dict[str, str]:
    try:
        field_names = [str(field.get("name") or "") for field in note.model().get("flds") or []]
    except Exception:
        field_names = []

    mapping: dict[str, str] = {}
    for field_name in field_names:
        try:
            mapping[field_name] = str(note[field_name] or "")
        except Exception:
            mapping[field_name] = ""
    return mapping

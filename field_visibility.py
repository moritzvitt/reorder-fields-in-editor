from __future__ import annotations

import json
import time

from aqt.qt import QCursor, QMenu, QTimer
from pathlib import Path

from .browser_utils import current_browser
from .config import (
    FIELD_VISIBILITY_ACTIVE_LAYOUTS,
    default_layouts_from_field_names,
    default_toggle_visible_fields,
    ensure_note_type_defaults,
    get_addon_config,
    get_field_visibility_active_layouts,
    get_field_visibility_disabled,
    get_field_visibility_layouts,
    get_field_visibility_map,
    layout_name,
    layout_visible_fields,
    save_addon_config,
    set_field_visibility_layouts,
    FIELD_VISIBILITY_DISABLED,
)
from .layout_dialog import LayoutDialog

_TOGGLE_BYPASS_UNTIL = 0.0


def apply_field_visibility(editor) -> None:
    global _TOGGLE_BYPASS_UNTIL
    if _TOGGLE_BYPASS_UNTIL and _TOGGLE_BYPASS_UNTIL > time.time():
        _reset_visibility(editor, _all_field_names_from_note(getattr(editor, "note", None)))
        return
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return
    if editor is not browser.editor:
        return
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    all_names = _all_field_names_from_note(note)
    if ensure_note_type_defaults(config, note_type_name, all_names):
        save_addon_config(config)
    layout_map = get_field_visibility_layouts(config)
    if note_type_name not in layout_map:
        _update_button_labels(editor)
        _reset_visibility(editor, all_names)
        return
    if note_type_name in get_field_visibility_disabled(config):
        _update_button_labels(editor)
        toggle_map = get_field_visibility_map(config)
        allowed = toggle_map.get(note_type_name) or default_toggle_visible_fields(all_names)
        allowed_indices, field_count, _ = _allowed_field_indices(note, allowed)
        js = _hide_fields_js(allowed_indices, field_count, all_names, allowed)
        try:
            editor.web.eval(js)
            editor.web.eval(f"setTimeout(function(){{ {js} }}, 50);")
            editor.web.eval(f"setTimeout(function(){{ {js} }}, 200);")
        except Exception:
            pass
        return
    _, _, allowed, _ = _current_layout_fields(note_type_name, config, all_names)
    allowed_indices, field_count, all_names = _allowed_field_indices(note, allowed)
    js = _hide_fields_js(allowed_indices, field_count, all_names, allowed)
    try:
        editor.web.eval(js)
        editor.web.eval(f"setTimeout(function(){{ {js} }}, 50);")
        editor.web.eval(f"setTimeout(function(){{ {js} }}, 200);")
    except Exception:
        pass
    _update_button_labels(editor)
    _debug_dump_fields(editor)


def editor_will_load_note(js: str, note, editor) -> str:
    global _TOGGLE_BYPASS_UNTIL
    if _TOGGLE_BYPASS_UNTIL and _TOGGLE_BYPASS_UNTIL > time.time():
        _, _, all_names = _allowed_field_indices(note, [])
        return js + _reset_fields_js(all_names)
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return js
    if editor is not browser.editor:
        return js
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return js
    config = get_addon_config()
    all_names = _all_field_names_from_note(note)
    if ensure_note_type_defaults(config, note_type_name, all_names):
        save_addon_config(config)
    layout_map = get_field_visibility_layouts(config)
    if note_type_name in get_field_visibility_disabled(config):
        toggle_map = get_field_visibility_map(config)
        allowed = toggle_map.get(note_type_name) or default_toggle_visible_fields(all_names)
        allowed_indices, field_count, _ = _allowed_field_indices(note, allowed)
        return js + _hide_fields_js(allowed_indices, field_count, all_names, allowed)
    if note_type_name not in layout_map:
        return js + _reset_fields_js(all_names)
    _, _, allowed, _ = _current_layout_fields(note_type_name, config, all_names)
    allowed_indices, field_count, all_names = _allowed_field_indices(note, allowed)
    return js + _hide_fields_js(allowed_indices, field_count, all_names, allowed)


def _reset_visibility(editor, all_names: list[str]) -> None:
    js = _reset_fields_js(all_names)
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _debug_dump_fields(editor) -> None:
    js = """
    (function() {
      const rows = Array.from(document.querySelectorAll('.field-container'));
      const names = rows.map((row) => {
        const nameEl = row.querySelector('.label-name');
        return nameEl ? nameEl.textContent.trim() : null;
      }).filter(Boolean);
      const rowIndices = rows.map((row) => row.getAttribute('data-index'));
      const editorFields = Array.from(document.querySelectorAll('.editor-field'));
      const labels = Array.from(document.querySelectorAll('.label-name')).map((el) => el.textContent.trim());
      return JSON.stringify({
        rowCount: rows.length,
        editorFieldCount: editorFields.length,
        labelCount: labels.length,
        names,
        rowIndices
      });
    })();
    """
    def _write(result: str) -> None:
        try:
            path = Path(__file__).with_name("field_visibility_debug.txt")
            path.write_text(str(result), encoding="utf-8")
        except Exception:
            pass
    try:
        editor.web.evalWithCallback(js, _write)
    except Exception:
        pass


def _hide_fields_js(
    allowed_indices: list[int],
    field_count: int,
    all_names: list[str],
    allowed_fields: list[str],
) -> str:
    allowed = json.dumps(sorted(allowed_fields))
    allowed_idx = json.dumps(sorted(allowed_indices))
    return f"""
    (function() {{
      const allowed = new Set({allowed});
      const allowedIdx = new Set({allowed_idx});
      const totalFields = {int(field_count)};
      const hiddenMarker = 'data-efm-hidden';
      const rowSelector = '.field-container';
      const labelSelector = '.label-name';
      const toInt = (value) => {{
        const parsed = Number.parseInt(value ?? '', 10);
        return Number.isNaN(parsed) ? null : parsed;
      }};
      const setVisible = (el) => {{
        if (!el) return;
        el.removeAttribute(hiddenMarker);
        el.style.display = '';
      }};
      const setHidden = (el) => {{
        if (!el) return;
        el.setAttribute(hiddenMarker, '1');
        el.style.display = 'none';
      }};
      const apply = () => {{
        const rows = Array.from(document.querySelectorAll(rowSelector));
        rows.forEach((row, idx) => {{
          const nameEl = row.querySelector(labelSelector);
          const name = nameEl && nameEl.textContent ? nameEl.textContent.trim() : '';
          const dataIndex = toInt(row.getAttribute('data-index'));
          const fallbackIndex = dataIndex === null ? idx : dataIndex;
          const matchesByName = Boolean(name) && allowed.has(name);
          const matchesByIndex = Boolean(totalFields && rows.length >= totalFields && allowedIdx.has(fallbackIndex));
          if (matchesByName || matchesByIndex) {{
            setVisible(row);
          }} else {{
            setHidden(row);
          }}
        }});
      }};
      apply();
      setTimeout(apply, 50);
      setTimeout(apply, 200);
    }})();
    """


def _allowed_field_indices(note, allowed_fields: list[str]) -> tuple[list[int], int, list[str]]:
    try:
        flds = note.model().get("flds") or []
    except Exception:
        return [], 0, []
    allowed = []
    all_names: list[str] = []
    for idx, fld in enumerate(flds):
        name = fld.get("name")
        if name:
            all_names.append(str(name))
        if fld.get("name") in set(allowed_fields):
            allowed.append(idx)
    return allowed, len(flds), all_names


def _all_field_names_from_note(note) -> list[str]:
    if note is None:
        return []
    try:
        flds = note.model().get("flds") or []
    except Exception:
        return []
    return [str(f.get("name")) for f in flds if f.get("name")]


def _note_type_name(note) -> str | None:
    try:
        return note.model().get("name")
    except Exception:
        return None


def toggle_field_visibility(editor) -> None:
    global _TOGGLE_BYPASS_UNTIL
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    all_names = _all_field_names_from_note(note)
    if ensure_note_type_defaults(config, note_type_name, all_names):
        save_addon_config(config)
    disabled = get_field_visibility_disabled(config)
    layout_map = get_field_visibility_layouts(config)
    if note_type_name not in layout_map:
        return
    if note_type_name in disabled:
        disabled = [n for n in disabled if n != note_type_name]
    else:
        disabled.append(note_type_name)
    config[FIELD_VISIBILITY_DISABLED] = disabled
    save_addon_config(config)
    if note_type_name in disabled:
        _TOGGLE_BYPASS_UNTIL = time.time() + 0.5
    else:
        _TOGGLE_BYPASS_UNTIL = 0.0
    if note_type_name in disabled:
        toggle_map = get_field_visibility_map(config)
        allowed = toggle_map.get(note_type_name) or default_toggle_visible_fields(all_names)
    else:
        _, _, allowed, _ = _current_layout_fields(note_type_name, config, all_names)
    allowed_indices, field_count, _ = _allowed_field_indices(note, allowed)
    if note_type_name in disabled:
        _reset_visibility(editor, all_names)
    else:
        js = _hide_fields_js(allowed_indices, field_count, all_names, allowed)
        try:
            editor.web.eval(js)
        except Exception:
            pass
        QTimer.singleShot(150, lambda: editor.web.eval(js))
        QTimer.singleShot(350, lambda: editor.web.eval(js))
        try:
            if hasattr(editor, "call_after_note_saved"):
                editor.call_after_note_saved(lambda: editor.loadNote(), keepFocus=True)
            else:
                editor.loadNote()
        except Exception:
            pass
    QTimer.singleShot(150, lambda: _update_button_labels(editor))
    QTimer.singleShot(300, lambda: _update_button_labels(editor))


def cycle_field_layout(editor) -> None:
    show_layout_menu(editor)


def show_layout_menu(editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    all_names = _all_field_names_from_note(note)
    if ensure_note_type_defaults(config, note_type_name, all_names):
        save_addon_config(config)
        config = get_addon_config()
    layout_map = get_field_visibility_layouts(config)
    layouts = layout_map.get(note_type_name) or []
    if not layouts:
        layouts = default_layouts_from_field_names(all_names)

    parent_widget = getattr(editor, "parentWindow", None) or current_browser() or editor
    menu = QMenu(parent_widget)
    menu.setToolTipsVisible(True)

    if not layouts:
        empty_action = menu.addAction("No layouts available")
        empty_action.setEnabled(False)
        menu.exec(QCursor.pos())
        return

    active_layouts = get_field_visibility_active_layouts(config)
    active_index = active_layouts.get(note_type_name, 0) % len(layouts)
    for index, layout in enumerate(layouts):
        action = menu.addAction(layout_name(layout, index))
        action.setCheckable(True)
        action.setChecked(index == active_index)
        action.setToolTip(f"Use {layout_name(layout, index)} for {note_type_name}")
        action.triggered.connect(
            lambda _checked=False, nt=note_type_name, idx=index: select_field_layout(editor, nt, idx)
        )

    menu.exec(QCursor.pos())


def select_field_layout(editor, note_type_name: str, layout_index: int) -> None:
    note = getattr(editor, "note", None)
    current_note_type = _note_type_name(note) if note is not None else None
    current_field_names = _all_field_names_from_note(note) if note is not None else []

    config = get_addon_config()
    if current_note_type and note_type_name == current_note_type:
        if ensure_note_type_defaults(config, note_type_name, current_field_names):
            save_addon_config(config)
            config = get_addon_config()

    layout_map = get_field_visibility_layouts(config)
    layouts = layout_map.get(note_type_name) or []
    if not layouts and note_type_name == current_note_type:
        layouts = default_layouts_from_field_names(current_field_names)
    if not layouts:
        return

    active_layouts = get_field_visibility_active_layouts(config)
    active_layouts[note_type_name] = max(0, min(layout_index, len(layouts) - 1))
    config[FIELD_VISIBILITY_ACTIVE_LAYOUTS] = active_layouts
    save_addon_config(config)

    if note is None or note_type_name != current_note_type:
        return

    if note_type_name in get_field_visibility_disabled(config):
        _reset_visibility(editor, current_field_names)
    else:
        _, _, allowed, _ = _current_layout_fields(note_type_name, config, current_field_names)
        allowed_indices, field_count, _ = _allowed_field_indices(note, allowed)
        js = _hide_fields_js(allowed_indices, field_count, current_field_names, allowed)
        try:
            editor.web.eval(js)
        except Exception:
            pass
        QTimer.singleShot(150, lambda: editor.web.eval(js))
        QTimer.singleShot(350, lambda: editor.web.eval(js))
    QTimer.singleShot(100, lambda: _update_button_labels(editor))


def configure_field_layout(editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    layout_map = get_field_visibility_layouts(config)
    layouts = layout_map.get(note_type_name) or []
    all_names = _all_field_names_from_note(note)
    if not layouts:
        layouts = default_layouts_from_field_names(all_names)
    active_layouts = get_field_visibility_active_layouts(config)
    current_index = active_layouts.get(note_type_name, 0) % len(layouts)
    parent_widget = getattr(editor, "parentWindow", None) or current_browser() or editor
    dialog = LayoutDialog(
        parent=parent_widget,
        note_type_name=note_type_name,
        field_names=all_names,
        layouts=layouts,
        active_index=current_index,
    )
    if dialog.exec() != dialog.DialogCode.Accepted:
        return
    updated_layouts, active_index = dialog.result_payload()
    set_field_visibility_layouts(
        config,
        note_type_name,
        updated_layouts,
        active_index=active_index,
    )
    save_addon_config(config)
    if note_type_name in get_field_visibility_disabled(config):
        _reset_visibility(editor, all_names)
    else:
        _, _, allowed, _ = _current_layout_fields(note_type_name, config, all_names)
        allowed_indices, field_count, _ = _allowed_field_indices(note, allowed)
        js = _hide_fields_js(allowed_indices, field_count, all_names, allowed)
        try:
            editor.web.eval(js)
        except Exception:
            pass
        QTimer.singleShot(150, lambda: editor.web.eval(js))
        QTimer.singleShot(350, lambda: editor.web.eval(js))
    QTimer.singleShot(100, lambda: _update_button_labels(editor))




def editor_init_buttons(buttons: list[str], editor) -> None:
    toggle_button = editor.addButton(
        icon=None,
        cmd="prompt_addon_toggle_fields",
        func=lambda ed: toggle_field_visibility(ed),
        tip="Toggle hidden fields",
        label="Show Fields",
        id="prompt-addon-toggle-fields",
        toggleable=True,
        rightside=True,
    )
    buttons.append(toggle_button)
    layout_button = editor.addButton(
        icon=None,
        cmd="prompt_addon_show_layout_menu",
        func=lambda ed: show_layout_menu(ed),
        tip="Choose a layout from a dropdown grouped by note type",
        label="Layout",
        id="prompt-addon-cycle-layout",
        rightside=True,
    )
    buttons.append(layout_button)
    configure_button = editor.addButton(
        icon=None,
        cmd="prompt_addon_configure_layout",
        func=lambda ed: configure_field_layout(ed),
        tip="Configure hidden fields for the current layout",
        label="Configure Layout",
        id="prompt-addon-configure-layout",
        rightside=True,
    )
    buttons.append(configure_button)
    QTimer.singleShot(100, lambda: _update_button_labels(editor))


def _update_button_labels(editor) -> None:
    _update_toggle_button_label(editor)
    _update_layout_button_label(editor)


def _update_toggle_button_label(editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    layout_map = get_field_visibility_layouts(config)
    if note_type_name not in layout_map:
        return
    disabled = note_type_name in get_field_visibility_disabled(config)
    label = "Hide Fields" if disabled else "Show Fields"
    js = f"""
    (function() {{
      const label = "{label}";
      const apply = () => {{
        const btn = document.getElementById("prompt-addon-toggle-fields");
        if (btn) {{
          btn.textContent = label;
          return true;
        }}
        return false;
      }};
      if (!apply()) {{
        setTimeout(apply, 50);
        setTimeout(apply, 200);
      }}
    }})();
    """
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _update_layout_button_label(editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        return
    note_type_name = _note_type_name(note)
    if not note_type_name:
        return
    config = get_addon_config()
    layouts, active_index, _, active_layout = _current_layout_fields(
        note_type_name,
        config,
        _all_field_names_from_note(note),
    )
    if not layouts:
        return
    label = layout_name(active_layout, active_index)
    js = f"""
    (function() {{
        const label = "{label}";
      const apply = () => {{
        const btn = document.getElementById("prompt-addon-cycle-layout");
        if (btn) {{
          btn.textContent = label;
          return true;
        }}
        return false;
      }};
      if (!apply()) {{
        setTimeout(apply, 50);
        setTimeout(apply, 200);
      }}
    }})();
    """
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _reset_fields_js(all_names: list[str]) -> str:
    return f"""
    (function() {{
      const hiddenMarker = 'data-efm-hidden';
      const reset = () => {{
        const rows = Array.from(document.querySelectorAll('.field-container'));
        rows.forEach((row) => {{
          row.removeAttribute(hiddenMarker);
          row.style.display = '';
        }});
        const marked = Array.from(document.querySelectorAll('[' + hiddenMarker + '="1"]'));
        marked.forEach((el) => {{
          el.removeAttribute(hiddenMarker);
          el.style.display = '';
        }});
      }};
      reset();
      setTimeout(reset, 50);
      setTimeout(reset, 200);
    }})();
    """


def _current_layout_fields(
    note_type_name: str,
    config: dict[str, str],
    all_field_names: list[str],
) -> tuple[list[dict[str, object]], int, list[str], dict[str, object] | None]:
    layout_map = get_field_visibility_layouts(config)
    layouts = layout_map.get(note_type_name) or []
    if not layouts:
        return [], 0, [], None
    active_layouts = get_field_visibility_active_layouts(config)
    active_index = active_layouts.get(note_type_name, 0) % len(layouts)
    active_layout = layouts[active_index]
    return (
        layouts,
        active_index,
        layout_visible_fields(active_layout, all_field_names),
        active_layout,
    )

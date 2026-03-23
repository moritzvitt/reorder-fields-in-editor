from __future__ import annotations

import json
from pathlib import Path

from .browser_utils import current_browser

TARGET_NOTE_TYPE = "Moritz Language Reactor"
ALLOWED_FIELDS = {"Lemma", "Cloze", "Synonyms", "Japanese Notes"}


def apply_field_visibility(editor) -> None:
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return
    if editor is not browser.editor:
        return
    note = getattr(editor, "note", None)
    if note is None:
        return
    try:
        note_type_name = note.model().get("name")
    except Exception:
        return
    if note_type_name != TARGET_NOTE_TYPE:
        _reset_visibility(editor)
        return
    allowed_indices, field_count, all_names = _allowed_field_indices(note)
    js = _hide_fields_js(allowed_indices, field_count, all_names)
    try:
        editor.web.eval(js)
        editor.web.eval(f"setTimeout(function(){{ {js} }}, 50);")
        editor.web.eval(f"setTimeout(function(){{ {js} }}, 200);")
    except Exception:
        pass
    _debug_dump_fields(editor)


def editor_will_load_note(js: str, note, editor) -> str:
    browser = current_browser()
    if browser is None or getattr(browser, "editor", None) is None:
        return js
    if editor is not browser.editor:
        return js
    try:
        note_type_name = note.model().get("name")
    except Exception:
        return js
    if note_type_name == TARGET_NOTE_TYPE:
        allowed_indices, field_count, all_names = _allowed_field_indices(note)
        return js + _hide_fields_js(allowed_indices, field_count, all_names)
    return js + _reset_fields_js()


def _reset_visibility(editor) -> None:
    js = """
    (function() {
      const candidates = document.querySelectorAll('[data-field-name]');
      if (candidates.length) {
        candidates.forEach((el) => { el.style.display = ''; });
        return;
      }
      const rowSelectors = ['.field', '.editor-field', '.field-row'];
      let rows = [];
      rowSelectors.forEach((sel) => { rows = rows.concat(Array.from(document.querySelectorAll(sel))); });
      rows.forEach((row) => { row.style.display = ''; });
    })();
    """
    try:
        editor.web.eval(js)
    except Exception:
        pass


def _debug_dump_fields(editor) -> None:
    js = """
    (function() {
      const names = [];
      const candidates = document.querySelectorAll('[data-field-name]');
      candidates.forEach((el) => names.push(el.getAttribute('data-field-name')));
      let rows = [];
      const rowSelectors = ['.field', '.editor-field', '.field-row', '.field-row-wrapper'];
      rowSelectors.forEach((sel) => { rows = rows.concat(Array.from(document.querySelectorAll(sel))); });
      const editables = Array.from(document.querySelectorAll('[contenteditable="true"]'));
      const editableContainers = editables.map((el) => {
        const container = el.closest('.field, .editor-field, .field-row, .field-row-wrapper, .anki-field, .editor-row, .row') || el.parentElement;
        if (!container) return null;
        return {
          tag: container.tagName,
          id: container.id || null,
          class: container.className || null,
        };
      }).filter(Boolean);
      if (!names.length) {
        rows.forEach((row) => {
          const nameEl = row.querySelector('.fieldname, .field-name, .name, label, .label, .title');
          if (nameEl) names.push(nameEl.textContent.trim());
        });
      }
      return JSON.stringify({
        dataFieldCount: candidates.length,
        rowCount: rows.length,
        names,
        editableCount: editables.length,
        editableContainers
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
    allowed_indices: list[int], field_count: int, all_names: list[str]
) -> str:
    allowed = json.dumps(sorted(ALLOWED_FIELDS))
    all_fields = json.dumps(sorted(set(all_names)))
    allowed_idx = json.dumps(sorted(allowed_indices))
    return f"""
    (function() {{
      const allowed = new Set({allowed});
      const allFieldNames = new Set({all_fields});
      const allowedIdx = new Set({allowed_idx});
      const totalFields = {int(field_count)};
      const headerSelectors = '.fieldname, .field-name, .name, label, .label, .title';
      const apply = () => {{
        const candidates = document.querySelectorAll('[data-field-name]');
        if (candidates.length) {{
          candidates.forEach((el) => {{
            const name = el.getAttribute('data-field-name');
            el.style.display = allowed.has(name) ? '' : 'none';
          }});
        }}
        const rowSelectors = ['.field', '.editor-field', '.field-row', '.field-row-wrapper'];
        let rows = [];
        rowSelectors.forEach((sel) => {{
          const found = Array.from(document.querySelectorAll(sel));
          if (found.length > rows.length) rows = found;
        }});
        rows.forEach((row, idx) => {{
          let name = null;
          const nameEl = row.querySelector(headerSelectors);
          if (nameEl) {{
            name = nameEl.textContent.trim();
          }}
          if (!name) {{
            const dataName = row.getAttribute('data-field-name');
            if (dataName) name = dataName;
          }}
          if (name) {{
            row.style.display = allowed.has(name) ? '' : 'none';
            return;
          }}
          if (totalFields && rows.length >= totalFields) {{
            row.style.display = allowedIdx.has(idx) ? '' : 'none';
          }}
        }});
        const headers = Array.from(document.querySelectorAll(headerSelectors));
        headers.forEach((el) => {{
          const text = el.textContent ? el.textContent.trim() : '';
          if (!text) return;
          if (allowed.has(text)) return;
          el.style.display = 'none';
          const row = el.closest('.field, .editor-field, .field-row, .field-row-wrapper');
          if (row) {{
            row.style.display = 'none';
          }} else if (el.parentElement) {{
            el.parentElement.style.display = 'none';
          }}
        }});
        const allEls = Array.from(document.querySelectorAll('body *'));
        allEls.forEach((el) => {{
          const text = el.textContent ? el.textContent.trim() : '';
          if (!text) return;
          if (!allFieldNames.has(text)) return;
          if (allowed.has(text)) return;
          el.style.display = 'none';
          const row = el.closest('.field, .editor-field, .field-row, .field-row-wrapper');
          if (row) row.style.display = 'none';
        }});
      }};
      apply();
      setTimeout(apply, 50);
      setTimeout(apply, 200);
    }})();
    """


def _allowed_field_indices(note) -> tuple[list[int], int, list[str]]:
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
        if fld.get("name") in ALLOWED_FIELDS:
            allowed.append(idx)
    return allowed, len(flds), all_names


def _reset_fields_js() -> str:
    return """
    (function() {
      const reset = () => {
        const candidates = document.querySelectorAll('[data-field-name]');
        if (candidates.length) {
          candidates.forEach((el) => { el.style.display = ''; });
        }
        const rowSelectors = ['.field', '.editor-field', '.field-row', '.field-row-wrapper'];
        let rows = [];
        rowSelectors.forEach((sel) => { rows = rows.concat(Array.from(document.querySelectorAll(sel))); });
        rows.forEach((row) => { row.style.display = ''; });
      };
      reset();
      setTimeout(reset, 50);
      setTimeout(reset, 200);
    })();
    """

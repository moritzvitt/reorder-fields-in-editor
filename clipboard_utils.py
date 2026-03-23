from __future__ import annotations

from aqt import mw
from anki.utils import strip_html


def copy_to_clipboard(text: str) -> None:
    mw.app.clipboard().setText(text)


def read_clipboard_payload() -> tuple[str, str]:
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


def normalize_response_text(text: str) -> str:
    raw = text or ""
    if raw.lstrip().startswith("{\\rtf"):
        raw = strip_html(raw)
    has_html = "<" in raw and ">" in raw
    if has_html and "<div" in raw:
        return trim_blank_divs(raw.strip())
    if has_html:
        converted = (
            raw.replace("<p>", "<div>")
            .replace("</p>", "</div>")
            .replace("<p ", "<div ")
        )
        return trim_blank_divs(converted.strip())
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in normalized:
        normalized = normalized.replace("\n\n\n", "\n\n")
    lines = normalized.split("\n")
    html_lines = []
    for line in lines:
        if line.strip() == "":
            html_lines.append("<div><br></div>")
        else:
            html_lines.append(f"<div>{line}</div>")
    return trim_blank_divs("\n".join(html_lines).strip())


def trim_blank_divs(html: str) -> str:
    lines = [line for line in html.splitlines()]

    def is_blank_div(line: str) -> bool:
        stripped = line.strip().lower()
        return stripped in ("<div><br></div>", "<div><br/></div>", "<div><br /></div>")

    while lines and is_blank_div(lines[0]):
        lines.pop(0)
    while lines and is_blank_div(lines[-1]):
        lines.pop()
    return "\n".join(lines).strip()

from __future__ import annotations

from aqt import gui_hooks, mw, qconnect
from aqt.qt import QAction

from .browser_utils import register_browser_instance
from .ui import add_chatgpt_menu, on_editor_context_menu, refresh_chatgpt_shortcut, run_open_config


action = QAction("Prompt Addon Configuration", mw)
qconnect(action.triggered, run_open_config)
mw.form.menuTools.addAction(action)

add_chatgpt_menu()
refresh_chatgpt_shortcut()

if hasattr(gui_hooks, "browser_menus"):
    gui_hooks.browser_menus.append(register_browser_instance)
elif hasattr(gui_hooks, "browser_will_show"):
    gui_hooks.browser_will_show.append(register_browser_instance)
if hasattr(gui_hooks, "editor_will_show_context_menu"):
    gui_hooks.editor_will_show_context_menu.append(on_editor_context_menu)

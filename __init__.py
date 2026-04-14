from __future__ import annotations

import aqt
from aqt import gui_hooks, mw
from aqt.addons import ConfigEditor
from aqt.utils import showInfo

from .browser_utils import register_browser_instance
from . import shared_menu
from .field_visibility import (
    apply_field_visibility,
    editor_will_load_note,
    editor_init_buttons,
)


def _open_config() -> None:
    if mw is None:
        return
    addon_id = mw.addonManager.addonFromModule(__name__)
    package_name = __name__.split(".", 1)[0]
    config = mw.addonManager.getConfig(package_name) or {}
    addons_dialog = aqt.dialogs.open("AddonsDialog", mw)
    addons_dialog.activateWindow()
    addons_dialog.raise_()
    ConfigEditor(addons_dialog, addon_id, config if isinstance(config, dict) else {})


def _show_usage_help() -> None:
    showInfo(
        "Editor Focus Mode works inside Anki's note editor.\n\n"
        "Open a note to use the editor toolbar integration and your configured field layouts.",
        parent=mw,
    )


shared_menu.add_action_to_addon_menu(
    addon_name="Editor Focus Mode",
    action_text="How to Use",
    callback=_show_usage_help,
)
shared_menu.add_action_to_addon_menu(
    addon_name="Editor Focus Mode",
    action_text="Open Add-on Config",
    callback=_open_config,
)

if hasattr(gui_hooks, "browser_menus_did_init"):
    gui_hooks.browser_menus_did_init.append(register_browser_instance)
elif hasattr(gui_hooks, "browser_will_show"):
    gui_hooks.browser_will_show.append(register_browser_instance)
if hasattr(gui_hooks, "editor_did_load_note"):
    gui_hooks.editor_did_load_note.append(apply_field_visibility)
if hasattr(gui_hooks, "editor_will_load_note"):
    gui_hooks.editor_will_load_note.append(editor_will_load_note)
if hasattr(gui_hooks, "editor_did_init_buttons"):
    gui_hooks.editor_did_init_buttons.append(editor_init_buttons)

from __future__ import annotations

import subprocess
import sys

from aqt.qt import QTimer


def focus_chatgpt_app() -> None:
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            ["/usr/bin/open", "-a", "ChatGPT"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["/usr/bin/osascript", "-e", 'tell application "ChatGPT" to activate'],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def paste_into_chatgpt_app() -> None:
    if sys.platform != "darwin":
        return
    script = (
        'tell application "ChatGPT" to activate\n'
        'tell application "System Events" to keystroke "v" using {command down}'
    )
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def press_enter_in_chatgpt() -> None:
    if sys.platform != "darwin":
        return
    script = (
        'tell application "ChatGPT" to activate\n'
        'tell application "System Events" to key code 36'
    )
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def focus_and_paste_chatgpt() -> None:
    focus_chatgpt_app()
    paste_into_chatgpt_app()
    if sys.platform == "darwin":
        QTimer.singleShot(200, press_enter_in_chatgpt)

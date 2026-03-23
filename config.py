from __future__ import annotations

import sys

from aqt import mw

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


ADDON_NAME = __name__.split(".")[0]


def get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
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


def save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(ADDON_NAME, config)


def chatgpt_required_fields(config: dict[str, str]) -> dict[str, str]:
    return {
        "lemma": str(config.get(CHATGPT_CONFIG_LEMMA_FIELD, "Lemma")),
        "subtitle": str(config.get(CHATGPT_CONFIG_SUBTITLE_FIELD, "Subtitle")),
        "question": str(config.get(CHATGPT_CONFIG_QUESTION_FIELD, "Question")),
        "grammar": str(config.get(CHATGPT_CONFIG_GRAMMAR_FIELD, "Grammar")),
    }

from __future__ import annotations

from aqt import mw

FIELD_VISIBILITY_MAP = "field_visibility_map"
FIELD_VISIBILITY_DISABLED = "field_visibility_disabled"


ADDON_NAME = __name__.split(".")[0]


def get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    if FIELD_VISIBILITY_MAP not in config or not isinstance(
        config.get(FIELD_VISIBILITY_MAP), dict
    ):
        config[FIELD_VISIBILITY_MAP] = {
            "Moritz Language Reactor": ["Lemma", "Cloze", "Synonyms", "Japanese Notes"]
        }
    if FIELD_VISIBILITY_DISABLED not in config or not isinstance(
        config.get(FIELD_VISIBILITY_DISABLED), list
    ):
        config[FIELD_VISIBILITY_DISABLED] = []
    return config


def save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(ADDON_NAME, config)


def get_field_visibility_map(config: dict[str, str]) -> dict[str, list[str]]:
    raw = config.get(FIELD_VISIBILITY_MAP)
    if isinstance(raw, dict):
        return {str(k): [str(vv) for vv in v] for k, v in raw.items() if isinstance(v, list)}
    return {}


def get_field_visibility_disabled(config: dict[str, str]) -> list[str]:
    raw = config.get(FIELD_VISIBILITY_DISABLED)
    if isinstance(raw, list):
        return [str(v) for v in raw]
    return []

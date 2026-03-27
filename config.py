from __future__ import annotations

from aqt import mw

FIELD_VISIBILITY_MAP = "field_visibility_map"
FIELD_VISIBILITY_LAYOUTS = "field_visibility_layouts"
FIELD_VISIBILITY_ACTIVE_LAYOUTS = "field_visibility_active_layouts"
FIELD_VISIBILITY_DISABLED = "field_visibility_disabled"

DEFAULT_NOTE_TYPE = "Moritz Language Reactor"
DEFAULT_FIELD_LAYOUTS = {
    DEFAULT_NOTE_TYPE: [
        ["Lemma", "Cloze", "Synonyms", "Japanese Notes"],
        ["Cloze"],
        ["Cloze", "Lemma"],
    ]
}


ADDON_NAME = __name__.split(".")[0]


def get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    if FIELD_VISIBILITY_LAYOUTS not in config or not isinstance(
        config.get(FIELD_VISIBILITY_LAYOUTS), dict
    ):
        config[FIELD_VISIBILITY_LAYOUTS] = _initial_layouts_from_config(config)
    if FIELD_VISIBILITY_MAP not in config or not isinstance(config.get(FIELD_VISIBILITY_MAP), dict):
        config[FIELD_VISIBILITY_MAP] = _first_layout_map(config[FIELD_VISIBILITY_LAYOUTS])
    if FIELD_VISIBILITY_ACTIVE_LAYOUTS not in config or not isinstance(
        config.get(FIELD_VISIBILITY_ACTIVE_LAYOUTS), dict
    ):
        config[FIELD_VISIBILITY_ACTIVE_LAYOUTS] = {}
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


def get_field_visibility_layouts(config: dict[str, str]) -> dict[str, list[list[str]]]:
    raw = config.get(FIELD_VISIBILITY_LAYOUTS)
    if isinstance(raw, dict):
        layouts: dict[str, list[list[str]]] = {}
        for key, value in raw.items():
            if not isinstance(value, list):
                continue
            normalized = []
            for entry in value:
                if not isinstance(entry, list):
                    continue
                normalized.append([str(item) for item in entry])
            if normalized:
                layouts[str(key)] = normalized
        if layouts:
            return layouts
    legacy_map = get_field_visibility_map(config)
    if legacy_map:
        return {key: [value] for key, value in legacy_map.items()}
    return {
        key: [list(layout) for layout in value]
        for key, value in DEFAULT_FIELD_LAYOUTS.items()
    }


def get_field_visibility_active_layouts(config: dict[str, str]) -> dict[str, int]:
    raw = config.get(FIELD_VISIBILITY_ACTIVE_LAYOUTS)
    if isinstance(raw, dict):
        active: dict[str, int] = {}
        for key, value in raw.items():
            try:
                active[str(key)] = max(0, int(value))
            except (TypeError, ValueError):
                continue
        return active
    return {}


def get_field_visibility_disabled(config: dict[str, str]) -> list[str]:
    raw = config.get(FIELD_VISIBILITY_DISABLED)
    if isinstance(raw, list):
        return [str(v) for v in raw]
    return []


def _initial_layouts_from_config(config: dict[str, str]) -> dict[str, list[list[str]]]:
    legacy_map = get_field_visibility_map(config)
    if not legacy_map:
        return {
            key: [list(layout) for layout in value]
            for key, value in DEFAULT_FIELD_LAYOUTS.items()
        }
    layouts = {key: [value] for key, value in legacy_map.items()}
    default_layouts = DEFAULT_FIELD_LAYOUTS.get(DEFAULT_NOTE_TYPE, [])
    if DEFAULT_NOTE_TYPE in layouts and len(layouts[DEFAULT_NOTE_TYPE]) == 1:
        for extra_layout in default_layouts[1:]:
            if extra_layout not in layouts[DEFAULT_NOTE_TYPE]:
                layouts[DEFAULT_NOTE_TYPE].append(list(extra_layout))
    return layouts


def _first_layout_map(layouts: object) -> dict[str, list[str]]:
    if not isinstance(layouts, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, value in layouts.items():
        if not isinstance(value, list) or not value:
            continue
        first = value[0]
        if not isinstance(first, list):
            continue
        normalized[str(key)] = [str(item) for item in first]
    return normalized

# Current Problems

This document lists the most important current issues and open questions in the add-on.

It is meant to help contributors quickly understand where help is needed.

## 1. Toggle Reliability

The biggest current problem is the hide/show toggle flow.

What should happen:

- initial note load hides non-allowed fields
- first click shows all fields
- second click hides non-allowed fields again

What is difficult:

- the editor DOM is still settling during note load
- the add-on currently uses both `editor_will_load_note()` and `apply_field_visibility()`
- the toggle flow relies on timing via `_TOGGLE_BYPASS_UNTIL`

Open question:

- is there a cleaner way to make the toggle deterministic without relying on delayed JS runs and a short-lived global bypass flag?

## 2. Two-Pass Visibility Logic

The add-on currently uses two stages:

- `editor_will_load_note()` for early JS injection
- `apply_field_visibility()` for the live DOM after load

This works, but it also increases complexity.

Open question:

- is this two-pass design actually necessary for current Anki, or is there a more robust single integration point?

## 3. DOM Coupling To Current Anki Structure

The add-on now targets current editor wrappers such as:

- `.field-container`
- `.label-name`
- `[data-index]`

This is better than the earlier broad selectors, but it is still tied to Anki's current DOM structure.

Open question:

- is there a more Anki-native or API-based way to control visible fields without depending so much on frontend wrapper names?

## 4. Version Compatibility Risk

The current implementation has been checked against the local Anki source tree in `/Users/moritzvitt/src/Anki`.

That means:

- current hook names were verified locally
- current editor wrapper names were verified locally

But this does not guarantee the same behavior across older or future Anki versions.

Open question:

- how much compatibility should the add-on aim for, and what is the right fallback strategy?

## 5. Browser-Only Scope

The add-on is intentionally scoped to the Browser editor by checking the current browser instance.

This avoids affecting other editor contexts, but it also narrows where the feature works.

Open question:

- should the add-on remain Browser-only, or should it eventually support Add Cards, Edit Current, and other editor contexts too?

## 6. Missing Automated Tests

There are currently no automated tests around:

- note switching
- different note types
- toggle timing
- supported vs unsupported note types

Right now, correctness depends on manual testing inside Anki.

Open question:

- what is the most practical testing strategy for this add-on: more structured manual test docs, lightweight regression checks, or some form of UI-driven testing?

## 7. Future Layout Rotation

A planned feature is a button that rotates through multiple field layouts for the same note type.

That will require more than the current single visible-field subset model.

Open questions:

- how should multiple layouts be stored in config?
- how should the active layout be remembered?
- should layout rotation be per note type, per session, or persisted globally?

## Best Places To Contribute

The highest-value contribution areas right now are:

1. making toggle behavior more reliable
2. simplifying the visibility lifecycle
3. improving version robustness
4. designing the future multi-layout feature

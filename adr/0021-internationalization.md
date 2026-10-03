# ADR-0021: Internationalization and localization

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** I18N-01…I18N-07, ADR-0009, ADR-0019, ADR-0022

## Context

BayanDocs must handle every script Word handles (including right-to-left and East Asian layout) and present a translated, mirrored interface. Interface strings are shared by two shells and should be translated once.

## Decision

1. **Interface strings use Project Fluent** (`.ftl` files) stored with the UI manifest in bayan-core and **formatted by the engine** (`fluent-rs`) for both shells, so plural rules, gender, number formatting and fallbacks behave identically everywhere.
2. **Locale data** (dates, numbers, plural rules, calendars including Gregorian, Hijri, Hebrew, Japanese era and Thai Buddhist, collation for sorting indexes and tables) comes from **ICU4X**, sliced to the locales we ship.
3. **Right-to-left interfaces** are mirrored in both shells; bidirectional text in the interface uses isolation.
4. **Document language tags** (`w:lang` for Latin, East Asian and complex-script runs) drive proofing, hyphenation, line breaking and field formatting, never the interface language.
5. **Pseudo-locales** (accented, expanded, right-to-left) are part of CI for interface changes.
6. **Translation workflow:** a translation platform is chosen in Phase 2 (preferring open-source, self-hostable options with free hosting for libre projects, such as Weblate). Translations are contributed under the repository license.
7. **Input methods** are a tested feature on every platform (ADR-0013, ADR-0014).

## Consequences

- One translation effort serves both shells.
- Every interface string passes through the engine; the formatting call is cheap and avoids a second implementation.

## Alternatives considered

- **Qt Linguist for desktop and i18next or FormatJS for web:** two systems, two sets of plural rules, double translation effort.

## Revisit when

A shell needs strings before the engine is available (for example a crash dialog); such strings get a minimal shell-side fallback.

# ADR-0020: Accessibility is a release gate

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** A11Y-01…A11Y-07, PUB-03, ADR-0011, ADR-0013, ADR-0014, CORE-128, DESK-103, WEB-102

## Context

Word is widely used by people who rely on screen readers, keyboard-only operation and high-contrast displays, and public-sector buyers require conformance with WCAG, EN 301 549 and Section 508 (and, in the EU, the European Accessibility Act). Our document surface is drawn on a canvas by our own engine, which means accessibility does not come for free from the platform; if it is bolted on late, the architecture may need rework.

## Decision

1. **Targets:** WCAG 2.2 AA and EN 301 549 for both interfaces; PDF/UA for exported PDFs; a VPAT published by 1.0.
2. **The engine produces an accessibility tree** of the document (`bayan-a11y`): structure (headings, paragraphs, lists, tables with headers, links, images with alternative text, comments, revisions), text with attributes, caret and selection, and incremental updates.
3. **Desktop bridge:** custom `QAccessible` interfaces for the canvas (text, editable text, table where relevant), mapped by Qt to UI Automation, NSAccessibility and AT-SPI2.
4. **Web bridge:** an off-screen semantic DOM mirror with ARIA roles kept in sync with the caret and selection.
5. **Every feature is keyboard-operable;** focus order and visible focus are tested.
6. **Release gates:** Phase 1 cannot exit without screen-reader reading on desktop and web (E1.6); Phase 2 cannot exit without screen-reader editing; automated accessibility checks run on every pull request; scripted manual screen-reader passes run before every release; disabled users test before each beta and major release.
7. **Accessible output:** tagged PDF from Phase 2, validated PDF/UA from Phase 4, and a document accessibility checker in Phase 4.

## Consequences

- Accessibility work starts in the Phase-0 spikes, not after the editor exists.
- Some interface designs will be rejected for accessibility reasons; that is intended.

## Alternatives considered

- **Accessibility after feature parity:** the most common failure mode for canvas editors. Rejected.

## Revisit when

Platform accessibility APIs change significantly (for example, a browser accessibility object model that replaces the DOM mirror).

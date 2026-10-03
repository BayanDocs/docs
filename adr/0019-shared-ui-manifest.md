# ADR-0019: Shared UI manifest; Classic and Focus modes

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** ARC-03, UI-01…UI-09, A11Y-03, I18N-05, ADR-0013, ADR-0014, ADR-0021

## Context

Two shells (Qt Quick and React) must offer the same commands, ribbon, menus, shortcuts and dialogs. Word has hundreds of commands and around a hundred dialogs; building each twice by hand would double the cost and guarantee drift. The specification calls for a customizable ribbon (Classic mode) and a distraction-free Focus mode.

## Decision

1. **The UI manifest lives in bayan-core** (`bayan-ui` crate and data files) and is the single definition of:
   - the **command registry**: identifier, label and tooltip message identifiers, icon, default shortcuts per platform, KeyTip, and how enablement and toggle state are computed (by the engine);
   - the **ribbon** (tabs, groups, controls such as buttons, split buttons, galleries, combo boxes, color pickers), the **Quick Access Toolbar** defaults, **menus** and **context menus**;
   - **declarative dialogs**: fields (number with units, choice, check, color, font, text), their bindings to commands or properties, validation, and engine-rendered preview panes; unit parsing and formatting happen in the engine;
   - **panes** (navigation, styles, comments, revisions) as data sources the shells present;
   - the **Focus mode** floating toolbar.
2. **Shells render the manifest generically.** A shell adds hand-built UI only where a generic rendering is inadequate (for example the comments pane), and still uses manifest commands.
3. **Classic mode:** a ribbon whose structure is familiar to Word users (Home, Insert, Design, Layout, References, Mailings, Review, View, Help), a simplified single-line ribbon option, Word-compatible shortcuts on each platform, and KeyTips (Alt sequences). Customization (tabs, groups, commands, shortcuts) is stored as an overlay on the manifest, exportable and importable.
4. **Focus mode:** interface hidden until text is selected, floating selection toolbar, Markdown-style autoformat shortcuts, typewriter scrolling, and a choice between the paginated view and a reflowed non-paginated view. It is a view mode only; the document is unchanged.
5. **Visual identity:** familiar structure, distinct look. No Microsoft logos, product names (except nominatively, as in "opens Microsoft Word files"), or trade dress. Icons come from **Fluent UI System Icons** (MIT) as SVG, supplemented by our own.
6. **Strings** are Fluent messages formatted by the engine (ADR-0021).
7. **Parity test:** each release lists every manifest command reachable in each shell; differences fail the release checklist.

## Consequences

- Most interface work is data, written once and translated once.
- Shells need a capable generic renderer for ribbons, menus and forms; this is front-loaded effort in Phase 2.
- Some platform-idiomatic touches (macOS menu bar conventions) are expressed as per-platform manifest variants.

## Alternatives considered

- **Hand-built interfaces per shell:** maximum flexibility, guaranteed drift. Rejected.
- **One web-based interface for both (desktop as a web view):** contrary to ADR-0013.

## Revisit when

Generic rendering proves unable to meet usability or accessibility standards for a class of dialogs.

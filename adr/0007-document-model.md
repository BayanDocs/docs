# ADR-0007: Document model — a Word-shaped stream of stories and atoms

- **Status:** Accepted — validated by CORE-004 (2026-10-08), except performance (the owner's decision is pending) and preserved atoms (not modelled; CORE-101)
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-03, COL-01, ADR-0008, [specs/document-model.md](../specs/document-model.md), CORE-004, CORE-101

## Context

The document model must (a) represent everything in WordprocessingML, including content we do not understand, so saves are lossless; (b) support Word's editing semantics; (c) merge concurrent edits from collaborators sensibly; (d) support fast incremental layout. Tree-shaped rich-text models (as in most web editors) struggle with collaborative paragraph splits and merges: splitting a paragraph means moving text between tree nodes, which CRDTs cannot express without losing concurrent edits. Word's own internal model, visible in the MS-DOC binary format, is a flat stream of characters in which paragraph marks, cell marks, field delimiters and object anchors are themselves characters carrying properties.

## Decision

1. **The Bayan Document Model (BDM) is a set of stories, each a flat sequence of atoms**, specified in [specs/document-model.md](../specs/document-model.md):
   - stories: main body, headers, footers, footnotes, endnotes, comments, text boxes, table cells, note separators;
   - atoms: text characters and special atoms (paragraph end, tab, line/page/column breaks, field begin/separator/end, object anchor, note reference, range start/end, preserved inline XML, and others);
   - character formatting as independent **marks** (one per property) over atom ranges;
   - paragraph properties attached to the **paragraph-end atom**, as Word attaches them to the paragraph mark; section properties attached to the paragraph end that closes the section, as in OOXML;
   - tables as **objects** with ordered rows and cells, each cell owning a story; nested tables recurse.
2. **Preservation:** any element or attribute the importer does not understand is kept as an opaque XML fragment anchored at the nearest model position (as an inline atom, a preserved child on a property set, or a preserved package part) and written back unchanged.
3. **Source spans:** the importer records, for each paragraph and table, the byte range of its original XML so that untouched content can be written back verbatim (ADR-0018, CORE-107).
4. **Invariants and normalization:** the model has explicit invariants (for example, every story ends with a paragraph end). Because concurrent edits can violate them, the model defines a **deterministic, view-time normalization** that every replica applies identically; normalization never writes repair operations back into the shared state on its own.
5. **Identity:** every paragraph, table, row, cell, object, note, comment, field and range has a stable unique identifier independent of OOXML identifiers; OOXML identifiers are preserved and regenerated only when uniqueness requires.
6. **Editing semantics** (what Enter, Delete and Backspace do to formatting at boundaries) follow Word's observed behavior, documented in Word Behavior Notes.

## Consequences

- Collaborative split and merge of paragraphs become single-atom insertions and deletions, which sequence CRDTs handle well.
- Import/export maps closely onto both OOXML and MS-DOC.
- The model is less convenient for "tree-shaped" queries; `bayan-model` provides a derived block tree view for layout and accessibility.

## Alternatives considered

- **Nested tree (document → paragraph → run):** natural for XML but loses concurrent edits on split/merge in a CRDT. Rejected as the canonical form; offered as a derived view.
- **Single flat stream including tables (Word's MS-DOC encoding with cell marks):** faithful, but concurrent row and column operations would produce frequent invalid structures. Tables as objects with per-cell stories are more robust.

## Validation gate

CORE-004 must demonstrate on Loro: the mapping of the model (including tables, fields, comments and preserved atoms); convergence with valid normalized structure in 100% of 1,000 randomized three-replica runs of 10,000 operations; and acceptable performance (criteria in the work package). If the mapping proves unworkable, the spike's report proposes an amendment.

## Validation result (CORE-004, 2026-10-07; revised 2026-10-08 after review)

The gate is met for the mapping of tables, fields and comments, and for convergence in the first run (the re-run on the code after the review is in progress). Preserved atoms were not modelled, and the performance result awaits the owner's decision. The [CORE-004 report](https://github.com/BayanDocs/bayan-core/pull/13) (`spikes/crdt-model/REPORT.md` in bayan-core) has the evidence.

- **Mapping:** stories, atoms (paragraph ends, field delimiters, object anchors, range delimiters, table blocks, comment references, and tabs, which normalization handles but no operation of the work package creates), marks, paragraph properties, tables with movable row and cell lists, objects, comments, fields and bookmarks were implemented on Loro behind the `bayan-crdt` adapter, with the operations of the work package. **Preserved atoms (PreservedInline) were not modelled**, because the brief's list of atoms left them out. They should map like object anchors, which the spike did exercise (an argument, not tested): a placeholder character bound to an entity in a registry map whose properties hold the opaque fragment, under the same binding, N5, N7 and I5 rules. CORE-101 adds them to the model and its randomized tests; CORE-102 (unknown content on import) and CORE-107 (lossless export) exercise the fragments themselves.
- **Convergence:** in the first run (2026-10-07), 1,000 randomized three-replica runs of 10,000 operations each, with partitions, out-of-order delivery, undo and redo, all ended with identical views satisfying I1–I7. The re-run on the code after the review, which also checks that no materialization changes a view and that a fresh replica loaded from each final snapshot shows the same view, is in progress; this line will give its result. Normalization was deterministic and idempotent in 100,000 randomly broken documents, judged by an invariant checker that now has a test for each invariant.
- **Performance:** not yet acceptable as measured, and the owner's decision is pending. With Loro 1.16.2, loading and reading the 500-page document takes 2.6 s natively and 7.0 s in WebAssembly (limits 0.3 s and 1 s), because of a decoding bug in Loro (ADR-0008). With a three-line fix to Loro it takes 0.51 s natively, still above the limit, partly because of the model's own map per entity (38% of the first read), and 0.76 s in WebAssembly, within it. The owner decides between requiring lazy reading of entity properties in CORE-101, a revised native limit and flatter maps (report §10, question 2).
- **Specification amendments**, made in [specs/document-model.md](../specs/document-model.md): mark keys name their family before the first colon, and no mark applies to structural atoms (§5); the paragraph mark's run properties live in the paragraph's properties, not in marks (§5, §6); materialization is committed outside undo (§14); I5 and N5 cover marks that name an entity, such as comment highlights; new normalization rules N8 (default final-section properties, provisional until a Word Behavior Note) and N9 (nesting limit for tables), and clarifications of N3 and N7 (§14); the mapping as validated (§16).

## Revisit when

The CORE-004 report recommends changes, or editing work packages in Phase 2 find Word semantics the model cannot express.

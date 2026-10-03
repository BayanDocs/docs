# ADR-0007: Document model — a Word-shaped stream of stories and atoms

- **Status:** Accepted — validation gate (CORE-004)
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

## Revisit when

The CORE-004 report recommends changes, or editing work packages in Phase 2 find Word semantics the model cannot express.

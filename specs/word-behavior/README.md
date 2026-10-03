# Word Behavior Notes (WBN)

Word Behavior Notes are the project's public, evidence-backed knowledge of how Microsoft Word lays out and edits documents where the specifications are silent or ambiguous. Each note answers one precise question, shows the probe documents and observations that answer it, states the rule, and links to the tests that encode it. Over time they become a unique open reference on Word's behavior.

All notes are produced by black-box observation of Word's output on the reference machine ([fidelity-lab.md §8](../fidelity-lab.md#8-reverse-engineering-method-word-behavior-notes)). Nobody decompiles, disassembles or debugs Microsoft software.

## How to write a note

1. Copy [TEMPLATE.md](TEMPLATE.md) to `WBN-NNNN-short-title.md` with the next free number.
2. Fill every section; attach or link probe documents and ground truth.
3. Add the probes to the T0 corpus and the rule's tests to the engine in the same or a linked pull request.
4. Add the note to the index below.

## Index

| WBN | Question | Status | Work package |
|---|---|---|---|
| WBN-0001 | How does Word turn font units into character advances, and where does it round when accumulating a line? | Planned | LAB-005 |
| WBN-0002 | Which font metrics does Word use for "single" line height, and how do "auto", "exact" and "at least" spacing compute line heights? | Planned | LAB-005 |
| WBN-0003 | When does Word apply kerning and ligatures by default, and how do `w:kern` and `w14:ligatures` change that? | Planned | LAB-005 |
| WBN-0004 | How does Word break lines around spaces, hyphens, dashes, slashes and punctuation (tailoring of UAX #14)? | Planned | LAB-102 |
| WBN-0005 | How do tab stops behave beyond the right margin, with hanging indents, and with the default tab stop? | Planned | LAB-102 |
| WBN-0006 | How does justified text distribute space, and how is the last line handled? | Planned | LAB-102 |
| WBN-0007 | How does the table autofit algorithm compute column widths? | Planned | LAB-103 |
| WBN-0008 | How are floating objects positioned and how does text wrap around them in each wrap mode? | Planned | LAB-104 |
| WBN-0009 | How do keep-with-next, keep-lines-together, widow/orphan control and footnote placement interact during pagination? | Planned | LAB-105 |
| WBN-0010 | Which paragraph's properties survive when two paragraphs are merged, and what formatting does newly typed text take at run and paragraph boundaries? | Planned | Phase 2 (E2-EDIT-CORE) |
| WBN-0011 | How does Word interpret literal tab, carriage-return and line-feed characters inside `w:t`? | Planned | CORE-102 |

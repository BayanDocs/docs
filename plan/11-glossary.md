# 11 — Glossary

| Term | Meaning |
|---|---|
| **ADR** | Architecture Decision Record: a short document recording one decision, its context, alternatives and consequences. See [adr/](../adr/README.md). |
| **Additional permission** | An extra permission that copyright holders attach to a GPL license (GPLv3 section 7), for example the proposed app-store permission in ADR-0003. |
| **AGPL** | GNU Affero General Public License: the GPL plus a rule that people who modify the software and offer it over a network must share their changes with its users. License of bayan-server. |
| **Apache-2.0** | A permissive license with an explicit patent license. Used for the protocol specifications and integration kits so anyone can integrate with BayanDocs. |
| **Anchor (object)** | The position in text a floating picture or shape is attached to; it moves with the text even though the object is drawn elsewhere on the page. |
| **Atom** | One element of a story in the BDM: a character, or a special item such as a paragraph end, tab, field delimiter or object anchor. |
| **AT / assistive technology** | Software such as screen readers (NVDA, JAWS, VoiceOver, Narrator, Orca) that presents an application to people with disabilities. |
| **BDM** | Bayan Document Model: the in-memory representation of a document in the core. See [specs/document-model.md](../specs/document-model.md). |
| **Bidi** | Bidirectional text: mixing right-to-left (Arabic, Hebrew) and left-to-right text, governed by the Unicode Bidirectional Algorithm (UAX #9). |
| **BLU** | Bayan Layout Unit: 1/25,400 of a point (1/1,828,800 inch). The integer unit for all layout arithmetic, chosen because twips, EMUs, eighths of a point, millimetres and inches are all whole numbers of BLU. |
| **C ABI** | The plain C calling convention used to connect the Rust core to the C++ desktop shell. |
| **CMYK / ICC** | Cyan-magenta-yellow-black print color; ICC profiles describe how to convert colors between devices. |
| **Compatibility mode** | Word's per-document setting (`w:compatibilityMode` 11, 12, 14, 15) and related options that change layout behavior to match older Word versions. |
| **Copyleft** | A license rule that software built from the code must be shared under the same license. The GPL and AGPL are copyleft; MIT and Apache-2.0 are not. |
| **CRDT** | Conflict-free Replicated Data Type: a data structure that lets several people edit independently and always merge to the same result without a central coordinator. |
| **DCO** | Developer Certificate of Origin: contributors certify they have the right to submit their code by signing off commits (`git commit -s`). |
| **Determinism matrix** | CI job that renders the same documents on every platform and requires identical layout and pixel hashes. |
| **Display list** | Resolution-independent list of drawing commands (glyph runs, paths, images) for one page, produced from the layout. |
| **DrawingML** | The OOXML vocabulary for pictures, shapes, charts and text boxes. |
| **E2EE** | End-to-end encryption: content is encrypted on the author's device and only decrypted on recipients' devices; servers in between cannot read it. |
| **EMF / WMF / EMF+** | Windows metafile vector image formats, common in older Word documents and embedded objects. |
| **EMU** | English Metric Unit: 1/914,400 inch, used by DrawingML. |
| **Epoch (layout)** | Version number of the layout behavior. Changes only for deliberate, documented fidelity improvements. |
| **Epoch (MLS)** | A numbered period of a group's shared key; each membership change starts a new epoch. |
| **Fidelity Lab** | The tools and process that measure how closely BayanDocs matches Microsoft Word. See [specs/fidelity-lab.md](../specs/fidelity-lab.md). |
| **Field** | A Word instruction embedded in text that produces a result: page numbers, dates, tables of contents, cross-references, formulas. |
| **Fluent** | Mozilla's localization system and file format (`.ftl`) used for interface strings. |
| **GPL** | GNU General Public License (version 3 or later): copyleft; anyone who distributes the software, or a program built from it, must share the source under the same license. License of bayan-core, bayan-desktop and bayan-web. |
| **Ground truth** | The reference output (Word's PDF and extracted layout) that BayanDocs is compared against. |
| **Host service** | Anything the engine asks the shell to do because it touches the outside world: fonts from the system, clipboard, network transport, AI inference. |
| **IME** | Input Method Editor: software that composes text in scripts with many characters (Chinese, Japanese, Korean, Indic) from keystrokes. |
| **Kashida** | Elongation of Arabic letters used to justify lines. |
| **KeyTips** | Word's Alt-key sequences that operate the ribbon from the keyboard. |
| **Kinsoku** | Japanese (and broader East Asian) rules about which characters may not start or end a line. |
| **Lossless round-trip** | Opening and saving a document without changing anything the user did not edit (Fidelity Contract Tier B). |
| **MCE** | Markup Compatibility and Extensibility (ECMA-376 Part 3): the `mc:` rules that let newer content degrade gracefully in older readers. |
| **Metric-compatible font** | A font whose characters have exactly the same widths (and line metrics) as another, so text breaks into the same lines even though the letters look different. |
| **MLS** | Messaging Layer Security (RFC 9420): the IETF standard for efficient end-to-end encrypted group key agreement. |
| **OMML** | Office Math Markup Language: how Word stores equations. |
| **OOXML** | Office Open XML (ECMA-376 / ISO/IEC 29500): the standard behind `.docx`, `.xlsx`, `.pptx`. |
| **OPC** | Open Packaging Conventions: the ZIP-based container format of OOXML files, with parts, content types and relationships. |
| **OPFS** | Origin Private File System: private, fast storage for a web application inside the browser. |
| **PDF/A, PDF/UA, PDF/X** | PDF standards for archiving, accessibility and print exchange respectively. |
| **Peritext** | A CRDT algorithm for rich-text formatting that merges concurrent formatting the way users expect. |
| **Probe document** | A small generated document designed to isolate one Word behavior in the Fidelity Lab. |
| **Run** | A stretch of text with the same character formatting (`w:r` in OOXML). |
| **Section** | A part of a Word document with its own page size, margins, columns, headers and footers. |
| **Shaping** | Turning a string of characters into positioned glyphs using a font's rules (ligatures, kerning, contextual forms). |
| **Shell** | The desktop or web application around the engine: windows, menus, input, display, platform integration. |
| **Spike** | A time-boxed experiment that answers a technical question before the project commits to an approach. |
| **Story** | A separate flow of text in a document: main body, each header, footer, footnote, comment, text box, table cell. |
| **Tier A/B/C/D** | The four levels of the Fidelity Contract: determinism, lossless round-trip, measured Word fidelity, reverse fidelity. |
| **Twip** | 1/20 of a point (1/1,440 inch); the main length unit in WordprocessingML. |
| **UI manifest** | The single definition of commands, ribbon, menus, shortcuts, dialogs and strings from which both shells build their interfaces. |
| **VBA** | Visual Basic for Applications: the macro language embedded in `.docm` files. |
| **WASM** | WebAssembly: a portable binary format that lets the Rust core run in browsers at near-native speed. |
| **WBN** | Word Behavior Note: a documented, evidence-backed description of how Word lays out or edits something. See [specs/word-behavior/](../specs/word-behavior/README.md). |
| **WP** | Work package: a self-contained task brief for an agent. See [workpackages/](../workpackages/README.md). |
| **Zero-knowledge server** | A server that stores and relays only data it cannot decrypt. |

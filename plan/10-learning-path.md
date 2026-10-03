# 10 — Learning Path for the Owner

You do not need to become an expert in Rust, C++, TypeScript, typography and cryptography. You need enough to steer: read a pull request's explanation and the code it points to, ask good questions, and recognize when something smells wrong. Your DevOps background already covers a large part of what keeps this project healthy (CI, supply chain, containers, releases). This path builds on it in the order the project needs it. Every resource listed is free unless marked otherwise.

## Phase 0 — now

| Goal | Resources |
|---|---|
| Read Rust comfortably | [The Rust Programming Language](https://doc.rust-lang.org/book/) chapters 1–10, with [Rustlings](https://github.com/rust-lang/rustlings) exercises alongside. Then [Rust by Example](https://doc.rust-lang.org/rust-by-example/) as a reference. |
| Understand why text is hard | Alexis Beingessner's essays "Text Rendering Hates You" and "Text Editing Hates You Too" (search the titles); Nikita Prokopov's "The Absolute Minimum Every Software Developer Must Know About Unicode in 2023". |
| Understand what a `.docx` is | Unzip any `.docx` and look inside `word/document.xml`, `styles.xml` and `numbering.xml`. Then skim the WordprocessingML introduction in ECMA-376 Part 1 (free from Ecma International) and the examples on [officeopenxml.com](http://officeopenxml.com/). |
| Know how decisions are made here | [adr/README.md](../adr/README.md) and three ADRs of your choice; [06-agent-workflow.md](06-agent-workflow.md). |

## Phase 1 — while the viewer is built

| Goal | Resources |
|---|---|
| Rust beyond the basics | The Rust Book chapters 11–20 (testing, iterators, smart pointers, concurrency); the [Cargo Book](https://doc.rust-lang.org/cargo/) sections on workspaces and features. |
| Server-side Rust (your strongest leverage, given DevOps) | The [Tokio tutorial](https://tokio.rs/tokio/tutorial); the [axum examples](https://github.com/tokio-rs/axum/tree/main/examples); *Zero To Production in Rust* by Luca Palmieri (paid book, excellent for API services). |
| Layout fundamentals | The [Fidelity Lab spec](../specs/fidelity-lab.md) and the first Word Behavior Notes the agents write; HarfBuzz's "What is text shaping?" documentation. |
| Supply chain in Rust | [cargo-deny documentation](https://embarkstudios.github.io/cargo-deny/); [SLSA](https://slsa.dev/) levels overview. |

## Phase 2 — while the editor and interfaces are built

| Goal | Resources |
|---|---|
| Modern C++ for reading Qt code | Bjarne Stroustrup, *A Tour of C++* (3rd edition, paid, short); [cppreference](https://en.cppreference.com/) as a reference. |
| Qt and QML | [Qt 6 QML Book](https://www.qt.io/product/qt6/qml-book) (free online); Qt's "Getting started with Qt Quick" documentation. |
| TypeScript and React | [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [react.dev/learn](https://react.dev/learn). |
| Accessibility | WAI's [WCAG 2.2 at a glance](https://www.w3.org/WAI/standards-guidelines/wcag/glance/); try NVDA (free) or VoiceOver on the viewer yourself. |

## Phase 3 — while collaboration is built

| Goal | Resources |
|---|---|
| Local-first and CRDTs | Ink & Switch, "Local-first software" (2019 essay); Martin Kleppmann's talk "CRDTs: The Hard Parts"; [crdt.tech](https://crdt.tech/); the Peritext paper (Ink & Switch). |
| End-to-end encryption with MLS | [RFC 9750, The MLS Architecture](https://www.rfc-editor.org/rfc/rfc9750) (readable overview); then skim the introduction of RFC 9420. |
| Prior art | CryptPad's and Proton Docs' public descriptions of their designs; the USENIX Security 2026 paper "End-to-End Encrypted Collaborative Documents". |
| Application security | [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) overview. |

## Habits that pay off

- Ask the reviewer agent to explain any pull request "as if to a DevOps engineer new to Rust"; it will.
- Keep a personal glossary next to [11-glossary.md](11-glossary.md).
- Once a month, read one Word Behavior Note end to end: they are the project's unique knowledge.
- Run the desktop and web apps yourself after each merge from Phase 1 on. A non-expert user is the best smoke test.

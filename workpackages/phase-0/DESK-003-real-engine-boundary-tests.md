# DESK-003: The desktop's tests and sanitizers against the real engine boundary

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DESKTOP / SECURITY |
| Repository | bayan-desktop |
| Attach to session | bayan-desktop, bayan-core (read, for the SDK's header and schema), docs |
| Size | M |
| Depends on | DESK-002, CORE-007 |
| Unblocks | DESK-101 and DESK-103, which build on the engine boundary |
| Status | Ready |
| Requirements | SEC-01, ARC-07 |
| Decisions | ADR-0006, ADR-0012, ADR-0013, ADR-0017 (amendment of 2026-10-12), ADR-0025 |
| Specs | [engine-protocol.md §3, §8, §12](../../specs/engine-protocol.md#3-transport) |

## Context

The desktop shell talks to the engine only through the engine's C interface and its JSON messages (ADR-0012). By default it builds against a stand-in: a stub engine written in C++ with a hand-written copy of the C header, so that the shell can be built and tested without Rust. Since CORE-007, bayan-core's C SDK provides the real engine, its generated header `bayan_ffi.h` and the protocol's JSON Schema. The architecture review of 2026-10-27, finding [M7](../../plan/reviews/2026-10-27.md#m7-the-desktops-tests-and-sanitizers-miss-the-real-engine-boundary), found that the desktop's tests and sanitizers still miss that boundary. All of it holds at `b9b217a`:

- **The stand-in header is out of date.** [`src/engine/stub/include/bayan_ffi.h`](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/src/engine/stub/include/bayan_ffi.h#L4) still says "PROVISIONAL … Until that SDK exists". It lacks `BAYAN_STATUS_WRONG_THREAD`, which the real header has (status 5, returned by `bayan_render_tile` from inside any engine's callback), and the stub renders a tile on the caller's thread, where the real engine renders it on its own thread, in order with the messages posted before it.
- **The sanitizers never meet the real engine.** AddressSanitizer and UndefinedBehaviorSanitizer find memory errors and undefined behavior while tests run. The `sanitizers` job of [`ci.yml`](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/.github/workflows/ci.yml#L77) runs only `cmake --workflow --preset asan`, and that preset inherits `BAYAN_ENGINE=stub` ([CMakePresets.json:11](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/CMakePresets.json#L11)). The Linux, macOS and Windows jobs do build the real engine from the bayan-core commit pinned in `deps/bayan-core.json` (`664c999`) and run the engine and app tests against it, with `BAYAN_REQUIRE_MOCK_DOCUMENT=1` so that none is skipped, but never under the sanitizers. So the riskiest code, where the Rust engine's thread calls into the shell's C++ callback, never runs under them.
- **Hand-made messages disagree with the schema.** The tests build the engine's messages by hand. [`tst_documentsession.cpp:318`](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/tests/tst_documentsession.cpp#L318) builds `engine.error` with its fields nested under `error`, which the real engine never sends: the schema's `EngineError` has `code`, `message_id`, `args` and `recoverable` side by side. The test still passes because the app reads only `recoverable` ([documentsession.cpp:147](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/src/app/documentsession.cpp#L147)), so it tests a message that does not exist. The SDK's JSON Schema is shipped but never read ([src/engine/README.md:13](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/src/engine/README.md#L13): "Nothing else in the SDK is read").

The stub keeps one job the real engine cannot do: its test switches make `doc.open` fail (`{"test": {"doc_open": "fail"}}`) or go unanswered (`"ignore"`), for the shell's error paths.

## Objective

The desktop's engine and app tests run under AddressSanitizer and UndefinedBehaviorSanitizer against the real engine; the stub implements the real C interface; and every message a test hands the shell as if from the engine is one the engine could send.

## Scope

### In scope

- **Sanitizers against the real engine.** A CI job that builds the C SDK from the pinned commit (`scripts/build-engine-sdk.sh`), configures bayan-desktop with `BAYAN_ENGINE=sdk` and `BAYAN_SANITIZERS=address;undefined` (a new preset next to `asan` and `engine-sdk`), and runs the engine and app tests under the sanitizers with `BAYAN_REQUIRE_MOCK_DOCUMENT=1`. Keep the existing stub sanitizer job for the tests that do not use the engine. The Rust library itself is not instrumented; what matters is the shell's side: its callback on the engine's thread, the copies it makes there, and the hand-over to Qt's main thread.
- **The real header for the stub.** Replace the hand-written `stub/include/bayan_ffi.h` with the SDK's generated header from the pinned commit, kept in the repository as a copy that CI compares byte for byte with the header of the SDK it builds, so that moving the pin without updating the copy fails. Make the stub implement it faithfully: `BAYAN_STATUS_WRONG_THREAD` from inside a callback, and tiles rendered on the engine's thread in order with the messages posted before them, as the real header documents. Keep the stub's test switches.
- **Messages that match the schema.** Keep a copy of the protocol's JSON Schema from the pinned commit beside the header, compared with the SDK's in the same way, and check every message that a test delivers to the shell as if from the engine against it, in a test helper that all such tests use. Fix `engine.error` and every other message that fails. Recommended: a small checker in the tests for the parts of JSON Schema that the generated schema uses, written with Qt's JSON classes, which fails on any keyword it does not implement, so that a later schema cannot pass unchecked; it adds no dependency. Taking the messages from the real engine's output instead is the alternative the review names; choose it only if it covers the error messages the tests need (the engine sends an unrecoverable `engine.error` after `diag.panic` with `test.allow_panic`).
- **Documentation.** `src/engine/README.md` (the SDK layout now includes the schema, and how the copies are kept equal), `AGENTS.md`, and, in a linked docs pull request, bayan-desktop's section of the [dependency update runbook](../../developer/dependency-update-runbook.md): when the bayan-core pin moves, the header and schema copies move with it.

### Out of scope

- How the shells recover from an engine panic (finding M6) and the key bindings of finding H5: small tasks of their own.
- Changes to the engine protocol (finding H5, a planning session) and to bayan-core.
- Moving the bayan-core pin, unless the work needs it; then follow ADR-0017's amendment of 2026-10-12 and say why.
- The stale comments of `.clang-tidy` (finding L11).

## Deliverables

- A CMake preset and a CI job (or a step in the existing `sanitizers` job) for the real engine under the sanitizers.
- The stub on the generated header, the copies of the header and the schema with their CI comparison, and the schema check in the tests.
- The documentation above, and the linked docs pull request.

## Acceptance criteria

- [ ] AC-1 The new job builds the pinned SDK and runs every engine and app test under AddressSanitizer and UndefinedBehaviorSanitizer, none skipped (link to a green run).
- [ ] AC-2 A deliberate heap-use-after-free in the shell's engine callback path (`src/engine/engine.cpp`), pushed to a test branch, makes the new job fail with AddressSanitizer's report (link to that run, then revert).
- [ ] AC-3 No sanitizer suppression is added, or each is limited to a third-party library, as the header of `tests/lsan-suppressions.txt` requires, with its reason in the pull request; nothing in the shell's code or the engine's library is suppressed.
- [ ] AC-4 The stub compiles against the copy of the generated header, which CI shows is byte-identical to the header of the SDK built from the pinned commit; a test shows that `bayan_render_tile` returns `BAYAN_STATUS_WRONG_THREAD` from inside a callback with the stub as with the real engine.
- [ ] AC-5 Every message that a test hands the shell as if from the engine passes the schema check; a test shows that the check rejects `engine.error` with a nested `error` object, a field of the wrong type and an unknown field where the schema forbids one, and that it fails on a schema keyword it does not implement.
- [ ] AC-6 The verification gate (`cmake --workflow --preset verify`) passes, CI is green on Linux, macOS and Windows, and the docs pull request is linked.

## Verification

`cmake --workflow --preset verify`; `cmake --workflow --preset asan`; `scripts/build-engine-sdk.sh` followed by the new preset's workflow; `scripts/test-engine-sdk.sh --sdk build/bayan-core-sdk`; the CI runs of AC-1 and AC-2.

## Notes and pitfalls

- Load the pinned tools first in every shell: `. ~/.local/share/bayandocs/desktop-tools/env.sh` ([plan/06](../../plan/06-agent-workflow.md#cloud-environment-for-agent-sessions)).
- AddressSanitizer needs its runtime in the program, not in the Rust library: link the test programs with the sanitizer flags and load the SDK's shared library into them, as the `engine-sdk` preset already does without sanitizers.
- The engine's thread starts when the engine is created and stops in `bayan_engine_free`; LeakSanitizer reports what is still allocated at exit, so every test must free its engine. A leak inside the engine's library is a bayan-core problem: report it as a follow-up rather than suppress it.
- The schema is generated by schemars in bayan-core; read it from the copy, never from a network location, and keep the checker strict rather than complete.
- The stub stays the default build, so contributors without Rust can still build and test the shell.

## Escalate if

- The real engine fails a test only under the sanitizers in a way that points into bayan-core's code: report it to the orchestrator for a bayan-core follow-up instead of working around it.
- Checking messages against the schema would need a JSON Schema library (a new dependency under ADR-0017).
- The pinned bayan-core commit lacks something this work needs, so that the pin must move.

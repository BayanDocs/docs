# ADR-0024: Local AI

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** AI-01…AI-05, A11Y-07, PRF-02, ADR-0006, ADR-0022, ADR-0023

## Context

The specification asks for grammar checking, context analysis and style auditing powered by small local language models running on the user's CPU or GPU, with no data leaving the machine. Facts verified on 2026-10-03:

- **Runtimes:** llama.cpp (MIT, C/C++, GGUF format, CPU/Metal/CUDA/Vulkan and a WebGPU backend; its team joined Hugging Face in February 2026) is the de facto standard; Rust options include `llama-cpp-2` bindings, mistral.rs and candle. In browsers: wllama (MIT, llama.cpp in WebAssembly with WebGPU), WebLLM (Apache-2.0, WebGPU only), Transformers.js with ONNX Runtime Web.
- **Small models under OSI-approved licenses** include the Qwen3 and Qwen3.5 small models (Apache-2.0), Gemma 4 E2B/E4B (Apache-2.0 since April 2026), IBM Granite 4.x (Apache-2.0), Ministral 3 3B (Apache-2.0), SmolLM3-3B (Apache-2.0), Phi-4-mini (MIT) and OLMo 2 1B (Apache-2.0, fully open data). Gemma 3, Llama 3.x, LFM2 and Nemotron use non-OSI licenses.
- **Speech:** whisper.cpp (MIT) for dictation. The Piper text-to-speech engine moved to GPL-3.0-or-later in 2025.

## Decision

1. **Provider interface in core** (`bayan-ai`): prompts, chunking of document text, structured results, mapping suggestions back to document ranges as annotations. The engine requests inference as a host service; shells or sidecars fulfil it.
2. **Desktop runtime:** llama.cpp in a **separate sidecar process** (C++ code isolated from the editor process, per ADR-0006), communicating over local IPC, using the best available backend (CPU, Metal, CUDA, Vulkan).
3. **Web runtime:** a WebGPU-capable in-browser runtime (wllama or WebLLM, chosen in Phase 5) in its own worker; disabled gracefully where WebGPU or memory is insufficient.
4. **Models:** chosen at Phase 5 by an evaluation harness (grammar and style quality on test sets, latency and memory on reference hardware) among models with **OSI-approved licenses** only. Models are downloaded on demand (from the organization's server or a configured mirror, never silently), verified by hash or signature, and never bundled in installers.
5. **Off-device inference** only when a user or administrator explicitly configures an endpoint they control (for example an on-premises server with an OpenAI-compatible API); the interface shows clearly when it is active. Nothing is ever sent to BayanDocs project servers.
6. **Off by default until enabled;** administrators can disable AI entirely by policy.
7. **Suggestions are annotations,** never applied without the user's action.
8. **Speech:** dictation via whisper.cpp in the same sidecar (desktop) and a browser runtime (web); read-aloud via the operating system's speech services (Qt TextToSpeech, LGPL) and the browser's Web Speech API, with optional open voices later where licenses permit.

## Consequences

- Privacy is guaranteed by architecture, not by policy text.
- Quality depends on the user's hardware; small models are weaker than cloud models, and we say so.
- The model landscape changes monthly; the decision fixes the interface and license rules, not a specific model.

## Alternatives considered

- **Cloud AI APIs:** contrary to the privacy principle.
- **llama.cpp in-process:** simpler, but puts a large C++ codebase inside the editor process.
- **Bundling a model in the installer:** inflates every download for an optional feature.

## Revisit when

Phase 5 planning (model choice); browsers or operating systems ship built-in local model APIs with acceptable privacy guarantees.

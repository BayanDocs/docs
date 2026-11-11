# Developing bayan-desktop

[bayan-desktop](https://github.com/BayanDocs/bayan-desktop) is the desktop app of BayanDocs for Windows, macOS and Linux, written in C++20 with Qt 6 (Qt Quick) and built with CMake presets: a thin shell that draws the engine's pages and passes it the user's input, while every behavior that concerns documents lives in bayan-core. This page is the setup map; the repository's [README.md](https://github.com/BayanDocs/bayan-desktop/blob/HEAD/README.md) and [AGENTS.md](https://github.com/BayanDocs/bayan-desktop/blob/HEAD/AGENTS.md) are the reference, in particular the README's "Building" and AGENTS.md's sections "Verification gate" and "Dependency mechanisms". Start with [Getting started](getting-started.md) for the base tools.

## Platforms

Linux (Ubuntu 24.04), macOS on Apple Silicon, and Windows with Visual Studio 2022. CI builds and tests every change on all three (`.github/workflows/ci.yml`: `ubuntu-24.04`, `macos-15` and `windows-2025`).

## What you need

What each system needs before the setup script runs, as the README lists it:

- **Linux (Ubuntu 24.04):** a C++20 compiler (GCC 13 or Clang 18), Python 3.11 or newer with `venv`, and the development packages that Qt needs: `sudo apt install build-essential python3-venv libgl-dev libegl-dev libvulkan-dev libxkbcommon-dev libfontconfig-dev libdbus-1-dev`.
- **macOS (Apple Silicon):** the Xcode command line tools (`xcode-select --install`) and Python 3.11 or newer, from [python.org](https://www.python.org/downloads/macos/).
- **Windows:** Visual Studio 2022 with the "Desktop development with C++" workload (Microsoft offers it on its [older downloads page](https://visualstudio.microsoft.com/vs/older-downloads/), under "Visual Studio 2022 family"), Git for Windows (run the setup script in Git Bash) and Python 3.11 or newer, from [python.org](https://www.python.org/downloads/windows/).
- **rustup** ([step 2 of Getting started](getting-started.md#step-2-rust)), only to build and test the real engine (below); the everyday build and the gate use a stand-in engine and need no Rust.

## Set up

```sh
git clone https://github.com/BayanDocs/bayan-desktop.git
cd bayan-desktop
scripts/dev-setup.sh
. ~/.local/share/bayandocs/desktop-tools/env.sh
```

`scripts/dev-setup.sh` installs, into `~/.local/share/bayandocs/desktop-tools`:

- **CMake, Ninja, clang-format and clang-tidy**, at the exact versions in `deps/requirements-tools.txt`, as prebuilt Python packages checked against their SHA-256 hashes, so that no package code runs while they are installed;
- **Qt**, at the exact version in `deps/qt.json`, with `scripts/install-qt.py`, which downloads it from Qt's own servers and checks every archive against the SHA-256 published there. Only Qt's LGPL modules are installed ([ADR-0013](../adr/0013-desktop-shell.md)). If you already have that Qt version, set `BAYAN_QT_DIR` to it and the script uses it instead.

The tools stay off your default `PATH`, so that they never replace the CMake of other projects. The last line above, `. ~/.local/share/bayandocs/desktop-tools/env.sh`, puts them first on `PATH` and points CMake at Qt: run it in every new terminal before you build. `scripts/dev-setup.sh --help` lists the script's options.

On **Windows**, the build runs in a Visual Studio developer environment: open an "x64 Native Tools" command prompt, put the tools folder and Qt's `bin` folder that the script printed at the front of `PATH`, and set `CMAKE_PREFIX_PATH` to the Qt folder, as the README describes. CI does the same in its Windows job, after the setup script.

## Run the gate

The gate is one command, from the repository's root, before every push:

```sh
cmake --workflow --preset verify
```

It configures an optimized build with warnings as errors and the Qt licensing check, builds the app and its tests, runs clang-format, clang-tidy and qmllint, and runs every test, including a headless smoke test of the app and the check that the Qt release is at least 24 hours old (which reads the Git history).

What CI runs on each system: `.github/workflows/ci.yml` runs `cmake --workflow --preset verify` on Linux, `cmake --workflow --preset ci` on macOS (the same build and tests, without the lint), and `cmake --workflow --preset msvc` on Windows, from the developer environment above. On Windows, `msvc` is also the command that the README gives, because the preset `verify` exists only on Linux and macOS.

`cmake --workflow --preset dev` is the quick Debug build and test for everyday work on Linux and macOS, and `cmake --build --preset verify --target format` fixes the formatting.

CI also runs, on Linux, the tests under AddressSanitizer and UndefinedBehaviorSanitizer (`cmake --workflow --preset asan`), and on every system the tests that use the engine against a stand-in SDK and against the real engine; then come the checks shared by every repository. [GitHub Settings Baseline](github-settings.md#rulesets) lists the checks that must pass.

## Deeper notes

- **The stub and the real engine.** The default build links a stub engine (`src/engine/stub/`), which shows a single test page. The real engine is bayan-core's C SDK: `scripts/build-engine-sdk.sh` builds it, with rustup, from the bayan-core commit pinned in `deps/bayan-core.json` into `build/bayan-core-sdk`, and `scripts/test-engine-sdk.sh --sdk build/bayan-core-sdk` builds the app against it and runs the tests that use the engine. On Windows, run both from Git Bash: `build-engine-sdk.sh` outside the Visual Studio developer environment, and `test-engine-sdk.sh` inside the x64 one, as the scripts' headers and the Windows job of `ci.yml` do. `src/engine/README.md` in the repository describes the SDK's layout and how to build against it.
- **Running the app.** After `cmake --workflow --preset dev`, run `./build/dev/src/bayan-desktop` (on macOS, `open build/dev/src/bayan-desktop.app`). `bayan-desktop --smoke-test` checks that the engine's page is displayed and exits, and `bayan-desktop --benchmark <file>` measures scrolling, zooming and typing (the README explains both).
- **Qt modules.** Only LGPL-licensed Qt modules may be used. Find Qt with the project's `bayan_find_qt()` rather than `find_package(Qt6 …)`, and have a new module reviewed and added to the allowlist in `cmake/BayanQtPolicy.cmake`, which the build's licensing check enforces.
- **Pins.** Qt in `deps/qt.json`, the build and lint tools in `deps/requirements-tools.txt`, the engine in `deps/bayan-core.json`, and the Ubuntu packages of CI in `.github/workflows/ci.yml`. Every pin and how it moves is in the [dependency update runbook](dependency-update-runbook.md#bayan-desktop).

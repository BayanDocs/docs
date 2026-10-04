// Renders Mermaid diagrams on the BayanDocs website (DOCS-001, ADR-0027).
//
// mdBook turns a ```mermaid code block into <pre><code class="language-mermaid">. On pages that contain one, this
// script loads the vendored Mermaid script next to it (site/mermaid/mermaid.min.js), lets the browser check it against
// the Subresource Integrity hash below, and replaces each code block with the rendered diagram. Pages without diagrams
// never download Mermaid. If the script cannot be loaded (or fails its integrity check), the code blocks stay as they are,
// so readers still see the diagram source. The diagrams themselves live in the Markdown files, which GitHub renders
// natively.
(() => {
  "use strict";

  // SHA-384 of mermaid.min.js in Subresource Integrity format. scripts/verify.sh checks that it matches the file.
  const MERMAID_INTEGRITY = "sha384-EOXBFmc3gx5mb+vn0vPvvGqACToJD24hhacX5Yx+8NUUQrHIle/Qi5Bg9o3zKwW2";
  // mdBook themes with a dark background; the others ("light", "rust") get Mermaid's default light theme.
  const DARK_THEMES = ["coal", "navy", "ayu"];

  const codeBlocks = Array.from(document.querySelectorAll("pre > code.language-mermaid"));
  if (codeBlocks.length === 0 || !document.currentScript) {
    return;
  }
  const mermaidUrl = new URL("mermaid.min.js", document.currentScript.src);

  const isDark = () => DARK_THEMES.some((theme) => document.documentElement.classList.contains(theme));

  // Each diagram keeps its source text so it can be drawn again when the reader switches between light and dark themes.
  // Only textContent is used: the source is never parsed as HTML here, and Mermaid's "strict" security level sanitizes
  // its own output.
  let diagrams = [];

  const render = (dark) => {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "default" });
    for (const diagram of diagrams) {
      diagram.element.removeAttribute("data-processed");
      diagram.element.textContent = diagram.source;
    }
    window.mermaid.run({ nodes: diagrams.map((diagram) => diagram.element) }).catch((error) => {
      console.error("Mermaid could not render a diagram on this page.", error);
    });
  };

  const onLoaded = () => {
    diagrams = codeBlocks.map((code) => {
      const element = document.createElement("div");
      element.className = "mermaid";
      const source = code.textContent;
      code.parentElement.replaceWith(element);
      return { element, source };
    });
    let dark = isDark();
    render(dark);
    new MutationObserver(() => {
      if (isDark() !== dark) {
        dark = isDark();
        render(dark);
      }
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  };

  const script = document.createElement("script");
  script.src = mermaidUrl.href;
  script.integrity = MERMAID_INTEGRITY;
  script.crossOrigin = "anonymous";
  script.addEventListener("load", onLoaded);
  script.addEventListener("error", () => {
    console.error("The Mermaid script failed to load or did not match its integrity hash; showing diagram sources.");
  });
  document.head.appendChild(script);
})();

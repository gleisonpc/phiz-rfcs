/* Hosted-RFC enhancements: Mermaid rendering for the active language + per-section comments (giscus, GitHub Discussions). */
(function () {
  const cfg = window.PHIZ_SITE || {};
  const rfcId = window.PHIZ_RFC_ID || "RFC";
  const T = {
    pt: { btn: "Comentar", close: "Fechar", fallback: "Abrir no GitHub", need: "Comentários usam sua conta do GitHub." },
    en: { btn: "Comment", close: "Close", fallback: "Open on GitHub", need: "Comments use your GitHub account." },
    zh: { btn: "评论", close: "关闭", fallback: "在 GitHub 打开", need: "评论需要使用 GitHub 账号。" }
  };
  const lang = () => document.documentElement.dataset.lang || "pt";
  const dark = () => matchMedia("(prefers-color-scheme: dark)").matches || document.documentElement.dataset.theme === "dark";

  /* ---------- Mermaid ---------- */
  function initMermaid() {
    if (!window.mermaid) return;
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: dark() ? "dark" : "neutral", flowchart: { htmlLabels: true } });
  }
  async function renderMermaid() {
    if (!window.mermaid) return;
    const nodes = [...document.querySelectorAll(".lang.active pre.mermaid:not([data-processed])")];
    if (!nodes.length) return;
    try { await window.mermaid.run({ nodes }); } catch (e) { console.warn("mermaid", e); }
  }

  /* ---------- Comments ---------- */
  const giscusReady = () => cfg.repo && cfg.repo !== "OWNER/REPO" && cfg.giscus && cfg.giscus.repoId && cfg.giscus.categoryId;

  function sectionKey(h) { return h.id.replace(/^(pt|en|zh)-/, ""); }

  function issueUrl(key, title) {
    const t = encodeURIComponent(`[${rfcId} · ${key}] `);
    const b = encodeURIComponent(`RFC: ${rfcId}\nSection: ${title}\nLink: ${location.href.split("#")[0]}#${key}\n\n`);
    return `https://github.com/${cfg.repo}/issues/new?labels=rfc-comment&title=${t}&body=${b}`;
  }

  function titleOf(h) { const c = h.cloneNode(true); c.querySelectorAll('.cmt-btn').forEach(x => x.remove()); c.querySelectorAll('.n').forEach(x => x.append(' ')); return c.textContent.replace(/\s+/g, ' ').trim(); }

  function openPanel(h, btn) {
    const key = sectionKey(h);
    let panel = h.nextElementSibling;
    if (panel && panel.classList.contains("cmt-panel")) { panel.remove(); btn.setAttribute("aria-expanded", "false"); return; }
    panel = document.createElement("div");
    panel.className = "cmt-panel";
    const L = T[lang()];
    if (giscusReady()) {
      const s = document.createElement("script");
      s.src = "https://giscus.app/client.js";
      s.async = true; s.crossOrigin = "anonymous";
      const a = {
        repo: cfg.repo, "repo-id": cfg.giscus.repoId, category: cfg.giscus.category, "category-id": cfg.giscus.categoryId,
        mapping: "specific", term: `${rfcId}#${key}`, strict: "0", "reactions-enabled": "1", "emit-metadata": "0",
        "input-position": "top", theme: "preferred_color_scheme", lang: { pt: "pt", en: "en", zh: "zh-CN" }[lang()], loading: "lazy"
      };
      Object.entries(a).forEach(([k, v]) => s.setAttribute("data-" + k, v));
      panel.append(Object.assign(document.createElement("p"), { className: "cmt-note", textContent: L.need }), s);
    } else {
      const p = document.createElement("p");
      p.className = "cmt-note";
      const link = document.createElement("a");
      link.href = issueUrl(key, titleOf(h)); link.target = "_blank"; link.rel = "noopener";
      link.textContent = L.fallback;
      p.append(link);
      panel.append(p);
    }
    h.after(panel);
    btn.setAttribute("aria-expanded", "true");
  }

  function decorate() {
    document.querySelectorAll(".lang h2[id]").forEach(h => {
      if (h.querySelector(".cmt-btn")) return;
      const b = document.createElement("button");
      b.type = "button"; b.className = "cmt-btn"; b.setAttribute("aria-expanded", "false");
      b.innerHTML = '<span aria-hidden="true">💬</span> <span class="cmt-l"></span>';
      b.addEventListener("click", () => openPanel(h, b));
      h.append(b);
    });
    document.querySelectorAll(".cmt-btn .cmt-l").forEach(el => { el.textContent = T[lang()].btn; });
  }

  function refresh() { decorate(); renderMermaid(); }

  initMermaid();
  new MutationObserver(refresh).observe(document.documentElement, { attributes: true, attributeFilter: ["data-lang"] });
  window.addEventListener("load", refresh);
  document.addEventListener("DOMContentLoaded", refresh);
})();

// SharpSignals landing — light interactivity only.
//
// Hydrates headline metrics + the public-sheet link from a static config
// rendered by deploy time (or live-fetched once we expose a stats JSON).
// Keeping it inert until config exists means the page degrades gracefully
// — values stay as "—" rather than showing a broken metric.

(() => {
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const config = window.SHARPSIGNALS_CONFIG ?? {
    sheetUrl: null,            // e.g. https://docs.google.com/spreadsheets/d/.../edit?usp=sharing
    statsUrl: "/stats.json",   // optional: /stats.json served by the site
    telegramUrl: "https://t.me/sharpsignals",
  };

  if (config.sheetUrl) {
    const sheetLink = document.getElementById("sheet-link");
    if (sheetLink) sheetLink.href = config.sheetUrl;
  }

  if (config.telegramUrl) {
    const tgCard = document.getElementById("telegram-card");
    if (tgCard) tgCard.href = config.telegramUrl;
  }

  if (!config.statsUrl) return;

  fetch(config.statsUrl, { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : null))
    .then((stats) => {
      if (!stats) return;
      setMetric("metric-picks", stats.totalPicks);
      setMetric("metric-clv", formatCLV(stats.avgClv));
      setMetric("metric-hit", formatHit(stats.hitRate));
    })
    .catch(() => {
      /* leave placeholders as "—" */
    });

  function setMetric(id, value) {
    const el = document.getElementById(id);
    if (!el || value === undefined || value === null) return;
    el.textContent = value;
  }

  function formatCLV(v) {
    if (typeof v !== "number") return null;
    const sign = v > 0 ? "+" : "";
    return `${sign}${v.toFixed(2)}%`;
  }

  function formatHit(v) {
    if (typeof v !== "number") return null;
    return `${(v * 100).toFixed(1)}%`;
  }
})();

/* ═══════════════════════════════════════════════════════════
   PredictView — Dynamic Frontend
   Framer Motion (motion.js) + Plotly.js + Vanilla JS
   ═══════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────
let DATA = null;
let activeAnalysis = 0;
let learnStates = {};
let chartDataCache = {};       // cache fetched chart JSONs
let currentPlatform = "all";   // "all" | "kalshi" | "polymarket"
let filteredAnalyses = [];     // analyses visible for current platform
const { animate, stagger, inView } = Motion;

// ── Plotly shared theme ────────────────────────────────────
const PLOTLY_LAYOUT = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(15,15,24,0.6)",
    font: { family: "Inter, system-ui, sans-serif", color: "#a1a1aa", size: 12 },
    margin: { l: 56, r: 24, t: 40, b: 48 },
    xaxis: { gridcolor: "rgba(255,255,255,0.04)", zerolinecolor: "rgba(255,255,255,0.08)" },
    yaxis: { gridcolor: "rgba(255,255,255,0.04)", zerolinecolor: "rgba(255,255,255,0.08)" },
    hoverlabel: { bgcolor: "#1a1a2e", bordercolor: "#333", font: { color: "#f0f0f3", size: 13 } },
    modebar: { bgcolor: "transparent", color: "#555", activecolor: "#818cf8" },
};
const PLOTLY_CONFIG = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d"] };
const C = { accent: "#818cf8", green: "#34d399", red: "#f87171", amber: "#fbbf24", blue: "#60a5fa", neutral: "#6b7280" };

// ── Init ───────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", boot);

async function boot() {
    setupCursorGlow();
    setupNavScroll();
    setupPlatformSwitcher();
    try {
        const res = await fetch("/api/data");
        DATA = await res.json();
        applyPlatform("all");
        setupIntersectionAnimations();
    } catch (err) {
        console.error("Failed to load data:", err);
        document.getElementById("hero-badge-text").textContent = "Error loading data";
    }
}

// ── Platform Switching ─────────────────────────────────────
function setupPlatformSwitcher() {
    const container = document.getElementById("platform-switcher");
    if (!container) return;
    container.addEventListener("click", (e) => {
        const btn = e.target.closest(".platform-btn");
        if (!btn || btn.classList.contains("active")) return;
        const platform = btn.dataset.platform;
        container.querySelectorAll(".platform-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        applyPlatform(platform);
    });
}

function applyPlatform(platform) {
    currentPlatform = platform;
    document.body.setAttribute("data-platform", platform);

    // Filter analyses for this platform
    filteredAnalyses = DATA.analyses.filter(a => {
        if (platform === "all") return true;
        return a.platform === platform || a.platform === "both";
    });

    // Get platform-specific hero/stats
    const pData = DATA.platforms && DATA.platforms[platform]
        ? DATA.platforms[platform]
        : { hero: DATA.hero, stats_bar: DATA.stats_bar };

    renderHero(pData.hero);
    renderStatsBar(pData.stats_bar);
    renderAnalysisNav();
    updateSectionHeader();
    updateFooter();

    if (filteredAnalyses.length > 0) {
        showAnalysis(0);
    } else {
        document.getElementById("analysis-detail").innerHTML = "";
    }
}

function updateSectionHeader() {
    const eyebrow = document.getElementById("section-eyebrow");
    const title = document.getElementById("section-title");
    if (!eyebrow || !title) return;

    const labels = {
        all: { eyebrow: "Deep Dives", title: `${filteredAnalyses.length} Analyses` },
        kalshi: { eyebrow: "Kalshi Exchange", title: `${filteredAnalyses.length} Analyses` },
        polymarket: { eyebrow: "Polymarket On-Chain", title: `${filteredAnalyses.length} Analyses` },
    };
    const l = labels[currentPlatform] || labels.all;
    eyebrow.textContent = l.eyebrow;
    title.textContent = l.title;
}

function updateFooter() {
    const el = document.getElementById("footer-trades");
    if (!el) return;
    const texts = { all: "476M+ trades", kalshi: "72M+ Kalshi trades", polymarket: "404M+ Polymarket trades" };
    el.textContent = texts[currentPlatform] || texts.all;
}

// ── Cursor Glow ────────────────────────────────────────────
function setupCursorGlow() {
    const glow = document.getElementById("cursor-glow");
    if (!glow || window.matchMedia("(pointer: coarse)").matches) return;
    let mouseX = 0, mouseY = 0, glowX = 0, glowY = 0;
    document.addEventListener("mousemove", (e) => { mouseX = e.clientX; mouseY = e.clientY; });
    (function lerp() {
        glowX += (mouseX - glowX) * 0.08;
        glowY += (mouseY - glowY) * 0.08;
        glow.style.left = glowX + "px";
        glow.style.top  = glowY + "px";
        requestAnimationFrame(lerp);
    })();
}

// ── Nav scroll effect ──────────────────────────────────────
function setupNavScroll() {
    const nav = document.getElementById("navbar");
    let ticking = false;
    window.addEventListener("scroll", () => {
        if (!ticking) {
            requestAnimationFrame(() => { nav.classList.toggle("scrolled", window.scrollY > 50); ticking = false; });
            ticking = true;
        }
    });
}

// ── Intersection animations ────────────────────────────────
function setupIntersectionAnimations() {
    const statsRow = document.querySelector(".stats-row");
    if (statsRow) {
        inView(statsRow, () => {
            animate(statsRow.querySelectorAll(".stat-card"), { opacity: [0, 1], y: [24, 0] }, { delay: stagger(0.08), duration: 0.5, easing: [0.22, 1, 0.36, 1] });
        }, { amount: 0.3 });
    }
    const navGrid = document.querySelector(".analysis-nav");
    if (navGrid) {
        inView(navGrid, () => {
            animate(navGrid.querySelectorAll(".analysis-nav-item"), { opacity: [0, 1], y: [20, 0], scale: [0.97, 1] }, { delay: stagger(0.06), duration: 0.5, easing: [0.22, 1, 0.36, 1] });
        }, { amount: 0.2 });
    }
}

// ── Hero ───────────────────────────────────────────────────
function renderHero(hero) {
    const h = hero || DATA.hero;
    document.getElementById("hero-badge-text").textContent = h.badge;
    // Smart line break: split roughly in the middle at a word boundary
    const words = h.title.split(" ");
    const mid = Math.ceil(words.length / 2);
    const titleHTML = words.slice(0, mid).join(" ") + "<br>" + words.slice(mid).join(" ");
    document.getElementById("hero-title").innerHTML = titleHTML;
    document.getElementById("hero-subtitle").textContent = h.subtitle;
    animate("#hero-badge", { opacity: [0, 1], y: [20, 0] }, { duration: 0.6, delay: 0.1 });
    animate("#hero-title", { opacity: [0, 1], y: [30, 0] }, { duration: 0.7, delay: 0.2 });
    animate("#hero-subtitle", { opacity: [0, 1], y: [20, 0] }, { duration: 0.6, delay: 0.35 });
    animate(".hero-cta", { opacity: [0, 1], y: [20, 0] }, { duration: 0.6, delay: 0.5 });
}

// ── Stats Bar ──────────────────────────────────────────────
function renderStatsBar(statsBar) {
    const stats = statsBar || DATA.stats_bar;
    document.getElementById("stats-row").innerHTML = stats
        .map((s) => `<div class="stat-card"><div class="stat-label">${s.label}</div><div class="stat-value color-${s.color}">${s.value}</div><div class="stat-sub">${s.sub}</div></div>`)
        .join("");
}

// ── Analysis Nav ───────────────────────────────────────────
function renderAnalysisNav() {
    const container = document.getElementById("analysis-nav");
    const tagLabels = { kalshi: "Kalshi", polymarket: "Poly", both: "Both" };
    container.innerHTML = filteredAnalyses.map((a, i) => {
        const tagClass = `tag-${a.platform}`;
        const showTag = currentPlatform === "all";
        return `
        <a class="analysis-nav-item${i === 0 ? " active" : ""}" id="nav-${i}" data-index="${i}">
            <div style="display:flex;align-items:center;gap:8px;">
                <div class="analysis-nav-num">${String(a.id).padStart(2, "0")}</div>
                ${showTag ? `<span class="analysis-platform-tag ${tagClass}">${tagLabels[a.platform]}</span>` : ""}
            </div>
            <div class="analysis-nav-text"><h4>${a.title}</h4><span>${a.nav_subtitle}</span></div>
        </a>`;
    }).join("");
    container.addEventListener("click", (e) => {
        const item = e.target.closest(".analysis-nav-item");
        if (item) showAnalysis(parseInt(item.dataset.index));
    });
}

// ── Show Analysis ──────────────────────────────────────────
function showAnalysis(index) {
    const detail = document.getElementById("analysis-detail");
    const a = filteredAnalyses[index];
    if (!a) return;

    document.querySelectorAll(".analysis-nav-item").forEach((el, i) => el.classList.toggle("active", i === index));
    detail.classList.add("fading");

    setTimeout(async () => {
        detail.innerHTML = buildAnalysisHTML(a);
        detail.classList.remove("fading");

        // Framer Motion entrance animations
        const heading = detail.querySelector(".analysis-heading");
        const desc = detail.querySelector(".analysis-desc");
        const kvItems = detail.querySelectorAll(".kv-item");
        const card = detail.querySelector(".analysis-card");
        if (heading) animate(heading, { opacity: [0, 1], x: [-12, 0] }, { duration: 0.4 });
        if (desc) animate(desc, { opacity: [0, 1], y: [10, 0] }, { duration: 0.4, delay: 0.05 });
        if (kvItems.length) animate(kvItems, { opacity: [0, 1], y: [12, 0] }, { delay: stagger(0.04), duration: 0.35, easing: [0.22, 1, 0.36, 1] });
        if (card) animate(card, { opacity: [0, 1], y: [20, 0] }, { duration: 0.5, delay: 0.1 });

        setupLearnToggle(a.id);

        // Load and render Plotly chart
        await renderPlotlyChart(a);
    }, 250);

    activeAnalysis = index;
    setTimeout(() => detail.scrollIntoView({ behavior: "smooth", block: "start" }), 300);
}

// ═══════════════════════════════════════════════════════════
//  PLOTLY CHART RENDERERS
// ═══════════════════════════════════════════════════════════

async function fetchChartData(chartPng) {
    const jsonName = chartPng.replace(".png", ".json");
    if (chartDataCache[jsonName]) return chartDataCache[jsonName];
    const res = await fetch(`/api/chart-data/${jsonName}`);
    const data = await res.json();
    chartDataCache[jsonName] = data;
    return data;
}

async function renderPlotlyChart(analysis) {
    const el = document.getElementById(`plotly-chart-${analysis.id}`);
    if (!el) return;
    el.innerHTML = '<div class="chart-loading">Loading interactive chart…</div>';

    try {
        const d = await fetchChartData(analysis.chart);
        const renderers = {
            1: renderChart1, 2: renderChart2, 3: renderChart3, 4: renderChart4,
            5: renderChart5, 6: renderChart6, 7: renderChart7, 8: renderChart8,
            9: renderChart9, 10: renderChart10, 11: renderChart11, 12: renderChart12,
        };
        if (renderers[analysis.id]) {
            await renderers[analysis.id](el, d);
        }
    } catch (err) {
        console.error("Chart render failed:", err);
        el.innerHTML = `<img class="chart-img loaded" src="/charts/${analysis.chart}" alt="${analysis.title}" style="max-width:100%;border-radius:10px">`;
    }
}

// 1 — Dataset Overview (two bar charts)
async function renderChart1(el, d) {
    const traces = [
        { x: d.months, y: d.trades_millions, type: "bar", name: "Trades (M)", marker: { color: C.blue, opacity: 0.85 }, yaxis: "y", hovertemplate: "%{x|%b %Y}<br>%{y:.1f}M trades<extra></extra>" },
        { x: d.months, y: d.contracts_millions, type: "bar", name: "Contracts (M)", marker: { color: C.green, opacity: 0.85 }, yaxis: "y2", hovertemplate: "%{x|%b %Y}<br>%{y:.0f}M contracts<extra></extra>" },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Monthly Trading Activity on Kalshi", font: { size: 16, color: "#f0f0f3" } },
        barmode: "group",
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Trades (millions)", domain: [0.55, 1] },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "Contracts (millions)", domain: [0, 0.42] },
        xaxis: { ...PLOTLY_LAYOUT.xaxis },
        showlegend: true,
        legend: { x: 0, y: 1.12, orientation: "h", font: { size: 11 } },
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 2 — Calibration Curve (scatter + diagonal)
async function renderChart2(el, d) {
    const maxTrades = Math.max(...d.total_trades);
    const sizes = d.total_trades.map(t => Math.max(6, (t / maxTrades) * 28));
    const traces = [
        { x: [0, 100], y: [0, 100], mode: "lines", name: "Perfect Calibration", line: { color: C.amber, dash: "dash", width: 2 }, hoverinfo: "skip" },
        { x: d.price, y: d.win_rate, mode: "markers", name: "Actual", marker: { color: C.blue, size: sizes, opacity: 0.8, line: { color: "rgba(255,255,255,0.3)", width: 0.5 } },
          hovertemplate: "Price: %{x}¢<br>Win rate: %{y:.1f}%<br>Trades: %{customdata:,}<extra></extra>", customdata: d.total_trades },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Market Calibration: Do Prices Match Reality?", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Contract Price (¢ = implied probability %)", range: [0, 100] },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Actual Win Rate (%)", range: [0, 100], scaleanchor: "x" },
        shapes: [{ type: "rect", x0: 0, x1: 15, y0: 0, y1: 100, fillcolor: "rgba(248,113,113,0.06)", line: { width: 0 }, layer: "below" }],
        annotations: [{ x: 7.5, y: 95, text: "Longshot<br>Zone", showarrow: false, font: { size: 11, color: C.red }, opacity: 0.7 }],
        showlegend: true, legend: { x: 0.02, y: 0.98, font: { size: 11 } },
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 3 — Longshot Bias (grouped bar + EV bar)
async function renderChart3(el, d) {
    const labels = d.price.map(p => p + "¢");
    const evColors = d.ev_per_dollar.map(ev => ev < 1 ? C.red : C.green);
    const traces = [
        { x: labels, y: d.implied_prob, type: "bar", name: "Implied Prob (%)", marker: { color: C.blue, opacity: 0.85 }, hovertemplate: "%{x}: %{y:.1f}% implied<extra></extra>" },
        { x: labels, y: d.actual_win_rate, type: "bar", name: "Actual Win Rate (%)", marker: { color: C.amber, opacity: 0.85 }, hovertemplate: "%{x}: %{y:.1f}% actual<extra></extra>" },
        { x: labels, y: d.ev_per_dollar, type: "bar", name: "EV per $1", marker: { color: evColors }, yaxis: "y2", hovertemplate: "%{x}: $%{y:.2f} per $1 bet<extra></extra>", visible: "legendonly" },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Longshot Bias: Cheap Contracts Are Overpriced", font: { size: 16, color: "#f0f0f3" } },
        barmode: "group",
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Contract Price" },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Probability (%)" },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "EV per $1", overlaying: "y", side: "right", showgrid: false },
        showlegend: true, legend: { x: 0, y: 1.12, orientation: "h", font: { size: 11 } },
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 4 — Maker vs Taker (excess return lines + P&L bars)
async function renderChart4(el, d) {
    const traces = [
        { x: d.price, y: d.taker_excess, type: "scatter", mode: "lines", name: "Taker Excess Return", line: { color: C.red, width: 2 }, fill: "tozeroy", fillcolor: "rgba(248,113,113,0.1)", hovertemplate: "Price: %{x}¢<br>Taker: %{y:+.2f}pp<extra></extra>" },
        { x: d.price, y: d.maker_excess, type: "scatter", mode: "lines", name: "Maker Excess Return", line: { color: C.green, width: 2 }, fill: "tozeroy", fillcolor: "rgba(52,211,153,0.1)", hovertemplate: "Price: %{x}¢<br>Maker: %{y:+.2f}pp<extra></extra>" },
        { x: d.price, y: d.taker_pnl, type: "bar", name: "Taker P&L", marker: { color: C.red, opacity: 0.5 }, yaxis: "y2", visible: "legendonly", hovertemplate: "Price: %{x}¢<br>Taker P&L: %{y:,.0f}<extra></extra>" },
        { x: d.price, y: d.maker_pnl, type: "bar", name: "Maker P&L", marker: { color: C.green, opacity: 0.5 }, yaxis: "y2", visible: "legendonly", hovertemplate: "Price: %{x}¢<br>Maker P&L: %{y:,.0f}<extra></extra>" },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Maker vs Taker: Excess Returns by Price", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Contract Price (¢)", range: [1, 99] },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Excess Return (pp)" },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "P&L (contracts)", overlaying: "y", side: "right", showgrid: false },
        showlegend: true, legend: { x: 0, y: 1.15, orientation: "h", font: { size: 11 } },
        shapes: [{ type: "line", x0: 1, x1: 99, y0: 0, y1: 0, line: { color: "rgba(255,255,255,0.2)", width: 1 } }],
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 5 — Trade Size Distribution (histogram + Lorenz)
async function renderChart5(el, d) {
    // Build bar centers from bin edges
    const barX = [], barY = [];
    for (let i = 0; i < d.hist_counts.length; i++) {
        barX.push((d.hist_bin_edges[i] + d.hist_bin_edges[i + 1]) / 2);
        barY.push(d.hist_counts[i]);
    }
    const traces = [
        { x: barX, y: barY, type: "bar", name: "Trade Count", marker: { color: C.blue, opacity: 0.8 },
          hovertemplate: "Size: %{x:.0f} contracts<br>Count: %{y:,}<extra></extra>", xaxis: "x", yaxis: "y" },
        { x: d.lorenz_pct_trades, y: d.lorenz_pct_volume, type: "scatter", mode: "lines", name: "Volume Concentration", line: { color: C.green, width: 2.5 },
          hovertemplate: "Bottom %{x:.0f}% of trades<br>= %{y:.1f}% of volume<extra></extra>", xaxis: "x2", yaxis: "y2" },
        { x: [0, 100], y: [0, 100], type: "scatter", mode: "lines", name: "Equal Distribution", line: { color: C.neutral, dash: "dash", width: 1 },
          hoverinfo: "skip", xaxis: "x2", yaxis: "y2", showlegend: false },
    ];
    const layout = {
        ...PLOTLY_LAYOUT, grid: { rows: 1, columns: 2, pattern: "independent" },
        title: { text: "Trade Size Distribution", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Trade Size (contracts)", type: "log", domain: [0, 0.46] },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Frequency", type: "log" },
        xaxis2: { ...PLOTLY_LAYOUT.xaxis, title: "% of Trades (smallest→largest)", domain: [0.54, 1] },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "% of Total Volume", anchor: "x2" },
        showlegend: true, legend: { x: 0, y: 1.12, orientation: "h", font: { size: 11 } },
        annotations: [
            { x: 100 - d.top_pct_half_volume, y: 50, xref: "x2", yref: "y2", text: `Top ${d.top_pct_half_volume}% = 50% vol`, showarrow: true, arrowhead: 2, arrowcolor: C.amber, font: { color: C.amber, size: 11 }, ax: -60, ay: -40 },
        ],
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 6 — Returns by Hour (bar + volume background)
async function renderChart6(el, d) {
    const barColors = d.excess_return.map(r => r < 0 ? C.red : C.green);
    const traces = [
        { x: d.hour, y: d.total_contracts_millions, type: "bar", name: "Volume (M)", marker: { color: C.neutral, opacity: 0.15 }, yaxis: "y2", hovertemplate: "Hour %{x}:00 UTC<br>Volume: %{y:.1f}M contracts<extra></extra>" },
        { x: d.hour, y: d.excess_return, type: "bar", name: "Taker Excess Return", marker: { color: barColors }, hovertemplate: "Hour %{x}:00 UTC<br>Excess: %{y:+.3f}pp<extra></extra>" },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Taker Excess Return & Volume by Hour (UTC)", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Hour (UTC)", dtick: 1, range: [-0.5, 23.5], tickvals: Array.from({ length: 24 }, (_, i) => i), ticktext: Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0")) },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Excess Return (pp)" },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "Volume (M contracts)", overlaying: "y", side: "right", showgrid: false },
        barmode: "overlay",
        showlegend: true, legend: { x: 0, y: 1.12, orientation: "h", font: { size: 11 } },
        shapes: [{ type: "line", x0: -0.5, x1: 23.5, y0: 0, y1: 0, line: { color: "rgba(255,255,255,0.2)", width: 1 } }],
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 7 — Calibration Surface (heatmap)
async function renderChart7(el, d) {
    const traces = [{
        z: d.mispricing, x: d.time_bins, y: d.price_bins, type: "heatmap",
        colorscale: [[0, "#ef5350"], [0.5, "#1a1a2e"], [1, "#34d399"]],
        zmid: 0, zmin: -Math.max(...d.mispricing.flat().filter(v => v !== null).map(Math.abs)),
        zmax: Math.max(...d.mispricing.flat().filter(v => v !== null).map(Math.abs)),
        hovertemplate: "Price: %{y}<br>Time: %{x}<br>Mispricing: %{z:+.1f}pp<extra></extra>",
        colorbar: { title: { text: "Mispricing (pp)", side: "right" }, ticksuffix: "pp", len: 0.9 },
    }];
    const annotations = [];
    d.mispricing.forEach((row, i) => {
        row.forEach((val, j) => {
            if (val !== null) {
                annotations.push({ x: d.time_bins[j], y: d.price_bins[i], text: (val >= 0 ? "+" : "") + val.toFixed(1), showarrow: false,
                    font: { size: 10, color: Math.abs(val) > 3 ? "#fff" : "#aaa", weight: "bold" } });
            }
        });
    });
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Calibration Surface: Where & When Markets Are Wrong", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Time to Market Close" },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Price Bucket" },
        annotations,
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 8 — Monte Carlo Kelly (4 subplots)
async function renderChart8(el, d) {
    // We'll use make_subplots manually via 4 axes
    const posReturns = d.final_returns.filter(r => r >= 0);
    const negReturns = d.final_returns.filter(r => r < 0);

    const traces = [
        // Drawdown histogram (top-left)
        { x: d.drawdowns, type: "histogram", nbinsx: 50, marker: { color: C.red, opacity: 0.8 }, name: "Max Drawdown", xaxis: "x", yaxis: "y",
          hovertemplate: "Drawdown: %{x:.1f}%<br>Count: %{y}<extra></extra>" },
        // Final returns positive (top-right)
        { x: posReturns, type: "histogram", nbinsx: 40, marker: { color: C.green, opacity: 0.8 }, name: `Profitable (${(posReturns.length / d.final_returns.length * 100).toFixed(0)}%)`, xaxis: "x2", yaxis: "y2",
          hovertemplate: "Return: %{x:.1f}%<br>Count: %{y}<extra></extra>" },
        // Final returns negative
        { x: negReturns, type: "histogram", nbinsx: 40, marker: { color: C.red, opacity: 0.8 }, name: `Losing (${(negReturns.length / d.final_returns.length * 100).toFixed(0)}%)`, xaxis: "x2", yaxis: "y2",
          hovertemplate: "Return: %{x:.1f}%<br>Count: %{y}<extra></extra>" },
        // Kelly sensitivity (bottom-right)
        { x: d.kelly_fractions, y: d.kelly_median_return, type: "scatter", mode: "lines", name: "Median Return", line: { color: C.blue, width: 2 }, xaxis: "x4", yaxis: "y4",
          hovertemplate: "Kelly: %{x:.1f}%<br>Median: %{y:+.1f}%<extra></extra>" },
        { x: [...d.kelly_fractions, ...d.kelly_fractions.slice().reverse()],
          y: [...d.kelly_p95_return, ...d.kelly_p5_return.slice().reverse()],
          type: "scatter", fill: "toself", fillcolor: "rgba(96,165,250,0.15)", line: { width: 0 },
          name: "5th-95th pctl", xaxis: "x4", yaxis: "y4", hoverinfo: "skip" },
    ];
    // 50 equity curves (bottom-left)
    d.equity_curves.forEach((curve, i) => {
        const x = Array.from({ length: curve.length }, (_, j) => j);
        traces.push({
            x, y: curve, type: "scatter", mode: "lines",
            line: { color: curve[curve.length - 1] > 1 ? C.green : C.red, width: 0.8 },
            opacity: 0.2, xaxis: "x3", yaxis: "y3", showlegend: false, hoverinfo: "skip",
        });
    });

    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Monte Carlo Risk Sizing (5-15¢ Longshot Signal)", font: { size: 16, color: "#f0f0f3" } },
        margin: { l: 56, r: 56, t: 50, b: 48 },
        grid: { rows: 2, columns: 2, pattern: "independent", xgap: 0.08, ygap: 0.1 },
        xaxis:  { ...PLOTLY_LAYOUT.xaxis, title: "Max Drawdown (%)", domain: [0, 0.46] },
        yaxis:  { ...PLOTLY_LAYOUT.yaxis, title: "Frequency", domain: [0.55, 1] },
        xaxis2: { ...PLOTLY_LAYOUT.xaxis, title: "Total Return (%)", domain: [0.54, 1] },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "Frequency", domain: [0.55, 1], anchor: "x2" },
        xaxis3: { ...PLOTLY_LAYOUT.xaxis, title: "Trade #", domain: [0, 0.46] },
        yaxis3: { ...PLOTLY_LAYOUT.yaxis, title: "Portfolio Value ($)", domain: [0, 0.42] },
        xaxis4: { ...PLOTLY_LAYOUT.xaxis, title: "Kelly Fraction (%)", domain: [0.54, 1] },
        yaxis4: { ...PLOTLY_LAYOUT.yaxis, title: "Total Return (%)", domain: [0, 0.42], anchor: "x4" },
        showlegend: true, legend: { x: 0, y: 1.15, orientation: "h", font: { size: 10 } },
        height: 700,
        shapes: [
            { type: "line", x0: 0, x1: 200, y0: 1, y1: 1, xref: "x3", yref: "y3", line: { color: "rgba(255,255,255,0.15)", dash: "dash", width: 1 } },
            { type: "line", x0: 0, x1: 30, y0: 0, y1: 0, xref: "x4", yref: "y4", line: { color: "rgba(255,255,255,0.15)", dash: "dash", width: 1 } },
        ],
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 9 — Kalshi vs Polymarket (monthly bars + cumulative lines)
async function renderChart9(el, d) {
    const traces = [
        { x: d.kalshi_months, y: d.kalshi_trades_m, type: "bar", name: "Kalshi", marker: { color: C.accent, opacity: 0.85 },
          hovertemplate: "%{x|%b %Y}<br>%{y:.2f}M trades<extra>Kalshi</extra>", xaxis: "x", yaxis: "y" },
        { x: d.poly_months, y: d.poly_trades_m, type: "bar", name: "Polymarket", marker: { color: C.green, opacity: 0.85 },
          hovertemplate: "%{x|%b %Y}<br>%{y:.2f}M trades<extra>Poly</extra>", xaxis: "x", yaxis: "y" },
        { x: d.kalshi_months, y: d.kalshi_cum_m, type: "scatter", mode: "lines", name: "Kalshi Cumulative",
          line: { color: C.accent, width: 2.5 }, fill: "tozeroy", fillcolor: "rgba(129,140,248,0.1)",
          hovertemplate: "%{x|%b %Y}<br>%{y:.1f}M cumulative<extra>Kalshi</extra>", xaxis: "x2", yaxis: "y2" },
        { x: d.poly_months, y: d.poly_cum_m, type: "scatter", mode: "lines", name: "Polymarket Cumulative",
          line: { color: C.green, width: 2.5 }, fill: "tozeroy", fillcolor: "rgba(52,211,153,0.1)",
          hovertemplate: "%{x|%b %Y}<br>%{y:.1f}M cumulative<extra>Poly</extra>", xaxis: "x2", yaxis: "y2" },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Kalshi vs Polymarket: Monthly Trade Count", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, domain: [0, 1] },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, title: "Trades (millions)", domain: [0.55, 1] },
        xaxis2: { ...PLOTLY_LAYOUT.xaxis, domain: [0, 1], anchor: "y2" },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "Cumulative Trades (M)", domain: [0, 0.42], anchor: "x2" },
        barmode: "group",
        showlegend: true, legend: { x: 0, y: 1.12, orientation: "h", font: { size: 11 } },
        height: 650,
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 10 — Whale Tracker (top20 bar + Lorenz + distribution + pie)
async function renderChart10(el, d) {
    const shortAddr = d.top20_addresses.map(a => "..." + a.slice(-6));
    const traces = [
        { y: shortAddr, x: d.top20_volume_m, type: "bar", orientation: "h", name: "Top 20 Volume ($M)",
          marker: { color: C.green, opacity: 0.85 },
          hovertemplate: "%{y}<br>$%{x:.1f}M USDC<br>%{customdata:,} trades<extra></extra>",
          customdata: d.top20_trades, xaxis: "x", yaxis: "y" },
        { x: d.lorenz_x, y: d.lorenz_y, type: "scatter", mode: "lines", name: "Lorenz Curve",
          line: { color: C.green, width: 2.5 }, fill: "tozeroy", fillcolor: "rgba(52,211,153,0.1)",
          hovertemplate: "Bottom %{x:.1f}% of traders<br>= %{y:.1f}% of volume<extra></extra>",
          xaxis: "x2", yaxis: "y2" },
        { x: [0, 100], y: [0, 100], type: "scatter", mode: "lines",
          line: { color: C.neutral, dash: "dash", width: 1 }, hoverinfo: "skip",
          xaxis: "x2", yaxis: "y2", showlegend: false },
        { x: d.bins_labels, y: d.bins_counts, type: "bar", name: "Addresses",
          marker: { color: C.amber, opacity: 0.85 },
          hovertemplate: "%{x} trades<br>%{y:,} addresses<extra></extra>",
          xaxis: "x3", yaxis: "y3" },
        { values: [d.top100_pct, Math.max(0, d.top10_pct - d.top100_pct), Math.max(0, 100 - d.top10_pct)],
          labels: ["Top 100", "Top 10% (excl.)", "Remaining"], type: "pie",
          marker: { colors: [C.red, C.amber, C.neutral] },
          textinfo: "label+percent", textfont: { color: "#e0e0e0", size: 11 },
          hovertemplate: "%{label}<br>%{percent}<extra></extra>",
          domain: { x: [0.55, 1], y: [0, 0.42] }, showlegend: false },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: `Polymarket Whale Tracker (Gini: ${d.gini})`, font: { size: 16, color: "#f0f0f3" } },
        xaxis:  { ...PLOTLY_LAYOUT.xaxis, title: "Volume ($M USDC)", domain: [0, 0.45] },
        yaxis:  { ...PLOTLY_LAYOUT.yaxis, domain: [0.55, 1], automargin: true, tickfont: { size: 8, family: "JetBrains Mono, monospace" } },
        xaxis2: { ...PLOTLY_LAYOUT.xaxis, title: "% of Traders", domain: [0.55, 1] },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "% of Volume", domain: [0.55, 1], anchor: "x2" },
        xaxis3: { ...PLOTLY_LAYOUT.xaxis, title: "Trades per Address", domain: [0, 0.45] },
        yaxis3: { ...PLOTLY_LAYOUT.yaxis, title: "Addresses (log)", type: "log", domain: [0, 0.42] },
        showlegend: true, legend: { x: 0, y: 1.12, orientation: "h", font: { size: 10 } },
        height: 700,
        annotations: [
            { x: 50, y: 2, xref: "x2", yref: "y2", text: `Gini = ${d.gini}`, showarrow: false, font: { color: C.red, size: 13 } },
        ],
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 11 — Market Categories (horizontal bars + stacked area)
async function renderChart11(el, d) {
    const traces = [
        { y: d.categories, x: d.total_volume_m, type: "bar", orientation: "h", name: "Volume (M)",
          marker: { color: d.categories.map(c => d.cat_colors[c] || C.neutral), opacity: 0.85 },
          hovertemplate: "%{y}<br>%{x:.1f}M volume<extra></extra>",
          xaxis: "x", yaxis: "y" },
    ];
    const cats = Object.keys(d.monthly_stacks);
    cats.forEach(cat => {
        traces.push({
            x: d.monthly_months, y: d.monthly_stacks[cat], type: "scatter",
            mode: "lines", stackgroup: "one", name: cat,
            line: { color: d.cat_colors[cat] || C.neutral, width: 0.5 },
            fillcolor: (d.cat_colors[cat] || C.neutral) + "b3",
            hovertemplate: `%{x|%b %Y}<br>${cat}: %{y:,} markets<extra></extra>`,
            xaxis: "x2", yaxis: "y2",
        });
    });
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Kalshi Market Categories", font: { size: 16, color: "#f0f0f3" } },
        xaxis: { ...PLOTLY_LAYOUT.xaxis, title: "Total Volume (M contracts)", domain: [0, 0.42] },
        yaxis: { ...PLOTLY_LAYOUT.yaxis, domain: [0, 1], automargin: true },
        xaxis2: { ...PLOTLY_LAYOUT.xaxis, domain: [0.52, 1] },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "Markets Created", domain: [0, 1], anchor: "x2" },
        showlegend: true, legend: { x: 0.52, y: 1.12, orientation: "h", font: { size: 10 } },
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// 12 — Spread & Liquidity (4 subplots)
async function renderChart12(el, d) {
    const barX = [];
    for (let i = 0; i < d.hist_counts.length; i++) {
        barX.push((d.hist_edges[i] + d.hist_edges[i + 1]) / 2);
    }
    const traces = [
        { x: barX, y: d.hist_counts, type: "bar", name: "Spread Dist", marker: { color: C.blue, opacity: 0.8 },
          hovertemplate: "Spread: %{x:.0f}¢<br>Count: %{y:,}<extra></extra>", xaxis: "x", yaxis: "y" },
        { x: d.vol_x, y: d.vol_y, type: "scatter", mode: "lines+markers", name: "Spread vs Volume",
          marker: { color: C.blue, size: 8 }, line: { color: C.blue, width: 2 },
          hovertemplate: "Avg Vol: %{x:,.0f}<br>Avg Spread: %{y:.1f}¢<extra></extra>",
          xaxis: "x2", yaxis: "y2" },
        { x: d.time_labels, y: d.time_spread, type: "bar", name: "Spread vs Time",
          marker: { color: C.amber, opacity: 0.85 },
          hovertemplate: "%{x}<br>Avg Spread: %{y:.1f}¢<br>%{customdata:,} markets<extra></extra>",
          customdata: d.time_counts, xaxis: "x3", yaxis: "y3" },
        { x: d.price_x, y: d.price_y, type: "scatter", mode: "lines+markers", name: "Liquidity Smile",
          marker: { color: C.green, size: 6 }, line: { color: C.green, width: 2 },
          hovertemplate: "Mid: %{x}¢<br>Avg Spread: %{y:.1f}¢<extra></extra>",
          xaxis: "x4", yaxis: "y4" },
    ];
    const layout = {
        ...PLOTLY_LAYOUT,
        title: { text: "Kalshi Spread & Liquidity Analysis", font: { size: 16, color: "#f0f0f3" } },
        xaxis:  { ...PLOTLY_LAYOUT.xaxis, title: "Bid-Ask Spread (¢)", domain: [0, 0.46] },
        yaxis:  { ...PLOTLY_LAYOUT.yaxis, title: "Markets", domain: [0.55, 1] },
        xaxis2: { ...PLOTLY_LAYOUT.xaxis, title: "Volume (log)", type: "log", domain: [0.56, 1] },
        yaxis2: { ...PLOTLY_LAYOUT.yaxis, title: "Avg Spread (¢)", domain: [0.55, 1], anchor: "x2" },
        xaxis3: { ...PLOTLY_LAYOUT.xaxis, title: "Time to Close", domain: [0, 0.46] },
        yaxis3: { ...PLOTLY_LAYOUT.yaxis, title: "Avg Spread (¢)", domain: [0, 0.42] },
        xaxis4: { ...PLOTLY_LAYOUT.xaxis, title: "Mid Price (¢)", domain: [0.56, 1] },
        yaxis4: { ...PLOTLY_LAYOUT.yaxis, title: "Avg Spread (¢)", domain: [0, 0.42], anchor: "x4" },
        showlegend: true, legend: { x: 0, y: 1.12, orientation: "h", font: { size: 10 } },
        height: 650,
        shapes: [
            { type: "line", x0: d.avg_spread, x1: d.avg_spread, y0: 0, y1: 1, yref: "paper", xref: "x",
              line: { color: C.amber, dash: "dash", width: 1.5 } },
        ],
        annotations: [
            { x: d.avg_spread, y: 1, xref: "x", yref: "paper", text: `Mean: ${d.avg_spread}¢`,
              showarrow: false, font: { color: C.amber, size: 11 }, yshift: 10 },
        ],
    };
    await Plotly.newPlot(el, traces, layout, PLOTLY_CONFIG);
}

// ═══════════════════════════════════════════════════════════
//  BUILD ANALYSIS HTML
// ═══════════════════════════════════════════════════════════

function buildAnalysisHTML(a) {
    const statsHTML = a.stats && a.stats.length
        ? `<div class="kv-grid">${a.stats.map((s) => `<div class="kv-item"><div class="label">${s.label}</div><div class="value color-${s.color}${s.small ? " small" : ""}">${s.value}</div></div>`).join("")}</div>`
        : "";

    const insightsHTML = a.insights.map((ins) => `<span class="insight ${ins.color}">${ins.text}</span>`).join("");
    const isOpen = learnStates[a.id] || false;

    const learnHTML = a.learn
        ? `<div class="learn-section" id="learn-${a.id}">
            <div class="learn-header" id="learn-toggle-${a.id}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                <h3>${a.learn.title}</h3>
                <span class="learn-toggle">${isOpen ? "Hide" : "Learn"} <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="${isOpen ? "18 15 12 9 6 15" : "6 9 12 15 18 9"}"/></svg></span>
            </div>
            <div class="learn-body${isOpen ? " open" : ""}" id="learn-body-${a.id}">
                <p>${a.learn.body}</p>
                ${a.learn.key_terms ? `<div class="learn-terms">${a.learn.key_terms.map((t) => `<div class="learn-term"><div class="learn-term-name">${t.term}</div><div class="learn-term-def">${t.definition}</div></div>`).join("")}</div>` : ""}
            </div>
        </div>` : "";

    return `
        <div class="analysis-heading">
            <span class="num">${String(a.id).padStart(2, "0")} / ${String(filteredAnalyses.length).padStart(2, "0")}</span>
            <h2>${a.title}</h2>
        </div>
        <p class="analysis-desc">${a.description}</p>
        ${statsHTML}
        <div class="analysis-card">
            <div class="chart-container">
                <div class="plotly-chart" id="plotly-chart-${a.id}"></div>
            </div>
            <div class="analysis-content">
                <h3>What This Shows</h3>
                <p>${a.what_it_shows}</p>
                <h3>Key Takeaways</h3>
                <p>${a.takeaways}</p>
                <div class="insights">${insightsHTML}</div>
            </div>
        </div>
        ${learnHTML}
        <div style="display:flex;gap:12px;margin-top:24px;justify-content:space-between;">
            ${activeAnalysis > 0 ? `<button class="nav-btn" onclick="showAnalysis(${activeAnalysis - 1})"><svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13 8H3M7 4L3 8l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg> Previous</button>` : '<div></div>'}
            ${activeAnalysis < filteredAnalyses.length - 1 ? `<button class="nav-btn" onclick="showAnalysis(${activeAnalysis + 1})">Next <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>` : '<div></div>'}
        </div>`;
}

// ── Learn Toggle ───────────────────────────────────────────
function setupLearnToggle(analysisId) {
    const toggle = document.getElementById(`learn-toggle-${analysisId}`);
    if (!toggle) return;
    toggle.addEventListener("click", () => {
        const body = document.getElementById(`learn-body-${analysisId}`);
        const toggleLabel = toggle.querySelector(".learn-toggle");
        const isOpen = body.classList.toggle("open");
        learnStates[analysisId] = isOpen;
        toggleLabel.innerHTML = `${isOpen ? "Hide" : "Learn"} <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="${isOpen ? "18 15 12 9 6 15" : "6 9 12 15 18 9"}"/></svg>`;
        if (isOpen) {
            const terms = body.querySelectorAll(".learn-term");
            if (terms.length) animate(terms, { opacity: [0, 1], y: [16, 0] }, { delay: stagger(0.06), duration: 0.4, easing: [0.22, 1, 0.36, 1] });
            animate(body.querySelector("p"), { opacity: [0, 1], y: [10, 0] }, { duration: 0.4 });
        }
    });
}

// ── Keyboard Navigation ────────────────────────────────────
document.addEventListener("keydown", (e) => {
    if (!DATA || !filteredAnalyses.length) return;
    const max = filteredAnalyses.length - 1;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); showAnalysis(Math.min(activeAnalysis + 1, max)); }
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); showAnalysis(Math.max(activeAnalysis - 1, 0)); }
});

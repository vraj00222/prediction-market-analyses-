// ── State ──────────────────────────────────────────────────────────
let DATA = null;
let activeAnalysis = 0;

// ── Bootstrap ─────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);

async function init() {
    try {
        const res = await fetch("/api/data");
        DATA = await res.json();
        renderHero();
        renderStatsBar();
        renderAnalysisNav();
        showAnalysis(0);
    } catch (err) {
        console.error("Failed to load data:", err);
        document.getElementById("hero-badge-text").textContent = "Error loading data";
    }
}

// ── Render Hero ───────────────────────────────────────────────────
function renderHero() {
    const h = DATA.hero;
    document.getElementById("hero-badge-text").textContent = h.badge;
    document.getElementById("hero-title").innerHTML = h.title.replace(
        "Microstructure",
        "<br>Microstructure"
    );
    document.getElementById("hero-subtitle").textContent = h.subtitle;
}

// ── Render Stats Bar ──────────────────────────────────────────────
function renderStatsBar() {
    const container = document.getElementById("stats-row");
    container.innerHTML = DATA.stats_bar
        .map(
            (s, i) => `
        <div class="stat-card" style="animation-delay: ${i * 80}ms">
            <div class="stat-label">${s.label}</div>
            <div class="stat-value color-${s.color}">${s.value}</div>
            <div class="stat-sub">${s.sub}</div>
        </div>`
        )
        .join("");
}

// ── Render Analysis Navigation ────────────────────────────────────
function renderAnalysisNav() {
    const container = document.getElementById("analysis-nav");
    container.innerHTML = DATA.analyses
        .map(
            (a, i) => `
        <a class="analysis-nav-item${i === 0 ? " active" : ""}"
           id="nav-${i}"
           onclick="showAnalysis(${i})"
           style="animation-delay: ${i * 60}ms">
            <div class="analysis-nav-num">${String(a.id).padStart(2, "0")}</div>
            <div class="analysis-nav-text">
                <h4>${a.title}</h4>
                <span>${a.nav_subtitle}</span>
            </div>
        </a>`
        )
        .join("");
}

// ── Show Analysis Detail ──────────────────────────────────────────
function showAnalysis(index) {
    const detail = document.getElementById("analysis-detail");
    const a = DATA.analyses[index];

    // Update nav active state
    document.querySelectorAll(".analysis-nav-item").forEach((el, i) => {
        el.classList.toggle("active", i === index);
    });

    // Fade out
    detail.classList.add("fading");

    setTimeout(() => {
        detail.innerHTML = buildAnalysisHTML(a);
        detail.classList.remove("fading");

        // Lazy-load chart image with fade
        const img = detail.querySelector(".chart-img");
        if (img) {
            img.onload = () => img.classList.add("loaded");
            // If already cached, trigger manually
            if (img.complete) img.classList.add("loaded");
        }
    }, 200);

    activeAnalysis = index;

    // Scroll to detail
    setTimeout(() => {
        detail.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 250);
}

// ── Build Analysis HTML ───────────────────────────────────────────
function buildAnalysisHTML(a) {
    const statsHTML =
        a.stats && a.stats.length
            ? `<div class="kv-grid">
            ${a.stats
                .map(
                    (s) => `
                <div class="kv-item">
                    <div class="label">${s.label}</div>
                    <div class="value color-${s.color}${s.small ? " small" : ""}">${s.value}</div>
                </div>`
                )
                .join("")}
        </div>`
            : "";

    const insightsHTML = a.insights
        .map((ins) => `<span class="insight ${ins.color}">${ins.text}</span>`)
        .join("");

    return `
        <div class="section-header">
            <span class="section-number">${String(a.id).padStart(2, "0")} / ${String(DATA.analyses.length).padStart(2, "0")}</span>
            <h2>${a.title}</h2>
        </div>
        <p class="section-desc">${a.description}</p>

        ${statsHTML}

        <div class="analysis-card" style="margin-top: 24px;">
            <div class="chart-container">
                <img class="chart-img" src="/charts/${a.chart}" alt="${a.title}">
            </div>
            <div class="analysis-content">
                <h3>What This Shows</h3>
                <p>${a.what_it_shows}</p>
                <h3>Key Takeaways</h3>
                <p>${a.takeaways}</p>
                <div class="insights">${insightsHTML}</div>
            </div>
        </div>
    `;
}

// ── Keyboard Navigation ───────────────────────────────────────────
document.addEventListener("keydown", (e) => {
    if (!DATA) return;
    const max = DATA.analyses.length - 1;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        showAnalysis(Math.min(activeAnalysis + 1, max));
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        showAnalysis(Math.max(activeAnalysis - 1, 0));
    }
});

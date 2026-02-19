/* ═══════════════════════════════════════════════════════════
   PredictView — Dynamic Frontend
   Framer Motion (motion.js) + Vanilla JS
   ═══════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────
let DATA = null;
let activeAnalysis = 0;
let learnStates = {};          // track open/closed per analysis id
const { animate, stagger, inView, scroll } = Motion;  // from motion.js CDN

// ── Init ───────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", boot);

async function boot() {
    setupCursorGlow();
    setupNavScroll();

    try {
        const res = await fetch("/api/data");
        DATA = await res.json();
        renderHero();
        renderStatsBar();
        renderAnalysisNav();
        showAnalysis(0);
        setupIntersectionAnimations();
    } catch (err) {
        console.error("Failed to load data:", err);
        document.getElementById("hero-badge-text").textContent = "Error loading data";
    }
}

// ── Cursor Glow ────────────────────────────────────────────
function setupCursorGlow() {
    const glow = document.getElementById("cursor-glow");
    if (!glow || window.matchMedia("(pointer: coarse)").matches) return;

    let mouseX = 0, mouseY = 0, glowX = 0, glowY = 0;
    document.addEventListener("mousemove", (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function lerp() {
        glowX += (mouseX - glowX) * 0.08;
        glowY += (mouseY - glowY) * 0.08;
        glow.style.left = glowX + "px";
        glow.style.top  = glowY + "px";
        requestAnimationFrame(lerp);
    }
    lerp();
}

// ── Nav scroll effect ──────────────────────────────────────
function setupNavScroll() {
    const nav = document.getElementById("navbar");
    let ticking = false;
    window.addEventListener("scroll", () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                nav.classList.toggle("scrolled", window.scrollY > 50);
                ticking = false;
            });
            ticking = true;
        }
    });
}

// ── Intersection animations ────────────────────────────────
function setupIntersectionAnimations() {
    // Stats row stagger
    const statsRow = document.querySelector(".stats-row");
    if (statsRow) {
        inView(statsRow, () => {
            animate(
                statsRow.querySelectorAll(".stat-card"),
                { opacity: [0, 1], y: [24, 0] },
                { delay: stagger(0.08), duration: 0.5, easing: [0.22, 1, 0.36, 1] }
            );
        }, { amount: 0.3 });
    }

    // Analysis nav stagger
    const navGrid = document.querySelector(".analysis-nav");
    if (navGrid) {
        inView(navGrid, () => {
            animate(
                navGrid.querySelectorAll(".analysis-nav-item"),
                { opacity: [0, 1], y: [20, 0], scale: [0.97, 1] },
                { delay: stagger(0.06), duration: 0.5, easing: [0.22, 1, 0.36, 1] }
            );
        }, { amount: 0.2 });
    }
}

// ── Hero ───────────────────────────────────────────────────
function renderHero() {
    const h = DATA.hero;
    document.getElementById("hero-badge-text").textContent = h.badge;

    const titleEl = document.getElementById("hero-title");
    titleEl.innerHTML = h.title.replace("Market", "Market<br>");
    document.getElementById("hero-subtitle").textContent = h.subtitle;

    // Animate hero elements with Framer Motion
    animate("#hero-badge", { opacity: [0, 1], y: [20, 0] }, { duration: 0.6, delay: 0.1 });
    animate("#hero-title", { opacity: [0, 1], y: [30, 0] }, { duration: 0.7, delay: 0.2 });
    animate("#hero-subtitle", { opacity: [0, 1], y: [20, 0] }, { duration: 0.6, delay: 0.35 });
    animate(".hero-cta", { opacity: [0, 1], y: [20, 0] }, { duration: 0.6, delay: 0.5 });
}

// ── Stats Bar ──────────────────────────────────────────────
function renderStatsBar() {
    const container = document.getElementById("stats-row");
    container.innerHTML = DATA.stats_bar
        .map((s) => `
            <div class="stat-card">
                <div class="stat-label">${s.label}</div>
                <div class="stat-value color-${s.color}">${s.value}</div>
                <div class="stat-sub">${s.sub}</div>
            </div>`)
        .join("");
}

// ── Analysis Nav ───────────────────────────────────────────
function renderAnalysisNav() {
    const container = document.getElementById("analysis-nav");
    container.innerHTML = DATA.analyses
        .map((a, i) => `
            <a class="analysis-nav-item${i === 0 ? " active" : ""}"
               id="nav-${i}" data-index="${i}">
                <div class="analysis-nav-num">${String(a.id).padStart(2, "0")}</div>
                <div class="analysis-nav-text">
                    <h4>${a.title}</h4>
                    <span>${a.nav_subtitle}</span>
                </div>
            </a>`)
        .join("");

    // Event delegation
    container.addEventListener("click", (e) => {
        const item = e.target.closest(".analysis-nav-item");
        if (item) showAnalysis(parseInt(item.dataset.index));
    });
}

// ── Show Analysis ──────────────────────────────────────────
function showAnalysis(index) {
    const detail = document.getElementById("analysis-detail");
    const a = DATA.analyses[index];

    // Update nav state
    document.querySelectorAll(".analysis-nav-item").forEach((el, i) => {
        el.classList.toggle("active", i === index);
    });

    // Animate out
    detail.classList.add("fading");

    setTimeout(() => {
        detail.innerHTML = buildAnalysisHTML(a);
        detail.classList.remove("fading");

        // Animate in elements
        const card = detail.querySelector(".analysis-card");
        const kvItems = detail.querySelectorAll(".kv-item");
        const heading = detail.querySelector(".analysis-heading");
        const desc = detail.querySelector(".analysis-desc");

        if (heading) animate(heading, { opacity: [0, 1], x: [-12, 0] }, { duration: 0.4 });
        if (desc) animate(desc, { opacity: [0, 1], y: [10, 0] }, { duration: 0.4, delay: 0.05 });

        if (kvItems.length) {
            animate(kvItems, { opacity: [0, 1], y: [12, 0] },
                { delay: stagger(0.04), duration: 0.35, easing: [0.22, 1, 0.36, 1] });
        }

        if (card) {
            animate(card, { opacity: [0, 1], y: [20, 0] }, { duration: 0.5, delay: 0.1 });
        }

        // Chart image fade
        const img = detail.querySelector(".chart-img");
        if (img) {
            img.onload = () => img.classList.add("loaded");
            if (img.complete) img.classList.add("loaded");
        }

        // Learn section toggle
        setupLearnToggle(a.id);
    }, 250);

    activeAnalysis = index;

    // Scroll
    setTimeout(() => {
        detail.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 300);
}

// ── Build Analysis HTML ────────────────────────────────────
function buildAnalysisHTML(a) {
    const statsHTML = a.stats && a.stats.length
        ? `<div class="kv-grid">
            ${a.stats.map((s) => `
                <div class="kv-item">
                    <div class="label">${s.label}</div>
                    <div class="value color-${s.color}${s.small ? " small" : ""}">${s.value}</div>
                </div>`).join("")}
           </div>`
        : "";

    const insightsHTML = a.insights
        .map((ins) => `<span class="insight ${ins.color}">${ins.text}</span>`)
        .join("");

    const isOpen = learnStates[a.id] || false;

    const learnHTML = a.learn
        ? `<div class="learn-section" id="learn-${a.id}">
            <div class="learn-header" id="learn-toggle-${a.id}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                </svg>
                <h3>${a.learn.title}</h3>
                <span class="learn-toggle">${isOpen ? "Hide" : "Learn"} <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="${isOpen ? "18 15 12 9 6 15" : "6 9 12 15 18 9"}"/></svg></span>
            </div>
            <div class="learn-body${isOpen ? " open" : ""}" id="learn-body-${a.id}">
                <p>${a.learn.body}</p>
                ${a.learn.key_terms ? `
                    <div class="learn-terms">
                        ${a.learn.key_terms.map((t) => `
                            <div class="learn-term">
                                <div class="learn-term-name">${t.term}</div>
                                <div class="learn-term-def">${t.definition}</div>
                            </div>`).join("")}
                    </div>` : ""}
            </div>
        </div>`
        : "";

    return `
        <div class="analysis-heading">
            <span class="num">${String(a.id).padStart(2, "0")} / ${String(DATA.analyses.length).padStart(2, "0")}</span>
            <h2>${a.title}</h2>
        </div>
        <p class="analysis-desc">${a.description}</p>

        ${statsHTML}

        <div class="analysis-card">
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

        ${learnHTML}

        <div style="display:flex;gap:12px;margin-top:24px;justify-content:space-between;">
            ${a.id > 1 ? `<button class="nav-btn" onclick="showAnalysis(${a.id - 2})">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13 8H3M7 4L3 8l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Previous
            </button>` : '<div></div>'}
            ${a.id < DATA.analyses.length ? `<button class="nav-btn" onclick="showAnalysis(${a.id})">
                Next
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>` : '<div></div>'}
        </div>
    `;
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
            if (terms.length) {
                animate(terms,
                    { opacity: [0, 1], y: [16, 0] },
                    { delay: stagger(0.06), duration: 0.4, easing: [0.22, 1, 0.36, 1] }
                );
            }
            animate(body.querySelector("p"),
                { opacity: [0, 1], y: [10, 0] },
                { duration: 0.4 }
            );
        }
    });
}

// ── Keyboard Navigation ────────────────────────────────────
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

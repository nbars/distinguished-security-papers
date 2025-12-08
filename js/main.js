// Best Papers in Systems Security - Main JavaScript

let allPapers = [];
let currentVenue = 'all';
let yearFrom = null;
let yearTo = null;
let minYear = 2012;
let maxYear = 2025;

// Load papers data
async function loadPapers() {
    try {
        const response = await fetch('data/papers.json');
        const data = await response.json();
        allPapers = data.papers;

        // Set year range from data
        const years = allPapers.map(p => p.year);
        minYear = Math.min(...years);
        maxYear = Math.max(...years);

        // Initialize sliders
        initYearSlider();

        renderPapers(allPapers);
        setupFilters();
    } catch (error) {
        console.error('Error loading papers:', error);
        document.getElementById('papers-container').innerHTML =
            '<p class="text-danger">Error loading papers. Please try again later.</p>';
    }
}

// Initialize the year range slider
function initYearSlider() {
    const sliderFrom = document.getElementById('year-slider-from');
    const sliderTo = document.getElementById('year-slider-to');
    const labelFrom = document.getElementById('year-label-from');
    const labelTo = document.getElementById('year-label-to');

    sliderFrom.min = minYear;
    sliderFrom.max = maxYear;
    sliderFrom.value = minYear;

    sliderTo.min = minYear;
    sliderTo.max = maxYear;
    sliderTo.value = maxYear;

    labelFrom.textContent = minYear;
    labelTo.textContent = maxYear;

    yearFrom = minYear;
    yearTo = maxYear;

    // Update visual range indicator
    updateRangeHighlight();
}

// Update the visual range highlight
function updateRangeHighlight() {
    const sliderFrom = document.getElementById('year-slider-from');
    const sliderTo = document.getElementById('year-slider-to');
    const rangeSelected = document.getElementById('range-selected');

    const min = parseInt(sliderFrom.min);
    const max = parseInt(sliderFrom.max);
    const fromVal = parseInt(sliderFrom.value);
    const toVal = parseInt(sliderTo.value);

    const fromPercent = ((fromVal - min) / (max - min)) * 100;
    const toPercent = ((toVal - min) / (max - min)) * 100;

    rangeSelected.style.left = fromPercent + '%';
    rangeSelected.style.width = (toPercent - fromPercent) + '%';
}

// Format authors array for display
function formatAuthors(authors) {
    if (!authors || !Array.isArray(authors) || authors.length === 0) {
        return '';
    }

    return authors.map(a => {
        if (a.institution) {
            return `${a.name} (${a.institution})`;
        }
        return a.name;
    }).join(', ');
}

// Apply all filters and render
function applyFilters() {
    let filtered = allPapers;

    // Venue filter
    if (currentVenue !== 'all') {
        filtered = filtered.filter(p => p.venue === currentVenue);
    }

    // Year range filter
    if (yearFrom !== null) {
        filtered = filtered.filter(p => p.year >= yearFrom);
    }
    if (yearTo !== null) {
        filtered = filtered.filter(p => p.year <= yearTo);
    }

    renderPapers(filtered);
}

// Render papers grouped by year
function renderPapers(papers) {
    const container = document.getElementById('papers-container');

    if (papers.length === 0) {
        container.innerHTML = '<p class="text-muted">No papers found matching the filters.</p>';
        return;
    }

    // Group papers by year
    const papersByYear = {};
    papers.forEach(paper => {
        if (!papersByYear[paper.year]) {
            papersByYear[paper.year] = [];
        }
        papersByYear[paper.year].push(paper);
    });

    // Sort years descending
    const years = Object.keys(papersByYear).sort((a, b) => b - a);

    // Build HTML
    let html = '';
    years.forEach(year => {
        html += `<section class="year-section">`;
        html += `<h2 class="year-header">${year}</h2>`;

        papersByYear[year].forEach(paper => {
            html += renderPaper(paper);
        });

        html += `</section>`;
    });

    container.innerHTML = html;
}

// Render a single paper entry
function renderPaper(paper) {
    const titleHtml = paper.url
        ? `<a href="${escapeHtml(paper.url)}" target="_blank" rel="noopener">${escapeHtml(paper.title)}</a>`
        : escapeHtml(paper.title);

    const authorsStr = formatAuthors(paper.authors);

    return `
        <article class="paper-entry" data-venue="${escapeHtml(paper.venue)}">
            <h3 class="paper-title">${titleHtml}</h3>
            ${authorsStr ? `<p class="paper-authors">${escapeHtml(authorsStr)}</p>` : ''}
            <div class="paper-meta">
                <span class="paper-venue">${escapeHtml(paper.venue)}</span>
            </div>
        </article>
    `;
}

// Setup filter buttons and inputs
function setupFilters() {
    // Venue buttons
    const buttons = document.querySelectorAll('[data-venue]');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            buttons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentVenue = button.dataset.venue;
            applyFilters();
        });
    });

    // Year range sliders
    const sliderFrom = document.getElementById('year-slider-from');
    const sliderTo = document.getElementById('year-slider-to');
    const labelFrom = document.getElementById('year-label-from');
    const labelTo = document.getElementById('year-label-to');
    const resetBtn = document.getElementById('reset-years');

    sliderFrom.addEventListener('input', () => {
        let val = parseInt(sliderFrom.value);
        // Ensure from <= to
        if (val > parseInt(sliderTo.value)) {
            val = parseInt(sliderTo.value);
            sliderFrom.value = val;
        }
        yearFrom = val;
        labelFrom.textContent = val;
        updateRangeHighlight();
        applyFilters();
    });

    sliderTo.addEventListener('input', () => {
        let val = parseInt(sliderTo.value);
        // Ensure to >= from
        if (val < parseInt(sliderFrom.value)) {
            val = parseInt(sliderFrom.value);
            sliderTo.value = val;
        }
        yearTo = val;
        labelTo.textContent = val;
        updateRangeHighlight();
        applyFilters();
    });

    resetBtn.addEventListener('click', () => {
        sliderFrom.value = minYear;
        sliderTo.value = maxYear;
        labelFrom.textContent = minYear;
        labelTo.textContent = maxYear;
        yearFrom = minYear;
        yearTo = maxYear;
        updateRangeHighlight();
        applyFilters();
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', loadPapers);

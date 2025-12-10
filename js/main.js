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
        renderAuthorsRanking(allPapers);
        renderFirstAuthorsRanking(allPapers);
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
    renderAuthorsRanking(filtered);
    renderFirstAuthorsRanking(filtered);
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

// Calculate author statistics and render ranking
function renderAuthorsRanking(papers) {
    const container = document.getElementById('authors-container');

    // Build author -> papers mapping
    const authorPapers = {};
    papers.forEach(paper => {
        if (!paper.authors || !Array.isArray(paper.authors)) return;
        paper.authors.forEach(author => {
            const name = author.name;
            if (!name) return;
            if (!authorPapers[name]) {
                authorPapers[name] = [];
            }
            authorPapers[name].push(paper);
        });
    });

    // Extract surname (last word) from full name
    const getSurname = (name) => {
        const parts = name.trim().split(/\s+/);
        return parts[parts.length - 1];
    };

    // Convert to array and sort by paper count, then alphabetically by surname
    const authorList = Object.entries(authorPapers)
        .map(([name, papers]) => ({ name, papers, count: papers.length }))
        .sort((a, b) => {
            if (b.count !== a.count) {
                return b.count - a.count; // Higher count first
            }
            return getSurname(a.name).localeCompare(getSurname(b.name)); // Alphabetical by surname
        });

    if (authorList.length === 0) {
        container.innerHTML = '<p class="text-muted">No authors found.</p>';
        return;
    }

    // Calculate ranks (with ties - dense ranking: 1, 1, 2, 2, 3...)
    let previousCount = null;
    let currentRank = 0;
    authorList.forEach((author) => {
        if (author.count !== previousCount) {
            currentRank++;
        }
        author.rank = currentRank;
        previousCount = author.count;
    });

    // Build HTML with limit
    const INITIAL_LIMIT = 25;
    const showAll = authorList.length <= INITIAL_LIMIT;

    let html = '<div class="authors-list">';
    authorList.forEach((author, index) => {
        const authorId = `author-${index}`;
        const isHidden = !showAll && index >= INITIAL_LIMIT;
        const papersHtml = author.papers
            .sort((a, b) => b.year - a.year)
            .map(p => {
                const titleHtml = p.url
                    ? `<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.title)}</a>`
                    : escapeHtml(p.title);
                return `<li class="author-paper-item">${titleHtml} <span class="text-muted">(${escapeHtml(p.venue)} ${p.year})</span></li>`;
            })
            .join('');

        html += `
            <div class="author-entry${isHidden ? ' author-hidden' : ''}" ${isHidden ? 'style="display:none;"' : ''}>
                <div class="author-header" onclick="toggleAuthorPapers('${authorId}')">
                    <span class="author-rank">#${author.rank}</span>
                    <span class="author-name">${escapeHtml(author.name)}</span>
                    <span class="author-count">${author.count} award${author.count > 1 ? 's' : ''}</span>
                    <span class="author-toggle" id="${authorId}-toggle">+</span>
                </div>
                <ul class="author-papers collapsed" id="${authorId}-papers">
                    ${papersHtml}
                </ul>
            </div>
        `;
    });
    html += '</div>';

    // Add show more/less button if needed
    if (authorList.length > INITIAL_LIMIT) {
        html += `
            <div class="text-center mt-3">
                <button class="btn btn-outline-primary" id="toggle-authors-btn" onclick="toggleAuthorsList()">
                    Show all ${authorList.length} authors
                </button>
            </div>
        `;
    }

    container.innerHTML = html;
}

// Calculate first author statistics and render ranking
function renderFirstAuthorsRanking(papers) {
    const container = document.getElementById('first-authors-container');

    // Build first author -> papers mapping (only first author counts)
    const authorPapers = {};
    papers.forEach(paper => {
        if (!paper.authors || !Array.isArray(paper.authors) || paper.authors.length === 0) return;
        const firstAuthor = paper.authors[0];
        const name = firstAuthor.name;
        if (!name) return;
        if (!authorPapers[name]) {
            authorPapers[name] = [];
        }
        authorPapers[name].push(paper);
    });

    // Extract surname (last word) from full name
    const getSurname = (name) => {
        const parts = name.trim().split(/\s+/);
        return parts[parts.length - 1];
    };

    // Convert to array and sort by paper count, then alphabetically by surname
    const authorList = Object.entries(authorPapers)
        .map(([name, papers]) => ({ name, papers, count: papers.length }))
        .sort((a, b) => {
            if (b.count !== a.count) {
                return b.count - a.count; // Higher count first
            }
            return getSurname(a.name).localeCompare(getSurname(b.name)); // Alphabetical by surname
        });

    if (authorList.length === 0) {
        container.innerHTML = '<p class="text-muted">No authors found.</p>';
        return;
    }

    // Calculate ranks (with ties - dense ranking: 1, 1, 2, 2, 3...)
    let previousCount = null;
    let currentRank = 0;
    authorList.forEach((author) => {
        if (author.count !== previousCount) {
            currentRank++;
        }
        author.rank = currentRank;
        previousCount = author.count;
    });

    // Build HTML with limit
    const INITIAL_LIMIT = 25;
    const showAll = authorList.length <= INITIAL_LIMIT;

    let html = '<div class="authors-list">';
    authorList.forEach((author, index) => {
        const authorId = `first-author-${index}`;
        const isHidden = !showAll && index >= INITIAL_LIMIT;
        const papersHtml = author.papers
            .sort((a, b) => b.year - a.year)
            .map(p => {
                const titleHtml = p.url
                    ? `<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.title)}</a>`
                    : escapeHtml(p.title);
                return `<li class="author-paper-item">${titleHtml} <span class="text-muted">(${escapeHtml(p.venue)} ${p.year})</span></li>`;
            })
            .join('');

        html += `
            <div class="author-entry${isHidden ? ' first-author-hidden' : ''}" ${isHidden ? 'style="display:none;"' : ''}>
                <div class="author-header" onclick="toggleAuthorPapers('${authorId}')">
                    <span class="author-rank">#${author.rank}</span>
                    <span class="author-name">${escapeHtml(author.name)}</span>
                    <span class="author-count">${author.count} award${author.count > 1 ? 's' : ''}</span>
                    <span class="author-toggle" id="${authorId}-toggle">+</span>
                </div>
                <ul class="author-papers collapsed" id="${authorId}-papers">
                    ${papersHtml}
                </ul>
            </div>
        `;
    });
    html += '</div>';

    // Add show more/less button if needed
    if (authorList.length > INITIAL_LIMIT) {
        html += `
            <div class="text-center mt-3">
                <button class="btn btn-outline-primary" id="toggle-first-authors-btn" onclick="toggleFirstAuthorsList()">
                    Show all ${authorList.length} authors
                </button>
            </div>
        `;
    }

    container.innerHTML = html;
}

// Toggle first authors list visibility
let firstAuthorsExpanded = false;
function toggleFirstAuthorsList() {
    const hiddenAuthors = document.querySelectorAll('.author-entry.first-author-hidden');
    const btn = document.getElementById('toggle-first-authors-btn');

    firstAuthorsExpanded = !firstAuthorsExpanded;

    hiddenAuthors.forEach(el => {
        el.style.display = firstAuthorsExpanded ? '' : 'none';
    });

    if (firstAuthorsExpanded) {
        btn.textContent = 'Show less';
    } else {
        btn.textContent = `Show all ${hiddenAuthors.length + 25} authors`;
    }
}

// Toggle author papers visibility
function toggleAuthorPapers(authorId) {
    const papersEl = document.getElementById(`${authorId}-papers`);
    const toggleEl = document.getElementById(`${authorId}-toggle`);

    if (papersEl.classList.contains('collapsed')) {
        papersEl.classList.remove('collapsed');
        toggleEl.textContent = '−';
    } else {
        papersEl.classList.add('collapsed');
        toggleEl.textContent = '+';
    }
}

// Toggle full authors list visibility
let authorsExpanded = false;
function toggleAuthorsList() {
    const hiddenAuthors = document.querySelectorAll('.author-entry.author-hidden');
    const btn = document.getElementById('toggle-authors-btn');

    authorsExpanded = !authorsExpanded;

    hiddenAuthors.forEach(el => {
        el.style.display = authorsExpanded ? '' : 'none';
    });

    if (authorsExpanded) {
        btn.textContent = 'Show less';
    } else {
        btn.textContent = `Show all ${hiddenAuthors.length + 25} authors`;
    }
}

// Handle tab URL hash
function initTabFromHash() {
    const hash = window.location.hash;
    if (hash) {
        const tabId = hash.replace('#', '') + '-tab';
        const tabEl = document.getElementById(tabId);
        if (tabEl) {
            const tab = new bootstrap.Tab(tabEl);
            tab.show();
        }
    }
}

// Update URL hash when tab changes
function setupTabHashSync() {
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', (event) => {
            const paneId = event.target.getAttribute('data-bs-target').replace('#', '').replace('-pane', '');
            history.replaceState(null, null, '#' + paneId);
        });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', () => {
        initTabFromHash();
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPapers();
    setupTabHashSync();
    initTabFromHash();
});

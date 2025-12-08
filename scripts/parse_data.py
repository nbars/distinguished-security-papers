#!/usr/bin/env python3
"""
Parse best paper awards data from prncoprs/best-papers-in-computer-security
and output a structured JSON file.

No external dependencies required.
"""

import json
import re
import urllib.request
from pathlib import Path


def fetch_readme():
    """Fetch README.md from the source repository."""
    url = "https://raw.githubusercontent.com/prncoprs/best-papers-in-computer-security/main/README.md"
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')


def parse_papers(content):
    """Parse papers from markdown table content."""
    papers = []

    # Define venue sections with their patterns
    venue_sections = [
        ("IEEE S&P", r'<a id="ieee-sp"></a>\s*## IEEE S&P.*?(?=<a id="acm-ccs"|$)'),
        ("ACM CCS", r'<a id="acm-ccs"></a>\s*## ACM CCS.*?(?=<a id="usenix-security"|$)'),
        ("USENIX Security", r'<a id="usenix-security"></a>\s*## USENIX Security.*?(?=<a id="ndss"|$)'),
        ("NDSS", r'<a id="ndss"></a>\s*## NDSS.*?(?=$)'),
    ]

    for venue_name, pattern in venue_sections:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if not match:
            print(f"Warning: Could not find section for {venue_name}")
            continue

        section = match.group(0)
        venue_papers = parse_venue_table(section, venue_name)
        papers.extend(venue_papers)
        print(f"  {venue_name}: found {len(venue_papers)} papers")

    return papers


def parse_venue_table(section, venue_name):
    """Parse papers from a venue's markdown table."""
    papers = []

    # Find table rows (lines starting with |)
    lines = section.split('\n')

    for line in lines:
        line = line.strip()

        # Skip non-table lines, headers, and separators
        if not line.startswith('|'):
            continue
        if 'Year' in line and 'Paper' in line:
            continue
        if ':-' in line:
            continue

        # Parse table row: | Year | Paper content |
        parts = line.split('|')
        if len(parts) < 3:
            continue

        year_str = parts[1].strip()
        paper_content = parts[2].strip()

        # Extract year
        year_match = re.match(r'(\d{4})', year_str)
        if not year_match:
            continue
        year = int(year_match.group(1))

        # Parse papers from the cell (separated by <br>)
        paper_entries = parse_paper_cell(paper_content, year, venue_name)
        papers.extend(paper_entries)

    return papers


def parse_paper_cell(cell_content, year, venue_name):
    """Parse individual papers from a table cell."""
    papers = []

    # Determine award type
    if venue_name in ["NDSS", "USENIX Security"]:
        award = "Distinguished Paper"
    else:
        award = "Best Paper"

    # Split by <br>
    parts = re.split(r'<br>\s*', cell_content)

    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if not part:
            i += 1
            continue

        title = None
        url = ""
        authors = ""

        # Pattern 1: [**Title**](url) - markdown link with bold
        match = re.match(r'\[\*\*(.+?)\*\*\]\(([^)]+)\)', part)
        if match:
            title = match.group(1).strip()
            url = match.group(2).strip()
        else:
            # Pattern 2: [Title](url) - markdown link without bold
            match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', part)
            if match:
                title = match.group(1).strip('*')
                url = match.group(2).strip()
            else:
                # Pattern 3: **Title** - bold without link
                match = re.match(r'\*\*(.+?)\*\*', part)
                if match:
                    title = match.group(1).strip()

        if title:
            # Look ahead for authors in next part
            if i + 1 < len(parts):
                next_part = parts[i + 1].strip()
                # Check if next part is authors (not a new title)
                is_title = (
                    re.match(r'\[\*\*', next_part) or
                    re.match(r'\[', next_part) or
                    re.match(r'\*\*', next_part)
                )
                if not is_title and next_part:
                    authors = next_part
                    i += 1

            papers.append({
                "title": title,
                "authors": authors,
                "venue": venue_name,
                "year": year,
                "award": award,
                "url": url if url and not url.startswith('#') else ""
            })

        i += 1

    return papers


def main():
    print("Fetching README from source repository...")
    content = fetch_readme()

    print("Parsing paper entries...")
    papers = parse_papers(content)

    if not papers:
        print("Error: No papers found!")
        return

    # Sort by year (descending) then by venue then by title
    papers.sort(key=lambda p: (-p['year'], p['venue'], p['title']))

    # Output path
    output_path = Path(__file__).parent.parent / "data" / "papers.json"

    # Write JSON
    output = {
        "description": "Best Papers in Systems Security - Award-winning papers from top security conferences",
        "source": "https://github.com/prncoprs/best-papers-in-computer-security",
        "venues": ["IEEE S&P", "ACM CCS", "USENIX Security", "NDSS"],
        "papers": papers
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(papers)} papers to {output_path}")

    # Print summary
    venues = {}
    years = set()
    for p in papers:
        venues[p['venue']] = venues.get(p['venue'], 0) + 1
        years.add(p['year'])

    print("\nSummary:")
    for venue, count in sorted(venues.items()):
        print(f"  {venue}: {count} papers")
    print(f"  Years: {min(years)}-{max(years)}")


if __name__ == "__main__":
    main()

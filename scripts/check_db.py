#!/usr/bin/env python3
"""
Check the papers.json database for issues:
- Missing years (gaps in coverage)
- Potential duplicate entries using fuzzy matching
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher


def load_papers():
    """Load papers from JSON file."""
    json_path = Path(__file__).parent.parent / "data" / "papers.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['papers']


def normalize_title(title):
    """Normalize title for comparison."""
    # Convert to lowercase
    t = title.lower()
    # Remove punctuation and extra whitespace
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def fuzzy_similarity(s1, s2):
    """Calculate fuzzy similarity between two strings."""
    return SequenceMatcher(None, s1, s2).ratio()


def check_missing_years(papers):
    """Check for missing years in the data."""
    print("\n" + "=" * 60)
    print("CHECKING FOR MISSING YEARS")
    print("=" * 60)

    venues = {}
    for p in papers:
        venue = p['venue']
        year = p['year']
        if venue not in venues:
            venues[venue] = set()
        venues[venue].add(year)

    issues_found = False
    for venue, years in sorted(venues.items()):
        min_year = min(years)
        max_year = max(years)
        expected = set(range(min_year, max_year + 1))
        missing = expected - years

        print(f"\n{venue}:")
        print(f"  Coverage: {min_year} - {max_year}")
        print(f"  Years with data: {sorted(years)}")

        if missing:
            issues_found = True
            print(f"  MISSING YEARS: {sorted(missing)}")
        else:
            print(f"  No gaps found")

    return issues_found


def check_duplicates(papers, threshold=0.85):
    """Check for potential duplicate entries using fuzzy matching."""
    print("\n" + "=" * 60)
    print(f"CHECKING FOR DUPLICATES (threshold: {threshold})")
    print("=" * 60)

    # Group papers by year and venue for more efficient comparison
    grouped = {}
    for i, p in enumerate(papers):
        key = (p['year'], p['venue'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append((i, p))

    duplicates = []

    # Check within same year and venue
    for (year, venue), group in grouped.items():
        for i, (idx1, p1) in enumerate(group):
            for idx2, p2 in group[i + 1:]:
                t1 = normalize_title(p1['title'])
                t2 = normalize_title(p2['title'])
                similarity = fuzzy_similarity(t1, t2)

                if similarity >= threshold:
                    duplicates.append({
                        'similarity': similarity,
                        'paper1': p1,
                        'paper2': p2,
                        'idx1': idx1,
                        'idx2': idx2
                    })

    # Also check across years (same venue) for very high similarity
    for venue in set(p['venue'] for p in papers):
        venue_papers = [(i, p) for i, p in enumerate(papers) if p['venue'] == venue]
        for i, (idx1, p1) in enumerate(venue_papers):
            for idx2, p2 in venue_papers[i + 1:]:
                if p1['year'] == p2['year']:
                    continue  # Already checked above

                t1 = normalize_title(p1['title'])
                t2 = normalize_title(p2['title'])
                similarity = fuzzy_similarity(t1, t2)

                # Higher threshold for cross-year duplicates
                if similarity >= 0.95:
                    duplicates.append({
                        'similarity': similarity,
                        'paper1': p1,
                        'paper2': p2,
                        'idx1': idx1,
                        'idx2': idx2
                    })

    # Sort by similarity descending
    duplicates.sort(key=lambda x: -x['similarity'])

    if duplicates:
        print(f"\nFound {len(duplicates)} potential duplicate(s):\n")
        for dup in duplicates:
            print(f"Similarity: {dup['similarity']:.2%}")
            print(f"  Paper 1 [{dup['idx1']}]: {dup['paper1']['title'][:60]}...")
            print(f"           ({dup['paper1']['venue']} {dup['paper1']['year']})")
            print(f"  Paper 2 [{dup['idx2']}]: {dup['paper2']['title'][:60]}...")
            print(f"           ({dup['paper2']['venue']} {dup['paper2']['year']})")
            print()
        return True
    else:
        print("\nNo potential duplicates found.")
        return False


def check_data_quality(papers):
    """Check for data quality issues."""
    print("\n" + "=" * 60)
    print("CHECKING DATA QUALITY")
    print("=" * 60)

    issues = []

    for i, p in enumerate(papers):
        # Check for missing title
        if not p.get('title') or len(p['title'].strip()) < 5:
            issues.append(f"[{i}] Missing or very short title: {p.get('title', 'N/A')}")

        # Check for missing authors (now an array)
        authors = p.get('authors', [])
        if not authors or not isinstance(authors, list) or len(authors) == 0:
            issues.append(f"[{i}] Missing authors: {p['title'][:50]}...")

        # Check for missing URL (warning only)
        if not p.get('url'):
            # Don't report as issue, just info
            pass

        # Check for suspicious year
        if p.get('year') and (p['year'] < 2000 or p['year'] > 2030):
            issues.append(f"[{i}] Suspicious year {p['year']}: {p['title'][:50]}...")

    if issues:
        print(f"\nFound {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  - {issue}")
        return True
    else:
        print("\nNo data quality issues found.")
        return False


def print_summary(papers):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    print(f"\nTotal papers: {len(papers)}")

    # By venue
    venues = {}
    for p in papers:
        venues[p['venue']] = venues.get(p['venue'], 0) + 1
    print("\nBy venue:")
    for venue, count in sorted(venues.items()):
        print(f"  {venue}: {count}")

    # By year
    years = {}
    for p in papers:
        years[p['year']] = years.get(p['year'], 0) + 1
    print("\nBy year:")
    for year in sorted(years.keys(), reverse=True):
        print(f"  {year}: {years[year]}")

    # Papers with URLs
    with_url = sum(1 for p in papers if p.get('url'))
    print(f"\nPapers with URLs: {with_url}/{len(papers)} ({100*with_url/len(papers):.1f}%)")

    # Top authors
    author_counts = {}
    for p in papers:
        authors = p.get('authors', [])
        if isinstance(authors, list):
            for a in authors:
                name = a.get('name', '') if isinstance(a, dict) else str(a)
                if name:
                    author_counts[name] = author_counts.get(name, 0) + 1

    top_authors = sorted(author_counts.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 authors:")
    for i, (name, count) in enumerate(top_authors, 1):
        print(f"  {i}. {name}: {count} papers")


def main():
    print("Best Papers Database Checker")
    print("=" * 60)

    papers = load_papers()
    print(f"Loaded {len(papers)} papers from database.")

    # Run checks
    has_missing_years = check_missing_years(papers)
    has_duplicates = check_duplicates(papers)
    has_quality_issues = check_data_quality(papers)

    # Print summary
    print_summary(papers)

    # Final status
    print("\n" + "=" * 60)
    print("CHECK RESULTS")
    print("=" * 60)
    if has_missing_years or has_duplicates or has_quality_issues:
        print("\nIssues found! Review the above output.")
        return 1
    else:
        print("\nAll checks passed!")
        return 0


if __name__ == "__main__":
    exit(main())

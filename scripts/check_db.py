#!/usr/bin/env python3
"""
Check the papers.json database for issues:
- Missing years (gaps in coverage)
- Potential duplicate entries using fuzzy matching
- Verify papers against DBLP
"""

import json
import re
import urllib.request
import urllib.parse
import time
import hashlib
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime, timedelta


# Cache configuration
CACHE_DIR = Path(__file__).parent / '.cache'
CACHE_EXPIRY_HOURS = 24 * 7  # Cache expires after 7 days


def get_cache_path(url):
    """Get cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


def load_from_cache(url):
    """Load cached response for a URL if it exists and isn't expired."""
    cache_path = get_cache_path(url)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached = json.load(f)

        # Check expiry
        cached_time = datetime.fromisoformat(cached['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=CACHE_EXPIRY_HOURS):
            return None

        return cached['data']
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def save_to_cache(url, data):
    """Save response data to cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = get_cache_path(url)

    cached = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'data': data
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cached, f, ensure_ascii=False)


def clear_cache():
    """Clear all cached responses."""
    if CACHE_DIR.exists():
        count = 0
        for cache_file in CACHE_DIR.glob('*.json'):
            cache_file.unlink()
            count += 1
        return count
    return 0


def is_dblp_cached(title, max_results=5):
    """Check if a DBLP query is cached."""
    base_url = "https://dblp.org/search/publ/api"
    params = {'q': title, 'format': 'json', 'h': max_results}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return load_from_cache(url) is not None


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


def strip_dblp_disambiguation(name):
    """Strip DBLP disambiguation numbers from author names (e.g., 'Wenbo Guo 0002' -> 'Wenbo Guo')."""
    return re.sub(r'\s+\d{4}$', '', name)


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


def query_dblp(title, max_results=5, use_cache=True):
    """Query DBLP API for a paper title."""
    base_url = "https://dblp.org/search/publ/api"
    params = {
        'q': title,
        'format': 'json',
        'h': max_results
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Check cache first
    if use_cache:
        cached = load_from_cache(url)
        if cached is not None:
            return cached

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'BestPapersChecker/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            result = data.get('result', {}).get('hits', {}).get('hit', [])

            # Cache the result
            if use_cache:
                save_to_cache(url, result)

            return result
    except Exception as e:
        return None


def extract_dblp_authors(info):
    """Extract author names from DBLP result."""
    authors = info.get('authors', {}).get('author', [])
    if isinstance(authors, dict):
        authors = [authors]
    return [a.get('text', '') for a in authors if isinstance(a, dict)]


def extract_dblp_ee(info):
    """Extract electronic edition URL from DBLP result."""
    ee = info.get('ee', '')
    if isinstance(ee, list):
        # Prefer DOI or direct PDF links
        for url in ee:
            if 'doi.org' in url or url.endswith('.pdf'):
                return url
        return ee[0] if ee else ''
    return ee


def query_arxiv(title, max_results=3, use_cache=True):
    """Query arXiv API for a paper title."""
    import xml.etree.ElementTree as ET

    base_url = "http://export.arxiv.org/api/query"
    # Clean title for search
    clean_title = re.sub(r'[^\w\s]', ' ', title)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    params = {
        'search_query': f'ti:"{clean_title}"',
        'start': 0,
        'max_results': max_results
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Check cache first
    if use_cache:
        cached = load_from_cache(url)
        if cached is not None:
            return cached

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'BestPapersChecker/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            root = ET.fromstring(data)

            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)

            results = []
            for entry in entries:
                entry_title = entry.find('atom:title', ns)
                entry_id = entry.find('atom:id', ns)
                if entry_title is not None and entry_id is not None:
                    results.append({
                        'title': entry_title.text.strip().replace('\n', ' '),
                        'url': entry_id.text.strip()
                    })

            # Cache the result
            if use_cache:
                save_to_cache(url, results)

            return results
    except Exception as e:
        return None


def verify_against_dblp(papers, sample_size=None, delay=0.5, log_file=None, use_cache=True):
    """Verify papers against DBLP database."""
    print("\n" + "=" * 60)
    print("VERIFYING AGAINST DBLP")
    print("=" * 60)

    if use_cache:
        print(f"(Using cache from {CACHE_DIR})")

    papers_to_check = papers
    if sample_size and sample_size < len(papers):
        import random
        papers_to_check = random.sample(papers, sample_size)
        print(f"\nChecking {sample_size} random papers (use --dblp-all for full check)")
    else:
        print(f"\nChecking all {len(papers)} papers against DBLP...")

    issues = []
    verified = 0
    not_found = 0
    cache_hits = 0

    for i, paper in enumerate(papers_to_check):
        title = paper['title']
        print(f"  [{i+1}/{len(papers_to_check)}] {title[:50]}...", end=" ", flush=True)

        # Check if cached to avoid delay
        was_cached = use_cache and is_dblp_cached(title)
        if was_cached:
            cache_hits += 1

        results = query_dblp(title, use_cache=use_cache)

        if results is None:
            print("ERROR (API)")
            issues.append({
                'paper': paper,
                'issue': 'DBLP API error',
                'dblp_data': None
            })
            if not was_cached:
                time.sleep(delay)
            continue

        if not results:
            print("NOT FOUND")
            not_found += 1
            issues.append({
                'paper': paper,
                'issue': 'Not found in DBLP',
                'dblp_data': None
            })
            if not was_cached:
                time.sleep(delay)
            continue

        # Find best match
        best_match = None
        best_similarity = 0

        for hit in results:
            info = hit.get('info', {})
            dblp_title = info.get('title', '').rstrip('.')

            similarity = fuzzy_similarity(
                normalize_title(title),
                normalize_title(dblp_title)
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = info

        dblp_authors = extract_dblp_authors(best_match) if best_match else []
        dblp_title = best_match.get('title', '').rstrip('.') if best_match else ''
        dblp_year = best_match.get('year', '') if best_match else ''
        dblp_venue = best_match.get('venue', '') if best_match else ''
        dblp_url = best_match.get('url', '') if best_match else ''
        dblp_ee = extract_dblp_ee(best_match) if best_match else ''

        if best_similarity < 0.8:
            print(f"LOW MATCH ({best_similarity:.0%})")
            issues.append({
                'paper': paper,
                'issue': f'Low title match ({best_similarity:.0%})',
                'dblp_data': {
                    'title': dblp_title,
                    'authors': dblp_authors,
                    'year': dblp_year,
                    'venue': dblp_venue,
                    'url': dblp_url,
                    'ee': dblp_ee
                }
            })
        else:
            # Check authors
            paper_authors = [a.get('name', '') for a in paper.get('authors', [])]

            # Normalize author names for comparison
            # Strip DBLP disambiguation numbers (e.g., "0002") before comparing
            dblp_names = set(normalize_title(strip_dblp_disambiguation(a)) for a in dblp_authors)
            paper_names = set(normalize_title(a) for a in paper_authors)

            author_overlap = len(dblp_names & paper_names) / max(len(dblp_names), len(paper_names), 1)

            has_issue = False

            if author_overlap < 0.5 and len(paper_authors) > 0:
                print(f"AUTHOR MISMATCH ({author_overlap:.0%})", end="")
                has_issue = True
                issues.append({
                    'paper': paper,
                    'issue': f'Author mismatch ({author_overlap:.0%} overlap)',
                    'dblp_data': {
                        'title': dblp_title,
                        'authors': dblp_authors,
                        'year': dblp_year,
                        'venue': dblp_venue,
                        'url': dblp_url,
                        'ee': dblp_ee
                    }
                })

            # Check for missing URL
            if not paper.get('url') and (dblp_ee or dblp_url):
                found_url = dblp_ee or dblp_url
                if has_issue:
                    print(f" + MISSING URL")
                else:
                    print(f"MISSING URL", end="")
                    has_issue = True

                # Check if we already added an issue for this paper
                existing_issue = None
                for iss in issues:
                    if iss['paper'] is paper:
                        existing_issue = iss
                        break

                if existing_issue:
                    existing_issue['issue'] += ' + Missing URL'
                    existing_issue['dblp_data']['ee'] = dblp_ee
                else:
                    issues.append({
                        'paper': paper,
                        'issue': 'Missing URL',
                        'dblp_data': {
                            'title': dblp_title,
                            'authors': dblp_authors,
                            'year': dblp_year,
                            'venue': dblp_venue,
                            'url': dblp_url,
                            'ee': dblp_ee
                        }
                    })

            if not has_issue:
                print("OK")
                verified += 1
            else:
                print()  # Newline after issue status

        # Only rate limit for non-cached requests
        if not was_cached:
            time.sleep(delay)

    # Report results
    print(f"\n\nDBLP Verification Results:")
    print(f"  Verified: {verified}/{len(papers_to_check)}")
    print(f"  Not found: {not_found}")
    print(f"  Issues: {len(issues) - not_found}")
    if use_cache:
        print(f"  Cache hits: {cache_hits}/{len(papers_to_check)}")

    if issues:
        print(f"\n\n" + "=" * 60)
        print("DETAILED ISSUES")
        print("=" * 60)

        for idx, issue in enumerate(issues, 1):
            p = issue['paper']
            dblp = issue['dblp_data']
            paper_authors = [a.get('name', '') for a in p.get('authors', [])]

            print(f"\n{'─' * 60}")
            print(f"Issue #{idx}: {issue['issue']}")
            print(f"{'─' * 60}")

            print(f"\n  DATABASE ENTRY (incorrect):")
            print(f"    Title:   {p['title']}")
            print(f"    Authors: {', '.join(paper_authors) if paper_authors else '(none)'}")
            print(f"    Venue:   {p['venue']} {p['year']}")
            print(f"    URL:     {p.get('url') or '(none)'}")

            if dblp:
                print(f"\n  DBLP DATA (correct):")
                print(f"    Title:   {dblp['title']}")
                print(f"    Authors: {', '.join(dblp['authors']) if dblp['authors'] else '(none)'}")
                print(f"    Year:    {dblp['year']}")
                print(f"    Venue:   {dblp['venue']}")
                print(f"    DBLP:    {dblp['url'] or '(none)'}")
                if dblp.get('ee'):
                    print(f"    Paper:   {dblp['ee']}")
            else:
                print(f"\n  DBLP DATA: Not available")

        print(f"\n{'─' * 60}")

    # Write log file if requested
    if log_file:
        from datetime import datetime
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"DBLP Verification Log\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"Papers checked: {len(papers_to_check)}\n")
            f.write(f"Verified: {verified}\n")
            f.write(f"Not found: {not_found}\n")
            f.write(f"Issues: {len(issues) - not_found}\n\n")

            if issues:
                f.write(f"{'=' * 60}\n")
                f.write(f"DETAILED ISSUES\n")
                f.write(f"{'=' * 60}\n\n")

                for idx, issue in enumerate(issues, 1):
                    p = issue['paper']
                    dblp = issue['dblp_data']
                    paper_authors = [a.get('name', '') for a in p.get('authors', [])]

                    f.write(f"{'─' * 60}\n")
                    f.write(f"Issue #{idx}: {issue['issue']}\n")
                    f.write(f"{'─' * 60}\n\n")

                    f.write(f"DATABASE ENTRY (incorrect):\n")
                    f.write(f"  Title:   {p['title']}\n")
                    f.write(f"  Authors: {', '.join(paper_authors) if paper_authors else '(none)'}\n")
                    f.write(f"  Venue:   {p['venue']} {p['year']}\n")
                    f.write(f"  URL:     {p.get('url') or '(none)'}\n\n")

                    if dblp:
                        f.write(f"DBLP DATA (correct):\n")
                        f.write(f"  Title:   {dblp['title']}\n")
                        f.write(f"  Authors: {', '.join(dblp['authors']) if dblp['authors'] else '(none)'}\n")
                        f.write(f"  Year:    {dblp['year']}\n")
                        f.write(f"  Venue:   {dblp['venue']}\n")
                        f.write(f"  DBLP:    {dblp['url'] or '(none)'}\n")
                        if dblp.get('ee'):
                            f.write(f"  Paper:   {dblp['ee']}\n")
                    else:
                        f.write(f"DBLP DATA: Not available\n")

                    f.write(f"\n")

            f.write(f"{'─' * 60}\n")
            f.write(f"End of log\n")

        print(f"\nLog written to: {log_file}")

    if issues:
        return True
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

    top_authors = sorted(author_counts.items(), key=lambda x: -x[1])[:25]
    print("\nTop 25 authors:")
    for i, (name, count) in enumerate(top_authors, 1):
        print(f"  {i}. {name}: {count} papers")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check the papers database for issues")
    parser.add_argument('--dblp', action='store_true', help='Verify papers against DBLP (sample of 10)')
    parser.add_argument('--dblp-all', action='store_true', help='Verify ALL papers against DBLP (slow)')
    parser.add_argument('--dblp-sample', type=int, metavar='N', help='Verify N random papers against DBLP')
    parser.add_argument('--log', type=str, metavar='FILE', help='Write DBLP verification results to log file')
    parser.add_argument('--no-cache', action='store_true', help='Disable request caching')
    parser.add_argument('--clear-cache', action='store_true', help='Clear the request cache and exit')
    args = parser.parse_args()

    # Handle cache clear
    if args.clear_cache:
        count = clear_cache()
        print(f"Cleared {count} cached responses from {CACHE_DIR}")
        return 0

    print("Distinguished Papers Database Checker")
    print("=" * 60)

    papers = load_papers()
    print(f"Loaded {len(papers)} papers from database.")

    # Run checks
    has_missing_years = check_missing_years(papers)
    has_duplicates = check_duplicates(papers)
    has_quality_issues = check_data_quality(papers)

    # DBLP verification (optional)
    has_dblp_issues = False
    log_file = args.log
    use_cache = not args.no_cache
    if args.dblp_all:
        has_dblp_issues = verify_against_dblp(papers, log_file=log_file, use_cache=use_cache)
    elif args.dblp_sample:
        has_dblp_issues = verify_against_dblp(papers, sample_size=args.dblp_sample, log_file=log_file, use_cache=use_cache)
    elif args.dblp:
        has_dblp_issues = verify_against_dblp(papers, sample_size=10, log_file=log_file, use_cache=use_cache)

    # Print summary
    print_summary(papers)

    # Final status
    print("\n" + "=" * 60)
    print("CHECK RESULTS")
    print("=" * 60)
    if has_missing_years or has_duplicates or has_quality_issues or has_dblp_issues:
        print("\nIssues found! Review the above output.")
        return 1
    else:
        print("\nAll checks passed!")
        return 0


if __name__ == "__main__":
    exit(main())

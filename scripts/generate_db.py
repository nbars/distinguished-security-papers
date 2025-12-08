#!/usr/bin/env python3
"""
Generate the papers database from multiple sources.
Authors are stored as a list of tuples: [{"name": "...", "institution": "..."}]
"""

import json
import re
import urllib.request
from pathlib import Path


def fetch_url(url):
    """Fetch content from URL."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')


def parse_author_string(author_str):
    """
    Parse an author string into list of {"name": ..., "institution": ...} objects.
    Handles formats like:
    - "Name (Institution), Name2 (Institution2)"
    - "Name (Institution); Name2 (Institution2)"
    - "Name (Institution) Name2 (Institution2)" (space-separated)
    - "Name, Institution; Name2, Institution2" (USENIX format)
    """
    authors = []

    if not author_str or not author_str.strip():
        return authors

    # Format 1: "Name (Institution)" patterns - check if this format is used
    pattern = r'([A-Z][a-zA-Z\-\'\.\s]+?)\s*\(([^)]+)\)'
    matches = re.findall(pattern, author_str)

    if matches:
        for name, institution in matches:
            name = name.strip()
            institution = institution.strip()
            name = re.sub(r'\s+', ' ', name).strip()

            if is_institution_name(name):
                continue

            # Split names containing " and "
            for split_name in split_and_names(name):
                if split_name and len(split_name) > 1 and not is_institution_name(split_name):
                    authors.append({
                        "name": split_name,
                        "institution": institution
                    })

        if authors:
            return authors

    # Format 2: "Name, Institution; Name2, Institution2" (USENIX/some venues)
    # Split by semicolon first
    if ';' in author_str:
        segments = author_str.split(';')
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            # Split by comma - first part is name, rest is institution
            if ',' in segment:
                parts = segment.split(',', 1)
                name = parts[0].strip()
                institution = parts[1].strip() if len(parts) > 1 else ""

                name = re.sub(r'\s+', ' ', name).strip()

                # Check if this looks like a valid author name
                if name and len(name) > 1 and not is_institution_name(name):
                    # Split names containing " and "
                    for split_name in split_and_names(name):
                        # Verify it looks like a person's name (contains at least two parts)
                        name_parts = split_name.split()
                        if len(name_parts) >= 2 and all(p[0].isupper() for p in name_parts if p):
                            authors.append({
                                "name": split_name,
                                "institution": institution
                            })

        if authors:
            return authors

    # Format 3: Simple comma-separated names without institutions
    parts = re.split(r',\s*', author_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        name = re.sub(r'\s+', ' ', part).strip()

        if name and len(name) > 1 and not is_institution_name(name):
            # Split names containing " and "
            for split_name in split_and_names(name):
                if split_name and len(split_name) > 1 and not is_institution_name(split_name):
                    authors.append({
                        "name": split_name,
                        "institution": ""
                    })

    return authors


def is_institution_name(name):
    """Check if a string looks like an institution name rather than a person's name."""
    institution_keywords = [
        'university', 'institute', 'college', 'school', 'lab', 'laboratory',
        'center', 'centre', 'research', 'corporation', 'inc', 'llc', 'ltd',
        'google', 'microsoft', 'amazon', 'facebook', 'meta', 'apple', 'ibm',
        'intel', 'nvidia', 'samsung', 'huawei', 'alibaba', 'tencent', 'baidu',
        'cispa', 'inria', 'epfl', 'eth', 'mit', 'kaist', 'rub', 'tu ',
        'deepmind', 'openai', 'brave', 'mozilla',
        'national', 'state', 'federal', 'dept', 'department',
    ]
    name_lower = name.lower()

    # Check for institution keywords
    for keyword in institution_keywords:
        if keyword in name_lower:
            return True

    # Check if it ends with common institution suffixes
    if re.search(r'\b(university|institute|lab|center|tech)\s*$', name_lower):
        return True

    return False


def split_and_names(name):
    """Split names that contain ' and ' into separate names."""
    # Check if name contains " and " (case insensitive)
    if re.search(r'\s+and\s+', name, re.IGNORECASE):
        parts = re.split(r'\s+and\s+', name, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]
    return [name]


def parse_github_readme():
    """Parse papers from the GitHub README."""
    print("Fetching GitHub README...")
    url = "https://raw.githubusercontent.com/prncoprs/best-papers-in-computer-security/main/README.md"
    content = fetch_url(url)

    papers = []

    venue_sections = [
        ("IEEE S&P", r'<a id="ieee-sp"></a>\s*## IEEE S&P.*?(?=<a id="acm-ccs"|$)'),
        ("ACM CCS", r'<a id="acm-ccs"></a>\s*## ACM CCS.*?(?=<a id="usenix-security"|$)'),
        ("USENIX Security", r'<a id="usenix-security"></a>\s*## USENIX Security.*?(?=<a id="ndss"|$)'),
        ("NDSS", r'<a id="ndss"></a>\s*## NDSS.*?(?=$)'),
    ]

    for venue_name, pattern in venue_sections:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if not match:
            continue

        section = match.group(0)
        venue_papers = parse_venue_table(section, venue_name)
        papers.extend(venue_papers)
        print(f"  {venue_name}: {len(venue_papers)} papers from GitHub")

    return papers


def parse_venue_table(section, venue_name):
    """Parse papers from a venue's markdown table."""
    papers = []
    lines = section.split('\n')

    for line in lines:
        line = line.strip()
        if not line.startswith('|') or 'Year' in line or ':-' in line:
            continue

        parts = line.split('|')
        if len(parts) < 3:
            continue

        year_str = parts[1].strip()
        paper_content = parts[2].strip()

        year_match = re.match(r'(\d{4})', year_str)
        if not year_match:
            continue
        year = int(year_match.group(1))

        # Determine award type
        award = "Distinguished Paper" if venue_name in ["NDSS", "USENIX Security"] else "Best Paper"

        # Parse papers from cell
        cell_papers = parse_paper_cell(paper_content, year, venue_name, award)
        papers.extend(cell_papers)

    return papers


def parse_paper_cell(cell_content, year, venue_name, award):
    """Parse individual papers from a table cell."""
    papers = []
    parts = re.split(r'<br>\s*', cell_content)

    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if not part:
            i += 1
            continue

        title = None
        url = ""
        authors_str = ""

        # Pattern 1: [**Title**](url) or [Title](url)
        match = re.match(r'\[\*?\*?([^\]]+?)\*?\*?\]\(([^)]+)\)', part)
        if match:
            title = match.group(1).strip('*')
            url = match.group(2).strip()
        else:
            # Pattern 2: **Title**
            match = re.match(r'\*\*(.+?)\*\*', part)
            if match:
                title = match.group(1).strip()

        if title:
            # Look for authors in next part
            if i + 1 < len(parts):
                next_part = parts[i + 1].strip()
                is_title = re.match(r'^\[\*?\*?|^\*\*', next_part)
                if not is_title and next_part:
                    authors_str = next_part
                    i += 1

            papers.append({
                "title": title,
                "authors": parse_author_string(authors_str),
                "venue": venue_name,
                "year": year,
                "award": award,
                "url": url if url and not url.startswith('#') else ""
            })

        i += 1

    return papers


def parse_usenix_best_papers():
    """Parse USENIX Security best papers page."""
    print("Fetching USENIX Security best papers...")

    # These are manually extracted from the USENIX page we fetched earlier
    usenix_2025 = [
        {"title": "How Transparent is Usable Privacy and Security Research?", "authors": "Jan H. Klemmer, Juliane Schmüser, Fabian Fischer, Jacques Suray, Jan-Ulrich Holtgrave, Simon Lenau, Byron M. Lowens, Florian Schaub, Sascha Fahl", "year": 2025},
        {"title": "Catch-22: Uncovering Compromised Hosts using SSH Public Keys", "authors": "Cristian Munteanu, Georgios Smaragdakis, Anja Feldmann, Tobias Fiebig", "year": 2025},
        {"title": "We Have a Package for You!", "authors": "Joseph Spracklen, Raveen Wijewickrama, A H M Nazmus Sakib, Anindya Maiti, Bimal Viswanath", "year": 2025},
        {"title": "Branch Privilege Injection", "authors": "Sandro Rüegge, Johannes Wikner, Kaveh Razavi", "year": 2025},
        {"title": "Fuzzing the PHP Interpreter via Dataflow Fusion", "authors": "Yuancheng Jiang, Chuqi Zhang, Bonan Ruan, Jiahao Liu, Manuel Rigger, Roland H. C. Yap, Zhenkai Liang", "year": 2025},
        {"title": "Confusing Value with Enumeration", "authors": "Moritz Schloegel, Daniel Klischies, Simon Koch, David Klein, Lukas Gerlach, Malte Wessels, Leon Trampert, Martin Johns, Mathy Vanhoef, Michael Schwarz, Thorsten Holz, Jo Van Bulck", "year": 2025},
        {"title": "Characterizing and Detecting Propaganda-Spreading Accounts on Telegram", "authors": "Klim Kireev, Yevhen Mykhno, Carmela Troncoso, Rebekah Overdorf", "year": 2025},
        {"title": "My ZIP isn't your ZIP", "authors": "Yufan You, Jianjun Chen, Qi Wang, Haixin Duan", "year": 2025},
    ]

    papers = []
    for p in usenix_2025:
        papers.append({
            "title": p["title"],
            "authors": parse_author_string(p["authors"]),
            "venue": "USENIX Security",
            "year": p["year"],
            "award": "Distinguished Paper",
            "url": ""
        })

    print(f"  USENIX Security 2025: {len(papers)} papers")
    return papers


def parse_ndss_2025():
    """Parse NDSS 2025 distinguished papers."""
    print("Fetching NDSS 2025 papers...")

    ndss_2025 = [
        {"title": "ReThink: Reveal the Threat of Electromagnetic Interference on Power Inverters", "authors": "Fengchen Yang (Zhejiang University), Zihao Dan (Zhejiang University), Kaikai Pan (Zhejiang University), Chen Yan (Zhejiang University), Xiaoyu Ji (Zhejiang University), Wenyuan Xu (Zhejiang University)"},
        {"title": "An Empirical Study on Fingerprint API Misuse with Lifecycle Analysis in Real-world Android Apps", "authors": "Xin Zhang (Fudan University), Xiaohan Zhang (Fudan University), Zhichen Liu (Fudan University), Bo Zhao (Fudan University), Zhemin Yang (Fudan University), Min Yang (Fudan University)"},
        {"title": "SafeSplit: A Novel Defense Against Client-Side Backdoor Attacks in Split Learning", "authors": "Phillip Rieger (Technical University of Darmstadt), Alessandro Pegoraro (Technical University of Darmstadt), Kavita Kumari (Technical University of Darmstadt), Tigist Abera (Technical University of Darmstadt), Jonathan Knauer (Technical University of Darmstadt), Ahmad-Reza Sadeghi (Technical University of Darmstadt)"},
        {"title": "Provably Unlearnable Data Examples", "authors": "Derui Wang (CSIRO's Data61), Minhui Xue (CSIRO's Data61), Bo Li (University of Chicago), Seyit Camtepe (CSIRO's Data61), Liming Zhu (CSIRO's Data61)"},
        {"title": "DUMPLING: Fine-grained Differential JavaScript Engine Fuzzing", "authors": "Liam Wachter (EPFL), Julian Gremminger (EPFL), Christian Wressnegger (Karlsruhe Institute of Technology), Mathias Payer (EPFL), Flavio Toffalini (EPFL)"},
        {"title": "type++: Prohibiting Type Confusion with Inline Type Information", "authors": "Nicolas Badoux (EPFL), Flavio Toffalini (Ruhr-Universität Bochum), Yuseok Jeon (UNIST), Mathias Payer (EPFL)"},
        {"title": "Rethinking Trust in Forge-Based Git Security", "authors": "Aditya Sirish A Yelgundhalli (NYU), Patrick Zielinski (NYU), Reza Curtmola (NJIT), Justin Cappos (NYU)"},
        {"title": "Blindfold: Confidential Memory Management by Untrusted Operating System", "authors": "Caihua Li (Yale University), Seung-seob Lee (Yale University), Ling Zhong (Yale University)"},
        {"title": "PropertyGPT: LLM-driven Formal Verification of Smart Contracts", "authors": "Ye Liu (SMU), Yue Xue (MetaTrust Labs), Daoyuan Wu (HKUST)"},
        {"title": "DiStefano: Decentralized Infrastructure for Sharing Trusted Encrypted Facts", "authors": "Sofía Celi (Brave Software), Alex Davidson (NOVA LINCS), Hamed Haddadi (Imperial College London), Gonçalo Pestana (Hashmatter), Joe Rowell (University of London)"},
        {"title": "ReDAN: An Empirical Study on Remote DoS Attacks against NAT Networks", "authors": "Xuewei Feng (Tsinghua University), Yuxiang Yang (Tsinghua University), Qi Li (Tsinghua University)"},
        {"title": "VoiceRadar: Voice Deepfake Detection using Micro-Frequency and Compositional Analysis", "authors": "Kavita Kumari (TU Darmstadt), Maryam Abbasihafshejani (UT San Antonio)"},
    ]

    papers = []
    for p in ndss_2025:
        papers.append({
            "title": p["title"],
            "authors": parse_author_string(p["authors"]),
            "venue": "NDSS",
            "year": 2025,
            "award": "Distinguished Paper",
            "url": ""
        })

    print(f"  NDSS 2025: {len(papers)} papers")
    return papers


def parse_ieee_sp_2025():
    """Parse IEEE S&P 2025 distinguished papers."""
    print("Fetching IEEE S&P 2025 papers...")

    sp_2025 = [
        {"title": "COBBL: Dynamic Constraint Generation for SNARKs", "authors": "Kunming Jiang (Carnegie Mellon University), Fraser Brown (Carnegie Mellon University), Riad Wahby (Carnegie Mellon University)"},
        {"title": "Transport Layer Obscurity: Circumventing SNI Censorship on the TLS Layer", "authors": "Niklas Niere (Paderborn University), Felix Lange (Paderborn University), Juraj Somorovsky (Paderborn University), Robert Merget (Technology Innovation Institute)"},
        {"title": "Follow My Flow: Unveiling Client-Side Prototype Pollution Gadgets from One Million Real-World Websites", "authors": "Zifeng Kang (Johns Hopkins University), Muxi Lyu (Johns Hopkins University), Zhengyu Liu (Johns Hopkins University), Jianjia Yu (Johns Hopkins University), Runqi Fan (Zhejiang University), Song Li (Zhejiang University), Yinzhi Cao (Johns Hopkins University)"},
        {"title": "CipherSteal: Stealing Input Data from TEE-Shielded Neural Networks with Ciphertext Side Channels", "authors": "Yuanyuan Yuan (HKUST), Zhibo Liu (HKUST), Sen Deng (HKUST), Yanzuo Chen (HKUST), Shuai Wang (HKUST), Yinqian Zhang (SUSTech), Zhendong Su (ETH Zurich)"},
        {"title": "Characterizing Robocalls with Multiple Vantage Points", "authors": "Sathvik Prasad (North Carolina State University), Aleksandr Nahapetyan (North Carolina State University), Bradley Reaves (North Carolina State University)"},
        {"title": "Verifiable Boosted Tree Ensembles", "authors": "Stefano Calzavara (Università Ca' Foscari Venezia), Lorenzo Cazzaro (Università Ca' Foscari Venezia), Claudio Lucchese (Università Ca' Foscari Venezia), Giulio Ermanno Pibiri (Università Ca' Foscari Venezia)"},
        {"title": "Breaking the Barrier: Post-Barrier Spectre Attacks", "authors": "Johannes Wikner (ETH Zurich), Kaveh Razavi (ETH Zurich)"},
        {"title": "Unveiling Security Vulnerabilities in Git Large File Storage Protocol", "authors": "Yuan Chen (Zhejiang University), Qinying Wang (Zhejiang University), Yong Yang (Zhejiang University), Yuanchao Chen (NUDT), Yuwei Li (NUDT), Shouling Ji (Zhejiang University)"},
        {"title": "The Inadequacy of Similarity-based Privacy Metrics", "authors": "Georgi Ganev (UCL), Emiliano De Cristofaro (UC Riverside)"},
        {"title": "Empc: Effective Path Prioritization for Symbolic Execution with Path Cover", "authors": "Shuangjie Yao (HKUST), Dongdong She (HKUST)"},
        {"title": "SLAP: Data Speculation Attacks via Load Address Prediction on Apple Silicon", "authors": "Jason Kim (Georgia Institute of Technology), Daniel Genkin (Georgia Institute of Technology), Yuval Yarom (Ruhr University Bochum)"},
        {"title": "Detecting Taint-Style Vulnerabilities in Microservice-Structured Web Applications", "authors": "Fengyu Liu (Fudan University), Yuan Zhang (Fudan University), Tian Chen (Fudan University), Youkun Shi (Fudan University), Guangliang Yang (Fudan University), Zihan Lin (Fudan University), Min Yang (Fudan University), Junyao He (Alibaba Group), Qi Li (Alibaba Group)"},
        {"title": "DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks", "authors": "Yupei Liu (Penn State), Yuqi Jia (Duke University), Neil Zhenqiang Gong (Duke University), Jinyuan Jia (Penn State), Dawn Song (UC Berkeley)"},
    ]

    papers = []
    for p in sp_2025:
        papers.append({
            "title": p["title"],
            "authors": parse_author_string(p["authors"]),
            "venue": "IEEE S&P",
            "year": 2025,
            "award": "Best Paper",
            "url": ""
        })

    print(f"  IEEE S&P 2025: {len(papers)} papers")
    return papers


def normalize_title(title):
    """Normalize title for duplicate detection."""
    t = title.lower()
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def deduplicate_papers(papers):
    """Remove duplicate papers based on title similarity."""
    seen_titles = {}
    unique_papers = []

    for paper in papers:
        norm_title = normalize_title(paper['title'])

        # Check for exact match
        if norm_title in seen_titles:
            # Keep the one with more data (URL, authors)
            existing = seen_titles[norm_title]
            if not existing.get('url') and paper.get('url'):
                unique_papers.remove(existing)
                unique_papers.append(paper)
                seen_titles[norm_title] = paper
            continue

        seen_titles[norm_title] = paper
        unique_papers.append(paper)

    return unique_papers


def main():
    print("=" * 60)
    print("Generating Best Papers Database")
    print("=" * 60)

    all_papers = []

    # 1. Parse GitHub README (base data)
    github_papers = parse_github_readme()
    all_papers.extend(github_papers)

    # 2. Add USENIX Security 2025
    usenix_papers = parse_usenix_best_papers()
    all_papers.extend(usenix_papers)

    # 3. Add NDSS 2025
    ndss_papers = parse_ndss_2025()
    all_papers.extend(ndss_papers)

    # 4. Add IEEE S&P 2025
    sp_papers = parse_ieee_sp_2025()
    all_papers.extend(sp_papers)

    # Deduplicate
    print("\nDeduplicating...")
    all_papers = deduplicate_papers(all_papers)

    # Sort by year (descending), venue, title
    all_papers.sort(key=lambda p: (-p['year'], p['venue'], p['title']))

    # Output
    output_path = Path(__file__).parent.parent / "data" / "papers.json"

    output = {
        "description": "Best Papers in Systems Security - Award-winning papers from top security conferences",
        "source": "https://github.com/prncoprs/best-papers-in-computer-security",
        "venues": ["IEEE S&P", "ACM CCS", "USENIX Security", "NDSS"],
        "papers": all_papers
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total papers: {len(all_papers)}")

    venues = {}
    years = set()
    for p in all_papers:
        venues[p['venue']] = venues.get(p['venue'], 0) + 1
        years.add(p['year'])

    print("\nBy venue:")
    for venue, count in sorted(venues.items()):
        print(f"  {venue}: {count}")

    print(f"\nYears: {min(years)} - {max(years)}")
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()

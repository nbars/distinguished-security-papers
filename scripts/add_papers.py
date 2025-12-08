#!/usr/bin/env python3
"""
Add new papers to papers.json without duplicates.
"""

import json
from pathlib import Path

# New papers to add
new_papers = [
    # USENIX Security 2025
    {"title": "How Transparent is Usable Privacy and Security Research?", "authors": "Jan H. Klemmer, Juliane Schmüser, Fabian Fischer, Jacques Suray, Jan-Ulrich Holtgrave, Simon Lenau, Byron M. Lowens, Florian Schaub, Sascha Fahl", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Catch-22: Uncovering Compromised Hosts using SSH Public Keys", "authors": "Cristian Munteanu, Georgios Smaragdakis, Anja Feldmann, Tobias Fiebig", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "We Have a Package for You!", "authors": "Joseph Spracklen, Raveen Wijewickrama, A H M Nazmus Sakib, Anindya Maiti, Bimal Viswanath", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Branch Privilege Injection", "authors": "Sandro Rüegge, Johannes Wikner, Kaveh Razavi", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Fuzzing the PHP Interpreter via Dataflow Fusion", "authors": "Yuancheng Jiang, Chuqi Zhang, Bonan Ruan, Jiahao Liu, Manuel Rigger, Roland H. C. Yap, Zhenkai Liang", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Confusing Value with Enumeration", "authors": "Moritz Schloegel, Daniel Klischies, Simon Koch, David Klein, Lukas Gerlach, Malte Wessels, Leon Trampert, Martin Johns, Mathy Vanhoef, Michael Schwarz, Thorsten Holz, Jo Van Bulck", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Characterizing and Detecting Propaganda-Spreading Accounts on Telegram", "authors": "Klim Kireev, Yevhen Mykhno, Carmela Troncoso, Rebekah Overdorf", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "My ZIP isn't your ZIP", "authors": "Yufan You, Jianjun Chen, Qi Wang, Haixin Duan", "venue": "USENIX Security", "year": 2025, "award": "Distinguished Paper", "url": ""},

    # NDSS 2025
    {"title": "ReThink: Reveal the Threat of Electromagnetic Interference on Power Inverters", "authors": "Fengchen Yang, Zihao Dan, Kaikai Pan, Chen Yan, Xiaoyu Ji, Wenyuan Xu (Zhejiang University)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "An Empirical Study on Fingerprint API Misuse with Lifecycle Analysis in Real-world Android Apps", "authors": "Xin Zhang, Xiaohan Zhang, Zhichen Liu, Bo Zhao, Zhemin Yang, Min Yang (Fudan University)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "SafeSplit: A Novel Defense Against Client-Side Backdoor Attacks in Split Learning", "authors": "Phillip Rieger, Alessandro Pegoraro, Kavita Kumari, Tigist Abera, Jonathan Knauer, Ahmad-Reza Sadeghi (Technical University of Darmstadt)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Provably Unlearnable Data Examples", "authors": "Derui Wang, Minhui Xue (CSIRO's Data61), Bo Li (University of Chicago), Seyit Camtepe, Liming Zhu (CSIRO's Data61)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "DUMPLING: Fine-grained Differential JavaScript Engine Fuzzing", "authors": "Liam Wachter, Julian Gremminger (EPFL), Christian Wressnegger (Karlsruhe Institute of Technology), Mathias Payer, Flavio Toffalini (EPFL)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "type++: Prohibiting Type Confusion with Inline Type Information", "authors": "Nicolas Badoux (EPFL), Flavio Toffalini (Ruhr-Universität Bochum), Yuseok Jeon (UNIST), Mathias Payer (EPFL)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Rethinking Trust in Forge-Based Git Security", "authors": "Aditya Sirish A Yelgundhalli, Patrick Zielinski (NYU), Reza Curtmola (NJIT), Justin Cappos (NYU)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "Blindfold: Confidential Memory Management by Untrusted Operating System", "authors": "Caihua Li, Seung-seob Lee, Ling Zhong (Yale University)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "PropertyGPT: LLM-driven Formal Verification of Smart Contracts", "authors": "Ye Liu (SMU), Yue Xue (MetaTrust Labs), Daoyuan Wu (HKUST)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "DiStefano: Decentralized Infrastructure for Sharing Trusted Encrypted Facts", "authors": "Sofía Celi (Brave Software), Alex Davidson (NOVA LINCS), Hamed Haddadi (Imperial College London), Gonçalo Pestana (Hashmatter), Joe Rowell (University of London)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "ReDAN: An Empirical Study on Remote DoS Attacks against NAT Networks", "authors": "Xuewei Feng, Yuxiang Yang, Qi Li (Tsinghua University)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},
    {"title": "VoiceRadar: Voice Deepfake Detection using Micro-Frequency and Compositional Analysis", "authors": "Kavita Kumari (TU Darmstadt), Maryam Abbasihafshejani (UT San Antonio)", "venue": "NDSS", "year": 2025, "award": "Distinguished Paper", "url": ""},

    # IEEE S&P 2025
    {"title": "COBBL: Dynamic Constraint Generation for SNARKs", "authors": "Kunming Jiang, Fraser Brown, Riad Wahby (Carnegie Mellon University)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Transport Layer Obscurity: Circumventing SNI Censorship on the TLS Layer", "authors": "Niklas Niere, Felix Lange, Juraj Somorovsky (Paderborn University), Robert Merget (Technology Innovation Institute)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Follow My Flow: Unveiling Client-Side Prototype Pollution Gadgets from One Million Real-World Websites", "authors": "Zifeng Kang, Muxi Lyu, Zhengyu Liu, Jianjia Yu (Johns Hopkins University), Runqi Fan, Song Li (Zhejiang University), Yinzhi Cao", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "CipherSteal: Stealing Input Data from TEE-Shielded Neural Networks with Ciphertext Side Channels", "authors": "Yuanyuan Yuan, Zhibo Liu, Sen Deng, Yanzuo Chen, Shuai Wang (HKUST), Yinqian Zhang (SUSTech), Zhendong Su (ETH Zurich)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Characterizing Robocalls with Multiple Vantage Points", "authors": "Sathvik Prasad, Aleksandr Nahapetyan, Bradley Reaves (North Carolina State University)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Verifiable Boosted Tree Ensembles", "authors": "Stefano Calzavara, Lorenzo Cazzaro, Claudio Lucchese, Giulio Ermanno Pibiri (Università Ca' Foscari Venezia)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Breaking the Barrier: Post-Barrier Spectre Attacks", "authors": "Johannes Wikner, Kaveh Razavi (ETH Zurich)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Unveiling Security Vulnerabilities in Git Large File Storage Protocol", "authors": "Yuan Chen, Qinying Wang, Yong Yang (Zhejiang University), Yuanchao Chen, Yuwei Li (NUDT), Shouling Ji", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "The Inadequacy of Similarity-based Privacy Metrics", "authors": "Georgi Ganev (UCL, SAS), Emiliano De Cristofaro (UC Riverside)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Empc: Effective Path Prioritization for Symbolic Execution with Path Cover", "authors": "Shuangjie Yao, Dongdong She (HKUST)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "SLAP: Data Speculation Attacks via Load Address Prediction on Apple Silicon", "authors": "Jason Kim, Daniel Genkin (Georgia Institute of Technology), Yuval Yarom (Ruhr University Bochum)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "Detecting Taint-Style Vulnerabilities in Microservice-Structured Web Applications", "authors": "Fengyu Liu, Yuan Zhang, Tian Chen, Youkun Shi, Guangliang Yang, Zihan Lin, Min Yang (Fudan University), Junyao He, Qi Li (Alibaba Group)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
    {"title": "DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks", "authors": "Yupei Liu (Penn State), Yuqi Jia, Neil Zhenqiang Gong (Duke University), Jinyuan Jia, Dawn Song (UC Berkeley)", "venue": "IEEE S&P", "year": 2025, "award": "Best Paper", "url": ""},
]


def normalize_title(title):
    """Normalize title for comparison."""
    return title.lower().strip().rstrip('.').replace('"', '').replace("'", "")


def main():
    json_path = Path(__file__).parent.parent / "data" / "papers.json"

    # Load existing papers
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    existing_papers = data['papers']

    # Create set of existing titles for duplicate detection
    existing_titles = {normalize_title(p['title']) for p in existing_papers}

    # Add new papers if not duplicates
    added = 0
    skipped = 0
    for paper in new_papers:
        norm_title = normalize_title(paper['title'])
        if norm_title not in existing_titles:
            existing_papers.append(paper)
            existing_titles.add(norm_title)
            added += 1
            print(f"  Added: {paper['title'][:50]}...")
        else:
            skipped += 1
            print(f"  Skipped (duplicate): {paper['title'][:50]}...")

    # Sort by year (descending), venue, title
    existing_papers.sort(key=lambda p: (-p['year'], p['venue'], p['title']))

    # Update data
    data['papers'] = existing_papers

    # Write back
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Added {added} papers, skipped {skipped} duplicates.")
    print(f"Total papers: {len(existing_papers)}")


if __name__ == "__main__":
    main()

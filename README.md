# Best Papers in Systems Security

A static website showcasing award-winning papers from the top computer security conferences IEEE S&P, ACM CCS, USENIX Security and NDSS

**Note:** There is no guarantee regarding the correctness or completeness of the data.

## Data

Paper data is stored in `data/papers.json` and can be easily edited manually.

### Updating the Data

1. **Manual editing**: Edit `data/papers.json` directly to add, remove, or modify entries.
2. **Validate data**: Run `python3 scripts/check_db.py --dblp-all` to verify entries against DBLP.

### JSON Structure

```json
{
  "papers": [
    {
      "title": "Paper Title",
      "authors": [
        {"name": "Author 1", "institution": "University A"},
        {"name": "Author 2", "institution": "University B"}
      ],
      "venue": "IEEE S&P",
      "year": 2024,
      "award": "Best Paper",
      "url": "https://doi.org/...",
      "data_checked_via": "https://dblp.org/rec/..."
    }
  ]
}
```

## Development

This is a static site with no build step required. To run locally:

```bash
# Using Python
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## Data Source

Paper data is sourced from [prncoprs/best-papers-in-computer-security](https://github.com/prncoprs/best-papers-in-computer-security).

## Acknowledgments

- Design inspired by [oaklandsok.github.io](https://oaklandsok.github.io/)
- Built with [Bootstrap 5](https://getbootstrap.com/)

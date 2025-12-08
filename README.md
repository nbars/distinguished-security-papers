# Best Papers in Systems Security

A static website showcasing award-winning papers from top computer security conferences.

## Live Site

Visit: [your-username.github.io/best-security-papers](https://your-username.github.io/best-security-papers)

## Features

- Papers from 4 major security conferences: IEEE S&P, ACM CCS, USENIX Security, NDSS
- Filter by venue
- Papers grouped by year (newest first)
- Direct links to paper PDFs where available
- Responsive design with Bootstrap 5

## Data

Paper data is stored in `data/papers.json` and can be easily edited manually.

### Updating the Data

1. **Manual editing**: Edit `data/papers.json` directly to add, remove, or modify entries.

2. **Re-run the parser**: To fetch the latest data from the source repository:
   ```bash
   python3 scripts/parse_data.py
   ```

### JSON Structure

```json
{
  "papers": [
    {
      "title": "Paper Title",
      "authors": "Author 1 (Affiliation), Author 2 (Affiliation)",
      "venue": "IEEE S&P",
      "year": 2024,
      "award": "Best Paper",
      "url": "https://example.com/paper.pdf"
    }
  ]
}
```

## Development

This is a static site with no build step required. To run locally:

```bash
# Using Python
python3 -m http.server 8000

# Using Node.js
npx serve .
```

Then open http://localhost:8000 in your browser.

## Deployment to GitHub Pages

1. Create a new repository on GitHub
2. Push this code to the repository
3. Go to Settings > Pages
4. Select "Deploy from a branch" and choose `main` branch
5. Your site will be available at `https://your-username.github.io/repository-name`

## Data Source

Paper data is sourced from [prncoprs/best-papers-in-computer-security](https://github.com/prncoprs/best-papers-in-computer-security).

## Acknowledgments

- Design inspired by [oaklandsok.github.io](https://oaklandsok.github.io/)
- Built with [Bootstrap 5](https://getbootstrap.com/)

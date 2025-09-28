# Font Downloader

A CLI to find and download Google Fonts. It consolidates TTF/OTF/TTC from the family ZIP or the google/fonts repo, adds all available WOFF/WOFF2 weights via the CSS2 API, writes OFL.txt, and generates an SCSS snippet.

## Installation

```bash
pip install -e .
```

## Commands

### Search
```bash
python -m fontdownloader.cli search "Roboto"
```

### Download one family (consolidated)
```bash
python -m fontdownloader.cli download "Roboto" --force
```
- Downloads TTF/OTF/TTC + OFL.txt (ZIP first, repo fallback)
- Adds all WOFF/WOFF2 weights (100–900, normal/italic) via CSS2
- Writes SCSS to `assets/scss/Roboto.scss`
- Outputs files under `assets/fonts/Roboto/`

### Download many families
```bash
python -m fontdownloader.cli download-all --limit 100
```
- Uses the same consolidated flow per family

### Generate SCSS only
```bash
python -m fontdownloader.cli generate-scss "Roboto"
```
- Regenerates `assets/scss/Roboto.scss` based on current files in `assets/fonts/Roboto/`

## Output
- `assets/fonts/<Family>/`: TTF/OTF/TTC and WOFF/WOFF2 files, plus `OFL.txt`
- `assets/scss/<Family>.scss`: @font-face rules for downloaded variants

## Notes
- No API key required. If the ZIP is blocked, the tool falls back to the google/fonts GitHub repo for TTF/OTF/TTC.
- Optional: set a `GITHUB_TOKEN` in your environment to raise GitHub API rate limits.
- The `assets/` directory is ignored by git by default.

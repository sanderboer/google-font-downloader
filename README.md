# Font Downloader

A CLI to find and download Google Fonts. It consolidates TTF/OTF/TTC from the family ZIP or the google/fonts repo, adds all available WOFF/WOFF2 weights via the CSS2 API, writes OFL.txt, and generates an SCSS snippet.

**✨ Features:**
- **Variable font detection** - Automatically detects and handles variable fonts correctly
- **Smart subsetting** - Uses Google's optimized WOFF2 subsets (20-50KB per font)
- **Optional TTF conversion** - Convert TTF to WOFF/WOFF2 for full unicode coverage
- **No duplicates** - Intelligently avoids downloading the same file multiple times

## Installation

From PyPI (recommended):
```bash
pip install fontdownloader
```

From source (development):
```bash
pip install -e .[dev]
```

### Optional Dependencies

For TTF to WOFF/WOFF2 conversion (full unicode support):
```bash
pip install fonttools[woff,woff2] brotli
```

## Commands

### Search
```bash
fontdownloader search "Roboto"
fontdownloader search "Inter" --details  # Show variant details
```

### Download one or more families (consolidated)
```bash
# Single font (Google's optimized subsets)
fontdownloader download "Inter"

# Multiple fonts
fontdownloader download "Inter" "Roboto" "Lora"

# From file (one name per line)
fontdownloader download --file fonts.txt

# Force reinstall
fontdownloader download "Inter" --force

# Convert TTF to WOFF/WOFF2 for full unicode coverage
fontdownloader download "Inter" --convert-ttf
```

**What gets downloaded:**
- TTF/OTF/TTC files + OFL.txt (from ZIP or google/fonts repo)
- WOFF/WOFF2 files via CSS2 API (all weights 100-900, normal/italic)
- For **variable fonts**: Downloads once per style (no duplicates!)
- SCSS file in `assets/scss/<Family>.scss` with proper @font-face rules
- All files in `assets/fonts/<Family>/`

### Generate SCSS only
```bash
fontdownloader generate-scss "Roboto"
```
- Regenerates `assets/scss/Roboto.scss` based on current files in `assets/fonts/Roboto/`

### Update Font Catalog
```bash
fontdownloader update-catalog
fontdownloader update-catalog --force  # Force update even if cache is fresh
```

### Download Multiple Popular Fonts
```bash
fontdownloader download-all --limit 50
fontdownloader download-all --limit 100 --convert-ttf  # With TTF conversion
```

## Output Structure
```
assets/
├── fonts/
│   └── Inter/
│       ├── Inter-normal.woff2          # Variable font (100-900 weights)
│       ├── Inter-italic.woff2          # Variable italic
│       ├── Inter[opsz,wght].ttf        # Full TTF (if available)
│       └── OFL.txt                     # License
└── scss/
    └── Inter.scss                       # @font-face rules
```

## Font Formats Explained

### Google's WOFF2 Subsets (Default)
- ✅ **Small files** (20-50KB per font) - Fast page loads
- ✅ **Web optimized** - Google's subsetting strategy
- ✅ **No extra tools** needed
- ❌ Limited unicode coverage (Latin, Cyrillic, Greek subsets)

### TTF Conversion (`--convert-ttf`)
- ✅ **Full unicode** coverage (all languages)
- ✅ **Offline use** without Google CDN
- ✅ Good compression (60% vs TTF)
- ❌ **Larger files** (300-400KB vs 25KB)
- ❌ Requires fonttools installation

**See [FONT_FORMATS_EXPLAINED.md](FONT_FORMATS_EXPLAINED.md) for detailed comparison and use cases.**

## Variable Fonts

fontdownloader automatically detects variable fonts (fonts with weight/style axes) and handles them efficiently:

**Before (old behavior):**
- Downloaded Inter-100-normal.woff2, Inter-200-normal.woff2, ..., Inter-900-normal.woff2
- All were identical files (duplicates!)
- 18 files × 25KB = 450KB wasted space

**After (v0.2.0+):**
- Downloads Inter-normal.woff2 once (contains all weights 100-900)
- Generates proper CSS with weight ranges: `font-weight: 100 900;`
- 2 files × 25KB = 50KB total

## Examples

### Basic web project (Latin characters only)
```bash
fontdownloader download "Inter" "Roboto"
# Downloads ~50KB of optimized WOFF2 files per font
```

### Multi-language website (need Cyrillic, Greek, etc.)
```bash
fontdownloader download "Inter" "Roboto"
# Downloads all Google subsets automatically (~175KB per font)
```

### Full unicode coverage (convert TTF)
```bash
fontdownloader download --convert-ttf "Source Code Pro"
# Downloads TTF and converts to WOFF2 (~350KB per font)
```

## Notes
- **No API key required**. If ZIP download is blocked, falls back to google/fonts GitHub repo.
- **Optional**: Set `GITHUB_TOKEN` environment variable to raise GitHub API rate limits.
- **Variable font support**: Automatically detected and handled correctly.
- **Smart caching**: Font catalog cached for 24 hours to reduce API calls.
- The `assets/` directory is gitignored by default.

## Troubleshooting

### "Missing characters in my downloaded font"
Google's WOFF2 subsets only include specific unicode ranges. Use `--convert-ttf` for full coverage:
```bash
fontdownloader download --convert-ttf "Inter"
```

### "fonttools not found"
Install optional dependencies:
```bash
pip install fonttools[woff,woff2] brotli
```

### "Downloaded many identical files"
Update to the latest version - variable font detection was added in v0.2.0:
```bash
pip install --upgrade fontdownloader
```

## License

See [LICENSE](LICENSE) file.

**Note**: Downloaded fonts have their own licenses (typically OFL). See each font's `OFL.txt` file.

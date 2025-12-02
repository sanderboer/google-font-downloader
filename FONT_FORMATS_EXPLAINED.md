# Font Formats and Google Fonts Subsetting Explained

## Overview

This document explains the different font file formats provided by fontdownloader, the subsetting strategy used by Google Fonts, and when to use each approach.

## Font File Formats

### TTF/OTF (Desktop Fonts)
- **Full unicode coverage** - Contains all characters (Latin, Cyrillic, Greek, Arabic, etc.)
- **Large file sizes** - Typically 500KB - 2MB per font file
- **Desktop optimized** - Best for desktop applications and print
- **Source format** - Can be converted to web formats

### WOFF2 (Web Font, Google's Default)
- **Highly compressed** - 50-60% smaller than TTF
- **Subset by default** - Google provides language-specific subsets
- **Small file sizes** - Typically 20-50KB per subset
- **Web optimized** - Fastest page load times
- **Limited unicode** - Only includes specific character ranges

### WOFF (Legacy Web Font)
- **Older compression** - Not as efficient as WOFF2
- **Better compatibility** - Works with older browsers
- **Rarely needed** - WOFF2 is supported by all modern browsers

## Google Fonts Subsetting Strategy

When you download fonts via Google's CSS API, they use **unicode-range subsetting**:

```css
/* Example: Inter font has multiple subsets per weight */

/* Cyrillic Extended subset */
@font-face {
  font-family: 'Inter';
  font-weight: 400;
  src: url(https://fonts.gstatic.com/s/inter/v20/...UUMJng.woff2);
  unicode-range: U+0460-052F, U+1C80-1C8A, ...;
}

/* Latin subset */
@font-face {
  font-family: 'Inter';
  font-weight: 400;
  src: url(https://fonts.gstatic.com/s/inter/v20/...9hiA.woff2);
  unicode-range: U+0000-00FF, U+0131, ...;
}
```

### Subset Breakdown

For a typical font like Inter, Google provides these subsets:
- **cyrillic-ext** - Extended Cyrillic characters (~25KB)
- **cyrillic** - Basic Cyrillic (~25KB)
- **greek-ext** - Extended Greek (~25KB)
- **greek** - Basic Greek (~25KB)
- **vietnamese** - Vietnamese characters (~25KB)
- **latin-ext** - Extended Latin (~25KB)
- **latin** - Basic Latin (~25KB)

**Total if you need all subsets**: ~175KB per weight
**Total if you only need Latin**: ~25KB per weight

Compare to full TTF: ~850KB (contains ALL subsets in one file)

## Variable Fonts

### What are Variable Fonts?

Variable fonts contain **multiple weights/styles in a single file** using font variation axes.

Example: `Inter[wght].ttf` contains:
- Weight axis: 100 (Thin) → 900 (Black)
- All weights in between with smooth interpolation

### Google's Variable Font Handling

Google Fonts serves variable fonts as **static subsets**. For Inter:
- They provide the SAME variable font file for weights 100, 200, 300, ..., 900
- Each file is a subset (e.g., latin-only) variable font
- Browser uses CSS `font-weight` to select the weight from the variable font

**Before fontdownloader v0.2.0**: Downloaded duplicates (same file 9 times)
**After fontdownloader v0.2.0**: Detects variable fonts, downloads once per style

### Proper CSS for Variable Fonts

```scss
// Old way (incorrect for variable fonts)
@font-face {
  font-family: 'Inter';
  font-weight: 400;  // Only weight 400
  src: url('../fonts/Inter/Inter-normal.woff2') format('woff2');
}

// New way (correct for variable fonts)
@font-face {
  font-family: 'Inter';
  font-weight: 100 900;  // Weight range
  src: url('../fonts/Inter/Inter-normal.woff2') format('woff2');
}
```

## When to Use Each Approach

### Use Google's WOFF2 Subsets (Default)

**Best for:**
- ✅ **Web projects** with fast page load requirements
- ✅ **Latin-only** content (English, Spanish, French, etc.)
- ✅ **Small file sizes** (25KB vs 850KB)
- ✅ **Production websites**

**Limitations:**
- ❌ Limited unicode support (only included subsets)
- ❌ Missing characters show as � or fallback fonts

### Use TTF → WOFF2 Conversion (`--convert-ttf`)

**Best for:**
- ✅ **Multi-language** projects (need Cyrillic, Arabic, etc.)
- ✅ **Full unicode coverage** required
- ✅ **Offline use** without Google's CDN
- ✅ **Font editing** workflows

**Limitations:**
- ❌ **13x larger files** (350KB vs 25KB for variable fonts)
- ❌ Slower page load times
- ❌ Requires fonttools: `pip install fonttools[woff,woff2] brotli`

## File Size Comparison

Example: **Inter** variable font

| Format | Size | Unicode Coverage | Use Case |
|--------|------|------------------|----------|
| TTF (full) | 856 KB | All languages | Desktop, source |
| TTF→WOFF2 (converted) | 342 KB | All languages | Multi-language web |
| Google WOFF2 (latin) | 25 KB | Latin only | English websites |
| Google WOFF2 (all subsets) | ~175 KB | All subsets | Multi-language (subsets) |

## Recommendations

### For Most Projects
```bash
# Default: Small, fast, Google-optimized subsets
fontdownloader download Inter "Open Sans" Roboto
```

### For Multi-Language Projects
```bash
# Option 1: Get all Google subsets (automatic)
fontdownloader download Inter

# Option 2: Convert TTF for full coverage (larger files)
fontdownloader download --convert-ttf Inter
```

### For Offline/Desktop Use
```bash
# Download and convert TTF files
fontdownloader download --convert-ttf "Source Code Pro"
```

## Technical Details

### Variable Font Detection

fontdownloader detects variable fonts by:
1. Parsing CSS responses from Google Fonts API
2. Checking if multiple weights share the same URL
3. If 3+ weights have identical URLs → Variable font detected
4. Downloads once per style instead of once per weight

### Conversion Process

When using `--convert-ttf`:
1. Downloads TTF/OTF files from Google Fonts ZIP or GitHub
2. Uses fontTools to convert to WOFF/WOFF2
3. Detects variable font axes (weight, optical size, etc.)
4. Generates appropriate CSS with weight ranges
5. Provides ~60% compression vs TTF

### Browser Support

| Format | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| WOFF2 | 36+ | 39+ | 10+ | 14+ |
| WOFF | 6+ | 3.6+ | 5.1+ | 12+ |
| TTF | ✅ | ✅ | ✅ | ✅ |

**Recommendation**: Use WOFF2 only (2024+), all modern browsers support it.

## Common Issues

### "Missing characters in downloaded font"

**Problem**: Google's subset doesn't include the characters you need (e.g., Cyrillic).

**Solution**: Use `--convert-ttf` to get full unicode coverage:
```bash
fontdownloader download --convert-ttf Inter
```

### "Downloaded 18 identical WOFF2 files"

**Problem**: Old fontdownloader versions didn't detect variable fonts.

**Solution**: Update fontdownloader and re-download:
```bash
pip install --upgrade fontdownloader
rm -rf assets/fonts/Inter
fontdownloader download Inter
```

### "fonttools not found error"

**Problem**: Trying to use `--convert-ttf` without fonttools installed.

**Solution**: Install optional dependencies:
```bash
pip install fonttools[woff,woff2] brotli
```

## Further Reading

- [Google Fonts CSS API Documentation](https://developers.google.com/fonts/docs/css2)
- [Variable Fonts Guide](https://web.dev/variable-fonts/)
- [WOFF2 Specification](https://www.w3.org/TR/WOFF2/)
- [fontTools Documentation](https://fonttools.readthedocs.io/)

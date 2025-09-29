# Google Fonts Automation System

## Quick Start

### 1. Generate Complete Catalog
```bash
# Install dependencies
pip install requests urllib3

# Generate catalog (takes ~45-60 minutes for complete)
python catalog_builder.py --output google_fonts_catalog.json --verbose

# Or test with limited fonts (faster)
python catalog_builder.py --max-fonts 50 --verbose
```

### 2. Validate Catalog
```bash
python validate_catalog.py google_fonts_catalog.json
```

### 3. Integrate with Fontdownloader
```bash
python integrate_catalog.py google_fonts_catalog.json --cli-path ../fontdownloader/cli.py --verify
```

## Automation Schedule

The GitHub Actions workflow automatically:
- 🕐 Runs every Sunday at 2 AM UTC
- 🔍 Generates complete catalog of 1,052+ fonts
- ✅ Validates quality and completeness
- 📝 Creates PR if changes detected
- 📊 Updates documentation with stats

## Manual Trigger

Trigger automation manually:
1. Go to Actions tab in GitHub
2. Select "Update Google Fonts Catalog"  
3. Click "Run workflow"
4. Optional: Set font limits for testing

## Files

- `catalog_builder.py` - Main catalog generator
- `validate_catalog.py` - Quality validation
- `integrate_catalog.py` - Fontdownloader integration  
- `requirements.txt` - Python dependencies

## Status & Limitations

Current automation provides:
- ✅ **Comprehensive coverage**: 1,052+ font families from GitHub repository
- ✅ **Zero maintenance**: Fully automated updates
- ✅ **Quality assured**: Comprehensive validation
- ✅ **Future proof**: Adapts to Google changes

### ⚠️ Important Limitations

**This system does not absolutely guarantee complete parity with Google Web Fonts:**

- **API Blocking**: Google's CSS2 API actively blocks automated requests, so variant detection relies on fallbacks for many fonts
- **Timing Differences**: New fonts may appear on fonts.google.com before being available in the GitHub repository
- **Variant Accuracy**: Some fonts may have fewer variants detected than actually available due to API restrictions
- **Regional Availability**: Google may serve different font subsets based on geographic location
- **Real-time Changes**: Google can modify font availability instantly, while this system updates weekly

### 🎯 What This Provides

- **Best-effort completeness** using all available data sources
- **Reliable fallbacks** when Google's APIs are restricted
- **Consistent updates** to maintain reasonable parity over time
- **Graceful degradation** when perfect data isn't available

For the most up-to-date font availability, always verify against fonts.google.com directly.

See `AUTOMATION_IMPLEMENTATION.md` for complete technical details.
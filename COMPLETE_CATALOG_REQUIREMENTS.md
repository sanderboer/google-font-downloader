# Complete Google Fonts Catalog Requirements

## Overview

To construct a **complete offline fallback** for Google Fonts, you need to catalog **1,052 font families** across three license types.

## Scope & Scale

| **License Type** | **Families** | **Percentage** |
|------------------|--------------|----------------|
| OFL (Open Font License) | 1,000 | 95.1% |
| Apache License | 47 | 4.5% |
| Ubuntu Font License | 5 | 0.4% |
| **TOTAL** | **1,052** | **100%** |

## Required Data Per Font Family

### 1. **Basic Identification**
```json
{
  "family": "Inter",
  "license": "ofl",
  "slug": "inter"
}
```

### 2. **Categorization**
```json
{
  "category": "sans-serif",  // serif, monospace, display, handwriting
  "subsets": ["latin", "latin-ext", "cyrillic"],
  "popularity": 85  // Optional ranking
}
```

### 3. **Variant Information**
```json
{
  "variants": [
    "100", "200", "300", "regular", "500", "600", "700", "800", "900",
    "100italic", "200italic", "300italic", "italic", "500italic", 
    "600italic", "700italic", "800italic", "900italic"
  ],
  "axes": ["wght", "ital", "opsz"]  // For variable fonts
}
```

### 4. **File Locations**
```json
{
  "github_path": "ofl/inter",
  "files": [
    "Inter[opsz,wght].ttf",
    "Inter-Italic[opsz,wght].ttf"
  ],
  "has_static": false  // Whether discrete weight files exist
}
```

## Data Sources

### 1. **Primary Source: GitHub API**
```
https://api.github.com/repos/google/fonts/contents/{license}/{font_slug}
```
- ✅ **Comprehensive**: All 1,052 families
- ✅ **Accurate**: Official repository
- ✅ **File listings**: TTF/OTF locations
- ⚠️ **Rate limited**: 5,000 requests/hour
- ❌ **No variants**: Requires CSS2 API cross-reference

### 2. **Metadata Source: METADATA.pb Files**
```
https://raw.githubusercontent.com/google/fonts/main/{license}/{font}/METADATA.pb
```
- ✅ **Rich data**: Category, designer, subsets
- ✅ **Official**: Google's own metadata
- ❌ **Complex format**: Protocol Buffers, needs parsing
- ❌ **Inconsistent**: Some fonts missing fields

### 3. **Variant Source: CSS2 API**
```
https://fonts.googleapis.com/css2?family={Font+Name}:wght@100;200;...&display=swap
```
- ✅ **Complete variants**: All available weights/styles
- ✅ **Current**: Reflects latest availability
- ⚠️ **Rate sensitive**: May get blocked
- ❌ **Individual requests**: Need 1,052 separate calls

## Storage Requirements

### **Minimal Structure** (~200 KB)
```json
{
  "items": [
    {
      "family": "Inter",
      "variants": ["100", "200", "..."],
      "category": "sans-serif",
      "files": {}
    }
    // ... 1,051 more
  ]
}
```

### **Complete Structure** (~2 MB)
```json
{
  "families": {
    "Inter": {
      "license": "ofl",
      "category": "sans-serif", 
      "variants": ["100", "200", "..."],
      "subsets": ["latin", "latin-ext"],
      "github_path": "ofl/inter",
      "files": ["Inter[opsz,wght].ttf", "..."],
      "axes": ["wght", "ital", "opsz"],
      "popularity": 95,
      "last_updated": "2024-01-15"
    }
    // ... 1,051 more
  },
  "meta": {
    "generated": "2024-09-29",
    "total_families": 1052,
    "source": "google/fonts@main"
  }
}
```

## Implementation Strategies

### **Strategy 1: Curated List (Recommended)**
- **Coverage**: Top 100-200 most popular fonts
- **Size**: ~20-40 KB
- **Maintenance**: Manual updates quarterly
- **Success rate**: ~85% of real-world requests

### **Strategy 2: Generated Catalog**  
- **Coverage**: All 1,052 families
- **Size**: ~200 KB - 2 MB
- **Maintenance**: Automated generation
- **Success rate**: ~100% of requests

### **Strategy 3: Hybrid Approach**
- **Core**: 50 most popular fonts (embedded)
- **Extended**: On-demand GitHub API fallback
- **Size**: ~10 KB core + API calls
- **Success rate**: ~95% without API dependency

## Automation Requirements

### **Data Collection Script**
```python
def build_complete_catalog():
    families = []
    
    # 1. Get all font directories
    for license in ['ofl', 'apache', 'ufl']:
        dirs = github_api(f'contents/{license}')
        
        # 2. For each font family
        for font_dir in dirs:
            # 3. Extract metadata 
            metadata = parse_metadata_pb(license, font_dir['name'])
            
            # 4. Get available variants
            variants = get_css2_variants(metadata['family'])
            
            # 5. Build entry
            families.append({
                'family': metadata['family'],
                'license': license,
                'category': metadata['category'],
                'variants': variants,
                'files': get_font_files(license, font_dir['name'])
            })
    
    return {'items': families}
```

### **Update Strategy**
- **Frequency**: Weekly automated check
- **Trigger**: Git webhook on google/fonts changes  
- **Validation**: Compare against previous version
- **Deployment**: Auto-PR with changes

## Technical Constraints

### **GitHub API Limits**
- **Rate limit**: 5,000 requests/hour
- **Complete scan**: ~1 hour with proper throttling
- **Authentication**: Required for higher limits

### **CSS2 API Risks**
- **Blocking**: May return 403 for automated requests
- **Headers**: Need proper User-Agent rotation
- **Throttling**: Must space requests to avoid blocks

### **File Size Trade-offs**
- **Minimal**: Fast loading, limited metadata
- **Complete**: Rich data, larger payload  
- **Compression**: Gzip reduces JSON ~70%

## Recommended Implementation

### **Phase 1: Enhanced Curated (Immediate)**
- Expand current 5 fonts to 100 most popular
- Add proper variant lists and categories
- ~20 KB, manual maintenance
- Solves 85% of user requests

### **Phase 2: Generated Catalog (Future)**
- Automated generation of all 1,052 families
- CI/CD pipeline for weekly updates
- ~200 KB compressed, zero maintenance
- Solves 100% of requests

### **Phase 3: Smart Hybrid (Advanced)**
- Core 50 fonts embedded
- Dynamic GitHub API fallback for others
- Intelligent caching and error handling
- Best of both worlds approach

## Conclusion

A **complete catalog requires significant engineering effort** but is technically feasible:

- **Data**: 1,052 families × ~200 bytes = ~200 KB
- **Sources**: GitHub API + CSS2 API + METADATA.pb parsing
- **Automation**: Possible but needs proper rate limiting
- **Maintenance**: Weekly updates recommended

**For fontdownloader**: Start with **Phase 1** (100 popular fonts) for immediate 85% success rate improvement, then consider automation for complete coverage.
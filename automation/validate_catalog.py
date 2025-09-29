#!/usr/bin/env python3
"""
Catalog Validation Script

Validates the generated Google Fonts catalog for completeness and correctness.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set


class CatalogValidator:
    """Validates Google Fonts catalog"""
    
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def _load_catalog(self) -> Dict:
        """Load catalog from JSON file"""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load catalog: {e}")
            sys.exit(1)
    
    def validate_structure(self) -> bool:
        """Validate basic catalog structure"""
        print("🔍 Validating catalog structure...")
        
        # Check top-level structure
        required_keys = ['items', 'meta']
        for key in required_keys:
            if key not in self.catalog:
                self.errors.append(f"Missing top-level key: {key}")
        
        # Check items structure
        if 'items' in self.catalog:
            if not isinstance(self.catalog['items'], list):
                self.errors.append("'items' must be a list")
            elif len(self.catalog['items']) == 0:
                self.errors.append("'items' list is empty")
        
        # Check meta structure
        if 'meta' in self.catalog:
            meta = self.catalog['meta']
            meta_keys = ['generated', 'total_families', 'generator']
            for key in meta_keys:
                if key not in meta:
                    self.warnings.append(f"Missing meta key: {key}")
        
        return len(self.errors) == 0
    
    def validate_families(self) -> bool:
        """Validate individual font families"""
        print("🔍 Validating font families...")
        
        if 'items' not in self.catalog:
            return False
        
        family_names: Set[str] = set()
        required_keys = ['family', 'variants', 'category']
        valid_categories = {'sans-serif', 'serif', 'monospace', 'display', 'handwriting'}
        
        for i, item in enumerate(self.catalog['items']):
            # Check required keys
            for key in required_keys:
                if key not in item:
                    self.errors.append(f"Item {i}: Missing key '{key}'")
                    continue
            
            # Check family name
            family = item.get('family', '')
            if not family:
                self.errors.append(f"Item {i}: Empty family name")
            elif family in family_names:
                self.errors.append(f"Item {i}: Duplicate family name '{family}'")
            else:
                family_names.add(family)
            
            # Check variants
            variants = item.get('variants', [])
            if not isinstance(variants, list):
                self.errors.append(f"Item {i} ({family}): variants must be a list")
            elif len(variants) == 0:
                self.errors.append(f"Item {i} ({family}): No variants specified")
            else:
                # Check variant format
                valid_variants = set()
                for variant in variants:
                    if not isinstance(variant, str):
                        self.errors.append(f"Item {i} ({family}): Invalid variant type: {type(variant)}")
                    elif variant in valid_variants:
                        self.warnings.append(f"Item {i} ({family}): Duplicate variant '{variant}'")
                    else:
                        valid_variants.add(variant)
            
            # Check category
            category = item.get('category', '')
            if category not in valid_categories:
                self.warnings.append(f"Item {i} ({family}): Unknown category '{category}' (valid: {valid_categories})")
        
        return len(self.errors) == 0
    
    def validate_completeness(self) -> bool:
        """Validate catalog completeness"""
        print("🔍 Validating catalog completeness...")
        
        if 'items' not in self.catalog:
            return False
        
        total_families = len(self.catalog['items'])
        total_variants = sum(len(item.get('variants', [])) for item in self.catalog['items'])
        
        # Check minimum thresholds
        if total_families < 100:
            self.warnings.append(f"Low family count: {total_families} (expected >100)")
        elif total_families < 1000:
            self.warnings.append(f"Moderate family count: {total_families} (expected >1000 for complete catalog)")
        
        if total_variants < 1000:
            self.warnings.append(f"Low variant count: {total_variants} (expected >1000)")
        
        # Check category distribution
        categories = {}
        for item in self.catalog['items']:
            cat = item.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"📊 Category distribution:")
        for cat, count in sorted(categories.items()):
            percentage = 100 * count / total_families
            print(f"   {cat}: {count} ({percentage:.1f}%)")
        
        # Expect sans-serif to be majority
        sans_serif_pct = 100 * categories.get('sans-serif', 0) / total_families
        if sans_serif_pct < 50:
            self.warnings.append(f"Low sans-serif percentage: {sans_serif_pct:.1f}% (expected >50%)")
        
        return True
    
    def validate_popular_fonts(self) -> bool:
        """Check that popular fonts are included"""
        print("🔍 Validating popular fonts coverage...")
        
        # List of fonts that should definitely be included
        popular_fonts = {
            'Inter', 'Roboto', 'Open Sans', 'Lato', 'Montserrat',
            'Source Sans Pro', 'Raleway', 'Nunito', 'Poppins', 'Ubuntu',
            'Oswald', 'Playfair Display', 'Merriweather', 'Work Sans',
            'Rubik', 'Fira Sans', 'DM Sans', 'Manrope', 'Source Code Pro',
            'Inconsolata', 'Lora', 'Crimson Text'
        }
        
        catalog_families = {item.get('family', '') for item in self.catalog.get('items', [])}
        
        missing_popular = popular_fonts - catalog_families
        if missing_popular:
            self.warnings.append(f"Missing popular fonts: {', '.join(sorted(missing_popular))}")
        
        coverage = 100 * (len(popular_fonts & catalog_families) / len(popular_fonts))
        print(f"📈 Popular fonts coverage: {coverage:.1f}% ({len(popular_fonts & catalog_families)}/{len(popular_fonts)})")
        
        if coverage < 80:
            self.warnings.append(f"Low popular fonts coverage: {coverage:.1f}% (expected >80%)")
        
        return True
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print(f"🧪 Validating catalog: {self.catalog_path}")
        print("=" * 50)
        
        validations = [
            self.validate_structure,
            self.validate_families,
            self.validate_completeness,
            self.validate_popular_fonts
        ]
        
        all_passed = True
        for validation in validations:
            if not validation():
                all_passed = False
        
        # Print results
        print("\n" + "=" * 50)
        print("📋 VALIDATION RESULTS")
        print("=" * 50)
        
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
            print()
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")
        elif not self.errors:
            print("✅ No errors found (warnings only)")
        else:
            print("❌ Validation failed with errors")
        
        # Print summary stats
        if 'items' in self.catalog:
            total_families = len(self.catalog['items'])
            total_variants = sum(len(item.get('variants', [])) for item in self.catalog['items'])
            
            print(f"\n📊 CATALOG STATS:")
            print(f"   Total families: {total_families:,}")
            print(f"   Total variants: {total_variants:,}")
            
            if 'meta' in self.catalog and 'generation_time_seconds' in self.catalog['meta']:
                gen_time = self.catalog['meta']['generation_time_seconds']
                print(f"   Generation time: {gen_time}s")
        
        return all_passed and len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description='Validate Google Fonts catalog')
    parser.add_argument('catalog', help='Path to catalog JSON file')
    parser.add_argument('--strict', action='store_true',
                      help='Treat warnings as errors')
    
    args = parser.parse_args()
    
    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"❌ Catalog file not found: {catalog_path}")
        sys.exit(1)
    
    validator = CatalogValidator(catalog_path)
    success = validator.run_all_validations()
    
    if args.strict and validator.warnings:
        print("\n⚠️  Strict mode: treating warnings as errors")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
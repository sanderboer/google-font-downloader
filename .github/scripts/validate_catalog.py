#!/usr/bin/env python3
"""
Simple catalog validation script for GitHub Actions
"""

import json
import os
import sys


def validate_catalog():
    """Validate the generated catalog"""
    try:
        # Check if file exists
        catalog_path = "fontdownloader/google_fonts_catalog.json"
        if not os.path.exists(catalog_path):
            print(f"❌ Catalog file not found: {catalog_path}")
            return False

        # Check file size
        file_size = os.path.getsize(catalog_path)
        if file_size < 1000:  # Less than 1KB is suspicious
            print(f"❌ Catalog file too small: {file_size} bytes")
            return False

        with open(catalog_path) as f:
            data = json.load(f)

        # Validate structure
        if "items" not in data:
            print('❌ Missing "items" key in catalog')
            return False

        if "meta" not in data:
            print('❌ Missing "meta" key in catalog')
            return False

        items = data["items"]
        if not isinstance(items, list):
            print('❌ "items" should be a list')
            return False

        # More lenient threshold for manual runs with --max-fonts
        min_families = int(os.environ.get("MIN_FAMILIES", "100"))
        if len(items) < min_families:
            print(f"❌ Too few families: {len(items)} < {min_families}")
            return False

        # Validate sample items
        sample_size = min(5, len(items))
        for i, item in enumerate(items[:sample_size]):
            if not isinstance(item, dict):
                print(f"❌ Item {i} is not a dictionary")
                return False

            required_keys = ["family", "variants", "category"]
            missing_keys = [k for k in required_keys if k not in item]
            if missing_keys:
                print(f"❌ Item {i} missing keys: {missing_keys}")
                return False

            if not isinstance(item["variants"], list) or len(item["variants"]) == 0:
                print(f"❌ Item {i} ({item.get('family', 'unknown')}) has no variants")
                return False

        # Validate metadata
        meta = data["meta"]
        if "generated" not in meta:
            print("⚠️  Warning: Missing generation timestamp")

        print(f"✅ Catalog validation passed:")
        print(f"   - Families: {len(items)}")
        print(f"   - File size: {file_size:,} bytes")
        if "total_variants" in meta:
            print(f"   - Total variants: {meta['total_variants']}")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in catalog: {e}")
        return False
    except Exception as e:
        print(f"❌ Catalog validation failed: {e}")
        return False


if __name__ == "__main__":
    success = validate_catalog()
    sys.exit(0 if success else 1)

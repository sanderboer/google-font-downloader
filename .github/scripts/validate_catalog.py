#!/usr/bin/env python3
"""
Simple catalog validation script for GitHub Actions
"""
import json
import sys


def validate_catalog():
    """Validate the generated catalog"""
    try:
        with open('fontdownloader/google_fonts_catalog.json') as f:
            data = json.load(f)

        # Validate structure
        assert 'items' in data and 'meta' in data, 'Missing required keys'
        assert len(data['items']) > 100, f'Too few families: {len(data["items"])}'

        # Validate items
        for item in data['items'][:5]:
            assert all(k in item for k in ['family', 'variants', 'category']), 'Missing required item keys'
            assert len(item['variants']) > 0, f'No variants for {item["family"]}'

        print(f'✅ Catalog validation passed: {len(data["items"])} families')
        return True

    except Exception as e:
        print(f'❌ Catalog validation failed: {e}')
        return False

if __name__ == '__main__':
    success = validate_catalog()
    sys.exit(0 if success else 1)

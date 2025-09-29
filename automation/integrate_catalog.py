#!/usr/bin/env python3
"""
Catalog Integration Script

Integrates the generated catalog into fontdownloader by updating the offline fallback.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Optional


def load_catalog(catalog_path: Path) -> Dict:
    """Load the generated catalog"""
    with open(catalog_path, encoding="utf-8") as f:
        return json.load(f)


def generate_fallback_code(catalog: Dict, max_families: Optional[int] = None) -> str:
    """Generate the offline fallback code for fontdownloader"""

    items = catalog.get("items", [])
    if max_families is not None:
        items = items[:max_families]

    lines = [
        "        # Comprehensive offline fallback (auto-generated)",
        f"        # Generated: {catalog.get('meta', {}).get('generated', 'unknown')}",
        f"        # Total families: {len(items)}",
        "        return {",
        '            "items": [',
    ]

    for i, item in enumerate(items):
        family = item["family"]
        variants = item.get("variants", [])
        category = item.get("category", "sans-serif")

        # Format variants as Python list
        variants_str = json.dumps(variants)

        # Add family entry
        lines.append("                {")
        lines.append(f'                    "family": "{family}",')
        lines.append(f'                    "variants": {variants_str},')
        lines.append(f'                    "category": "{category}",')
        lines.append('                    "files": {}')

        if i < len(items) - 1:
            lines.append("                },")
        else:
            lines.append("                }")

    lines.extend(["            ]", "        }"])

    return "\\n".join(lines)


def update_fontdownloader_cli(
    cli_path: Path,
    catalog: Dict,
    max_families: Optional[int] = None,
    backup: bool = True,
):
    """Update the fontdownloader CLI with new offline fallback"""

    if not cli_path.exists():
        raise FileNotFoundError(f"CLI file not found: {cli_path}")

    # Read current file
    with open(cli_path, encoding="utf-8") as f:
        content = f.read()

    # Backup original if requested
    if backup:
        backup_path = cli_path.with_suffix(".py.backup")
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📁 Backup saved to: {backup_path}")

    # Generate new fallback code
    new_fallback = generate_fallback_code(catalog, max_families)

    # Find the fallback section using regex
    # Pattern: return { "items": [ ... ] }
    pattern = (
        r'(\\s+# Fallback list.*?\\n\\s+return\\s+{\\s*\\n\\s*"items":\\s*\\[)'
        r"(.*?)(\\n\\s*\\]\\s*\\n\\s*})"
    )

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        # Try alternative pattern
        pattern = (
            r'(\\s+return\\s+{\\s*\\n\\s*"items":\\s*\\[)(.*?)(\\n\\s*\\]\\s*\\n\\s*})'
        )
        match = re.search(pattern, content, re.DOTALL)

    if match:
        # Replace the fallback section
        before = content[: match.start()]
        after = content[match.end() :]

        new_content = before + new_fallback + after

        # Write updated file
        with open(cli_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Updated {cli_path}")

        # Show statistics
        old_items = len(re.findall(r'"family":', match.group(2)))
        new_items = len(catalog.get("items", []))
        if max_families is not None:
            new_items = min(new_items, max_families)

        print("📊 Fallback update:")
        print(f"   Before: {old_items} families")
        print(f"   After: {new_items} families")
        print(f"   Change: +{new_items - old_items}")

    else:
        raise ValueError("Could not find fallback section in CLI file")


def verify_integration(cli_path: Path) -> bool:
    """Verify that the integration was successful"""
    try:
        # Try to import and validate the updated CLI
        import importlib.util

        spec = importlib.util.spec_from_file_location("cli", cli_path)
        if spec is None or spec.loader is None:
            return False

        cli_module = importlib.util.module_from_spec(spec)

        # Test import
        spec.loader.exec_module(cli_module)

        # Test the fallback function
        if hasattr(cli_module, "_get_google_fonts_api_data"):
            try:
                fallback_data = cli_module._get_google_fonts_api_data()
                if "items" in fallback_data and len(fallback_data["items"]) > 0:
                    family_count = len(fallback_data["items"])
                    print(f"✅ Integration verified: {family_count} families loaded")
                    return True
            except Exception as e:
                print(f"❌ Integration test failed: {e}")

        return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Integrate catalog into fontdownloader"
    )
    parser.add_argument("catalog", help="Path to generated catalog JSON")
    parser.add_argument(
        "--cli-path",
        default="../fontdownloader/cli.py",
        help="Path to fontdownloader CLI file",
    )
    parser.add_argument(
        "--max-families", type=int, help="Limit number of families to include"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of original CLI file",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify integration after update"
    )

    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    cli_path = Path(args.cli_path)

    print("🔧 Integrating catalog into fontdownloader")
    print(f"   Catalog: {catalog_path}")
    print(f"   CLI: {cli_path}")
    if args.max_families:
        print(f"   Max families: {args.max_families}")
    print()

    try:
        # Load catalog
        catalog = load_catalog(catalog_path)
        print(f"📚 Loaded catalog with {len(catalog.get('items', []))} families")

        # Update CLI
        update_fontdownloader_cli(
            cli_path=cli_path,
            catalog=catalog,
            max_families=args.max_families,
            backup=not args.no_backup,
        )

        # Verify if requested
        if args.verify:
            print("\\n🧪 Verifying integration...")
            if verify_integration(cli_path):
                print("✅ Integration successful!")
            else:
                print("❌ Integration verification failed")
                return 1

        print("\\n🎉 Catalog integration complete!")
        return 0

    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

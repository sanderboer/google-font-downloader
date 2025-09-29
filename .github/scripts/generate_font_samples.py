#!/usr/bin/env python3
"""Generate sample font listing for catalog summary."""

import json
import sys
import os


def generate_samples(catalog_path, output_path):
    """Generate sample font listing."""
    try:
        with open(catalog_path) as f:
            data = json.load(f)

        with open(output_path, "a") as f:
            for i, item in enumerate(data.get("items", [])[:10], 1):
                family = item.get("family", "Unknown")
                category = item.get("category", "unknown")
                variants = len(item.get("variants", []))
                f.write(f"{i}. **{family}** ({category}) - {variants} variants\n")
    except Exception as e:
        with open(output_path, "a") as f:
            f.write(f"Error displaying sample fonts: {e}\n")


if __name__ == "__main__":
    catalog_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "../fontdownloader/google_fonts_catalog.json"
    )
    output_path = sys.argv[2] if len(sys.argv) > 2 else "catalog_summary.md"
    generate_samples(catalog_path, output_path)

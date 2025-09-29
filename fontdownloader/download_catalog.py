#!/usr/bin/env python3
"""
Download latest Google Fonts catalog from GitHub Releases
"""
import json
import urllib.request
import os
from pathlib import Path

def download_latest_catalog(repo="sanderboer/google-font-downloader", output_path="google_fonts_catalog.json"):
    """Download the latest catalog from GitHub Releases"""
    try:
        # Get latest release info
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        with urllib.request.urlopen(url) as response:
            release_data = json.loads(response.read().decode())

        # Find the catalog asset
        catalog_asset = None
        for asset in release_data["assets"]:
            if asset["name"] == "google_fonts_catalog.json":
                catalog_asset = asset
                break

        if not catalog_asset:
            print("❌ No catalog found in latest release")
            return False

        # Download the catalog
        catalog_url = catalog_asset["browser_download_url"]
        print(f"📥 Downloading catalog from: {catalog_url}")

        with urllib.request.urlopen(catalog_url) as response:
            catalog_data = response.read()

        # Save to file
        with open(output_path, "wb") as f:
            f.write(catalog_data)

        print(f"✅ Catalog downloaded to: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to download catalog: {e}")
        return False

if __name__ == "__main__":
    success = download_latest_catalog()
    exit(0 if success else 1)
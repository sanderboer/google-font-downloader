#!/usr/bin/env python3
"""
Download latest Google Fonts catalog from GitHub Releases
"""

import json
import os
import urllib.error
import urllib.request


def download_latest_catalog(
    repo="sanderboer/google-font-downloader", output_path="google_fonts_catalog.json"
):
    """Download the latest catalog from GitHub Releases

    Supports optional GitHub token via GITHUB_TOKEN environment variable
    to avoid rate limiting.
    """
    try:
        # Get latest release info
        url = f"https://api.github.com/repos/{repo}/releases/latest"

        # Create request with optional authentication
        request = urllib.request.Request(url)
        request.add_header("Accept", "application/vnd.github.v3+json")

        # Add GitHub token if available (to avoid rate limits)
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            request.add_header("Authorization", f"token {github_token}")

        with urllib.request.urlopen(request, timeout=10) as response:
            release_data = json.loads(response.read().decode())

        # Find the catalog asset
        catalog_asset = None
        for asset in release_data.get("assets", []):
            if asset["name"] == "google_fonts_catalog.json":
                catalog_asset = asset
                break

        if not catalog_asset:
            print("❌ No catalog found in latest release")
            return False

        # Download the catalog
        catalog_url = catalog_asset["browser_download_url"]
        print(f"📥 Downloading catalog from: {catalog_url}")

        download_request = urllib.request.Request(catalog_url)
        if github_token:
            download_request.add_header("Authorization", f"token {github_token}")

        with urllib.request.urlopen(download_request, timeout=30) as response:
            catalog_data = response.read()

        # Save to file
        with open(output_path, "wb") as f:
            f.write(catalog_data)

        print(f"✅ Catalog downloaded to: {output_path}")
        return True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"❌ No releases found for {repo}")
        elif e.code == 403:
            print(
                "❌ GitHub API rate limit exceeded. Set GITHUB_TOKEN environment variable."
            )
        else:
            print(f"❌ HTTP error {e.code}: {e.reason}")
        return False
    except Exception as e:
        # Print error for debugging but still fail gracefully
        print(f"❌ Error downloading catalog: {e}")
        return False


if __name__ == "__main__":
    success = download_latest_catalog()
    exit(0 if success else 1)

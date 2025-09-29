#!/usr/bin/env python3
"""
Google Fonts Catalog Builder - Full Automation

Generates a complete offline catalog of all Google Fonts families
by scraping GitHub repository and CSS2 API.

Usage:
    python catalog_builder.py [--output catalog.json] [--max-fonts 100] [--verbose]
"""

import argparse
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
from requests.adapters import HTTPAdapter

# Handle urllib3 Retry import variations
try:
    from urllib3.util.retry import Retry
except ImportError:
    # Fallback - disable retry functionality
    Retry = None


class RateLimiter:
    """Simple rate limiter to avoid API blocks"""

    def __init__(self, calls_per_second: float = 2.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self):
        """Wait if necessary to respect rate limit"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class GoogleFontsCatalogBuilder:
    """Main catalog builder class"""

    def __init__(self, github_token: Optional[str] = None, verbose: bool = False):
        self.github_token = github_token
        self.logger = self._setup_logging(verbose)

        # Rate limiters
        self.github_limiter = RateLimiter(calls_per_second=10)  # Conservative
        self.css_limiter = RateLimiter(calls_per_second=1)  # Very conservative

        # Session with retry strategy
        self.session = self._create_session()

        # Statistics
        self.stats = {
            "total_families": 0,
            "successful_families": 0,
            "failed_families": 0,
            "total_variants": 0,
            "api_calls": {"github": 0, "css2": 0, "metadata": 0},
        }

    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """Setup logging configuration"""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        return logging.getLogger(__name__)

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        # Retry strategy
        if Retry is not None:
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
        else:
            adapter = HTTPAdapter(max_retries=3)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Default headers
        session.headers.update(
            {
                "User-Agent": "GoogleFontsCatalogBuilder/1.0 (https://github.com/user/fontdownloader)"
            }
        )

        # GitHub token if provided
        if self.github_token:
            session.headers.update({"Authorization": f"token {self.github_token}"})

        return session

    def get_font_directories(self, license_type: str) -> List[str]:
        """Get all font directories for a license type using Git Trees API"""
        self.github_limiter.wait()

        # Try Git Trees API first (more reliable for large directories)
        try:
            url = "https://api.github.com/repos/google/fonts/git/trees/main?recursive=1"
            self.logger.debug(
                f"Fetching directories for {license_type} via Git Trees API"
            )

            response = self.session.get(url, timeout=60)
            self.stats["api_calls"]["github"] += 1

            if response.status_code == 200:
                tree = response.json().get("tree", [])
                prefix = f"{license_type}/"
                directories = set()

                # Extract font slugs from paths like "ofl/fontname" or "ofl/fontname/..."
                for node in tree:
                    path = node.get("path", "")
                    if not path.startswith(prefix):
                        continue

                    parts = path.split("/")
                    if (
                        len(parts) >= 2
                        and parts[0] == license_type
                        and node.get("type") == "tree"
                    ):
                        directories.add(parts[1])

                directories = sorted(list(directories))
                self.logger.info(
                    f"Found {len(directories)} {license_type} font families via Git Trees"
                )
                return directories

            else:
                self.logger.warning(
                    f"Git Trees API error for {license_type}: {response.status_code}, trying fallback"
                )

        except Exception as e:
            self.logger.warning(
                f"Git Trees API failed for {license_type}: {e}, trying fallback"
            )

        # Fallback to Contents API
        return self._get_font_directories_fallback(license_type)

    def _get_font_directories_fallback(self, license_type: str) -> List[str]:
        """Fallback method using Contents API"""
        self.github_limiter.wait()

        url = f"https://api.github.com/repos/google/fonts/contents/{license_type}"
        self.logger.debug(
            f"Fetching directories for {license_type} via Contents API (fallback)"
        )

        try:
            response = self.session.get(url, timeout=30)
            self.stats["api_calls"]["github"] += 1

            if response.status_code == 200:
                data = response.json()
                directories = [item["name"] for item in data if item["type"] == "dir"]
                self.logger.info(
                    f"Found {len(directories)} {license_type} font families via Contents API"
                )
                return directories
            else:
                self.logger.error(
                    f"Contents API error for {license_type}: {response.status_code}"
                )
                return []

        except Exception as e:
            self.logger.error(
                f"Failed to fetch {license_type} directories via Contents API: {e}"
            )
            return []

    def parse_metadata_pb(self, license_type: str, font_slug: str) -> Dict:
        """Parse METADATA.pb file for font metadata"""
        self.github_limiter.wait()

        url = f"https://raw.githubusercontent.com/google/fonts/main/{license_type}/{font_slug}/METADATA.pb"

        try:
            response = self.session.get(url, timeout=20)
            self.stats["api_calls"]["metadata"] += 1

            if response.status_code == 200:
                metadata_text = response.text

                # Parse basic metadata (simple text parsing for common fields)
                metadata = {
                    "name": font_slug,
                    "category": "sans-serif",  # Default
                    "subsets": ["latin"],  # Default
                    "designer": "",
                    "license": license_type,
                }

                # Extract family name
                name_match = re.search(r'name:\\s*"([^"]+)"', metadata_text)
                if name_match:
                    metadata["name"] = name_match.group(1)

                # Extract category
                category_match = re.search(r'category:\\s*"([^"]+)"', metadata_text)
                if category_match:
                    metadata["category"] = (
                        category_match.group(1).lower().replace("_", "-")
                    )

                # Extract subsets
                subset_matches = re.findall(r'subset:\\s*"([^"]+)"', metadata_text)
                if subset_matches:
                    metadata["subsets"] = subset_matches

                # Extract designer
                designer_match = re.search(r'designer:\\s*"([^"]+)"', metadata_text)
                if designer_match:
                    metadata["designer"] = designer_match.group(1)

                return metadata

        except Exception as e:
            self.logger.debug(f"Failed to parse metadata for {font_slug}: {e}")

        # Fallback metadata
        return {
            "name": self._slug_to_name(font_slug),
            "category": self._guess_category(font_slug),
            "subsets": ["latin"],
            "designer": "",
            "license": license_type,
        }

    def _slug_to_name(self, slug: str) -> str:
        """Convert font slug to proper family name"""
        # Special cases
        slug_to_name_map = {
            "opensans": "Open Sans",
            "sourcecodepro": "Source Code Pro",
            "sourcesanspro": "Source Sans Pro",
            "sourceserifpro": "Source Serif Pro",
            "robotocondensed": "Roboto Condensed",
            "robotoslab": "Roboto Slab",
            "playfairdisplay": "Playfair Display",
            "crimsontext": "Crimson Text",
            "faunaone": "Fauna One",
            "jetbrainsmono": "JetBrains Mono",
            "dmsans": "DM Sans",
            "dmseriftext": "DM Serif Text",
            "worksans": "Work Sans",
            "notosans": "Noto Sans",
            "notoserif": "Noto Serif",
            "firasans": "Fira Sans",
            "firamono": "Fira Mono",
        }

        if slug in slug_to_name_map:
            return slug_to_name_map[slug]

        # General conversion: split camelCase and capitalize
        # Handle numbers (e.g., "42dotsans" -> "42 Dot Sans")
        name = re.sub(r"([a-z])([A-Z])", r"\\1 \\2", slug)
        name = re.sub(r"([0-9])([a-z])", r"\\1 \\2", name)

        return " ".join(word.capitalize() for word in name.split())

    def _guess_category(self, font_slug: str) -> str:
        """Guess font category from slug"""
        serif_indicators = [
            "serif",
            "times",
            "georgia",
            "crimson",
            "merriweather",
            "playfair",
            "lora",
        ]
        mono_indicators = [
            "mono",
            "code",
            "inconsolata",
            "courier",
            "source code",
            "jetbrains",
        ]
        display_indicators = ["display", "impact", "lobster", "dancing", "pacifico"]

        slug_lower = font_slug.lower()

        if any(indicator in slug_lower for indicator in mono_indicators):
            return "monospace"
        elif any(indicator in slug_lower for indicator in serif_indicators):
            return "serif"
        elif any(indicator in slug_lower for indicator in display_indicators):
            return "display"
        else:
            return "sans-serif"

    def get_font_files(self, license_type: str, font_slug: str) -> List[str]:
        """Get list of font files from GitHub repository"""
        self.github_limiter.wait()

        url = f"https://api.github.com/repos/google/fonts/contents/{license_type}/{font_slug}"

        try:
            response = self.session.get(url, timeout=20)
            self.stats["api_calls"]["github"] += 1

            if response.status_code == 200:
                data = response.json()
                font_files = [
                    item["name"]
                    for item in data
                    if item["type"] == "file"
                    and item["name"].endswith((".ttf", ".otf", ".ttc"))
                ]
                return font_files

        except Exception as e:
            self.logger.debug(f"Failed to get font files for {font_slug}: {e}")

        return []

    def get_css2_variants(self, family_name: str, max_retries: int = 3) -> List[str]:
        """Extract available variants from CSS2 API"""
        self.css_limiter.wait()

        # Try comprehensive weight range first
        weights = [100, 200, 300, 400, 500, 600, 700, 800, 900]
        weight_str = ";".join(map(str, weights))

        # Test with both normal and italic
        css_url = f"https://fonts.googleapis.com/css2?family={quote_plus(family_name)}:ital,wght@0,{weight_str};1,{weight_str}&display=swap"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/css,*/*;q=0.1",
            "Referer": "https://fonts.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(css_url, headers=headers, timeout=20)
                self.stats["api_calls"]["css2"] += 1

                if response.status_code == 200 and "@font-face" in response.text:
                    variants = self._parse_css_variants(response.text)
                    if variants:
                        self.logger.debug(
                            f"Found {len(variants)} variants for {family_name}"
                        )
                        return variants

                # If comprehensive failed, try basic
                if attempt == 0:
                    basic_url = f"https://fonts.googleapis.com/css2?family={quote_plus(family_name)}:wght@400;700&display=swap"
                    response = requests.get(basic_url, headers=headers, timeout=20)
                    self.stats["api_calls"]["css2"] += 1

                    if response.status_code == 200 and "@font-face" in response.text:
                        variants = self._parse_css_variants(response.text)
                        if variants:
                            return variants

            except Exception as e:
                self.logger.debug(
                    f"CSS2 attempt {attempt + 1} failed for {family_name}: {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff

        # Fallback variants
        self.logger.debug(f"Using fallback variants for {family_name}")
        return ["regular", "700"]

    def _parse_css_variants(self, css_text: str) -> List[str]:
        """Parse CSS to extract available font variants"""
        variants = set()

        # Find all font-weight and font-style declarations
        weight_matches = re.findall(r"font-weight:\s*(\d+)", css_text)
        style_matches = re.findall(r"font-style:\s*(normal|italic)", css_text)

        # Combine weights and styles
        weights = sorted(set(weight_matches))
        has_italic = "italic" in style_matches

        for weight in weights:
            if weight == "400":
                variants.add("regular")
                if has_italic:
                    variants.add("italic")
            else:
                variants.add(weight)
                if has_italic:
                    variants.add(f"{weight}italic")

        return sorted(variants, key=lambda x: (len(x), x))

    def build_font_entry(self, license_type: str, font_slug: str) -> Optional[Dict]:
        """Build complete font entry"""
        self.logger.debug(f"Processing {license_type}/{font_slug}")

        try:
            # Get metadata
            metadata = self.parse_metadata_pb(license_type, font_slug)

            # Get font files
            files = self.get_font_files(license_type, font_slug)

            # Get variants from CSS2
            variants = self.get_css2_variants(metadata["name"])

            entry = {
                "family": metadata["name"],
                "variants": variants,
                "category": metadata["category"],
                "license": license_type,
                "slug": font_slug,
                "subsets": metadata["subsets"],
                "files": files,
                "designer": metadata["designer"],
                "github_path": f"{license_type}/{font_slug}",
            }

            self.stats["total_variants"] += len(variants)
            self.stats["successful_families"] += 1

            self.logger.info(
                f"✅ {metadata['name']} - {len(variants)} variants, {len(files)} files"
            )
            return entry

        except Exception as e:
            self.logger.error(f"❌ Failed to process {font_slug}: {e}")
            self.stats["failed_families"] += 1
            return None

    def build_complete_catalog(
        self, max_fonts_per_license: Optional[int] = None
    ) -> Dict:
        """Build complete font catalog"""
        self.logger.info("🚀 Starting complete Google Fonts catalog generation")
        start_time = time.time()

        catalog = {
            "meta": {
                "generated": datetime.now().isoformat(),
                "generator": "GoogleFontsCatalogBuilder/1.0",
                "source": "google/fonts@main",
            },
            "families": {},
        }

        license_types = ["ofl", "apache", "ufl"]

        for license_type in license_types:
            self.logger.info(f"📁 Processing {license_type.upper()} fonts...")

            directories = self.get_font_directories(license_type)
            if max_fonts_per_license:
                directories = directories[:max_fonts_per_license]

            self.stats["total_families"] += len(directories)

            for i, font_slug in enumerate(directories, 1):
                self.logger.info(f"[{i}/{len(directories)}] Processing {font_slug}")

                entry = self.build_font_entry(license_type, font_slug)
                if entry:
                    catalog["families"][entry["family"]] = entry

        # Update metadata
        catalog["meta"].update(
            {
                "total_families": len(catalog["families"]),
                "total_variants": self.stats["total_variants"],
                "license_types": len(license_types),
                "generation_time_seconds": round(time.time() - start_time, 2),
                "api_calls": self.stats["api_calls"].copy(),
            }
        )

        # Convert to fontdownloader format
        fontdownloader_catalog = self._convert_to_fontdownloader_format(catalog)

        self._print_stats(catalog)
        return fontdownloader_catalog

    def _convert_to_fontdownloader_format(self, catalog: Dict) -> Dict:
        """Convert to fontdownloader-compatible format"""
        items = []

        for family_name, family_data in catalog["families"].items():
            item = {
                "family": family_name,
                "variants": family_data["variants"],
                "category": family_data["category"],
                "files": {},  # Empty as required by fontdownloader
            }
            items.append(item)

        return {"items": items, "meta": catalog["meta"]}

    def _print_stats(self, catalog: Dict):
        """Print generation statistics"""
        self.logger.info("📊 GENERATION COMPLETE")
        self.logger.info(f"   Total families: {len(catalog['families'])}")
        self.logger.info(f"   Total variants: {catalog['meta']['total_variants']}")
        success_rate = (
            100
            * self.stats["successful_families"]
            / max(self.stats["total_families"], 1)
        )
        success_count = self.stats["successful_families"]
        total_count = self.stats["total_families"]
        self.logger.info(
            f"   Success rate: {success_count}/{total_count} ({success_rate:.1f}%)"
        )
        self.logger.info(
            f"   Generation time: {catalog['meta']['generation_time_seconds']}s"
        )
        api_calls = self.stats["api_calls"]
        self.logger.info(
            f"   API calls: GitHub={api_calls['github']}, "
            f"CSS2={api_calls['css2']}, Metadata={api_calls['metadata']}"
        )


def main():
    parser = argparse.ArgumentParser(description="Build complete Google Fonts catalog")
    parser.add_argument(
        "--output",
        "-o",
        default="google_fonts_catalog.json",
        help="Output file path (default: google_fonts_catalog.json)",
    )
    parser.add_argument(
        "--max-fonts",
        type=int,
        help="Limit number of fonts per license type (for testing)",
    )
    parser.add_argument(
        "--github-token", help="GitHub API token for higher rate limits"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Build catalog
    builder = GoogleFontsCatalogBuilder(
        github_token=args.github_token, verbose=args.verbose
    )

    catalog = builder.build_complete_catalog(max_fonts_per_license=args.max_fonts)

    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    file_size = output_path.stat().st_size
    print(f"💾 Catalog saved to {output_path} ({file_size:,} bytes)")
    print(f"🎉 Generated {len(catalog['items'])} font families!")


if __name__ == "__main__":
    main()

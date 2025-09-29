import io
import json
import os
import pathlib
import re
import shutil
import time
import urllib.parse
import urllib.request
import zipfile

import click
import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def _slugify_google_fonts_dir(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _download_from_gfonts_repo(
    font_name: str, dest_dir: pathlib.Path
) -> tuple[int, bool]:
    """Download TTF/OTF/TTC and OFL from google/fonts GitHub repo.

    Returns (downloaded_file_count, license_found)
    """
    slug = _slugify_google_fonts_dir(font_name)
    license_dirs = ["ofl", "apache", "ufl"]
    headers = {
        "User-Agent": "fontdownloader/0.1",
        "Accept": "application/vnd.github.v3+json",
    }

    def fetch_dir(path: str) -> list:
        url = f"https://api.github.com/repos/google/fonts/contents/{path}"
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            return []
        try:
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def download_file(raw_url: str, out_path: pathlib.Path) -> bool:
        resp = requests.get(raw_url, timeout=60)
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            return True
        return False

    for lic in license_dirs:
        base_path = f"{lic}/{slug}"
        items = fetch_dir(base_path)
        if not items:
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        license_found = False

        # BFS into one level (e.g., static dir) to fetch static TTFs
        queue = [base_path]
        visited = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for it in fetch_dir(current):
                name = it.get("name", "")
                lower = name.lower()
                it_type = it.get("type")
                download_url = it.get("download_url")
                if not download_url:
                    path = it.get("path", "")
                    download_url = (
                        f"https://raw.githubusercontent.com/google/fonts/main/{path}"
                    )

                if it_type == "dir":
                    # descend into 'static' and immediate children once
                    if lower in ("static",) or current == base_path:
                        path = it.get("path", "")
                        if path:
                            queue.append(path)
                    continue

                if lower.endswith((".ttf", ".otf", ".ttc")):
                    target = dest_dir / name
                    if download_file(download_url, target):
                        count += 1
                elif lower == "ofl.txt" and not license_found:
                    target = dest_dir / "OFL.txt"
                    if download_file(download_url, target):
                        license_found = True
                elif lower in ("license.txt", "license") and not license_found:
                    target = dest_dir / "LICENSE.txt"
                    if download_file(download_url, target):
                        license_found = True

        return count, license_found

    return 0, False


def _get_google_fonts_api_data() -> dict:
    """Fetch Google Fonts data. Tries GitHub release catalog first, then API."""
    cache_dir = pathlib.Path.home() / ".fontdownloader" / "cache"
    cache_file = cache_dir / "google_fonts.json"

    # Check cache freshness (24 hours)
    if cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < 86400:  # 24 hours
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    # Try to get latest catalog from GitHub releases first
    try:
        from . import download_catalog

        catalog_temp = cache_dir / "temp_catalog.json"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Try current repository first, fallback to default
        repo_name = "sanderboer/google-font-downloader"
        if download_catalog.download_latest_catalog(
            repo=repo_name, output_path=str(catalog_temp)
        ):
            # Convert catalog format to API format for compatibility
            with open(catalog_temp, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)

            # Transform catalog to API format
            api_data = {"items": catalog_data.get("items", [])}

            # Cache the result
            cache_file.write_text(json.dumps(api_data, indent=2), encoding="utf-8")
            catalog_temp.unlink(missing_ok=True)  # Clean up temp file

            click.echo("✅ Using latest catalog from GitHub releases", err=True)
            return api_data

    except Exception as e:
        click.echo(f"⚠️  Failed to fetch catalog from releases: {e}", err=True)

    # Fallback to Google Fonts API
    api_url = "https://www.googleapis.com/webfonts/v1/webfonts?sort=popularity"
    try:
        click.echo("📡 Falling back to Google Fonts API...", err=True)
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Cache the result
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    except Exception as e:
        click.echo(f"⚠️  Failed to fetch Google Fonts data: {e}", err=True)
        click.echo("Using offline fallback list...", err=True)

        # Try bundled catalog as fallback
        try:
            bundled_catalog = (
                pathlib.Path(__file__).parent / "google_fonts_catalog.json"
            )
            if bundled_catalog.exists():
                click.echo("📦 Using bundled catalog as fallback...", err=True)
                with open(bundled_catalog, "r", encoding="utf-8") as f:
                    catalog_data = json.load(f)
                return {"items": catalog_data.get("items", [])}
        except Exception as fallback_error:
            click.echo(f"⚠️  Failed to load bundled catalog: {fallback_error}", err=True)

        # Final fallback list of popular fonts with updated URLs (using CSS API derived)
        click.echo("🔧 Using minimal fallback font list...", err=True)
        return {
            "items": [
                {
                    "family": "Inter",
                    "variants": ["regular", "700"],
                    "files": {
                        "regular": "https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2",
                        "700": "https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2",
                    },
                },
                {
                    "family": "Roboto",
                    "variants": ["regular", "700"],
                    "files": {
                        "regular": "https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.woff2",
                        "700": "https://fonts.gstatic.com/s/roboto/v30/KFOlCnqEu92Fr1MmWUlfBBc4.woff2",
                    },
                },
                {
                    "family": "Open Sans",
                    "variants": ["regular", "700"],
                    "files": {
                        "regular": "https://fonts.gstatic.com/s/opensans/v44/memvYaGs126MiZpBA-UvWbX2vVnXBbObj2OVTS-muw.woff2",
                        "700": "https://fonts.gstatic.com/s/opensans/v44/memvYaGs126MiZpBA-UvWbX2vVnXBbObj2OVTS-muw.woff2",
                    },
                },
                {
                    "family": "Lora",
                    "variants": ["regular"],
                    "files": {
                        "regular": "https://fonts.gstatic.com/s/lora/v37/0QI6MX1D_JOuGQbT0gvTJPa787weuxJBkq0.woff2"
                    },
                },
                {
                    "family": "Playfair Display",
                    "variants": ["regular"],
                    "files": {
                        "regular": "https://fonts.gstatic.com/s/playfairdisplay/v30/nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKdFvXDXbtXK-F2qC0s.woff2"
                    },
                },
            ]
        }


def _download_font_file(url: str, dest_path: pathlib.Path) -> bool:
    """Download a font file from URL to destination"""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status == 200:
                dest_path.write_bytes(response.read())
                return True
        return False

    except Exception as e:
        click.echo(f"  ❌ Failed to download {url}: {e}", err=True)
        return False


def _download_license_file(font_name: str, dest_path: pathlib.Path) -> bool:
    """Download the OFL license file for a font"""
    try:
        # Try to download the OFL license file from Google Fonts
        license_url = f"https://fonts.google.com/download/license?kit=OFL.txt&family={urllib.parse.quote(font_name)}"
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with urllib.request.urlopen(license_url, timeout=30) as response:
            if response.status == 200:
                dest_path.write_bytes(response.read())
                return True
        return False

    except Exception as e:
        # If the license file doesn't exist, try to get the license information
        # from the font's metadata
        try:
            click.echo(
                f"  ⚠️  Could not download standard license file for {font_name}: {e}",
                err=True,
            )
            # Create a basic license file with information
            license_text = (
                "This font is from Google Fonts and is used under the Open Font "
                "License (OFL).\n"
                f"Font Name: {font_name}\n"
                "Source: https://fonts.google.com/specimen/"
                f"{font_name.replace(' ', '+')}\n\n"
                "For the full license text, please visit:\n"
                "https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL\n"
            )
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(license_text, encoding="utf-8")
            return True
        except Exception as e2:
            click.echo(
                f"  ❌ Failed to create license file for {font_name}: {e2}", err=True
            )
            return False


def _download_and_extract_google_fonts_zip(
    font_name: str, dest_dir: pathlib.Path
) -> tuple[int, bool]:
    """Attempt to download the family ZIP from Google Fonts and extract files.

    Returns (extracted_file_count, license_found)
    """
    url = (
        f"https://fonts.google.com/download?family={urllib.parse.quote_plus(font_name)}"
    )
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/zip,application/octet-stream,*/*;q=0.8",
        "Referer": "https://fonts.google.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=120, allow_redirects=True)
        if resp.status_code != 200:
            click.echo(f"  ⚠️  ZIP request failed: HTTP {resp.status_code}", err=True)
            return 0, False

        ctype = resp.headers.get("Content-Type", "").lower()
        cdisp = resp.headers.get("Content-Disposition", "")
        if "zip" not in ctype and "filename=" not in cdisp:
            raise ValueError(f"Unexpected content-type: {ctype}")

        data = resp.content
        zf = zipfile.ZipFile(io.BytesIO(data))
        extracted = 0
        license_found = False
        dest_dir.mkdir(parents=True, exist_ok=True)

        for member in zf.namelist():
            lower = member.lower()
            if lower.endswith((".ttf", ".otf", ".ttc", ".woff", ".woff2")):
                target_path = dest_dir / pathlib.Path(member).name
                with zf.open(member) as src, open(target_path, "wb") as out:
                    shutil.copyfileobj(src, out)
                extracted += 1
            if lower.endswith("ofl.txt") and not license_found:
                target_path = dest_dir / "OFL.txt"
                with zf.open(member) as src, open(target_path, "wb") as out:
                    shutil.copyfileobj(src, out)
                license_found = True

        return extracted, license_found

    except Exception as e:
        click.echo(f"  ⚠️  Could not fetch family ZIP: {e}", err=True)
        return 0, False


def _search_google_fonts(query: str, limit: int = 10) -> list:
    """Search Google Fonts by name"""
    fonts_data = _get_google_fonts_api_data()
    query_lower = query.lower()

    matches = []
    for font in fonts_data.get("items", []):
        family = font["family"]
        if query_lower in family.lower():
            matches.append(
                {
                    "family": family,
                    "variants": len(font.get("files", {})),
                    "variants_list": list(font.get("files", {}).keys()),
                    "category": font.get("category", "unknown"),
                }
            )

    return matches[:limit]


def _fetch_css2_variants(font_name: str) -> list[tuple[str, str, str]]:
    """Fetch (style, weight, url) from the CSS2 API (usually WOFF2)."""
    css_url = f"https://fonts.googleapis.com/css2?family={urllib.parse.quote_plus(font_name)}&display=swap"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/css,*/*;q=0.1",
        "Referer": "https://fonts.google.com/",
    }
    try:
        r = requests.get(css_url, headers=headers, timeout=20)
        if r.status_code != 200:
            return []
        css = r.text
        # Regex to capture style, weight, and url(...) – compact form across lines
        pattern = re.compile(
            r"font-style:\s*(normal|italic).*?font-weight:\s*(\d+).*?src:[^;]*?url\(([^)]+)\)",
            re.IGNORECASE | re.DOTALL,
        )
        matches = pattern.findall(css)
        # De-dup by (style, weight, url)
        seen = set()
        out = []
        for style, weight, url in matches:
            key = (style, weight, url)
            if key in seen:
                continue
            seen.add(key)
            out.append((style, weight, url))
        return out
    except Exception:
        return []


def _download_css2_woff_variants(
    font_name: str, dest_dir: pathlib.Path
) -> list[tuple[str, str, pathlib.Path]]:
    """Download WOFF/WOFF2 variants using the CSS2 API.

    Strategy:
    - Request explicit weights (100..900) for normal and italic to get discrete files.
    - Fallback to the plain CSS2 endpoint to capture any remaining entries.

    Returns list of (style, weight, saved_path)
    """
    weights = ["100", "200", "300", "400", "500", "600", "700", "800", "900"]
    pairs = [f"0,{w}" for w in weights] + [f"1,{w}" for w in weights]
    css_url = (
        f"https://fonts.googleapis.com/css2?family="
        f"{urllib.parse.quote_plus(font_name)}:ital,wght@{';'.join(pairs)}&display=swap"
    )
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/css,*/*;q=0.1",
        "Referer": "https://fonts.google.com/",
    }

    def parse_css(css_text: str) -> list[tuple[str, str, str]]:
        pattern = re.compile(
            r"font-style:\s*(normal|italic).*?font-weight:\s*(\d+)\s*;.*?src:[^;]*?url\(([^)]+)\)",
            re.IGNORECASE | re.DOTALL,
        )
        return pattern.findall(css_text)

    chosen: dict[tuple[str, str], str] = {}

    try:
        r = requests.get(css_url, headers=headers, timeout=20)
        if r.status_code == 200:
            for style, weight, url in parse_css(r.text):
                key = (style, weight)
                if key not in chosen:
                    chosen[key] = url
    except Exception:
        pass

    # Fallback: plain CSS2 query (catches variable-font single entries or missed ones)
    if not chosen:
        for style, weight, url in _fetch_css2_variants(font_name):
            key = (style, weight)
            if key not in chosen:
                chosen[key] = url

    saved: list[tuple[str, str, pathlib.Path]] = []
    for (style, weight), url in chosen.items():
        ext = (
            "woff2"
            if url.endswith(".woff2")
            else ("woff" if url.endswith(".woff") else "woff2")
        )
        filename = f"{font_name.replace(' ', '')}-{weight}-{style}.{ext}"
        target = dest_dir / filename
        if _download_font_file(url, target):
            saved.append((style, weight, target))
    return saved


def _generate_scss(
    font_name: str,
    font_dir: pathlib.Path,
    woff_variants: list[tuple[str, str, pathlib.Path]],
):
    """Generate a basic SCSS file with @font-face rules for variants."""
    scss_dir = pathlib.Path("assets/scss")
    scss_dir.mkdir(parents=True, exist_ok=True)
    scss_file = scss_dir / f"{font_name.replace(' ', '_')}.scss"

    # Pick a TTF/OTF/TTC file (if any) for fallback src
    ttf_files = (
        list(font_dir.glob("*.ttf"))
        + list(font_dir.glob("*.otf"))
        + list(font_dir.glob("*.ttc"))
    )
    ttf_fallback = ttf_files[0].name if ttf_files else None

    lines = [f"// Font: {font_name}"]
    for style, weight, path in woff_variants:
        rel_woff = f"../fonts/{font_name}/{path.name}"
        lines.append("@font-face {")
        lines.append(f"  font-family: '{font_name}';")
        lines.append(f"  font-style: {style};")
        lines.append(f"  font-weight: {weight};")
        if ttf_fallback:
            rel_ttf = f"../fonts/{font_name}/{ttf_fallback}"
            lines.append(
                f"  src: url('{rel_woff}') format('woff2'), "
                f"url('{rel_ttf}') format('truetype');"
            )
        else:
            lines.append(f"  src: url('{rel_woff}') format('woff2');")
        lines.append("}")
        lines.append("")

    if not woff_variants and ttf_fallback:
        # Minimal single-face rule if only TTF exists
        rel_ttf = f"../fonts/{font_name}/{ttf_fallback}"
        lines.append("@font-face {")
        lines.append(f"  font-family: '{font_name}';")
        lines.append("  font-style: normal;")
        lines.append("  font-weight: 400;")
        lines.append(f"  src: url('{rel_ttf}') format('truetype');")
        lines.append("}")

    scss_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _download_full_family(font_name: str, force: bool) -> None:
    assets_fonts = pathlib.Path("assets/fonts")
    font_dir = assets_fonts / font_name

    # Check if already installed
    if font_dir.exists() and not force:
        existing_files = (
            list(font_dir.glob("*.ttf"))
            + list(font_dir.glob("*.otf"))
            + list(font_dir.glob("*.ttc"))
            + list(font_dir.glob("*.woff2"))
            + list(font_dir.glob("*.woff"))
        )
        if existing_files:
            click.echo(
                f"✅ Font '{font_name}' already installed ({len(existing_files)} files)"
            )
            return

    # Get Google Fonts data and validate family exists (for user feedback)
    fonts_data = _get_google_fonts_api_data()
    font_info = None
    for font in fonts_data.get("items", []):
        if font["family"].lower() == font_name.lower():
            font_info = font
            break
    if not font_info:
        click.echo(f"❌ Font '{font_name}' not found in Google Fonts")
        return

    # ZIP first
    click.echo("📦 Attempting family ZIP download (TTF/OTF/TTC + license)...")
    extracted_count, license_found = _download_and_extract_google_fonts_zip(
        font_name, font_dir
    )
    if extracted_count > 0:
        if not license_found:
            _ = _download_license_file(font_name, font_dir / "OFL.txt")
        click.echo(f"✅ Extracted {extracted_count} files from ZIP for '{font_name}'")
    else:
        # GitHub fallback
        click.echo("📚 ZIP failed; trying google/fonts GitHub repository...")
        repo_count, repo_license = _download_from_gfonts_repo(font_name, font_dir)
        if repo_count > 0:
            if not repo_license:
                _ = _download_license_file(font_name, font_dir / "OFL.txt")
            click.echo(
                f"✅ Downloaded {repo_count} files from google/fonts for '{font_name}'"
            )
        else:
            click.echo("⚠️  Could not obtain TTF/OTF/TTC via ZIP or repo")

    # Add WOFF/WOFF2 via CSS2
    click.echo("🌐 Fetching WOFF/WOFF2 variants from CSS2...")
    woff_variants = _download_css2_woff_variants(font_name, font_dir)
    if woff_variants:
        click.echo(f"✅ Added {len(woff_variants)} WOFF variants")
    else:
        click.echo("⚠️  No WOFF variants fetched")

    # Ensure license exists
    license_path = font_dir / "OFL.txt"
    if not license_path.exists():
        _ = _download_license_file(font_name, license_path)

    # Generate SCSS
    _generate_scss(font_name, font_dir, woff_variants)
    click.echo(
        f"🧬 SCSS snippet written to assets/scss/{font_name.replace(' ', '_')}.scss"
    )


@click.group()
def main():
    """CLI tool for searching and downloading Google Webfonts."""
    pass


@main.command()
@click.argument("query")
@click.option("--limit", default=10, help="Number of results to show")
@click.option("--details", is_flag=True, help="Show detailed variant information")
def search(query, limit, details):
    """Search for Google Webfonts by name."""
    click.echo(f"🔍 Searching Google Fonts for: '{query}'")

    matches = _search_google_fonts(query, limit)

    if not matches:
        click.echo(f"❌ No fonts found matching '{query}'")
        return

    click.echo(f"📊 Found {len(matches)} matching fonts:")

    for i, font in enumerate(matches, 1):
        family = font["family"]
        variants_count = font["variants"]
        category = font["category"].title()

        click.echo(f"  {i:2d}. {family}")
        click.echo(f"      📂 {category} • {variants_count} variants")

        if details:
            variants_list = ", ".join(
                font["variants_list"][:8]
            )  # Show first 8 variants
            if len(font["variants_list"]) > 8:
                variants_list += "..."
            click.echo(f"      🔤 Variants: {variants_list}")


@main.command()
@click.argument("font_names", nargs=-1)
@click.option(
    "--file",
    "names_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to file with font names (one per line)",
)
@click.option("--output", default="fonts", help="Output directory: fonts or web")
@click.option("--force", is_flag=True, help="Reinstall even if font already exists")
def download(font_names, names_file, output, force):
    """Download and install Google Webfonts to assets/fonts/.

    Accepts multiple FONT_NAMES or --file to read names (one per line).
    """
    names: list[str] = []
    if font_names:
        names.extend(list(font_names))
    if names_file:
        try:
            with open(names_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        names.append(line)
        except OSError as e:
            click.echo(f"❌ Failed to read names file: {e}")
            return

    # Default to help if no names provided
    if not names:
        click.echo("❌ No font names provided. Pass one or more names, or use --file.")
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return

    # Deduplicate while preserving order
    seen = set()
    unique_names = []
    for n in names:
        low = n.lower()
        if low not in seen:
            seen.add(low)
            unique_names.append(n)

    for n in unique_names:
        click.echo(f"\n🔤 Processing '{n}'...")
        _download_full_family(n, force)
    return


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable form"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


@main.command()
@click.argument("font_name")
def generate_scss(font_name):
    """Generate SCSS snippet for the font."""
    # Get Google Fonts data
    fonts_data = _get_google_fonts_api_data()

    # Find the font
    font_info = None
    for font in fonts_data.get("items", []):
        if font["family"].lower() == font_name.lower():
            font_info = font
            break

    if not font_info:
        click.echo(f"❌ Font '{font_name}' not found in Google Fonts")
        return

    variants_list = list(font_info.get("files", {}).keys())

    scss_dir = os.path.join(os.getcwd(), "assets", "scss")
    os.makedirs(scss_dir, exist_ok=True)
    scss_file = os.path.join(scss_dir, f"{font_name.replace(' ', '_')}.scss")
    scss_content = f"// Font: {font_name}\n"
    for variant in variants_list:
        weight = "normal"
        style = "normal"
        if "italic" in variant:
            style = "italic"
        if "bold" in variant or "700" in variant:
            weight = "bold"
        scss_content += f"""
@font-face {{
    font-family: '{font_name}';
    src: url('../fonts/{font_name.replace(" ", "_")}.ttf') format('truetype');
    font-weight: {weight};
    font-style: {style};
}}
"""
    scss_content += (
        f"\n// Usage\n// .my-class {{\n"
        f"//     font-family: '{font_name}', sans-serif;\n// }}\n"
    )

    with open(scss_file, "w") as f:
        f.write(scss_content)
    click.echo(f"Generated SCSS snippet at {scss_file}")


@main.command()
@click.option(
    "--repo",
    default="sanderboer/google-font-downloader",
    help="GitHub repository for catalog releases",
)
@click.option("--force", is_flag=True, help="Force update even if cache is fresh")
def update_catalog(repo, force):
    """Update local font catalog from GitHub releases."""
    cache_dir = pathlib.Path.home() / ".fontdownloader" / "cache"
    cache_file = cache_dir / "google_fonts.json"

    if not force and cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < 3600:  # 1 hour
            click.echo(
                f"✅ Catalog cache is fresh (updated {cache_age / 60:.1f} minutes ago)"
            )
            return

    click.echo(f"📡 Updating catalog from GitHub releases ({repo})...")

    try:
        from . import download_catalog

        temp_file = cache_dir / "temp_catalog.json"
        cache_dir.mkdir(parents=True, exist_ok=True)

        if download_catalog.download_latest_catalog(
            repo=repo, output_path=str(temp_file)
        ):
            # Validate and transform catalog
            with open(temp_file, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)

            families = len(catalog_data.get("items", []))
            if families < 10:  # Basic validation
                raise ValueError(f"Catalog seems incomplete: only {families} families")

            # Transform to API format and cache
            api_data = {"items": catalog_data.get("items", [])}
            cache_file.write_text(json.dumps(api_data, indent=2), encoding="utf-8")
            temp_file.unlink(missing_ok=True)

            click.echo(f"✅ Catalog updated: {families} font families available")
        else:
            raise RuntimeError("Failed to download catalog from releases")

    except Exception as e:
        click.echo(f"❌ Failed to update catalog: {e}", err=True)
        click.echo(
            "💡 The CLI will fall back to Google Fonts API when needed", err=True
        )


@main.command()
@click.option(
    "--limit", default=100, help="Maximum number of fonts to download (default: 100)"
)
@click.option("--force", is_flag=True, help="Reinstall even if fonts already exist")
def download_all(limit, force):
    """Download a large set of popular Google Webfonts using the consolidated flow."""
    click.echo(f"📥 Downloading top {limit} Google Fonts...")

    fonts_data = _get_google_fonts_api_data()
    fonts_to_download = fonts_data.get("items", [])[:limit]

    click.echo(f"📊 Will download {len(fonts_to_download)} fonts")

    success_count = 0
    for font in fonts_to_download:
        font_name = font["family"]
        click.echo(f"\n🔤 Processing '{font_name}'...")
        _download_full_family(font_name, force)

        # Consider success if directory contains any font files
        font_dir = pathlib.Path("assets/fonts") / font_name
        files = (
            list(font_dir.glob("*.ttf"))
            + list(font_dir.glob("*.otf"))
            + list(font_dir.glob("*.ttc"))
            + list(font_dir.glob("*.woff*"))
        )
        if files:
            success_count += 1

    click.echo(
        f"\n🎉 Downloaded {success_count}/{len(fonts_to_download)} fonts successfully!"
    )


if __name__ == "__main__":
    main()

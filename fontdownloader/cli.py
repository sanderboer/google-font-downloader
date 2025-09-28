import os
import shutil
import pathlib
import json
import time
import urllib.request
import urllib.parse
import re

import click
import requests


def _get_google_fonts_api_data() -> dict:
    """Fetch Google Fonts API data. Returns cached data or fetches from API."""
    cache_dir = pathlib.Path.home() / '.fontdownloader' / 'cache'
    cache_file = cache_dir / 'google_fonts.json'
    
    # Check cache freshness (24 hours)
    if cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < 86400:  # 24 hours
            try:
                return json.loads(cache_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                pass
    
    # Fetch from Google Fonts API
    api_url = 'https://www.googleapis.com/webfonts/v1/webfonts?sort=popularity'
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        # Cache the result
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return data
        
    except Exception as e:
        click.echo(f"⚠️  Failed to fetch Google Fonts data: {e}", err=True)
        click.echo("Using offline fallback list...", err=True)
        
        # Fallback list of popular fonts with updated URLs (using CSS API derived)
        return {
            'items': [
                {'family': 'Inter', 'variants': ['regular', '700'], 'files': {'regular': 'https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2', '700': 'https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2'}},
                {'family': 'Roboto', 'variants': ['regular', '700'], 'files': {'regular': 'https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.woff2', '700': 'https://fonts.gstatic.com/s/roboto/v30/KFOlCnqEu92Fr1MmWUlfBBc4.woff2'}},
                {'family': 'Open Sans', 'variants': ['regular', '700'], 'files': {'regular': 'https://fonts.gstatic.com/s/opensans/v44/memvYaGs126MiZpBA-UvWbX2vVnXBbObj2OVTS-muw.woff2', '700': 'https://fonts.gstatic.com/s/opensans/v44/memvYaGs126MiZpBA-UvWbX2vVnXBbObj2OVTS-muw.woff2'}},
                {'family': 'Lora', 'variants': ['regular'], 'files': {'regular': 'https://fonts.gstatic.com/s/lora/v37/0QI6MX1D_JOuGQbT0gvTJPa787weuxJBkq0.woff2'}},
                {'family': 'Playfair Display', 'variants': ['regular'], 'files': {'regular': 'https://fonts.gstatic.com/s/playfairdisplay/v30/nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKdFvXDXbtXK-F2qC0s.woff2'}}
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


def _search_google_fonts(query: str, limit: int = 10) -> list:
    """Search Google Fonts by name"""
    fonts_data = _get_google_fonts_api_data()
    query_lower = query.lower()
    
    matches = []
    for font in fonts_data.get('items', []):
        family = font['family']
        if query_lower in family.lower():
            matches.append({
                'family': family,
                'variants': len(font.get('files', {})),
                'variants_list': list(font.get('files', {}).keys()),
                'category': font.get('category', 'unknown')
            })
    
    return matches[:limit]


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
        family = font['family']
        variants_count = font['variants']
        category = font['category'].title()
        
        click.echo(f"  {i:2d}. {family}")
        click.echo(f"      📂 {category} • {variants_count} variants")
        
        if details:
            variants_list = ', '.join(font['variants_list'][:8])  # Show first 8 variants
            if len(font['variants_list']) > 8:
                variants_list += "..."
            click.echo(f"      🔤 Variants: {variants_list}")


@main.command()
@click.argument("font_name")
@click.option("--output", default="fonts", help="Output directory: fonts or web")
@click.option(
    "--variants",
    help="Comma-separated list of variants (e.g., regular,700,italic). If not specified, downloads common variants.",
)
@click.option("--force", is_flag=True, help="Reinstall even if font already exists")
def download(font_name, output, variants, force):
    """Download and install a Google Webfont to assets/fonts/."""
    assets_fonts = pathlib.Path('assets/fonts')
    font_dir = assets_fonts / font_name
    
    # Check if already installed
    if font_dir.exists() and not force:
        existing_files = list(font_dir.glob('*.ttf')) + list(font_dir.glob('*.otf')) + list(font_dir.glob('*.ttc')) + list(font_dir.glob('*.woff2')) + list(font_dir.glob('*.woff'))
        if existing_files:
            click.echo(f"✅ Font '{font_name}' already installed ({len(existing_files)} files)")
            return
    
    # Get Google Fonts data
    fonts_data = _get_google_fonts_api_data()
    
    # Find the font
    font_info = None
    for font in fonts_data.get('items', []):
        if font['family'].lower() == font_name.lower():
            font_info = font
            break
    
    if not font_info:
        click.echo(f"❌ Font '{font_name}' not found in Google Fonts")
        return
    
    # Determine variants to download
    available_variants = list(font_info.get('files', {}).keys())
    if not variants:
        # Default to common variants
        variants = ['regular']
        if '700' in available_variants:
            variants.append('700')
        if 'italic' in available_variants:
            variants.append('italic')
    else:
        variants = [v.strip() for v in variants.split(',')]
    
    # Filter to available variants
    variants = [v for v in variants if v in available_variants]
    if not variants:
        click.echo(f"❌ No valid variants found for '{font_name}'")
        click.echo(f"Available: {', '.join(available_variants)}")
        return
    
    click.echo(f"📥 Installing '{font_name}' variants: {', '.join(variants)}")
    
    # Download variants
    success_count = 0
    for variant in variants:
        url = font_info['files'][variant]
        
        # Determine file extension from URL
        if url.endswith('.ttf'):
            ext = 'ttf'
        elif url.endswith('.otf'):
            ext = 'otf'
        elif url.endswith('.ttc'):
            ext = 'ttc'
        elif url.endswith('.woff2'):
            ext = 'woff2'
        elif url.endswith('.woff'):
            ext = 'woff'
        else:
            ext = 'ttf'  # Default
        
        # Generate filename
        if variant == 'regular':
            filename = f"{font_name.replace(' ', '')}-Regular.{ext}"
        elif variant.isdigit():
            filename = f"{font_name.replace(' ', '')}-{variant}.{ext}"  
        else:
            filename = f"{font_name.replace(' ', '')}-{variant.title()}.{ext}"
        
        dest_path = font_dir / filename
        
        click.echo(f"  📁 {filename}...", nl=False)
        if _download_font_file(url, dest_path):
            size = _format_size(dest_path.stat().st_size)
            click.echo(f"✅ ({size})")
            success_count += 1
        else:
            click.echo("❌")
    
    if success_count > 0:
        click.echo(f"✅ Installed {success_count}/{len(variants)} variants of '{font_name}'")
    else:
        click.echo(f"❌ Failed to install '{font_name}'")


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
@click.option(
    "--variants", default="regular", help="Font variants (e.g., regular,italic)"
)
def generate_scss(font_name, variants):
    """Generate SCSS snippet for the font."""
    scss_dir = os.path.join(os.getcwd(), "assets", "scss")
    os.makedirs(scss_dir, exist_ok=True)
    scss_file = os.path.join(scss_dir, f"{font_name.replace(' ', '_')}.scss")

    variants_list = [v.strip() for v in variants.split(",")]
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
@click.option("--limit", default=100, help="Maximum number of fonts to download (default: 100)")
@click.option("--force", is_flag=True, help="Reinstall even if fonts already exist")
def download_all(limit, force):
    """Download a large set of popular Google Webfonts."""
    click.echo(f"📥 Downloading top {limit} Google Fonts...")
    
    fonts_data = _get_google_fonts_api_data()
    fonts_to_download = fonts_data.get('items', [])[:limit]
    
    click.echo(f"📊 Will download {len(fonts_to_download)} fonts")
    
    success_count = 0
    for font in fonts_to_download:
        font_name = font['family']
        click.echo(f"\n🔤 Processing '{font_name}'...")
        
        # Use the download function logic
        assets_fonts = pathlib.Path('assets/fonts')
        font_dir = assets_fonts / font_name
        
        if font_dir.exists() and not force:
            existing_files = list(font_dir.glob('*.ttf')) + list(font_dir.glob('*.otf')) + list(font_dir.glob('*.ttc'))
            if existing_files:
                click.echo(f"  ✅ Already installed ({len(existing_files)} files)")
                success_count += 1
                continue
        
        # Determine variants to download
        available_variants = list(font.get('files', {}).keys())
        variants = ['regular']
        if '700' in available_variants:
            variants.append('700')
        if 'italic' in available_variants:
            variants.append('italic')
        
        # Download variants
        variant_success_count = 0
        for variant in variants:
            if variant in available_variants:
                url = font['files'][variant]
                
                # Determine file extension
                if url.endswith('.ttf'):
                    ext = 'ttf'
                elif url.endswith('.otf'):
                    ext = 'otf'
                elif url.endswith('.ttc'):
                    ext = 'ttc'
                else:
                    ext = 'ttf'
                
                # Generate filename
                if variant == 'regular':
                    filename = f"{font_name.replace(' ', '')}-Regular.{ext}"
                elif variant.isdigit():
                    filename = f"{font_name.replace(' ', '')}-{variant}.{ext}"  
                else:
                    filename = f"{font_name.replace(' ', '')}-{variant.title()}.{ext}"
                
                dest_path = font_dir / filename
                
                if _download_font_file(url, dest_path):
                    variant_success_count += 1
        
        if variant_success_count > 0:
            click.echo(f"  ✅ Installed {variant_success_count} variants")
            success_count += 1
        else:
            click.echo(f"  ❌ Failed to install")
    
    click.echo(f"\n🎉 Downloaded {success_count}/{len(fonts_to_download)} fonts successfully!")


if __name__ == "__main__":
    main()

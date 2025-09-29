# Comprehensive offline fallback for Google Fonts API failure
# This replaces the limited fallback in cli.py:142-183

def get_comprehensive_offline_fallback():
    """
    Returns a comprehensive offline fallback with 25+ popular Google Fonts.

    Structure matches Google Fonts API format but with minimal data needed
    for the fontdownloader to work via GitHub repo + CSS2 fallbacks.
    """
    return {
        "items": [
            # Sans-serif fonts
            {
                "family": "Inter",
                "variants": ["100", "200", "300", "regular", "500", "600", "700", "800", "900", "100italic", "200italic", "300italic", "italic", "500italic", "600italic", "700italic", "800italic", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Roboto",
                "variants": ["100", "100italic", "300", "300italic", "regular", "italic", "500", "500italic", "700", "700italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Open Sans",
                "variants": ["300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Lato",
                "variants": ["100", "100italic", "300", "300italic", "regular", "italic", "700", "700italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Montserrat",
                "variants": ["100", "100italic", "200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Source Sans Pro",
                "variants": ["200", "200italic", "300", "300italic", "regular", "italic", "600", "600italic", "700", "700italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Raleway",
                "variants": ["100", "100italic", "200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Nunito",
                "variants": ["200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Poppins",
                "variants": ["100", "100italic", "200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Ubuntu",
                "variants": ["300", "300italic", "regular", "italic", "500", "500italic", "700", "700italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Oswald",
                "variants": ["200", "300", "regular", "500", "600", "700"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Work Sans",
                "variants": ["100", "200", "300", "regular", "500", "600", "700", "800", "900", "100italic", "200italic", "300italic", "italic", "500italic", "600italic", "700italic", "800italic", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Rubik",
                "variants": ["300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Fira Sans",
                "variants": ["100", "100italic", "200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "DM Sans",
                "variants": ["regular", "italic", "500", "500italic", "700", "700italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Manrope",
                "variants": ["200", "300", "regular", "500", "600", "700", "800"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Noto Sans",
                "variants": ["regular", "italic", "700", "700italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Roboto Condensed",
                "variants": ["300", "300italic", "regular", "italic", "700", "700italic"],
                "category": "sans-serif",
                "files": {}
            },
            {
                "family": "Kanit",
                "variants": ["100", "100italic", "200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "sans-serif",
                "files": {}
            },

            # Serif fonts
            {
                "family": "Playfair Display",
                "variants": ["regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "serif",
                "files": {}
            },
            {
                "family": "Merriweather",
                "variants": ["300", "300italic", "regular", "italic", "700", "700italic", "900", "900italic"],
                "category": "serif",
                "files": {}
            },
            {
                "family": "Lora",
                "variants": ["regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic"],
                "category": "serif",
                "files": {}
            },
            {
                "family": "Crimson Text",
                "variants": ["regular", "italic", "600", "600italic", "700", "700italic"],
                "category": "serif",
                "files": {}
            },

            # Monospace fonts
            {
                "family": "Source Code Pro",
                "variants": ["200", "200italic", "300", "300italic", "regular", "italic", "500", "500italic", "600", "600italic", "700", "700italic", "800", "800italic", "900", "900italic"],
                "category": "monospace",
                "files": {}
            },
            {
                "family": "Inconsolata",
                "variants": ["200", "300", "regular", "500", "600", "700", "800", "900"],
                "category": "monospace",
                "files": {}
            },

            # Additional popular/niche fonts
            {
                "family": "Fauna One",
                "variants": ["regular"],
                "category": "serif",
                "files": {}
            },
            {
                "family": "JetBrains Mono",
                "variants": ["100", "200", "300", "regular", "500", "600", "700", "800", "100italic", "200italic", "300italic", "italic", "500italic", "600italic", "700italic", "800italic"],
                "category": "monospace",
                "files": {}
            },
            {
                "family": "Mukti",
                "variants": ["regular"],
                "category": "sans-serif",
                "files": {}
            },
        ]
    }


if __name__ == "__main__":
    # Test the structure
    data = get_comprehensive_offline_fallback()
    print(f"Total fonts: {len(data['items'])}")

    categories = {}
    for font in data["items"]:
        cat = font["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(font["family"])

    for cat, fonts in categories.items():
        print(f"\n{cat.title()} ({len(fonts)}):")
        for font in fonts:
            print(f"  - {font}")

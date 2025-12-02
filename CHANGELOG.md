# Changelog

Alle noemenswaardige wijzigingen in dit project worden in dit bestand gedocumenteerd.

## [0.3.0] - 2025-12-02

### Toegevoegd
- Detectie en optimalisatie voor **variable fonts** op basis van CSS2-responses.
- Ondersteuning om variable fonts slechts één keer per stijl te downloaden, met juiste `font-weight` ranges in de gegenereerde SCSS.
- Optionele **TTF/OTF → WOFF/WOFF2 conversie** via `fontTools` met de nieuwe CLI-vlag `--convert-ttf` voor `download` en `download-all`.
- Nieuwe helper `_convert_ttf_to_woff` en integratie in `_download_full_family`.
- Uitgebreide documentatie in `README.md` over variable fonts, subsets vs. volledige unicode, en troubleshooting.
- Nieuw document `FONT_FORMATS_EXPLAINED.md` met een overzicht van de verschillende fontformaten en use-cases.

### Gewijzigd
- `_download_css2_woff_variants` retourneert nu tuples met een extra boolean die aangeeft of het om een variable font gaat.
- `_generate_scss` ondersteunt nu zowel statische als variable varianten en genereert correcte `@font-face` regels met gewicht-ranges.
- CLI-commando's `download` en `download-all` accepteren nu een `--convert-ttf` vlag en geven die door aan `_download_full_family`.
- `.gitignore` uitgebreid met `tmp-resources`.

### Opgelost
- Tests in `tests/test_cli.py` bijgewerkt en gefixt om met de nieuwe tuple-structuur en variable font-ondersteuning te werken.
- Ruff-waarschuwing rond een ongebruikte loopvariabele in `_download_css2_woff_variants` opgelost.

## [0.2.1] - 2024-xx-xx

### Toegevoegd
- Basis CLI-functionaliteit om Google Fonts te zoeken en te downloaden.
- Download van TTF/OTF/TTC + OFL-licentiebestanden en WOFF/WOFF2 via de CSS2 API.
- Generatie van eenvoudige SCSS-bestanden per fontfamilie.

### Overig
- Eerste publieke release met basisfunctionaliteit.

## [0.2.0] - 2024-xx-xx

> Historische versies zijn samengevat op hoog niveau; exacte data en details zijn te vinden in de gitgeschiedenis.

### Toegevoegd
- Diverse verbeteringen aan de download- en SCSS-generatie-flow.
- Uitgebreidere testdekking en linterconfiguratie.

from pathlib import Path

import pytest

from fontdownloader import cli


def test_generate_scss_creates_rules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Arrange
    font_name = "My Test Font"
    cwd = tmp_path
    monkeypatch.chdir(cwd)

    font_dir = cwd / "assets" / "fonts" / font_name
    font_dir.mkdir(parents=True)

    # Create fallback TTF and one WOFF2 variant
    ttf_path = font_dir / "MyTestFont-Regular.ttf"
    ttf_path.write_bytes(b"")
    woff_path = font_dir / "MyTestFont-400-normal.woff2"
    woff_path.write_bytes(b"")

    # Act
    cli._generate_scss(font_name, font_dir, [("normal", "400", woff_path)])

    # Assert
    scss_file = cwd / "assets" / "scss" / "My_Test_Font.scss"
    assert scss_file.exists(), "SCSS file was not created"
    content = scss_file.read_text(encoding="utf-8")
    # Should reference both WOFF2 and TTF fallback
    assert "format('woff2')" in content
    assert "format('truetype')" in content
    # Should use normalized font directory in relative paths
    assert "../fonts/My Test Font/" in content


def test_download_css2_woff_variants_dedup_and_naming(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Arrange
    font_name = "Space Font"
    dest_dir = tmp_path / "assets" / "fonts" / font_name

    # Mock variant fetcher with duplicate (style,weight) entries
    def fake_fetch(name: str):
        assert name == font_name
        return [
            ("normal", "400", "https://example.com/a.woff2"),
            ("normal", "400", "https://example.com/b.woff2"),
            ("italic", "700", "https://example.com/c.woff"),
        ]

    # Mock downloader to write empty file
    def fake_dl(url: str, dest: Path) -> bool:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"")
        return True

    monkeypatch.setattr(cli, "_fetch_css2_variants", fake_fetch)
    monkeypatch.setattr(cli, "_download_font_file", fake_dl)

    # Act
    saved = cli._download_css2_woff_variants(font_name, dest_dir)

    # Assert
    names = sorted(p.name for _, _, p in saved)
    # Dedup keeps one 400-normal and includes 700-italic
    assert names == ["SpaceFont-400-normal.woff2", "SpaceFont-700-italic.woff"]
    for _, _, p in saved:
        assert p.exists(), f"Expected file to exist: {p}"

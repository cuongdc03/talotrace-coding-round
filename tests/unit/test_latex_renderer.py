from pathlib import Path

from app.pipeline.latex_renderer import LatexRenderer


def test_render_latex_simple():
    renderer = LatexRenderer()
    png_path = renderer.render_to_png(r"\mathrm{pH} = -\log_{10}[\mathrm{H}^+]")
    assert png_path is not None
    assert isinstance(png_path, Path)
    assert png_path.exists()
    assert png_path.suffix == ".png"
    assert png_path.stat().st_size > 0


def test_render_latex_caching():
    renderer = LatexRenderer()
    formula = r"\mathrm{H}^+ + \mathrm{OH}^- \rightarrow \mathrm{H}_2\mathrm{O}"
    path1 = renderer.render_to_png(formula)
    path2 = renderer.render_to_png(formula)
    assert path1 == path2
    assert path1.exists()


def test_render_latex_fallback_on_invalid():
    renderer = LatexRenderer()
    # Invalid syntax should not crash; it should fall back cleanly
    path = renderer.render_to_png(r"\invalid_command{{{")
    assert path is not None
    assert path.exists()

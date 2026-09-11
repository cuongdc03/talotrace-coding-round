"""Unit tests for ManimRenderer code generation and availability checks."""

from app.pipeline.manim_renderer import ManimRenderer


def test_manim_renderer_code_generation_ph_scale():
    renderer = ManimRenderer()
    code = renderer._generate_ph_scale_manim_code(duration=15.0)

    assert "class ChemistryScene(Scene):" in code
    assert "Line" in code
    assert "spectrum" in code
    assert "Lemon Juice" in code
    assert "Pure Water" in code
    assert "Bleach" in code


def test_manim_renderer_code_generation_covalent_bonds():
    renderer = ManimRenderer()
    code = renderer._generate_covalent_bonds_manim_code(duration=15.0)

    assert "class ChemistryScene(Scene):" in code
    assert "Why Atoms Form Covalent Bonds" in code
    assert "H+" in code
    assert "valence" in code.lower()
    assert "shared" in code.lower()


def test_manim_renderer_code_generation_ionic_vs_covalent():
    renderer = ManimRenderer()
    code = renderer._generate_ionic_vs_covalent_manim_code(duration=15.0)

    assert "class ChemistryScene(Scene):" in code
    assert "IONIC" in code
    assert "COVALENT" in code
    assert "Na" in code
    assert "Cl" in code
    assert "Na⁺" in code or "Na+" in code

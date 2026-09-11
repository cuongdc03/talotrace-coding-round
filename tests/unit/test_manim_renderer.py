from pathlib import Path

from app.pipeline.manim_renderer import ManimRenderer


def test_manim_renderer_code_generation_all_8_topics():
    renderer = ManimRenderer()
    dummy_eq = Path("/tmp/dummy_eq.png")

    generators = [
        renderer._generate_ph_scale_manim_code(30.0, dummy_eq),
        renderer._generate_covalent_bonds_manim_code(30.0, dummy_eq),
        renderer._generate_ionic_vs_covalent_manim_code(30.0, dummy_eq),
        renderer._generate_atomic_structure_manim_code(30.0, dummy_eq),
        renderer._generate_exo_vs_endothermic_manim_code(30.0, dummy_eq),
        renderer._generate_periodic_trends_manim_code(30.0, dummy_eq),
        renderer._generate_states_of_matter_manim_code(30.0, dummy_eq),
        renderer._generate_acid_base_neutralization_manim_code(30.0, dummy_eq),
        renderer._generate_stem_explainer_manim_code(30.0, dummy_eq),
    ]

    for code in generators:
        assert "class ChemistryScene(Scene):" in code
        assert "ImageMobject" in code
        assert 'self.camera.background_color = "#0B0F19"' in code
        assert "self.play(" in code

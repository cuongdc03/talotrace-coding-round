"""Unit tests for chemistry visual compositor."""

from pathlib import Path

from PIL import Image

from app.models.script import Scene, SupportedTopic
from app.pipeline.visual_compositor import VisualCompositor


def test_render_ph_spectrum_frame(tmp_path: Path):
    compositor = VisualCompositor()
    scene = Scene(
        scene_id=1,
        title="The 0 to 14 Spectrum",
        narration="The pH scale measures acidity from 0 to 14.",
        visual_type="ph_spectrum",
        key_takeaway="pH ranges from 0 (acidic) to 14 (basic).",
    )
    output_path = tmp_path / "ph_frame.png"
    compositor.render_scene_frame(scene, SupportedTopic.PH_SCALE, output_path)

    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.size == (1920, 1080)
        assert img.mode == "RGB"


def test_render_covalent_frame(tmp_path: Path):
    compositor = VisualCompositor()
    scene = Scene(
        scene_id=2,
        title="Sharing Electron Pairs",
        narration="Atoms overlap outer shells to share electrons.",
        visual_type="covalent_sharing",
        key_takeaway="Shared electron pairs form covalent bonds.",
    )
    output_path = tmp_path / "covalent_frame.png"
    compositor.render_scene_frame(scene, SupportedTopic.COVALENT_BONDS, output_path)

    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.size == (1920, 1080)


def test_render_ionic_vs_covalent_frame(tmp_path: Path):
    compositor = VisualCompositor()
    scene = Scene(
        scene_id=4,
        title="Key Physical Properties",
        narration="Ionic compounds form rigid crystal lattices.",
        visual_type="comparison_table",
        key_takeaway="Ionic compounds form lattices; covalent form molecules.",
    )
    output_path = tmp_path / "comparison_frame.png"
    compositor.render_scene_frame(scene, SupportedTopic.IONIC_VS_COVALENT, output_path)

    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.size == (1920, 1080)

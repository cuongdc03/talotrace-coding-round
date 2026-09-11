"""Manim-based mathematical and physics animation engine for chemistry videos."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from app.models.script import SupportedTopic

logger = logging.getLogger(__name__)


class ManimRenderer:
    """Renders 3Blue1Brown-style vector chemistry animations using Manim."""

    def __init__(self, quality: str = "l", fps: int = 24) -> None:
        """
        quality: 'l' (480p, fastest), 'm' (720p), 'h' (1080p full HD).
        Default to 'm' for optimal balance of speed and high visual fidelity.
        """
        self.quality = quality
        self.fps = fps
        venv_manim = Path(__file__).resolve().parent.parent.parent / ".venv" / "bin" / "manim"
        self.manim_bin = (
            str(venv_manim) if venv_manim.exists() else (shutil.which("manim") or "manim")
        )

    def is_available(self) -> bool:
        """Check if manim CLI is installed and accessible."""
        if Path(self.manim_bin).exists() and Path(self.manim_bin).is_file():
            return True
        return shutil.which("manim") is not None

    def _generate_ph_scale_manim_code(self, duration: float) -> str:
        """Generate Manim scene script for the pH scale explanation."""
        run_time_per_move = max(1.5, duration / 5.0)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        # Dark aesthetic background
        self.camera.background_color = "#0B0F19"

        # Title
        title = Text("The pH Scale: Acids, Neutral, and Bases", font_size=36, color="#38BDF8")
        title.to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.0)

        # Baseline
        base_line = Line(LEFT * 5, RIGHT * 5, color=WHITE, stroke_width=2).shift(DOWN * 0.9)
        self.play(Create(base_line), run_time=0.5)

        # Gradient spectrum bar
        colors = ["#EF4444", "#F97316", "#FACC15", "#22C55E", "#06B6D4", "#3B82F6", "#A855F7", "#C026D3"]
        spectrum = Rectangle(width=10, height=0.6).shift(DOWN * 0.5)
        spectrum.set_fill(color=colors, opacity=0.85)
        spectrum.set_stroke(width=0)

        # Number labels 0 to 14 (Pure Pango text, no LaTeX required)
        num_mobs = VGroup()
        for i in range(15):
            x = -5.0 + (i / 14.0) * 10.0
            num_txt = Text(str(i), font_size=16, color="#CBD5E1").move_to([x, -1.2, 0])
            tick = Line([x, -0.8, 0], [x, -1.0, 0], color=WHITE, stroke_width=1.5)
            num_mobs.add(num_txt, tick)

        self.play(FadeIn(spectrum), FadeIn(num_mobs), run_time=1.2)

        # Range labels
        acid_label = Text("ACIDIC (H+)", font_size=22, color="#EF4444").next_to(spectrum, UP, buff=0.8).shift(LEFT * 3.5)
        neutral_label = Text("NEUTRAL", font_size=22, color="#22C55E").next_to(spectrum, UP, buff=0.8)
        base_label = Text("ALKALINE (OH-)", font_size=22, color="#A855F7").next_to(spectrum, UP, buff=0.8).shift(RIGHT * 3.5)

        self.play(FadeIn(acid_label), FadeIn(neutral_label), FadeIn(base_label), run_time=1.0)

        # Helper coordinate mapper
        def n2p(val):
            return np.array([-5.0 + (val / 14.0) * 10.0, -0.5, 0])

        # Animated pointer
        pointer = Triangle(color="#FACC15", fill_opacity=1.0).scale(0.25).rotate(PI)
        pointer.move_to(n2p(7) + DOWN * 0.9)

        indicator_text = Text("Pure Water (pH 7)", font_size=24, color="#22C55E").next_to(pointer, DOWN, buff=0.3)
        self.play(FadeIn(pointer), FadeIn(indicator_text), run_time=0.8)

        # Move to Acid (Lemon Juice pH 2)
        target_pos_acid = n2p(2) + DOWN * 0.9
        new_text_acid = Text("Lemon Juice (pH 2 - High [H+])", font_size=24, color="#EF4444").next_to(target_pos_acid, DOWN, buff=0.3)
        self.play(
            pointer.animate.move_to(target_pos_acid),
            Transform(indicator_text, new_text_acid),
            run_time={run_time_per_move},
        )

        # Move to Base (Bleach pH 13)
        target_pos_base = n2p(13) + DOWN * 0.9
        new_text_base = Text("Bleach (pH 13 - High [OH-])", font_size=24, color="#A855F7").next_to(target_pos_base, DOWN, buff=0.3)
        self.play(
            pointer.animate.move_to(target_pos_base),
            Transform(indicator_text, new_text_base),
            run_time={run_time_per_move},
        )

        # Return to Neutral with Logarithmic takeaway
        takeaway = Text("Logarithmic: Each unit = 10x change in ion concentration", font_size=22, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(
            pointer.animate.move_to(n2p(7) + DOWN * 0.9),
            FadeIn(takeaway),
            run_time=1.5,
        )
        self.wait(1.0)
"""

    def _generate_covalent_bonds_manim_code(self, duration: float) -> str:
        """Generate Manim scene script for covalent bonding with orbiting electrons."""
        return """
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Why Atoms Form Covalent Bonds", font_size=36, color="#38BDF8")
        title.to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.0)

        # Hydrogen Atom 1 (Left)
        h1_center = LEFT * 3.5 + UP * 0.2
        nucleus1 = Dot(point=h1_center, radius=0.35, color="#EF4444")
        n1_label = Text("H+", font_size=24, color=WHITE).move_to(h1_center)
        atom1_group = VGroup(nucleus1, n1_label)
        shell1 = Circle(radius=1.4, color="#38BDF8", stroke_width=2).move_to(h1_center)
        electron1 = Dot(point=h1_center + UP * 1.4, radius=0.14, color="#FACC15")

        # Hydrogen Atom 2 (Right)
        h2_center = RIGHT * 3.5 + UP * 0.2
        nucleus2 = Dot(point=h2_center, radius=0.35, color="#EF4444")
        n2_label = Text("H+", font_size=24, color=WHITE).move_to(h2_center)
        atom2_group = VGroup(nucleus2, n2_label)
        shell2 = Circle(radius=1.4, color="#38BDF8", stroke_width=2).move_to(h2_center)
        electron2 = Dot(point=h2_center + DOWN * 1.4, radius=0.14, color="#FACC15")

        subtitle = Text("Isolated atoms seek a full valence shell (Octet/Duet Rule)", font_size=22, color="#94A3B8")
        subtitle.next_to(title, DOWN, buff=0.3)

        self.play(
            FadeIn(atom1_group), Create(shell1), FadeIn(electron1),
            FadeIn(atom2_group), Create(shell2), FadeIn(electron2),
            FadeIn(subtitle),
            run_time=1.5,
        )

        # Move atoms toward each other to overlap shells
        overlap_h1 = LEFT * 0.9 + UP * 0.2
        overlap_h2 = RIGHT * 0.9 + UP * 0.2

        shared_subtitle = Text("Valence shells overlap: mutually sharing 1 electron pair", font_size=22, color="#38BDF8")
        shared_subtitle.next_to(title, DOWN, buff=0.3)

        self.play(
            atom1_group.animate.move_to(overlap_h1),
            shell1.animate.move_to(overlap_h1),
            atom2_group.animate.move_to(overlap_h2),
            shell2.animate.move_to(overlap_h2),
            electron1.animate.move_to(UP * 0.6 + UP * 0.2),
            electron2.animate.move_to(DOWN * 0.2 + UP * 0.2),
            Transform(subtitle, shared_subtitle),
            run_time=3.0,
        )

        # Glow box around shared electron pair
        shared_zone = Ellipse(width=0.8, height=1.6, color="#FACC15", stroke_width=3).move_to(UP * 0.2)
        shared_label = Text("Shared Pair (Covalent Bond)", font_size=20, color="#FACC15").next_to(shared_zone, UP, buff=0.3)

        self.play(Create(shared_zone), Write(shared_label), run_time=1.5)

        # Summary takeaway
        molecule_name = Text("Stable H₂ Diatomic Molecule Formed", font_size=26, color="#22C55E")
        molecule_name.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(molecule_name), run_time=1.0)
        self.wait(1.5)
"""

    def _generate_ionic_vs_covalent_manim_code(self, duration: float) -> str:
        """Generate Manim scene script for Ionic vs Covalent bonding."""
        return """
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Ionic vs Covalent Bonding", font_size=36, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        # Divider
        divider = Line(UP * 2.2, DOWN * 2.8, color="#334155", stroke_width=2)
        self.play(Create(divider), run_time=0.6)

        # Headers
        ionic_head = Text("IONIC (Electron Transfer)", font_size=24, color="#F87171").move_to(LEFT * 3.5 + UP * 2.0)
        covalent_head = Text("COVALENT (Electron Sharing)", font_size=24, color="#38BDF8").move_to(RIGHT * 3.5 + UP * 2.0)
        self.play(FadeIn(ionic_head), FadeIn(covalent_head), run_time=0.8)

        # --- LEFT: IONIC (Na -> Cl) ---
        na_atom = Dot(point=LEFT * 5.0 + UP * 0.5, radius=0.4, color="#F87171")
        na_label = Text("Na", font_size=22, color=WHITE).move_to(na_atom)
        na_e = Dot(point=LEFT * 4.4 + UP * 0.5, radius=0.12, color="#FACC15")

        cl_atom = Dot(point=LEFT * 2.0 + UP * 0.5, radius=0.55, color="#4ADE80")
        cl_label = Text("Cl", font_size=22, color=WHITE).move_to(cl_atom)

        self.play(
            FadeIn(na_atom), FadeIn(na_label), FadeIn(na_e),
            FadeIn(cl_atom), FadeIn(cl_label),
            run_time=1.0,
        )

        # Animate electron transfer Na -> Cl
        cl_target = LEFT * 2.6 + UP * 0.5
        new_na_label = Text("Na⁺", font_size=22, color=WHITE).move_to(na_atom)
        new_cl_label = Text("Cl⁻", font_size=22, color=WHITE).move_to(cl_atom)

        self.play(
            na_e.animate.move_to(cl_target),
            Transform(na_label, new_na_label),
            Transform(cl_label, new_cl_label),
            run_time=2.0,
        )

        ionic_desc = VGroup(
            Text("• Metal transfers electron to nonmetal", font_size=16, color="#CBD5E1"),
            Text("• Electrostatic crystal lattice (NaCl)", font_size=16, color="#CBD5E1"),
            Text("• High melting point (>800°C)", font_size=16, color="#CBD5E1"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(na_atom, DOWN, buff=0.8).shift(RIGHT * 1.5)

        self.play(FadeIn(ionic_desc), run_time=1.0)

        # --- RIGHT: COVALENT (H - H sharing) ---
        h1 = Circle(radius=0.7, color="#38BDF8", stroke_width=2).move_to(RIGHT * 2.3 + UP * 0.5)
        h1_dot = Dot(point=RIGHT * 2.3 + UP * 0.5, radius=0.25, color="#38BDF8")
        h1_txt = Text("H", font_size=18, color=WHITE).move_to(h1_dot)

        h2 = Circle(radius=0.7, color="#38BDF8", stroke_width=2).move_to(RIGHT * 3.7 + UP * 0.5)
        h2_dot = Dot(point=RIGHT * 3.7 + UP * 0.5, radius=0.25, color="#38BDF8")
        h2_txt = Text("H", font_size=18, color=WHITE).move_to(h2_dot)

        shared_e = Dot(point=RIGHT * 3.0 + UP * 0.5, radius=0.12, color="#FACC15")

        self.play(
            Create(h1), FadeIn(h1_dot), FadeIn(h1_txt),
            Create(h2), FadeIn(h2_dot), FadeIn(h2_txt),
            FadeIn(shared_e),
            run_time=1.5,
        )

        covalent_desc = VGroup(
            Text("• Nonmetals share electron pairs", font_size=16, color="#CBD5E1"),
            Text("• Discrete molecules (H₂O, CH₄)", font_size=16, color="#CBD5E1"),
            Text("• Lower melting points, flexible", font_size=16, color="#CBD5E1"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(h1, DOWN, buff=0.8).shift(RIGHT * 0.7)

        self.play(FadeIn(covalent_desc), run_time=1.0)
        self.wait(1.5)
"""

    async def render_topic_video(
        self,
        topic: SupportedTopic,
        output_path: Path,
        duration: float = 15.0,
    ) -> Optional[Path]:
        """
        Render a topic's Manim animation to an MP4 file.
        Returns output_path if successful, None if Manim is unavailable or fails.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        manim_bin = shutil.which("manim")
        if not manim_bin:
            logger.warning("Manim is not installed on system; skipping Manim render")
            return None

        # Select scene code
        if topic == SupportedTopic.PH_SCALE:
            code = self._generate_ph_scale_manim_code(duration)
        elif topic == SupportedTopic.COVALENT_BONDS:
            code = self._generate_covalent_bonds_manim_code(duration)
        elif topic == SupportedTopic.IONIC_VS_COVALENT:
            code = self._generate_ionic_vs_covalent_manim_code(duration)
        else:
            logger.info("No dedicated Manim scene for %s; using standard visual engine", topic)
            return None

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            script_file = tmp_path / "scene.py"
            script_file.write_text(code, encoding="utf-8")

            # Quality flag mapping: -qm (720p 30fps), -qh (1080p 60fps), -ql (480p 15fps)
            quality_flag = f"-q{self.quality}"

            cmd = [
                manim_bin,
                quality_flag,
                "--fps",
                str(self.fps),
                "--media_dir",
                str(tmp_path / "media"),
                str(script_file),
                "ChemistryScene",
            ]

            logger.info("Executing Manim render: %s", " ".join(cmd))
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(
                    "Manim render failed with code %d: %s", proc.returncode, stderr.decode()
                )
                return None

            # Locate rendered MP4 in media directory
            rendered_files = list((tmp_path / "media").glob("**/*.mp4"))
            if not rendered_files:
                logger.error("Manim reported success but no MP4 was generated")
                return None

            # Copy to target path
            shutil.copy2(rendered_files[0], output_path)
            logger.info("Manim render succeeded: %s", output_path)
            return output_path

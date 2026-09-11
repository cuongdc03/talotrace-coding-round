"""Manim-based mathematical and physics animation engine for chemistry explainer videos."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from app.models.script import SupportedTopic
from app.pipeline.latex_renderer import LatexRenderer

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
        self.latex_renderer = LatexRenderer()

    def is_available(self) -> bool:
        """Check if manim CLI is installed and accessible."""
        if Path(self.manim_bin).exists() and Path(self.manim_bin).is_file():
            return True
        return shutil.which("manim") is not None

    def _generate_ph_scale_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for the pH scale explanation."""
        move_time = max(2.5, duration / 7.0)
        fixed_time = 1.2 + 1.5 + 1.2 + 1.2 + 1.0 + 1.5 + 2.0 + 2.0 + 2.0
        final_wait = max(2.5, duration - (fixed_time + 2 * move_time))
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        # Title
        title = Text("The pH Scale: Acids, Neutral, and Bases", font_size=34, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.2)

        # Baseline & Gradient Spectrum Bar
        colors = ["#EF4444", "#F97316", "#FACC15", "#22C55E", "#06B6D4", "#3B82F6", "#A855F7", "#C026D3"]
        spectrum = Rectangle(width=10.5, height=0.6).shift(UP * 0.5)
        spectrum.set_fill(color=colors, opacity=0.85)
        spectrum.set_stroke(width=0)

        num_mobs = VGroup()
        for i in range(15):
            x = -5.25 + (i / 14.0) * 10.5
            num_txt = Text(str(i), font_size=15, color="#CBD5E1").move_to([x, 0.0, 0])
            tick = Line([x, 0.2, 0], [x, 0.05, 0], color=WHITE, stroke_width=1.5)
            num_mobs.add(num_txt, tick)

        self.play(FadeIn(spectrum), FadeIn(num_mobs), run_time=1.5)

        # Section Labels
        acid_label = Text("ACIDIC (H+)", font_size=20, color="#EF4444").next_to(spectrum, UP, buff=0.3).shift(LEFT * 3.6)
        neutral_label = Text("NEUTRAL", font_size=20, color="#22C55E").next_to(spectrum, UP, buff=0.3)
        base_label = Text("ALKALINE (OH-)", font_size=20, color="#A855F7").next_to(spectrum, UP, buff=0.3).shift(RIGHT * 3.6)
        self.play(FadeIn(acid_label), FadeIn(neutral_label), FadeIn(base_label), run_time=1.2)

        # LaTeX Equation callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).shift(DOWN * 1.2)
        self.play(FadeIn(eq_mob), run_time=1.2)

        def n2p(val):
            return np.array([-5.25 + (val / 14.0) * 10.5, 0.5, 0])

        pointer = Triangle(color="#FACC15", fill_opacity=1.0).scale(0.22).rotate(PI)
        pointer.move_to(n2p(7) + DOWN * 0.7)
        indicator_text = Text("Pure Water (pH 7.0 - Balanced H+ and OH-)", font_size=20, color="#22C55E").shift(DOWN * 2.2)
        self.play(FadeIn(pointer), FadeIn(indicator_text), run_time=1.0)
        self.wait(1.5)

        # Sweep to Lemon Juice pH 2
        pos_acid = n2p(2) + DOWN * 0.7
        new_text_acid = Text("Lemon Juice (pH 2.0 - Concentrated Protons H+)", font_size=20, color="#EF4444").shift(DOWN * 2.2)
        self.play(pointer.animate.move_to(pos_acid), Transform(indicator_text, new_text_acid), run_time={move_time})
        self.wait(2.0)

        # Sweep to Bleach pH 13
        pos_base = n2p(13) + DOWN * 0.7
        new_text_base = Text("Household Bleach (pH 13.0 - High Hydroxide OH-)", font_size=20, color="#A855F7").shift(DOWN * 2.2)
        self.play(pointer.animate.move_to(pos_base), Transform(indicator_text, new_text_base), run_time={move_time})
        self.wait(2.0)

        # Return to Neutral with Logarithmic takeaway
        takeaway = Text("Logarithmic Law: Each 1 pH unit represents a 10x change in acidity", font_size=20, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(
            pointer.animate.move_to(n2p(7) + DOWN * 0.7),
            FadeIn(takeaway),
            run_time=2.0,
        )
        self.wait({final_wait:.1f})
"""

    def _generate_covalent_bonds_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for covalent bonding with orbiting electrons."""
        final_wait = max(2.5, duration - 25.0)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Why Atoms Form Covalent Bonds", font_size=34, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.5)

        subtitle = Text("Isolated atoms seek stable valence shells (Octet/Duet Rule)", font_size=20, color="#94A3B8")
        subtitle.next_to(title, DOWN, buff=0.25)
        self.play(FadeIn(subtitle), run_time=1.5)

        # Hydrogen Atom 1 (Left)
        h1_center = LEFT * 3.6 + UP * 0.4
        nucleus1 = Dot(point=h1_center, radius=0.35, color="#EF4444")
        n1_label = Text("H+", font_size=22, color=WHITE).move_to(h1_center)
        atom1_group = VGroup(nucleus1, n1_label)
        shell1 = Circle(radius=1.3, color="#38BDF8", stroke_width=2).move_to(h1_center)
        electron1 = Dot(point=h1_center + UP * 1.3, radius=0.14, color="#FACC15")

        # Hydrogen Atom 2 (Right)
        h2_center = RIGHT * 3.6 + UP * 0.4
        nucleus2 = Dot(point=h2_center, radius=0.35, color="#EF4444")
        n2_label = Text("H+", font_size=22, color=WHITE).move_to(h2_center)
        atom2_group = VGroup(nucleus2, n2_label)
        shell2 = Circle(radius=1.3, color="#38BDF8", stroke_width=2).move_to(h2_center)
        electron2 = Dot(point=h2_center + DOWN * 1.3, radius=0.14, color="#FACC15")

        self.play(
            FadeIn(atom1_group), Create(shell1), FadeIn(electron1),
            FadeIn(atom2_group), Create(shell2), FadeIn(electron2),
            run_time=2.5,
        )
        self.wait(2.5)

        # Move atoms inward to overlap shells
        overlap_h1 = LEFT * 0.85 + UP * 0.4
        overlap_h2 = RIGHT * 0.85 + UP * 0.4

        shared_subtitle = Text("Valence orbitals merge: mutually sharing an electron pair", font_size=20, color="#38BDF8")
        shared_subtitle.next_to(title, DOWN, buff=0.25)

        self.play(
            atom1_group.animate.move_to(overlap_h1),
            shell1.animate.move_to(overlap_h1),
            atom2_group.animate.move_to(overlap_h2),
            shell2.animate.move_to(overlap_h2),
            electron1.animate.move_to(UP * 0.75 + UP * 0.4),
            electron2.animate.move_to(DOWN * 0.05 + UP * 0.4),
            Transform(subtitle, shared_subtitle),
            run_time=4.5,
        )

        # Overlap glow zone
        shared_zone = Ellipse(width=0.9, height=1.6, color="#FACC15", stroke_width=3).move_to(UP * 0.4)
        shared_label = Text("Shared Electron Pair", font_size=18, color="#FACC15").next_to(shared_zone, UP, buff=0.2)
        self.play(Create(shared_zone), Write(shared_label), run_time=2.5)
        self.wait(3.5)

        # Formula callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).shift(DOWN * 1.4)
        self.play(FadeIn(eq_mob), run_time=2.0)
        self.wait(2.5)

        takeaway = Text("Electrostatic attraction between positive nuclei and shared electrons binds the molecule", font_size=18, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(takeaway), run_time=2.0)
        self.wait({final_wait:.1f})
"""

    def _generate_ionic_vs_covalent_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for Ionic vs Covalent bonding."""
        final_wait = max(2.5, duration - 25.5)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Ionic vs Covalent Bonding: The Essential Differences", font_size=32, color="#38BDF8")
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=1.5)

        divider = Line(UP * 2.2, DOWN * 2.8, color="#334155", stroke_width=2)
        self.play(Create(divider), run_time=1.0)

        ionic_head = Text("IONIC: Electron Transfer", font_size=22, color="#F87171").move_to(LEFT * 3.5 + UP * 1.8)
        covalent_head = Text("COVALENT: Electron Sharing", font_size=22, color="#38BDF8").move_to(RIGHT * 3.5 + UP * 1.8)
        self.play(FadeIn(ionic_head), FadeIn(covalent_head), run_time=1.5)

        # --- LEFT: IONIC (Na -> Cl) ---
        na_atom = Dot(point=LEFT * 5.2 + UP * 0.6, radius=0.38, color="#F87171")
        na_label = Text("Na", font_size=20, color=WHITE).move_to(na_atom)
        na_e = Dot(point=LEFT * 4.6 + UP * 0.6, radius=0.12, color="#FACC15")

        cl_atom = Dot(point=LEFT * 2.0 + UP * 0.6, radius=0.52, color="#4ADE80")
        cl_label = Text("Cl", font_size=20, color=WHITE).move_to(cl_atom)

        self.play(
            FadeIn(na_atom), FadeIn(na_label), FadeIn(na_e),
            FadeIn(cl_atom), FadeIn(cl_label),
            run_time=2.5,
        )

        cl_target = LEFT * 2.6 + UP * 0.6
        new_na_label = Text("Na+", font_size=20, color=WHITE).move_to(na_atom)
        new_cl_label = Text("Cl-", font_size=20, color=WHITE).move_to(cl_atom)

        self.play(
            na_e.animate.move_to(cl_target),
            Transform(na_label, new_na_label),
            Transform(cl_label, new_cl_label),
            run_time=4.0,
        )

        ionic_desc = VGroup(
            Text("- Metal loses electron to nonmetal", font_size=15, color="#CBD5E1"),
            Text("- Rigid crystal lattice (NaCl)", font_size=15, color="#CBD5E1"),
            Text("- High melting points (>800 deg C)", font_size=15, color="#CBD5E1"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(na_atom, DOWN, buff=0.8).shift(RIGHT * 1.5)
        self.play(FadeIn(ionic_desc), run_time=2.5)
        self.wait(2.5)

        # --- RIGHT: COVALENT ---
        h1 = Circle(radius=0.7, color="#38BDF8", stroke_width=2).move_to(RIGHT * 2.4 + UP * 0.6)
        h1_dot = Dot(point=RIGHT * 2.4 + UP * 0.6, radius=0.22, color="#38BDF8")
        h1_txt = Text("H", font_size=18, color=WHITE).move_to(h1_dot)

        h2 = Circle(radius=0.7, color="#38BDF8", stroke_width=2).move_to(RIGHT * 3.6 + UP * 0.6)
        h2_dot = Dot(point=RIGHT * 3.6 + UP * 0.6, radius=0.22, color="#38BDF8")
        h2_txt = Text("H", font_size=18, color=WHITE).move_to(h2_dot)

        shared_e = Dot(point=RIGHT * 3.0 + UP * 0.6, radius=0.12, color="#FACC15")

        self.play(
            Create(h1), FadeIn(h1_dot), FadeIn(h1_txt),
            Create(h2), FadeIn(h2_dot), FadeIn(h2_txt),
            FadeIn(shared_e),
            run_time=3.5,
        )

        covalent_desc = VGroup(
            Text("- Nonmetals share electron pairs", font_size=15, color="#CBD5E1"),
            Text("- Discrete molecules (H2O, CH4)", font_size=15, color="#CBD5E1"),
            Text("- Lower melting points, flexible", font_size=15, color="#CBD5E1"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(h1, DOWN, buff=0.8).shift(RIGHT * 0.7)
        self.play(FadeIn(covalent_desc), run_time=2.5)
        self.wait(2.0)

        # Formula Callout at bottom
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(eq_mob), run_time=2.0)
        self.wait({final_wait:.1f})
"""

    def _generate_atomic_structure_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for Atomic Structure and Bohr electron shells."""
        final_wait = max(2.5, duration - 22.0)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Atomic Structure & Subatomic Particles", font_size=34, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.5)

        # Central Nucleus
        nucleus = Circle(radius=0.7, color="#EF4444", fill_opacity=0.85).shift(UP * 0.4)
        p1 = Dot(point=UP * 0.6 + LEFT * 0.2, radius=0.15, color="#F87171")
        p2 = Dot(point=UP * 0.3 + RIGHT * 0.2, radius=0.15, color="#F87171")
        n1 = Dot(point=UP * 0.2 + LEFT * 0.15, radius=0.15, color="#94A3B8")
        n2 = Dot(point=UP * 0.5 + RIGHT * 0.15, radius=0.15, color="#94A3B8")
        n_label = Text("Nucleus (p+ & n0)", font_size=18, color=WHITE).next_to(nucleus, DOWN, buff=0.15)
        nuc_group = VGroup(nucleus, p1, p2, n1, n2, n_label)

        self.play(FadeIn(nuc_group), run_time=2.5)
        self.wait(2.0)

        # Concentric Bohr Shells: n=1, n=2
        shell_k = Circle(radius=1.5, color="#38BDF8", stroke_width=2).move_to(nucleus.get_center())
        shell_l = Circle(radius=2.3, color="#818CF8", stroke_width=2).move_to(nucleus.get_center())
        k_label = Text("n=1 (K Shell: max 2e-)", font_size=14, color="#38BDF8").next_to(shell_k, RIGHT, buff=0.2).shift(UP * 0.5)
        l_label = Text("n=2 (L Shell: max 8e-)", font_size=14, color="#818CF8").next_to(shell_l, RIGHT, buff=0.2).shift(UP * 0.8)

        self.play(Create(shell_k), FadeIn(k_label), run_time=2.5)
        self.play(Create(shell_l), FadeIn(l_label), run_time=2.5)

        # Orbiting Electrons
        e1 = Dot(point=nucleus.get_center() + UP * 1.5, radius=0.12, color="#FACC15")
        e2 = Dot(point=nucleus.get_center() + DOWN * 1.5, radius=0.12, color="#FACC15")
        e3 = Dot(point=nucleus.get_center() + LEFT * 2.3, radius=0.12, color="#FACC15")
        e4 = Dot(point=nucleus.get_center() + RIGHT * 2.3, radius=0.12, color="#FACC15")

        self.play(FadeIn(e1), FadeIn(e2), FadeIn(e3), FadeIn(e4), run_time=3.5)
        self.wait(3.0)

        # Formula callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).shift(DOWN * 1.6)
        self.play(FadeIn(eq_mob), run_time=2.0)

        takeaway = Text("Valence electrons in outermost shell dictate chemical bonding and reactivity", font_size=18, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(takeaway), run_time=2.5)
        self.wait({final_wait:.1f})
"""

    def _generate_exo_vs_endothermic_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for Exothermic vs Endothermic energy profiles."""
        final_wait = max(2.5, duration - 21.5)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Exothermic vs Endothermic Reactions: Energy Profiles", font_size=32, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.5)

        # Potential Energy Coordinate Axes
        origin = LEFT * 5.0 + DOWN * 1.5
        x_axis = Arrow(origin, origin + RIGHT * 10.0, color=WHITE, buff=0)
        y_axis = Arrow(origin, origin + UP * 3.8, color=WHITE, buff=0)
        x_label = Text("Reaction Coordinate (Time)", font_size=16, color="#94A3B8").next_to(x_axis, DOWN, buff=0.2)
        y_label = Text("Potential Energy (H)", font_size=16, color="#94A3B8").next_to(y_axis, UP, buff=0.2)

        self.play(Create(x_axis), Create(y_axis), FadeIn(x_label), FadeIn(y_label), run_time=2.5)

        # Exothermic Curve: Reactants (high) -> Peak (Ea) -> Products (low)
        r_line = Line(LEFT * 4.5 + UP * 0.5, LEFT * 3.2 + UP * 0.5, color="#F87171", stroke_width=4)
        r_txt = Text("Reactants", font_size=16, color="#F87171").next_to(r_line, UP, buff=0.1)

        peak_pt = LEFT * 1.5 + UP * 1.8
        p_line = Line(RIGHT * 0.2 + DOWN * 0.5, RIGHT * 1.8 + DOWN * 0.5, color="#38BDF8", stroke_width=4)
        p_txt = Text("Products", font_size=16, color="#38BDF8").next_to(p_line, DOWN, buff=0.1)

        curve_exo = CubicBezier(
            LEFT * 3.2 + UP * 0.5,
            LEFT * 2.2 + UP * 2.2,
            LEFT * 0.8 + UP * 2.0,
            RIGHT * 0.2 + DOWN * 0.5,
            color="#EF4444", stroke_width=3,
        )

        ea_arrow = DoubleArrow(LEFT * 3.2 + UP * 0.5, LEFT * 3.2 + UP * 1.8, color="#FACC15", buff=0)
        ea_txt = Text("Ea (Activation)", font_size=14, color="#FACC15").next_to(ea_arrow, LEFT, buff=0.1)

        dh_arrow = DoubleArrow(RIGHT * 1.0 + UP * 0.5, RIGHT * 1.0 + DOWN * 0.5, color="#EF4444", buff=0)
        dh_txt = Text("Delta H < 0 (Exothermic: Heat Released)", font_size=16, color="#EF4444").next_to(dh_arrow, RIGHT, buff=0.2)

        self.play(
            Create(r_line), FadeIn(r_txt),
            Create(curve_exo),
            Create(p_line), FadeIn(p_txt),
            run_time=4.0,
        )
        self.play(Create(ea_arrow), FadeIn(ea_txt), Create(dh_arrow), FadeIn(dh_txt), run_time=3.0)
        self.wait(3.5)

        # Formula callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(eq_mob), run_time=2.0)
        self.wait(2.5)

        takeaway = Text("Activation energy is the barrier to initiate; Delta H dictates heat flow", font_size=18, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(takeaway), run_time=2.5)
        self.wait({final_wait:.1f})
"""

    def _generate_periodic_trends_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for Periodic Table Trends & Electronegativity."""
        final_wait = max(2.5, duration - 22.5)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Periodic Table Trends: Electronegativity & Radius", font_size=32, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.5)

        # Stylized Periodic Table Outline Box
        pt_box = Rectangle(width=9.5, height=3.2, color="#334155", stroke_width=2).shift(UP * 0.2)
        pt_label = Text("Mendeleev Periodic Table (Periods & Groups)", font_size=18, color="#64748B").next_to(pt_box, UP, buff=0.15)
        self.play(Create(pt_box), FadeIn(pt_label), run_time=2.5)

        # Electronegativity Arrow: Left to Right across period (increases)
        en_arrow = Arrow(LEFT * 4.0 + DOWN * 0.8, RIGHT * 4.0 + DOWN * 0.8, color="#FACC15", stroke_width=5)
        en_txt = Text("Electronegativity Increases Across Periods ->", font_size=18, color="#FACC15").next_to(en_arrow, UP, buff=0.15)

        # Electronegativity Arrow: Bottom to Top up group (increases)
        up_arrow = Arrow(RIGHT * 4.2 + DOWN * 1.0, RIGHT * 4.2 + UP * 1.4, color="#FACC15", stroke_width=5)
        up_txt = Text("Increases Up Groups ^", font_size=15, color="#FACC15").next_to(up_arrow, RIGHT, buff=0.15)

        self.play(Create(en_arrow), FadeIn(en_txt), run_time=3.5)
        self.play(Create(up_arrow), FadeIn(up_txt), run_time=2.5)
        self.wait(2.5)

        # Atomic Radius Arrow: Opposite trend (Decreases across periods, increases down groups)
        rad_arrow = Arrow(RIGHT * 3.5 + UP * 0.8, LEFT * 3.5 + UP * 0.8, color="#38BDF8", stroke_width=4)
        rad_txt = Text("<- Atomic Radius Increases (Opposite Direction)", font_size=16, color="#38BDF8").next_to(rad_arrow, DOWN, buff=0.15)
        self.play(Create(rad_arrow), FadeIn(rad_txt), run_time=3.5)
        self.wait(2.0)

        # Formula callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(eq_mob), run_time=2.0)
        self.wait(2.5)

        takeaway = Text("Periodic trends allow chemists to predict reactivity across all elements", font_size=18, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(takeaway), run_time=2.5)
        self.wait({final_wait:.1f})
"""

    def _generate_states_of_matter_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for States of Matter & Phase Transitions."""
        final_wait = max(2.5, duration - 22.0)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("States of Matter and Phase Transitions", font_size=34, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.5)

        # Three Phase Boxes: Solid, Liquid, Gas
        b_solid = Rectangle(width=2.8, height=2.6, color="#38BDF8", stroke_width=2).move_to(LEFT * 3.6 + UP * 0.4)
        lbl_solid = Text("SOLID (Lattice)", font_size=18, color="#38BDF8").next_to(b_solid, UP, buff=0.15)

        b_liquid = Rectangle(width=2.8, height=2.6, color="#22C55E", stroke_width=2).move_to(UP * 0.4)
        lbl_liquid = Text("LIQUID (Fluid)", font_size=18, color="#22C55E").next_to(b_liquid, UP, buff=0.15)

        b_gas = Rectangle(width=2.8, height=2.6, color="#F87171", stroke_width=2).move_to(RIGHT * 3.6 + UP * 0.4)
        lbl_gas = Text("GAS (Kinetic)", font_size=18, color="#F87171").next_to(b_gas, UP, buff=0.15)

        self.play(
            Create(b_solid), FadeIn(lbl_solid),
            Create(b_liquid), FadeIn(lbl_liquid),
            Create(b_gas), FadeIn(lbl_gas),
            run_time=2.5,
        )

        # Solid dots in rigid 3x3 grid
        solid_dots = VGroup()
        for r in range(3):
            for c in range(3):
                pt = LEFT * 3.6 + UP * 0.4 + np.array([(c-1)*0.6, (r-1)*0.6, 0])
                solid_dots.add(Dot(point=pt, radius=0.12, color="#38BDF8"))

        # Liquid dots dispersed
        liquid_dots = VGroup()
        positions_l = [(-0.6, -0.6), (0.4, -0.7), (-0.2, -0.2), (0.5, 0.1), (-0.5, 0.4), (0.2, 0.6)]
        for dx, dy in positions_l:
            liquid_dots.add(Dot(point=UP * 0.4 + np.array([dx, dy, 0]), radius=0.12, color="#22C55E"))

        # Gas dots widely scattered
        gas_dots = VGroup()
        positions_g = [(-0.9, -0.8), (0.8, -0.5), (-0.4, 0.3), (0.9, 0.7), (-0.8, 0.8)]
        for dx, dy in positions_g:
            gas_dots.add(Dot(point=RIGHT * 3.6 + UP * 0.4 + np.array([dx, dy, 0]), radius=0.12, color="#F87171"))

        self.play(FadeIn(solid_dots), FadeIn(liquid_dots), FadeIn(gas_dots), run_time=3.5)
        self.wait(2.5)

        # Transition Arrows: Melting and Vaporization
        arrow_melt = Arrow(LEFT * 2.1 + UP * 0.4, LEFT * 1.5 + UP * 0.4, color="#FACC15", buff=0)
        lbl_melt = Text("Melting", font_size=12, color="#FACC15").next_to(arrow_melt, UP, buff=0.1)

        arrow_boil = Arrow(RIGHT * 1.5 + UP * 0.4, RIGHT * 2.1 + UP * 0.4, color="#FACC15", buff=0)
        lbl_boil = Text("Boiling", font_size=12, color="#FACC15").next_to(arrow_boil, UP, buff=0.1)

        self.play(Create(arrow_melt), FadeIn(lbl_melt), Create(arrow_boil), FadeIn(lbl_boil), run_time=2.5)
        self.wait(2.5)

        # Formula callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(eq_mob), run_time=2.0)
        self.wait(2.5)

        takeaway = Text("Kinetic thermal energy determines whether intermolecular bonds hold particles", font_size=18, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(takeaway), run_time=2.5)
        self.wait({final_wait:.1f})
"""

    def _generate_acid_base_neutralization_manim_code(self, duration: float, eq_png: Path) -> str:
        """Generate Manim scene script for Acid-Base Neutralization and Titration."""
        final_wait = max(2.5, duration - 22.5)
        return f"""
from manim import *

class ChemistryScene(Scene):
    def construct(self):
        self.camera.background_color = "#0B0F19"

        title = Text("Acid-Base Neutralization & Titration", font_size=34, color="#38BDF8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.5)

        # Acidic Beaker (Left, Red)
        beaker_a = Rectangle(width=2.5, height=3.0, color="#EF4444", stroke_width=2).move_to(LEFT * 3.5 + UP * 0.2)
        fluid_a = Rectangle(width=2.4, height=1.6, color="#EF4444", fill_opacity=0.4, stroke_width=0).align_to(beaker_a, DOWN)
        txt_a = Text("Acid (HCl)", font_size=20, color="#EF4444").next_to(beaker_a, UP, buff=0.2)
        ion_h = Text("H+", font_size=24, color=WHITE).move_to(fluid_a.get_center())
        acid_grp = VGroup(beaker_a, fluid_a, txt_a, ion_h)

        # Basic Beaker (Right, Purple)
        beaker_b = Rectangle(width=2.5, height=3.0, color="#A855F7", stroke_width=2).move_to(RIGHT * 3.5 + UP * 0.2)
        fluid_b = Rectangle(width=2.4, height=1.6, color="#A855F7", fill_opacity=0.4, stroke_width=0).align_to(beaker_b, DOWN)
        txt_b = Text("Base (NaOH)", font_size=20, color="#A855F7").next_to(beaker_b, UP, buff=0.2)
        ion_oh = Text("OH-", font_size=24, color=WHITE).move_to(fluid_b.get_center())
        base_grp = VGroup(beaker_b, fluid_b, txt_b, ion_oh)

        self.play(FadeIn(acid_grp), FadeIn(base_grp), run_time=3.0)
        self.wait(2.0)

        # Mix ions in center
        center_fluid = Rectangle(width=3.2, height=2.0, color="#22C55E", fill_opacity=0.5, stroke_width=2).shift(DOWN * 0.2)
        center_txt = Text("Neutral Water (H2O) + Salt (NaCl)", font_size=18, color="#22C55E").next_to(center_fluid, UP, buff=0.2)

        self.play(
            ion_h.animate.move_to(ORIGIN + DOWN * 0.2 + LEFT * 0.6),
            ion_oh.animate.move_to(ORIGIN + DOWN * 0.2 + RIGHT * 0.6),
            FadeIn(center_fluid), FadeIn(center_txt),
            run_time=4.0,
        )

        # Combine ions into H2O
        h2o_txt = Text("H2O (pH 7.0 Neutral)", font_size=24, color=WHITE).move_to(center_fluid.get_center())
        self.play(Transform(ion_h, h2o_txt), FadeOut(ion_oh), run_time=3.0)
        self.wait(2.0)

        # Formula callout
        eq_mob = ImageMobject(r"{eq_png}").scale(0.85).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(eq_mob), run_time=2.0)
        self.wait(2.5)

        takeaway = Text("Neutralization eliminates free protons, yielding salt and neutral water", font_size=18, color="#F8FAFC")
        takeaway.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(takeaway), run_time=2.5)
        self.wait({final_wait:.1f})
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
        if not self.is_available():
            logger.warning("Manim is not installed or accessible; skipping Manim render")
            return None

        # Pre-render appropriate LaTeX formula PNG for the topic
        latex_formula_map = {
            SupportedTopic.PH_SCALE: r"\mathrm{pH} = -\log_{10}[\mathrm{H}^+]",
            SupportedTopic.COVALENT_BONDS: r"\mathrm{H}\cdot + \cdot\mathrm{H} \rightarrow \mathrm{H}:\mathrm{H}",
            SupportedTopic.IONIC_VS_COVALENT: r"\mathrm{Na} + \mathrm{Cl} \rightarrow \mathrm{Na}^+ + \mathrm{Cl}^-",
            SupportedTopic.ATOMIC_STRUCTURE: r"\text{Atom} = p^+ + n^0 + e^-",
            SupportedTopic.EXO_VS_ENDOTHERMIC: r"\Delta H = H_{\mathrm{products}} - H_{\mathrm{reactants}} < 0",
            SupportedTopic.PERIODIC_TRENDS: r"\chi_{\mathrm{F}} = 3.98 > \chi_{\mathrm{Fr}} = 0.7",
            SupportedTopic.STATES_OF_MATTER: r"\overline{E_k} = \frac{3}{2} k_B T",
            SupportedTopic.ACID_BASE_NEUTRALIZATION: r"\mathrm{H}^+ + \mathrm{OH}^- \rightarrow \mathrm{H}_2\mathrm{O}",
        }

        formula_str = latex_formula_map.get(topic, r"E = mc^2")
        eq_png = self.latex_renderer.render_to_png(formula_str)

        # Select scene generator
        if topic == SupportedTopic.PH_SCALE:
            code = self._generate_ph_scale_manim_code(duration, eq_png)
        elif topic == SupportedTopic.COVALENT_BONDS:
            code = self._generate_covalent_bonds_manim_code(duration, eq_png)
        elif topic == SupportedTopic.IONIC_VS_COVALENT:
            code = self._generate_ionic_vs_covalent_manim_code(duration, eq_png)
        elif topic == SupportedTopic.ATOMIC_STRUCTURE:
            code = self._generate_atomic_structure_manim_code(duration, eq_png)
        elif topic == SupportedTopic.EXO_VS_ENDOTHERMIC:
            code = self._generate_exo_vs_endothermic_manim_code(duration, eq_png)
        elif topic == SupportedTopic.PERIODIC_TRENDS:
            code = self._generate_periodic_trends_manim_code(duration, eq_png)
        elif topic == SupportedTopic.STATES_OF_MATTER:
            code = self._generate_states_of_matter_manim_code(duration, eq_png)
        elif topic == SupportedTopic.ACID_BASE_NEUTRALIZATION:
            code = self._generate_acid_base_neutralization_manim_code(duration, eq_png)
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
                self.manim_bin,
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

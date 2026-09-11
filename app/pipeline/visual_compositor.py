"""Chemistry visual compositor creating high-production 1080p educational visual cards."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.models.script import Scene, SupportedTopic


class VisualCompositor:
    """Renders scientific diagrams and educational slide frames at 1920x1080."""

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        self.width = width
        self.height = height
        self._load_fonts()

    def _load_fonts(self) -> None:
        """Attempt to load system TrueType fonts, falling back to default."""
        font_candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        self.font_title: ImageFont.ImageFont = ImageFont.load_default()
        self.font_subtitle: ImageFont.ImageFont = ImageFont.load_default()
        self.font_body: ImageFont.ImageFont = ImageFont.load_default()
        self.font_label: ImageFont.ImageFont = ImageFont.load_default()
        self.font_badge: ImageFont.ImageFont = ImageFont.load_default()

        for font_path in font_candidates:
            if Path(font_path).exists():
                try:
                    self.font_title = ImageFont.truetype(font_path, 52)
                    self.font_subtitle = ImageFont.truetype(font_path, 36)
                    self.font_body = ImageFont.truetype(font_path, 28)
                    self.font_label = ImageFont.truetype(font_path, 22)
                    self.font_badge = ImageFont.truetype(font_path, 18)
                    break
                except Exception:
                    continue

    def _create_background(self) -> Image.Image:
        """Create a deep slate modern gradient background with subtle grid markings."""
        img = Image.new("RGB", (self.width, self.height), color=(11, 15, 25))
        draw = ImageDraw.Draw(img)

        # Subtle vertical gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(11 + (15 - 11) * ratio)
            g = int(15 + (23 - 15) * ratio)
            b = int(25 + (42 - 25) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Subtle decorative grid dots
        dot_color = (30, 41, 59)
        for x in range(60, self.width, 100):
            for y in range(60, self.height, 100):
                draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=dot_color)

        return img

    def _draw_header(self, draw: ImageDraw.ImageDraw, scene: Scene, topic: SupportedTopic) -> None:
        """Draw branded top header and scene title."""
        # Top pill badge
        topic_name = topic.value.replace("_", " ")
        badge_text = f"GROWTRICS LEARNING • {topic_name}"
        draw.rounded_rectangle(
            [100, 50, 480, 95], radius=22, fill=(30, 41, 59), outline=(56, 189, 248), width=2
        )
        draw.text((125, 62), badge_text, fill=(56, 189, 248), font=self.font_badge)

        # Scene index counter
        scene_badge = f"SCENE {scene.scene_id}"
        draw.rounded_rectangle(
            [self.width - 240, 50, self.width - 100, 95],
            radius=22,
            fill=(30, 41, 59),
            outline=(148, 163, 184),
            width=1,
        )
        draw.text((self.width - 215, 62), scene_badge, fill=(203, 213, 225), font=self.font_badge)

        # Scene Title
        draw.text((100, 120), scene.title, fill=(248, 250, 252), font=self.font_title)
        draw.line([(100, 195), (self.width - 100, 195)], fill=(51, 65, 85), width=2)

    def _draw_footer_card(self, draw: ImageDraw.ImageDraw, scene: Scene) -> None:
        """Draw modern lower-third card displaying the key takeaway."""
        y_top = self.height - 180
        y_bottom = self.height - 60
        # Translucent styled card
        draw.rounded_rectangle(
            [100, y_top, self.width - 100, y_bottom],
            radius=16,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=2,
        )

        # Key takeaway label
        draw.rounded_rectangle([130, y_top + 20, 310, y_top + 55], radius=10, fill=(56, 189, 248))
        draw.text((145, y_top + 26), "KEY TAKEAWAY", fill=(11, 15, 25), font=self.font_badge)

        # Content text
        draw.text(
            (330, y_top + 24), scene.key_takeaway, fill=(241, 245, 249), font=self.font_subtitle
        )

    # --- Chemistry Diagram Renderers ---

    def _render_ph_diagram(self, draw: ImageDraw.ImageDraw, scene: Scene) -> None:
        """Draw pH spectrum (0-14) with gradient blocks and chemical reference labels."""
        center_y = 480
        bar_x_start = 120
        bar_width = (self.width - 240) / 15  # 15 segments (0 to 14)
        bar_height = 100

        # Colors from pH 0 (deep red) to 7 (neutral green) to 14 (deep purple)
        ph_colors = [
            (239, 68, 68),  # 0 - Deep Red
            (248, 113, 113),  # 1
            (251, 146, 60),  # 2 - Orange
            (251, 191, 36),  # 3
            (250, 204, 21),  # 4 - Yellow
            (234, 179, 8),  # 5
            (163, 230, 53),  # 6 - Lime
            (34, 197, 94),  # 7 - Neutral Green
            (20, 184, 166),  # 8 - Teal
            (6, 182, 212),  # 9 - Cyan
            (59, 130, 246),  # 10 - Blue
            (99, 102, 241),  # 11 - Indigo
            (139, 92, 246),  # 12 - Purple
            (168, 85, 247),  # 13 - Violet
            (192, 38, 211),  # 14 - Magenta
        ]

        # Draw Title and Range Header
        draw.text(
            (bar_x_start, center_y - 180),
            "ACIDIC (Excess H+)",
            fill=(239, 68, 68),
            font=self.font_subtitle,
        )
        draw.text(
            (self.width // 2 - 100, center_y - 180),
            "NEUTRAL (H+ = OH-)",
            fill=(34, 197, 94),
            font=self.font_subtitle,
        )
        draw.text(
            (self.width - 400, center_y - 180),
            "ALKALINE (Excess OH-)",
            fill=(168, 85, 247),
            font=self.font_subtitle,
        )

        # Draw the 15 colored segments
        for i in range(15):
            x1 = int(bar_x_start + i * bar_width)
            x2 = int(x1 + bar_width - 4)
            y1 = center_y - 50
            y2 = y1 + bar_height
            color = ph_colors[i]
            draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=color)

            # pH Number
            num_str = str(i)
            draw.text(
                (x1 + int(bar_width / 2) - 10, y1 + 30),
                num_str,
                fill=(15, 23, 42),
                font=self.font_subtitle,
            )

        # Example Markers
        examples = [
            (1, "Battery Acid\npH 0-1", -1),
            (2, "Lemon Juice\npH 2", 1),
            (4, "Tomato Juice\npH 4", -1),
            (7, "Pure Water\npH 7 (Neutral)", 1),
            (10, "Soap Solution\npH 10", -1),
            (13, "Bleach / NaOH\npH 13-14", 1),
        ]

        for ph_val, label, direction in examples:
            x = int(bar_x_start + ph_val * bar_width + bar_width / 2)
            if direction == -1:
                # Above bar
                draw.line([(x, center_y - 55), (x, center_y - 100)], fill=(148, 163, 184), width=2)
                draw.text(
                    (x - 60, center_y - 145), label, fill=(226, 232, 240), font=self.font_label
                )
            else:
                # Below bar
                draw.line([(x, center_y + 55), (x, center_y + 100)], fill=(148, 163, 184), width=2)
                draw.text(
                    (x - 60, center_y + 110), label, fill=(226, 232, 240), font=self.font_label
                )

    def _render_covalent_diagram(self, draw: ImageDraw.ImageDraw, scene: Scene) -> None:
        """Draw dual-atom covalent bonding with overlapping valence shells and shared electron pair."""
        center_x = self.width // 2
        center_y = 480
        radius = 160
        overlap_offset = 120  # Atoms overlapping

        atom1_x = center_x - overlap_offset
        atom2_x = center_x + overlap_offset

        # Orbitals (Dashed/Outlined circles)
        draw.ellipse(
            [atom1_x - radius, center_y - radius, atom1_x + radius, center_y + radius],
            outline=(56, 189, 248),
            width=3,
        )
        draw.ellipse(
            [atom2_x - radius, center_y - radius, atom2_x + radius, center_y + radius],
            outline=(56, 189, 248),
            width=3,
        )

        # Nuclei
        draw.ellipse([atom1_x - 35, center_y - 35, atom1_x + 35, center_y + 35], fill=(239, 68, 68))
        draw.text(
            (atom1_x - 14, center_y - 18), "H+", fill=(255, 255, 255), font=self.font_subtitle
        )

        draw.ellipse([atom2_x - 35, center_y - 35, atom2_x + 35, center_y + 35], fill=(239, 68, 68))
        draw.text(
            (atom2_x - 14, center_y - 18), "H+", fill=(255, 255, 255), font=self.font_subtitle
        )

        # Shared Electron Pair in intersection zone (glowing cyan & gold)
        draw.ellipse(
            [center_x - 12, center_y - 40, center_x + 12, center_y - 16],
            fill=(251, 191, 36),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((center_x - 6, center_y - 38), "e-", fill=(15, 23, 42), font=self.font_label)

        draw.ellipse(
            [center_x - 12, center_y + 16, center_x + 12, center_y + 40],
            fill=(251, 191, 36),
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((center_x - 6, center_y + 18), "e-", fill=(15, 23, 42), font=self.font_label)

        # Annotations
        draw.text(
            (center_x - 150, center_y - 200),
            "Shared Electron Pair",
            fill=(251, 191, 36),
            font=self.font_subtitle,
        )
        draw.line(
            [(center_x, center_y - 160), (center_x, center_y - 50)], fill=(251, 191, 36), width=2
        )

        draw.text(
            (atom1_x - 120, center_y + 180),
            "Hydrogen Atom A",
            fill=(148, 163, 184),
            font=self.font_body,
        )
        draw.text(
            (atom2_x - 20, center_y + 180),
            "Hydrogen Atom B",
            fill=(148, 163, 184),
            font=self.font_body,
        )

        draw.text(
            (center_x - 170, center_y + 240),
            "Stable H₂ Diatomic Molecule Formed",
            fill=(56, 189, 248),
            font=self.font_subtitle,
        )

    def _render_ionic_vs_covalent_diagram(self, draw: ImageDraw.ImageDraw, scene: Scene) -> None:
        """Draw side-by-side comparison: Ionic electron transfer vs Covalent sharing."""
        col1_center = 500
        col2_center = 1420
        center_y = 480

        # Column Dividers & Headers
        draw.line([(self.width // 2, 220), (self.width // 2, 780)], fill=(51, 65, 85), width=2)

        draw.text(
            (col1_center - 180, 230),
            "IONIC BONDING (Transfer)",
            fill=(248, 113, 113),
            font=self.font_subtitle,
        )
        draw.text(
            (col2_center - 190, 230),
            "COVALENT BONDING (Sharing)",
            fill=(56, 189, 248),
            font=self.font_subtitle,
        )

        # Left Column: Ionic (Na+ Cl-)
        # Na+ ion
        draw.ellipse(
            [col1_center - 180, center_y - 70, col1_center - 40, center_y + 70],
            outline=(248, 113, 113),
            width=3,
        )
        draw.text(
            (col1_center - 125, center_y - 20), "Na⁺", fill=(248, 113, 113), font=self.font_subtitle
        )

        # Transfer Arrow with electron
        draw.line(
            [(col1_center - 30, center_y), (col1_center + 30, center_y)],
            fill=(251, 191, 36),
            width=4,
        )
        draw.ellipse(
            [col1_center - 10, center_y - 28, col1_center + 10, center_y - 8], fill=(251, 191, 36)
        )
        draw.text((col1_center - 8, center_y - 26), "e-", fill=(15, 23, 42), font=self.font_label)

        # Cl- ion
        draw.ellipse(
            [col1_center + 40, center_y - 80, col1_center + 200, center_y + 80],
            outline=(34, 197, 94),
            width=3,
        )
        draw.text(
            (col1_center + 105, center_y - 20), "Cl⁻", fill=(34, 197, 94), font=self.font_subtitle
        )

        draw.text(
            (col1_center - 180, center_y + 120),
            "• Metal transfers electron to nonmetal",
            fill=(203, 213, 225),
            font=self.font_body,
        )
        draw.text(
            (col1_center - 180, center_y + 160),
            "• Forms electrostatic crystal lattice",
            fill=(203, 213, 225),
            font=self.font_body,
        )
        draw.text(
            (col1_center - 180, center_y + 200),
            "• High melting point (e.g. Table Salt NaCl)",
            fill=(203, 213, 225),
            font=self.font_body,
        )

        # Right Column: Covalent (H2O / H2)
        draw.ellipse(
            [col2_center - 110, center_y - 60, col2_center + 10, center_y + 60],
            outline=(56, 189, 248),
            width=3,
        )
        draw.ellipse(
            [col2_center - 10, center_y - 60, col2_center + 110, center_y + 60],
            outline=(56, 189, 248),
            width=3,
        )
        draw.ellipse(
            [col2_center - 8, center_y - 12, col2_center + 8, center_y + 12], fill=(251, 191, 36)
        )
        draw.text(
            (col2_center - 55, center_y - 15), "H", fill=(248, 250, 252), font=self.font_subtitle
        )
        draw.text(
            (col2_center + 40, center_y - 15), "H", fill=(248, 250, 252), font=self.font_subtitle
        )

        draw.text(
            (col2_center - 190, center_y + 120),
            "• Nonmetals mutually share electron pairs",
            fill=(203, 213, 225),
            font=self.font_body,
        )
        draw.text(
            (col2_center - 190, center_y + 160),
            "• Forms discrete, distinct molecules",
            fill=(203, 213, 225),
            font=self.font_body,
        )
        draw.text(
            (col2_center - 190, center_y + 200),
            "• Lower melting point (e.g. Water H₂O)",
            fill=(203, 213, 225),
            font=self.font_body,
        )

    def _render_generic_stem_diagram(self, draw: ImageDraw.ImageDraw, scene: Scene) -> None:
        """Draw generic clean STEM explanation card."""
        center_x = self.width // 2
        center_y = 480
        draw.rounded_rectangle(
            [center_x - 400, center_y - 160, center_x + 400, center_y + 160],
            radius=20,
            fill=(15, 23, 42),
            outline=(56, 189, 248),
            width=2,
        )
        draw.text(
            (center_x - 300, center_y - 80),
            scene.title,
            fill=(56, 189, 248),
            font=self.font_subtitle,
        )
        draw.text(
            (center_x - 300, center_y),
            scene.narration[:120] + "...",
            fill=(226, 232, 240),
            font=self.font_body,
        )

    def render_scene_frame(
        self,
        scene: Scene,
        topic: SupportedTopic,
        output_path: Path,
    ) -> Path:
        """Render a single 1080p slide frame for a scene and save to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img = self._create_background()
        draw = ImageDraw.Draw(img)

        # Header and Footer
        self._draw_header(draw, scene, topic)
        self._draw_footer_card(draw, scene)

        # Diagram Selection based on topic and visual_type
        if topic == SupportedTopic.PH_SCALE or "ph" in scene.visual_type.lower():
            self._render_ph_diagram(draw, scene)
        elif (
            topic == SupportedTopic.COVALENT_BONDS
            or "covalent" in scene.visual_type.lower()
            and "ionic" not in scene.visual_type.lower()
        ):
            self._render_covalent_diagram(draw, scene)
        elif (
            topic == SupportedTopic.IONIC_VS_COVALENT
            or "comparison" in scene.visual_type.lower()
            or "bonding" in scene.visual_type.lower()
        ):
            self._render_ionic_vs_covalent_diagram(draw, scene)
        else:
            self._render_generic_stem_diagram(draw, scene)

        img.save(output_path, format="PNG", quality=95)
        return output_path

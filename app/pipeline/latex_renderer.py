"""Zero-dependency LaTeX equation and chemical formula renderer using Matplotlib mathtext."""

import hashlib
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.core.config import settings

logger = logging.getLogger(__name__)


class LatexRenderer:
    """Renders LaTeX mathematical and chemical formulas into transparent PNGs."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or (settings.TMP_DIR / "latex_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def render_to_png(
        self,
        formula: str,
        color: str = "#FACC15",
        fontsize: int = 24,
        dpi: int = 200,
    ) -> Path:
        """Render a LaTeX formula into a transparent PNG and return the file path."""
        formula_clean = formula.strip()
        if not formula_clean:
            formula_clean = r"\text{}"

        # Ensure surrounded with math delimiters for mathtext
        math_str = formula_clean
        if not math_str.startswith("$"):
            math_str = f"${math_str}$"

        # Unique hash for caching
        cache_key = f"{math_str}_{color}_{fontsize}_{dpi}"
        formula_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:16]
        output_path = self.cache_dir / f"latex_{formula_hash}.png"

        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path

        try:
            self._render(math_str, output_path, color=color, fontsize=fontsize, dpi=dpi)
        except Exception as e:
            logger.warning(
                f"Mathtext render failed for '{formula}': {e}. Using fallback plain text."
            )
            # Fallback to plain text rendering without math mode
            clean_plain = (
                formula_clean.replace("$", "").replace("\\mathrm", "").replace("\\text", "")
            )
            self._render_plain(clean_plain, output_path, color=color, fontsize=fontsize, dpi=dpi)

        return output_path

    def _render(
        self, math_str: str, output_path: Path, color: str, fontsize: int, dpi: int
    ) -> None:
        fig, ax = plt.subplots(figsize=(7, 1.6))
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        ax.axis("off")

        ax.text(
            0.5,
            0.5,
            math_str,
            fontsize=fontsize,
            color=color,
            ha="center",
            va="center",
        )

        fig.savefig(
            output_path,
            bbox_inches="tight",
            pad_inches=0.1,
            transparent=True,
            dpi=dpi,
        )
        plt.close(fig)

    def _render_plain(
        self, text_str: str, output_path: Path, color: str, fontsize: int, dpi: int
    ) -> None:
        fig, ax = plt.subplots(figsize=(7, 1.6))
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        ax.axis("off")

        ax.text(
            0.5,
            0.5,
            text_str,
            fontsize=fontsize,
            color=color,
            ha="center",
            va="center",
        )

        fig.savefig(
            output_path,
            bbox_inches="tight",
            pad_inches=0.1,
            transparent=True,
            dpi=dpi,
        )
        plt.close(fig)

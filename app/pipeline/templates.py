"""Curated pedagogical script templates for high-fidelity fallback generation."""
from typing import Dict
from app.models.script import Scene, SupportedTopic, VideoScript

TEMPLATES: Dict[SupportedTopic, VideoScript] = {
    SupportedTopic.PH_SCALE: VideoScript(
        topic=SupportedTopic.PH_SCALE,
        title="How the pH Scale Works: Acids, Bases, and Ions",
        overview="Explore the pH scale from 0 to 14, discovering how hydrogen ion concentration determines whether a substance is acidic, neutral, or alkaline.",
        scenes=[
            Scene(
                scene_id=1,
                title="The 0 to 14 Spectrum",
                narration="The pH scale measures how acidic or basic a liquid is, running on a spectrum from 0 all the way to 14. A pH of 7 represents pure neutral water.",
                visual_type="ph_spectrum",
                key_takeaway="pH ranges from 0 (strong acid) to 14 (strong base), with 7 as neutral.",
                duration_target_seconds=6.0,
            ),
            Scene(
                scene_id=2,
                title="Acids vs Bases: The Ion Balance",
                narration="Acids, like lemon juice or stomach acid, have a pH below 7 and are packed with excess hydrogen ions. Bases, like soap and bleach, have a pH above 7 with excess hydroxide ions.",
                visual_type="ph_ions",
                key_takeaway="Acids release H+ ions (pH < 7); Bases release OH- ions (pH > 7).",
                duration_target_seconds=7.0,
            ),
            Scene(
                scene_id=3,
                title="The Logarithmic Nature of pH",
                narration="Crucially, the pH scale is logarithmic. Each whole unit change represents a ten-fold difference in acidity. A pH of 5 is ten times more acidic than a pH of 6, and a hundred times more acidic than 7!",
                visual_type="ph_logarithmic",
                key_takeaway="Each step on the pH scale represents a 10x change in ion concentration.",
                duration_target_seconds=8.0,
            ),
        ],
    ),
    SupportedTopic.COVALENT_BONDS: VideoScript(
        topic=SupportedTopic.COVALENT_BONDS,
        title="Why Atoms Form Covalent Bonds",
        overview="Understand how nonmetal atoms achieve electronic stability by sharing valence electron pairs to complete their outer shells.",
        scenes=[
            Scene(
                scene_id=1,
                title="The Quest for Stability",
                narration="Atoms form chemical bonds to achieve electron stability. Most atoms are most stable when their outermost valence shell is completely full of electrons, following the octet rule.",
                visual_type="covalent_octet",
                key_takeaway="Atoms seek full valence electron shells for maximum stability.",
                duration_target_seconds=6.5,
            ),
            Scene(
                scene_id=2,
                title="Sharing Electron Pairs",
                narration="When nonmetal atoms meet, neither has enough electronegativity to completely strip electrons from the other. Instead, their outer electron orbitals overlap, and they share pairs of electrons.",
                visual_type="covalent_sharing",
                key_takeaway="Covalent bonds form when overlapping atoms share valence electron pairs.",
                duration_target_seconds=7.5,
            ),
            Scene(
                scene_id=3,
                title="The Molecular Glue",
                narration="The shared negatively charged electrons are simultaneously attracted to the positively charged nuclei of both atoms. This electrostatic attraction holds the atoms tightly together into a molecule.",
                visual_type="covalent_molecule",
                key_takeaway="Electrostatic attraction between positive nuclei and shared electrons binds the molecule.",
                duration_target_seconds=7.5,
            ),
        ],
    ),
    SupportedTopic.IONIC_VS_COVALENT: VideoScript(
        topic=SupportedTopic.IONIC_VS_COVALENT,
        title="Ionic vs Covalent Bonding: The Essential Differences",
        overview="Compare the two fundamental chemical bonding mechanisms: electron transfer forming ionic crystal lattices versus electron sharing forming covalent molecules.",
        scenes=[
            Scene(
                scene_id=1,
                title="Two Ways to Bond",
                narration="To achieve stable outer electron shells, atoms either transfer electrons completely or share them mutually. This fundamental choice defines ionic versus covalent bonding.",
                visual_type="bonding_overview",
                key_takeaway="Atoms form chemical bonds either through electron transfer or electron sharing.",
                duration_target_seconds=6.0,
            ),
            Scene(
                scene_id=2,
                title="Ionic Bonding: Complete Transfer",
                narration="Ionic bonding occurs between metals and nonmetals. For example, sodium transfers an electron to chlorine, creating oppositely charged ions that attract into a rigid crystal lattice.",
                visual_type="ionic_transfer",
                key_takeaway="Ionic: Metal transfers electron to nonmetal, creating oppositely charged ions in a lattice.",
                duration_target_seconds=7.5,
            ),
            Scene(
                scene_id=3,
                title="Covalent Bonding: Mutual Sharing",
                narration="In contrast, covalent bonding occurs between nonmetals, such as hydrogen and oxygen in water. Here, electrons are shared within discrete molecules rather than continuous crystal networks.",
                visual_type="covalent_molecular",
                key_takeaway="Covalent: Nonmetals share electron pairs, forming distinct molecular compounds.",
                duration_target_seconds=7.5,
            ),
            Scene(
                scene_id=4,
                title="Key Physical Properties",
                narration="Because ionic bonds form rigid electrostatic lattices, they have high melting points. Covalent molecular compounds have lower melting points and distinct chemical geometry.",
                visual_type="comparison_table",
                key_takeaway="Ionic compounds form crystalline solids; covalent compounds form flexible molecular structures.",
                duration_target_seconds=7.0,
            ),
        ],
    ),
    SupportedTopic.OTHER_STEM: VideoScript(
        topic=SupportedTopic.OTHER_STEM,
        title="Exploring Science: Fundamental Principles",
        overview="An introductory scientific exploration of foundational physical principles.",
        scenes=[
            Scene(
                scene_id=1,
                title="The Scientific Inquiry",
                narration="Scientific principles help us understand the behavior of matter, energy, and forces across our universe.",
                visual_type="general_intro",
                key_takeaway="Scientific inquiry models natural interactions through observation.",
                duration_target_seconds=6.0,
            ),
            Scene(
                scene_id=2,
                title="Core Mechanism",
                narration="At every level of physical reality, fundamental laws govern how systems transfer energy and reach equilibrium.",
                visual_type="general_mechanism",
                key_takeaway="Systems evolve toward energy minimization and stability.",
                duration_target_seconds=6.0,
            ),
            Scene(
                scene_id=3,
                title="Conclusion & Applications",
                narration="Understanding these underlying concepts allows scientists and engineers to predict outcomes and create new technologies.",
                visual_type="general_summary",
                key_takeaway="Theoretical principles enable practical technological application.",
                duration_target_seconds=6.0,
            ),
        ],
    ),
}


def get_template_script(topic: SupportedTopic) -> VideoScript:
    """Retrieve the high-fidelity curated script for a topic."""
    return TEMPLATES.get(topic, TEMPLATES[SupportedTopic.OTHER_STEM])

"""Concept classifier for learner queries."""

import re
from typing import List

from app.models.script import SupportedTopic


class ConceptClassifier:
    """Classifies natural language science queries into canonical STEM topics."""

    def __init__(self) -> None:
        # Ordered rules: more specific comparison rules first
        self.rules: List[tuple[SupportedTopic, list[re.Pattern]]] = [
            (
                SupportedTopic.IONIC_VS_COVALENT,
                [
                    re.compile(r"ionic.*(covalent|versus|vs|difference|compare)", re.IGNORECASE),
                    re.compile(r"difference.*(ionic|covalent)", re.IGNORECASE),
                    re.compile(r"covalent.*(versus|vs|ionic)", re.IGNORECASE),
                    re.compile(r"compare.*(ionic|covalent)", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.ACID_BASE_NEUTRALIZATION,
                [
                    re.compile(r"neutraliz(ation|e)", re.IGNORECASE),
                    re.compile(r"titration", re.IGNORECASE),
                    re.compile(r"acid.*base.*(reaction|combine)", re.IGNORECASE),
                    re.compile(r"h\+\s*\+\s*oh\-", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.PH_SCALE,
                [
                    re.compile(r"\bph\b", re.IGNORECASE),
                    re.compile(r"acid(ic|s)?\b", re.IGNORECASE),
                    re.compile(r"base(s)?|alkal(i|ine)", re.IGNORECASE),
                    re.compile(r"neutral.*scale", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.COVALENT_BONDS,
                [
                    re.compile(r"covalent\b", re.IGNORECASE),
                    re.compile(r"share.*electron", re.IGNORECASE),
                    re.compile(r"electron.*shar(ing|e)", re.IGNORECASE),
                    re.compile(r"why.*atoms.*form.*bond", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.PERIODIC_TRENDS,
                [
                    re.compile(r"periodic\s+table", re.IGNORECASE),
                    re.compile(r"periodic\s+trend", re.IGNORECASE),
                    re.compile(r"electronegativity", re.IGNORECASE),
                    re.compile(r"atomic\s+radius", re.IGNORECASE),
                    re.compile(r"ionization\s+energy", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.ATOMIC_STRUCTURE,
                [
                    re.compile(r"atomic\s+structure", re.IGNORECASE),
                    re.compile(r"structure\s+of\s+(an\s+)?atom", re.IGNORECASE),
                    re.compile(r"subatomic(\s+particles)?", re.IGNORECASE),
                    re.compile(r"electron\s+shell", re.IGNORECASE),
                    re.compile(r"bohr(\s+model)?", re.IGNORECASE),
                    re.compile(r"protons?.*neutrons?", re.IGNORECASE),
                    re.compile(r"atom.*(vs|versus|diff|and).*ion", re.IGNORECASE),
                    re.compile(r"ion.*(vs|versus|diff|and).*atom", re.IGNORECASE),
                    re.compile(r"\b(ion|ions|cation|cations|anion|anions)\b", re.IGNORECASE),
                    re.compile(r"\batoms?\b", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.EXO_VS_ENDOTHERMIC,
                [
                    re.compile(r"exothermic", re.IGNORECASE),
                    re.compile(r"endothermic", re.IGNORECASE),
                    re.compile(r"activation\s+energy", re.IGNORECASE),
                    re.compile(r"energy\s+profile", re.IGNORECASE),
                    re.compile(r"heat\s+of\s+reaction", re.IGNORECASE),
                ],
            ),
            (
                SupportedTopic.STATES_OF_MATTER,
                [
                    re.compile(r"states?\s+of\s+matter", re.IGNORECASE),
                    re.compile(r"phase\s+transition", re.IGNORECASE),
                    re.compile(r"phase\s+change", re.IGNORECASE),
                    re.compile(r"solid.*liquid.*gas", re.IGNORECASE),
                    re.compile(r"melting.*boiling", re.IGNORECASE),
                ],
            ),
        ]

    def classify(self, query: str) -> SupportedTopic:
        """Classify a user query string into a SupportedTopic."""
        cleaned_query = query.strip()
        for topic, patterns in self.rules:
            for pattern in patterns:
                if pattern.search(cleaned_query):
                    return topic

        return SupportedTopic.OTHER_STEM

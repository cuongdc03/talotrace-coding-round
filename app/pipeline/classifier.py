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
        ]

    def classify(self, query: str) -> SupportedTopic:
        """Classify a user query string into a SupportedTopic."""
        cleaned_query = query.strip()
        for topic, patterns in self.rules:
            for pattern in patterns:
                if pattern.search(cleaned_query):
                    return topic

        return SupportedTopic.OTHER_STEM

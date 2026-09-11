"""Unit tests for concept classifier."""

from app.models.script import SupportedTopic
from app.pipeline.classifier import ConceptClassifier


def test_classify_ph_scale_queries():
    classifier = ConceptClassifier()
    assert classifier.classify("How does the pH scale work?") == SupportedTopic.PH_SCALE
    assert classifier.classify("Explain acids, bases, and pH") == SupportedTopic.PH_SCALE
    assert classifier.classify("What is neutral on the pH scale?") == SupportedTopic.PH_SCALE


def test_classify_covalent_bonds_queries():
    classifier = ConceptClassifier()
    assert classifier.classify("Why do atoms form covalent bonds?") == SupportedTopic.COVALENT_BONDS
    assert (
        classifier.classify("Explain electron sharing in covalent bonding")
        == SupportedTopic.COVALENT_BONDS
    )


def test_classify_ionic_vs_covalent_queries():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("What is the difference between ionic and covalent bonding?")
        == SupportedTopic.IONIC_VS_COVALENT
    )
    assert (
        classifier.classify("Compare ionic vs covalent bonds") == SupportedTopic.IONIC_VS_COVALENT
    )
    assert (
        classifier.classify("Difference between ionic lattice and covalent molecules")
        == SupportedTopic.IONIC_VS_COVALENT
    )


def test_classify_unsupported_query():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("How do black holes form in astrophysics?") == SupportedTopic.OTHER_STEM
    )

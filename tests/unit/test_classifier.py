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


def test_classify_atomic_structure_queries():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("What is the structure of an atom and its subatomic particles?")
        == SupportedTopic.ATOMIC_STRUCTURE
    )
    assert (
        classifier.classify("Explain electron shells and Bohr model")
        == SupportedTopic.ATOMIC_STRUCTURE
    )


def test_classify_exo_vs_endothermic_queries():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("How do exothermic and endothermic reactions differ?")
        == SupportedTopic.EXO_VS_ENDOTHERMIC
    )
    assert (
        classifier.classify("Explain activation energy and energy profile curves")
        == SupportedTopic.EXO_VS_ENDOTHERMIC
    )


def test_classify_periodic_trends_queries():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("How does the periodic table organize chemical elements?")
        == SupportedTopic.PERIODIC_TRENDS
    )
    assert (
        classifier.classify("Explain electronegativity and atomic radius trends")
        == SupportedTopic.PERIODIC_TRENDS
    )


def test_classify_states_of_matter_queries():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("What are the states of matter and phase transitions?")
        == SupportedTopic.STATES_OF_MATTER
    )
    assert (
        classifier.classify("Explain solid, liquid, gas and melting boiling points")
        == SupportedTopic.STATES_OF_MATTER
    )


def test_classify_acid_base_neutralization_queries():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("What happens during an acid-base neutralization reaction?")
        == SupportedTopic.ACID_BASE_NEUTRALIZATION
    )
    assert (
        classifier.classify("Explain titration reaction between H+ and OH-")
        == SupportedTopic.ACID_BASE_NEUTRALIZATION
    )


def test_classify_unsupported_query():
    classifier = ConceptClassifier()
    assert (
        classifier.classify("How do black holes form in astrophysics?") == SupportedTopic.OTHER_STEM
    )

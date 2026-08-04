from pathlib import Path

from src.complexity import ComplexityEvaluator, load_glossary


def test_complexity_detects_terms():
    root = Path(__file__).resolve().parent.parent
    glossary = load_glossary(root / "data" / "term_glossary.csv")
    evaluator = ComplexityEvaluator(glossary)
    result = evaluator.evaluate("Artificial intelligence and data privacy are important in clinical diagnosis.")
    assert result.total_score > 0
    assert "artificial intelligence" in result.matched_terms
    assert "data privacy" in result.matched_terms


def test_complexity_long_sentence_higher_than_short():
    evaluator = ComplexityEvaluator([])
    short = evaluator.evaluate("Hello world.")
    long = evaluator.evaluate("Although the system is simple, it must preserve numbers, clauses, and context, which makes evaluation harder.")
    assert long.total_score > short.total_score

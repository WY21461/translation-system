from pathlib import Path

from src.complexity import load_glossary
from src.scoring import TranslationScorer


def test_scoring_penalizes_missing_number():
    scorer = TranslationScorer([])
    result = scorer.score("Revenue increased by 25% in 2024.", "收入增加。")
    assert result.score < 100
    assert any(d.rule == "数字/单位遗漏" for d in result.deductions)


def test_scoring_penalizes_missing_term():
    root = Path(__file__).resolve().parent.parent
    glossary = load_glossary(root / "data" / "term_glossary.csv")
    scorer = TranslationScorer(glossary)
    result = scorer.score("Artificial intelligence changes clinical diagnosis.", "AI 改变了诊断。")
    assert any(d.rule == "专业术语不一致" for d in result.deductions)


def test_scoring_good_translation_keeps_score_high():
    root = Path(__file__).resolve().parent.parent
    glossary = load_glossary(root / "data" / "term_glossary.csv")
    scorer = TranslationScorer(glossary)
    result = scorer.score("Artificial intelligence improves clinical diagnosis.", "人工智能提升了临床诊断。")
    assert result.score >= 80

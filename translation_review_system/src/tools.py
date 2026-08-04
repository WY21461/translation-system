from __future__ import annotations

from pathlib import Path

try:
    from langchain_core.tools import tool
except ImportError:  # 允许无 langchain-core 时仍能导入项目
    def tool(fn):  # type: ignore
        return fn

from src.complexity import ComplexityEvaluator, load_glossary
from src.scoring import TranslationScorer

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = load_glossary(ROOT / "data" / "term_glossary.csv")


@tool
def evaluate_text_complexity_tool(text: str) -> dict:
    """评估待翻译文本复杂度，返回句长、嵌套从句、术语密度和总分。"""
    evaluator = ComplexityEvaluator(GLOSSARY)
    return evaluator.evaluate(text).to_dict()


@tool
def score_translation_tool(source_text: str, translation: str) -> dict:
    """按可量化审校规则为译文打分，返回总分和扣分明细。"""
    scorer = TranslationScorer(GLOSSARY)
    return scorer.score(source_text, translation).to_dict()

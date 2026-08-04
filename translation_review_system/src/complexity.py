from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import re
from typing import Iterable, List


@dataclass(frozen=True)
class GlossaryEntry:
    source_term: str
    target_term: str
    domain: str = "general"


@dataclass(frozen=True)
class ComplexityResult:
    sentence_count: int
    avg_sentence_length: float
    sentence_length_score: int
    nested_clause_count: int
    nested_clause_score: int
    matched_terms: List[str]
    terminology_density: float
    terminology_score: int
    total_score: int
    level: str

    def to_dict(self) -> dict:
        return asdict(self)


class ComplexityEvaluator:
    """文本复杂度评估器。

    评分维度严格对应课题要求：
    1. 句子长度：平均句长越长，理解和翻译难度越高。
    2. 嵌套从句数：通过从属连词、关系代词、分号和括号等规则估计。
    3. 专业术语密度：术语表命中数 / 词数。

    该模块不依赖 LLM，评分可复现。
    """

    EN_CLAUSE_MARKERS = {
        "which", "that", "who", "whom", "whose", "where", "when", "while",
        "although", "because", "since", "if", "unless", "whereas", "therefore",
        "however", "provided", "whether", "once", "before", "after"
    }
    ZH_CLAUSE_MARKERS = ["因为", "虽然", "但是", "然而", "如果", "由于", "导致", "同时", "并且", "以及", "从而", "其中"]

    def __init__(self, glossary: Iterable[GlossaryEntry] | None = None):
        self.glossary = list(glossary or [])

    @staticmethod
    def split_sentences(text: str) -> List[str]:
        parts = re.split(r"(?<=[.!?。！？])\s+|[\n]+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def token_count(text: str) -> int:
        words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?|\d+(?:\.\d+)?|[\u4e00-\u9fff]", text)
        return max(len(words), 1)

    def sentence_length_score(self, avg_len: float) -> int:
        if avg_len <= 12:
            return 5
        if avg_len <= 20:
            return 15
        if avg_len <= 30:
            return 25
        if avg_len <= 45:
            return 34
        return 40

    def count_nested_clauses(self, text: str) -> int:
        lower = text.lower()
        english_count = sum(len(re.findall(rf"\b{re.escape(marker)}\b", lower)) for marker in self.EN_CLAUSE_MARKERS)
        chinese_count = sum(text.count(marker) for marker in self.ZH_CLAUSE_MARKERS)
        punctuation_count = len(re.findall(r"[;；:：]", text))
        bracket_count = len(re.findall(r"[()（）]", text)) // 2
        long_comma_chains = sum(1 for s in self.split_sentences(text) if s.count(",") + s.count("，") >= 3)
        return english_count + chinese_count + punctuation_count + bracket_count + long_comma_chains

    @staticmethod
    def nested_clause_score(count: int) -> int:
        return min(30, count * 5)

    def match_terms(self, text: str) -> List[str]:
        lower = text.lower()
        matched = []
        for entry in self.glossary:
            if entry.source_term.lower() in lower or entry.target_term in text:
                matched.append(entry.source_term)
        return sorted(set(matched))

    @staticmethod
    def terminology_score(density: float) -> int:
        # density 为每 100 个 token 中的术语数量。
        if density <= 1:
            return 3
        if density <= 3:
            return 10
        if density <= 6:
            return 20
        return 30

    @staticmethod
    def level(total: int) -> str:
        if total < 35:
            return "低复杂度"
        if total < 70:
            return "中复杂度"
        return "高复杂度"

    def evaluate(self, text: str) -> ComplexityResult:
        sentences = self.split_sentences(text)
        total_tokens = self.token_count(text)
        avg_len = total_tokens / max(len(sentences), 1)
        length_score = self.sentence_length_score(avg_len)
        clause_count = self.count_nested_clauses(text)
        clause_score = self.nested_clause_score(clause_count)
        terms = self.match_terms(text)
        density = len(terms) / total_tokens * 100
        term_score = self.terminology_score(density)
        total = min(100, length_score + clause_score + term_score)
        return ComplexityResult(
            sentence_count=max(len(sentences), 1),
            avg_sentence_length=round(avg_len, 2),
            sentence_length_score=length_score,
            nested_clause_count=clause_count,
            nested_clause_score=clause_score,
            matched_terms=terms,
            terminology_density=round(density, 2),
            terminology_score=term_score,
            total_score=total,
            level=self.level(total),
        )


def load_glossary(path: str | Path) -> List[GlossaryEntry]:
    path = Path(path)
    if not path.exists():
        return []
    entries: List[GlossaryEntry] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = (row.get("source_term") or "").strip()
            target = (row.get("target_term") or "").strip()
            if not source or not target:
                continue
            entries.append(GlossaryEntry(source, target, (row.get("domain") or "general").strip()))
    return entries

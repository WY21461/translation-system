from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable, List

from src.complexity import GlossaryEntry


@dataclass(frozen=True)
class Deduction:
    rule: str
    detail: str
    points: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ScoreResult:
    score: int
    deductions: List[Deduction]

    def to_dict(self) -> dict:
        return {"score": self.score, "deductions": [d.to_dict() for d in self.deductions]}


class TranslationScorer:
    """可复现的审校评分模型。

    总分 100 分，按规则扣分。至少包含 5 条量化规则，本系统实现 8 条：
    1. 数字/单位遗漏
    2. 专业术语不一致
    3. 源语残留过多
    4. 译文长度异常
    5. 括号/引号/标点结构错误
    6. 专有名词或缩写遗漏
    7. 中文译文常见重复/语病
    8. Markdown 结构丢失
    """

    UNIT_PATTERN = r"(?:%|kg|g|mg|km|m|cm|mm|GB|MB|TB|ms|s|min|h|USD|RMB|℃|°C)"

    def __init__(self, glossary: Iterable[GlossaryEntry] | None = None):
        self.glossary = list(glossary or [])

    @staticmethod
    def _numbers_and_units(text: str) -> List[str]:
        pattern = rf"\b\d+(?:\.\d+)?\s*{TranslationScorer.UNIT_PATTERN}?\b"
        return re.findall(pattern, text, flags=re.IGNORECASE)

    @staticmethod
    def _ascii_words(text: str) -> List[str]:
        return re.findall(r"\b[A-Za-z][A-Za-z-]{2,}\b", text)

    @staticmethod
    def _source_word_count(text: str) -> int:
        words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?|\d+(?:\.\d+)?", text)
        return max(len(words), 1)

    @staticmethod
    def _cjk_count(text: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fff]", text))

    @staticmethod
    def _capital_terms(text: str) -> List[str]:
        # 捕获 GDP、API、AI 这类缩写，以及 OpenAI / Transformer 这类专名。
        acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
        proper = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        return sorted(set(acronyms + proper))

    def _add(self, deductions: List[Deduction], rule: str, detail: str, points: int, max_points: int | None = None) -> None:
        if points <= 0:
            return
        if max_points is not None:
            points = min(points, max_points)
        deductions.append(Deduction(rule=rule, detail=detail, points=points))

    def score(self, source: str, translation: str, preserve_markdown: bool = False) -> ScoreResult:
        deductions: List[Deduction] = []

        # 规则 1：数字和单位遗漏，每处扣 8 分，最多扣 24 分。
        source_nums = self._numbers_and_units(source)
        missing_nums = [n for n in source_nums if n and n not in translation]
        self._add(
            deductions,
            "数字/单位遗漏",
            f"译文未保留：{', '.join(missing_nums)}" if missing_nums else "",
            8 * len(missing_nums),
            24,
        )

        # 规则 2：术语不一致，每处扣 6 分，最多扣 30 分。
        term_misses = []
        lower_source = source.lower()
        for entry in self.glossary:
            if entry.source_term.lower() in lower_source and entry.target_term not in translation:
                term_misses.append(f"{entry.source_term}->{entry.target_term}")
        self._add(
            deductions,
            "专业术语不一致",
            f"术语未按表翻译：{', '.join(term_misses)}" if term_misses else "",
            6 * len(term_misses),
            30,
        )

        # 规则 3：中文译文中源语残留过多。
        ascii_words = [w for w in self._ascii_words(translation) if w.lower() not in {"ai", "api", "gdp", "rmb", "usd"}]
        source_words = self._source_word_count(source)
        residual_ratio = len(ascii_words) / source_words
        if residual_ratio > 0.30:
            self._add(deductions, "源语残留过多", f"英文残留比例 {residual_ratio:.0%}，残留词示例：{', '.join(ascii_words[:8])}", 20)
        elif residual_ratio > 0.15:
            self._add(deductions, "源语残留偏多", f"英文残留比例 {residual_ratio:.0%}，残留词示例：{', '.join(ascii_words[:8])}", 10)

        # 规则 4：长度异常。英译中大致 1 个英文词对应 1~3 个中文字符，过短可能漏译，过长可能啰嗦。
        cjk_len = self._cjk_count(translation)
        length_ratio = cjk_len / source_words
        if length_ratio < 0.45:
            self._add(deductions, "译文长度异常", f"译文过短，中文字符/源词数 = {length_ratio:.2f}", 15)
        elif length_ratio > 4.2:
            self._add(deductions, "译文长度异常", f"译文过长，中文字符/源词数 = {length_ratio:.2f}", 8)

        # 规则 5：括号、引号结构错误。
        bracket_pairs = [("(", ")"), ("（", "）"), ("[", "]"), ("“", "”"), ('"', '"')]
        structure_points = 0
        structure_details = []
        for left, right in bracket_pairs:
            if left == right:
                if translation.count(left) % 2 != 0:
                    structure_points += 5
                    structure_details.append(f"{left} 数量不成对")
            elif translation.count(left) != translation.count(right):
                structure_points += 5
                structure_details.append(f"{left}{right} 不成对")
        self._add(deductions, "标点/括号结构错误", "; ".join(structure_details), structure_points, 15)

        # 规则 6：缩写或专有名词遗漏，每处扣 4 分，最多扣 12 分。
        missing_capitals = []
        for term in self._capital_terms(source):
            # 已在术语表中翻译的专名不强制保留英文原形。
            in_glossary = any(term.lower() == e.source_term.lower() or term.lower() in e.source_term.lower() for e in self.glossary)
            if not in_glossary and term not in translation:
                missing_capitals.append(term)
        self._add(
            deductions,
            "专有名词/缩写遗漏",
            f"可能遗漏：{', '.join(missing_capitals)}" if missing_capitals else "",
            4 * len(missing_capitals),
            12,
        )

        # 规则 7：中文常见重复或语病，每处扣 5 分，最多扣 15 分。
        awkward_patterns = ["的的", "是是", "了了", "，，", "。。", "、、", "并且并且", "由于因为"]
        awkward_hits = [p for p in awkward_patterns if p in translation]
        self._add(deductions, "重复/语病", f"发现疑似重复或语病：{', '.join(awkward_hits)}" if awkward_hits else "", 5 * len(awkward_hits), 15)

        # 规则 8：Markdown 结构保持，标题层级或列表丢失扣分。
        if preserve_markdown:
            src_headings = [line for line in source.splitlines() if re.match(r"^#{1,6}\s+", line)]
            tgt_headings = [line for line in translation.splitlines() if re.match(r"^#{1,6}\s+", line)]
            src_lists = [line for line in source.splitlines() if re.match(r"^\s*([-*+] |\d+\. )", line)]
            tgt_lists = [line for line in translation.splitlines() if re.match(r"^\s*([-*+] |\d+\. )", line)]
            missing_structure = 0
            details = []
            if len(tgt_headings) < len(src_headings):
                missing_structure += len(src_headings) - len(tgt_headings)
                details.append("标题层级数量减少")
            if len(tgt_lists) < len(src_lists):
                missing_structure += len(src_lists) - len(tgt_lists)
                details.append("列表结构数量减少")
            self._add(deductions, "文档结构丢失", "; ".join(details), 8 * missing_structure, 24)

        final_score = max(0, 100 - sum(d.points for d in deductions))
        return ScoreResult(score=final_score, deductions=deductions)

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

from src.scoring import ScoreResult


@dataclass(frozen=True)
class ReviewResult:
    fidelity_score: int
    expressiveness_score: int
    elegance_score: int
    overall_comment: str
    suggestions: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


class ReviewAgent:
    """审校子 Agent：输出信、达、雅评分和修改建议。

    这里的“信达雅”评分是基于规则扣分明细的可复现版本：
    - 信：关注术语、数字、遗漏、源语残留。
    - 达：关注长度异常、结构错误、表达是否完整。
    - 雅：关注重复、语病和正式程度。
    """

    def review(self, source: str, translation: str, score_result: ScoreResult) -> ReviewResult:
        deductions = score_result.deductions
        fidelity_penalty = sum(d.points for d in deductions if d.rule in {"数字/单位遗漏", "专业术语不一致", "源语残留过多", "源语残留偏多", "专有名词/缩写遗漏"})
        express_penalty = sum(d.points for d in deductions if d.rule in {"译文长度异常", "标点/括号结构错误", "文档结构丢失"})
        elegance_penalty = sum(d.points for d in deductions if d.rule in {"重复/语病"})

        fidelity = max(0, 100 - fidelity_penalty)
        expressiveness = max(0, 100 - express_penalty)
        elegance = max(0, 100 - elegance_penalty)
        suggestions = self._suggestions(score_result)
        if not suggestions:
            suggestions = ["译文整体较稳定，可人工微调用词风格。"]
        comment = self._comment(fidelity, expressiveness, elegance)
        return ReviewResult(fidelity, expressiveness, elegance, comment, suggestions)

    @staticmethod
    def _suggestions(score_result: ScoreResult) -> List[str]:
        suggestions = []
        for d in score_result.deductions:
            if d.rule == "数字/单位遗漏":
                suggestions.append("补回原文中的数字、百分比、金额或单位，避免关键信息丢失。")
            elif d.rule == "专业术语不一致":
                suggestions.append("按术语表统一专业词汇，保证同一术语前后一致。")
            elif d.rule in {"源语残留过多", "源语残留偏多"}:
                suggestions.append("检查译文中的英文残留，除固定缩写外应翻译成目标语言。")
            elif d.rule == "译文长度异常":
                suggestions.append("核对是否漏译或过度解释，调整译文长度到合理范围。")
            elif d.rule == "标点/括号结构错误":
                suggestions.append("修复括号、引号、列表等结构符号，保证可读性。")
            elif d.rule == "专有名词/缩写遗漏":
                suggestions.append("核对专有名词、机构名、缩写是否保留或采用约定译法。")
            elif d.rule == "重复/语病":
                suggestions.append("删除重复词，改写不自然表达，提高流畅度。")
            elif d.rule == "文档结构丢失":
                suggestions.append("批量文档翻译时保留标题层级、列表编号和代码块。")
        # 去重但保持顺序
        seen = set()
        unique = []
        for item in suggestions:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique

    @staticmethod
    def _comment(fidelity: int, expressiveness: int, elegance: int) -> str:
        avg = (fidelity + expressiveness + elegance) / 3
        if avg >= 90:
            return "信达雅整体表现优秀，适合作为推荐译文。"
        if avg >= 75:
            return "译文基本可靠，但仍需按扣分项做局部修订。"
        if avg >= 60:
            return "译文可读但问题较明显，建议人工复核后再使用。"
        return "译文质量较低，不建议直接采用。"

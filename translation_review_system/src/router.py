from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

from src.complexity import ComplexityResult


@dataclass(frozen=True)
class RouteDecision:
    level: str
    strategy: str
    call_models: List[str]
    use_review_agent: bool
    glossary_required: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def decide_route(result: ComplexityResult) -> RouteDecision:
    """根据复杂度做模型路由。

    为满足课题中“两个模型效果对比”的验收要求，系统在演示和评测模式下始终调用两个模型；
    路由的作用是调整提示词强度、是否强制术语表、是否启用审校子 Agent。
    """
    if result.total_score < 35:
        return RouteDecision(
            level="低复杂度",
            strategy="快速双译对比：模型 A 优先，模型 B 作为质量对照",
            call_models=["model_a", "model_b"],
            use_review_agent=True,
            glossary_required=False,
            reason="平均句长短、术语少，重点比较流畅度与基本准确性。",
        )
    if result.total_score < 70:
        return RouteDecision(
            level="中复杂度",
            strategy="标准双模型协作：两个模型都使用术语提示，审校 Agent 汇总建议",
            call_models=["model_a", "model_b"],
            use_review_agent=True,
            glossary_required=True,
            reason="句子结构或术语密度达到中等水平，需要术语约束和审校。",
        )
    return RouteDecision(
        level="高复杂度",
        strategy="专业文本双译审校：强制术语表，推荐分数更高的译文并给出修改建议",
        call_models=["model_a", "model_b"],
        use_review_agent=True,
        glossary_required=True,
        reason="长句、嵌套结构或专业术语密集，必须进行严格审校。",
    )

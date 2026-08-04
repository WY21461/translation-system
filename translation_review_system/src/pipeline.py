from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from src.complexity import ComplexityEvaluator, load_glossary
from src.config import AppConfig, load_config
from src.metrics import CallStatsMiddleware, MetricsStore
from src.reviewer_agent import ReviewAgent
from src.router import decide_route
from src.scoring import TranslationScorer
from src.translator import TextTranslator


class TranslationPipeline:
    def __init__(self, config: AppConfig | None = None, glossary_path: str | Path | None = None):
        self.config = config or load_config()
        root = Path(__file__).resolve().parent.parent
        self.glossary_path = Path(glossary_path) if glossary_path else root / "data" / "term_glossary.csv"
        self.glossary = load_glossary(self.glossary_path)
        self.metrics_store = MetricsStore()
        self.middleware = CallStatsMiddleware(self.metrics_store)
        self.evaluator = ComplexityEvaluator(self.glossary)
        self.scorer = TranslationScorer(self.glossary)
        self.reviewer = ReviewAgent()
        self.translator = TextTranslator(
            model_configs={"model_a": self.config.model_a, "model_b": self.config.model_b},
            mock_mode=self.config.mock_mode,
            middleware=self.middleware,
        )

    def run(self, text: str, source_lang: str | None = None, target_lang: str | None = None, preserve_markdown: bool = False) -> Dict[str, Any]:
        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError("输入文本不能为空。")
        source_lang = source_lang or self.config.source_lang
        target_lang = target_lang or self.config.target_lang

        complexity = self.evaluator.evaluate(clean_text)
        route = decide_route(complexity)
        candidates = self.translator.translate_many(
            model_keys=route.call_models,
            text=clean_text,
            source_lang=source_lang,
            target_lang=target_lang,
            glossary=self.glossary,
            glossary_required=route.glossary_required,
        )

        scored = []
        for candidate in candidates:
            score = self.scorer.score(clean_text, candidate.translation, preserve_markdown=preserve_markdown)
            review = self.reviewer.review(clean_text, candidate.translation, score)
            scored.append({
                "candidate": candidate.to_dict(),
                "score": score.to_dict(),
                "review": review.to_dict(),
            })

        best = max(scored, key=lambda item: (item["score"]["score"], item["review"]["fidelity_score"], -item["candidate"]["latency_seconds"]))

        return {
            "source_text": clean_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "complexity": complexity.to_dict(),
            "route": route.to_dict(),
            "translations": scored,
            "recommended": best,
            "metrics": self.metrics_store.summary(),
        }

    def reset_metrics(self) -> None:
        self.metrics_store.clear()

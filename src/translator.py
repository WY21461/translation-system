from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Iterable, List

from src.complexity import GlossaryEntry
from src.config import ModelConfig
from src.llm_client import build_client
from src.metrics import CallStatsMiddleware


@dataclass(frozen=True)
class TranslationCandidate:
    model_key: str
    model_name: str
    translation: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    estimated_cost: float

    def to_dict(self) -> dict:
        data = asdict(self)
        data["latency_seconds"] = round(self.latency_seconds, 3)
        data["estimated_cost"] = round(self.estimated_cost, 6)
        return data


class TextTranslator:
    def __init__(self, model_configs: dict[str, ModelConfig], mock_mode: bool, middleware: CallStatsMiddleware | None = None):
        self.model_configs = model_configs
        self.mock_mode = mock_mode
        self.middleware = middleware or CallStatsMiddleware()

    @staticmethod
    def _format_glossary(glossary: Iterable[GlossaryEntry], source_text: str, max_terms: int = 20) -> str:
        source_lower = source_text.lower()
        lines = [
            f"- {entry.source_term} => {entry.target_term}（{entry.domain}）"
            for entry in glossary
            if entry.source_term.lower() in source_lower
        ]
        return "\n".join(lines[:max_terms]) if lines else "无命中术语。"

    def build_prompt(self, text: str, source_lang: str, target_lang: str,
                     glossary: Iterable[GlossaryEntry], glossary_required: bool) -> tuple[str, str]:
        glossary_text = self._format_glossary(glossary, text)
        requirement = "必须严格使用术语表中的目标译法。" if glossary_required else "如术语表有命中，请优先采用表中译法。"
        system_prompt = (
            "你是专业翻译模型。请准确、自然地翻译文本；保留数字、单位、专有名词、Markdown结构；"
            "不要解释，不要输出额外说明，只输出译文。"
        )
        user_prompt = (
            f"源语言：{source_lang}\n"
            f"目标语言：{target_lang}\n"
            f"{requirement}\n\n"
            f"术语表：\n{glossary_text}\n\n"
            f"待翻译文本：\n{text}\n\n"
            f"译文："
        )
        return system_prompt, user_prompt

    def translate_one(self, model_key: str, text: str, source_lang: str, target_lang: str,
                      glossary: Iterable[GlossaryEntry], glossary_required: bool) -> TranslationCandidate:
        config = self.model_configs[model_key]
        client = build_client(config, self.mock_mode)
        system_prompt, user_prompt = self.build_prompt(text, source_lang, target_lang, glossary, glossary_required)

        def _call():
            return client.chat(system_prompt, user_prompt)

        translation, record = self.middleware.invoke(config, _call)
        return TranslationCandidate(
            model_key=model_key,
            model_name=config.name,
            translation=translation,
            latency_seconds=record.latency_seconds,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            estimated_cost=record.estimated_cost,
        )

    def translate_many(self, model_keys: List[str], text: str, source_lang: str, target_lang: str,
                       glossary: Iterable[GlossaryEntry], glossary_required: bool) -> List[TranslationCandidate]:
        """并行调用多个模型翻译同一文本，大幅加快响应速度。"""
        if len(model_keys) <= 1:
            return [self.translate_one(k, text, source_lang, target_lang, glossary, glossary_required) for k in model_keys]

        results: dict[str, TranslationCandidate] = {}
        with ThreadPoolExecutor(max_workers=len(model_keys)) as executor:
            futures = {
                executor.submit(self.translate_one, key, text, source_lang, target_lang, glossary, glossary_required): key
                for key in model_keys
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception:
                    # 单个模型失败不影响另一个
                    pass

        return [results[k] for k in model_keys if k in results]

from __future__ import annotations

from dataclasses import dataclass, asdict
import time
from typing import Callable, List, Tuple, Any

from src.config import ModelConfig


@dataclass(frozen=True)
class CallRecord:
    model_key: str
    model_name: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    estimated_cost: float

    def to_dict(self) -> dict:
        data = asdict(self)
        data["latency_seconds"] = round(self.latency_seconds, 3)
        data["estimated_cost"] = round(self.estimated_cost, 6)
        return data


class MetricsStore:
    def __init__(self) -> None:
        self.records: List[CallRecord] = []

    def add(self, record: CallRecord) -> None:
        self.records.append(record)

    def clear(self) -> None:
        self.records.clear()

    def all(self) -> List[CallRecord]:
        return list(self.records)

    def summary(self) -> dict:
        total_latency = sum(r.latency_seconds for r in self.records)
        total_cost = sum(r.estimated_cost for r in self.records)
        by_model: dict[str, dict] = {}
        for r in self.records:
            item = by_model.setdefault(r.model_key, {"model_name": r.model_name, "calls": 0, "latency_seconds": 0.0, "estimated_cost": 0.0})
            item["calls"] += 1
            item["latency_seconds"] += r.latency_seconds
            item["estimated_cost"] += r.estimated_cost
        for item in by_model.values():
            item["latency_seconds"] = round(item["latency_seconds"], 3)
            item["estimated_cost"] = round(item["estimated_cost"], 6)
        return {
            "total_calls": len(self.records),
            "total_latency_seconds": round(total_latency, 3),
            "total_estimated_cost": round(total_cost, 6),
            "by_model": by_model,
        }


class CallStatsMiddleware:
    """模型调用中间件：统一统计耗时、token 估算和成本。"""

    def __init__(self, store: MetricsStore | None = None) -> None:
        self.store = store or MetricsStore()

    @staticmethod
    def estimate_cost(model: ModelConfig, input_tokens: int, output_tokens: int) -> float:
        return input_tokens / 1000 * model.price_input_per_1k + output_tokens / 1000 * model.price_output_per_1k

    def invoke(self, model: ModelConfig, fn: Callable[[], Tuple[str, int, int]]) -> tuple[str, CallRecord]:
        start = time.perf_counter()
        text, input_tokens, output_tokens = fn()
        latency = time.perf_counter() - start
        record = CallRecord(
            model_key=model.key,
            model_name=model.name,
            latency_seconds=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=self.estimate_cost(model, input_tokens, output_tokens),
        )
        self.store.add(record)
        return text, record
